import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.compare_round4_blind_reviews import (
    DEFAULT_SCHEMA,
    EXPECTED_CASE_IDS,
    EXPECTED_DATASET_SHA256,
    EXPECTED_LABELS,
    compare_reviews,
    load_crosswalk,
    validate_submission,
)

SCHEMA = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))
PACKET_HASHES = {
    "A": "0dff42e51bba9e85fc12df9f1ae170a6baec28793ad3ca3496e07a6abe94180f",
    "B": "205bd9bda8579c19c127cb1279e3f8378518fcc02f0cf84abbe33a7a8f733d92",
}


def make_item(label: str, *, freeze_decision: str = "YES", assertion_id: str = "A-01") -> dict:
    return {
        "blind_label": label,
        "construct_relevance": "ESSENTIAL",
        "clarity": 4,
        "executability": 4,
        "ambiguity_notes": "No material ambiguity identified.",
        "assertions": [{
            "assertion_id": assertion_id,
            "normative_ref": "business-rules.md#BR-01",
            "observation_method": ["api_state", "dom"],
            "pass_condition": "Observed state matches the normative rule.",
            "fail_condition": "Observed state contradicts the normative rule.",
            "unknown_condition": "Independent state evidence is unavailable.",
        }],
        "application_skill_separation": "Application compliance and Skill reporting are judged independently.",
        "max_write_actions": 0,
        "max_script_runs": 1,
        "prohibited_side_effects": ["No task mutation"],
        "freeze_decision": freeze_decision,
        "rationale": "The public rule and independent evidence method support this Oracle design.",
        "evidence_refs": ["business-rules.md#BR-01", "runtime-and-tool-contracts.md#read-only"],
    }


def make_submission(slot: str, reviewer_id: str | None = None) -> dict:
    return {
        "schema_version": "1.0.0",
        "reviewer_slot": slot,
        "reviewer_id": reviewer_id or f"RV-reviewer-{slot}",
        "submitted_at": "2026-11-25T12:00:00Z",
        "packet_sha256": PACKET_HASHES[slot],
        "dataset_sha256": EXPECTED_DATASET_SHA256,
        "protocol_version": "Round4 Oracle independent review v1.0",
        "items": [make_item(label) for label in sorted(EXPECTED_LABELS[slot])],
        "overall_notes": "All twelve tasks were reviewed independently against the public normative assets.",
    }


class Round4BlindReviewComparisonTests(unittest.TestCase):
    def setUp(self):
        self.a = make_submission("A")
        self.b = make_submission("B")
        self.temp = tempfile.TemporaryDirectory()
        self.crosswalk_path = Path(self.temp.name) / "crosswalk.csv"
        with self.crosswalk_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "reviewer_slot", "blind_label", "case_id", "case_sha256"
            ])
            writer.writeheader()
            for slot in ("A", "B"):
                for index, case_id in enumerate(sorted(EXPECTED_CASE_IDS), start=1):
                    writer.writerow({
                        "reviewer_slot": slot,
                        "blind_label": f"R{slot}-ITEM-{index:02d}",
                        "case_id": case_id,
                        "case_sha256": "a" * 64,
                    })
        self.crosswalk = load_crosswalk(self.crosswalk_path)

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_two_complete_blind_submissions(self):
        self.assertEqual(validate_submission(self.a, slot="A", schema=SCHEMA), [])
        self.assertEqual(validate_submission(self.b, slot="B", schema=SCHEMA), [])

    def test_rejects_duplicate_or_missing_blind_labels(self):
        self.a["items"][-1]["blind_label"] = self.a["items"][0]["blind_label"]
        errors = validate_submission(self.a, slot="A", schema=SCHEMA)
        self.assertTrue(any("each of the 12 packet labels exactly once" in error for error in errors))

    def test_comparison_reports_differences_without_adjudicating(self):
        self.b["items"][0]["freeze_decision"] = "NEEDS_REVISION"
        self.b["items"][0]["assertions"][0]["assertion_id"] = "B-CHANGED"
        report = compare_reviews(self.a, self.b, self.crosswalk)
        self.assertEqual(report["status"], "REQUIRES_HUMAN_ADJUDICATION")
        self.assertEqual(report["case_count"], 12)
        self.assertGreaterEqual(report["cases_with_differences"], 1)
        self.assertTrue(all(case["human_adjudication_required"] for case in report["cases"]))
        self.assertIn("does not resolve disagreements", report["guardrail"])

    def test_crosswalk_must_map_all_cases_once_per_reviewer(self):
        rows = self.crosswalk_path.read_text(encoding="utf-8").splitlines()
        self.crosswalk_path.write_text("\n".join(rows[:-1]) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "crosswalk B labels"):
            load_crosswalk(self.crosswalk_path)

    def test_crosswalk_rejects_duplicate_case_mapping(self):
        rows = list(csv.DictReader(self.crosswalk_path.open(encoding="utf-8")))
        rows[-1]["case_id"] = rows[-2]["case_id"]
        with self.crosswalk_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "exact 12 target cases"):
            load_crosswalk(self.crosswalk_path)

    def test_same_reviewer_identity_is_not_independent(self):
        self.b["reviewer_id"] = self.a["reviewer_id"]
        self.assertEqual(self.a["reviewer_id"], self.b["reviewer_id"])


if __name__ == "__main__":
    unittest.main()
