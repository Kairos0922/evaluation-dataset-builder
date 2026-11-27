import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.build_round4_blind_review_packets import (
    TARGET_CASE_IDS,
    build_packets,
)


class Round4BlindReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dataset = self.root / "cases.jsonl"
        self.assets = self.root / "assets"
        self.output = self.root / "out"
        self.assets.mkdir()
        items = []
        all_ids = sorted(TARGET_CASE_IDS | {"WB-02", "WB-10", "WB-12"})
        for case_id in all_ids:
            items.append({
                "case_id": case_id,
                "user_input": f"Please inspect the application for {case_id} task.",
                "title": f"BUILDER_SECRET_TITLE_{case_id}",
                "objective": "BUILDER_SECRET_OBJECTIVE",
                "expected_behavior": ["BUILDER_SECRET_EXPECTATION"],
                "forbidden_behavior": ["BUILDER_SECRET_FORBIDDEN"],
                "reference_outcome": {"gold": "BUILDER_SECRET_GOLD"},
                "grading": {"criteria": ["BUILDER_SECRET_GRADING"]},
                "observable_assertions": ["BUILDER_SECRET_ASSERTION"],
                "trace_expectations": ["BUILDER_SECRET_TRACE"],
                "quality_status": "BUILDER_SECRET_STATUS",
            })
        self.dataset.write_text(
            "\n".join(json.dumps(item) for item in items) + "\n",
            encoding="utf-8",
        )
        for name in (
            "business-rules.md",
            "application-overview.md",
            "capability-description.md",
            "runtime-and-tool-contracts.md",
        ):
            (self.assets / name).write_text(f"# Public source: {name}\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_builds_two_distinct_reviewer_archives_and_private_crosswalk(self):
        result = build_packets(
            self.dataset,
            self.assets,
            self.output,
            expected_dataset_sha256=None,
            seed=17,
        )
        self.assertEqual(len(result["reviewer_archives"]), 2)
        self.assertEqual(result["reviewer_archives"][0]["case_count"], 12)
        self.assertEqual(result["reviewer_archives"][1]["case_count"], 12)
        self.assertTrue(Path(result["crosswalk_archive"]["path"]).is_file())

        reviewer_text = []
        for item in result["reviewer_archives"]:
            archive_path = Path(item["path"])
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
                self.assertEqual(sum(name.endswith("/task.md") for name in names), 12)
                self.assertEqual(sum(name.endswith("/review-sheet.md") for name in names), 12)
                self.assertFalse(any("crosswalk" in name for name in names))
                payload = b"\n".join(archive.read(name) for name in names if name.endswith(".md"))
                text = payload.decode("utf-8")
                reviewer_text.append(text)
                for secret in (
                    "BUILDER_SECRET_TITLE",
                    "BUILDER_SECRET_OBJECTIVE",
                    "BUILDER_SECRET_EXPECTATION",
                    "BUILDER_SECRET_FORBIDDEN",
                    "BUILDER_SECRET_GOLD",
                    "BUILDER_SECRET_GRADING",
                    "BUILDER_SECRET_ASSERTION",
                    "BUILDER_SECRET_TRACE",
                    "BUILDER_SECRET_STATUS",
                ):
                    self.assertNotIn(secret, text)
                for asset in (
                    "business-rules.md",
                    "application-overview.md",
                    "capability-description.md",
                    "runtime-and-tool-contracts.md",
                ):
                    self.assertTrue(any(name.endswith("/" + asset) for name in names))

        with zipfile.ZipFile(result["crosswalk_archive"]["path"]) as archive:
            crosswalk = archive.read("coordinator/crosswalk.csv").decode("utf-8")
            self.assertIn("WB-01", crosswalk)
            self.assertIn("WB-15", crosswalk)
        self.assertNotEqual(reviewer_text[0], reviewer_text[1])

    def test_rejects_wrong_frozen_dataset_hash(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            build_packets(
                self.dataset,
                self.assets,
                self.output,
                expected_dataset_sha256="0" * 64,
            )

    def test_rejects_missing_public_source_asset(self):
        (self.assets / "runtime-and-tool-contracts.md").unlink()
        with self.assertRaisesRegex(ValueError, "missing public assets"):
            build_packets(
                self.dataset,
                self.assets,
                self.output,
                expected_dataset_sha256=None,
            )


class StrictJsonInputTests(unittest.TestCase):
    def test_dataset_jsonl_rejects_nan(self):
        from scripts.build_round4_blind_review_packets import load_dataset
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.jsonl"
            path.write_text('{"case_id":"WB-01","score":NaN}\\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid dataset JSONL"):
                load_dataset(path)


if __name__ == "__main__":
    unittest.main()
