import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.import_judge_calibration_evidence import build_report


def make_fixture(directory: Path, judge_type="llm"):
    suite = {"suite_id": "heldout-suite-v1", "cases": [{"id": "JC01"}, {"id": "JC02"}, {"id": "JC03"}]}
    suite_path = directory / "suite.json"
    suite_raw = json.dumps(suite, separators=(",", ":")).encode()
    suite_path.write_bytes(suite_raw)
    observations = {
        "schema_version": "0.0.2",
        "calibration_kind": "independent_empirical",
        "dataset": {
            "suite_id": suite["suite_id"], "suite_sha256": hashlib.sha256(suite_raw).hexdigest(),
            "case_ids": ["JC01", "JC02", "JC03"], "label_source": "adjudicated_oracle",
            "independent_gold": True, "split_id": "heldout-v1", "held_out": True
        },
        "judge": {
            "judge_type": judge_type, "provider": "manual-review" if judge_type == "human" else "independent-provider",
            "endpoint_origin": "offline://manual-review" if judge_type == "human" else "https://judge.example",
            "model_id": "human-panel-v1" if judge_type == "human" else "judge-model-v1",
            "model_revision": None, "prompt_sha256": "a" * 64, "implementation_sha256": "b" * 64,
            "separate_from_subject": True
        },
        "protocol": {
            "blinded": True, "independent_review": True, "repeats_per_case": 1,
            "abstention_policy": "Insufficient evidence => UNKNOWN", "run_id": "run-123", "commit_sha": "c" * 40
        },
        "observations": [
            {"case_id":"JC01","gold_status":"PASS","judge_status":"PASS","evidence_validated":True,"output_sha256":"d"*64,"gold_evidence_ref":"oracle://JC01","judge_evidence_ref":"judge://JC01","adjudicator_id":"arbiter-anon-01"},
            {"case_id":"JC02","gold_status":"FAIL","judge_status":"PASS","evidence_validated":True,"output_sha256":"e"*64,"gold_evidence_ref":"oracle://JC02","judge_evidence_ref":"judge://JC02","adjudicator_id":"arbiter-anon-01"},
            {"case_id":"JC03","gold_status":"UNKNOWN","judge_status":"UNKNOWN","evidence_validated":True,"output_sha256":"f"*64,"gold_evidence_ref":"oracle://JC03","judge_evidence_ref":"judge://JC03","adjudicator_id":"arbiter-anon-01"}
        ]
    }
    raw = json.dumps(observations, sort_keys=True, separators=(",", ":")).encode()
    return suite_path, observations, raw


class JudgeCalibrationImporterTests(unittest.TestCase):
    def test_imports_manual_and_llm_empirical_observations_as_partial(self):
        for judge_type in ("human", "llm"):
            with self.subTest(judge_type=judge_type), tempfile.TemporaryDirectory() as tmp:
                suite_path, source, raw = make_fixture(Path(tmp), judge_type)
                report = build_report(source, suite_path, raw)
                self.assertEqual(report["status"], "PARTIAL")
                self.assertEqual(report["judge"]["judge_type"], judge_type)
                self.assertEqual(report["summary"]["case_count"], 3)
                self.assertEqual(report["summary"]["observation_count"], 3)
                self.assertEqual(report["summary"]["adjudicable_count"], 2)
                self.assertEqual(report["summary"]["false_passes"], 1)
                self.assertEqual(report["summary"]["abstentions"], 1)
                self.assertEqual(report["summary"]["accuracy"], 0.5)
                self.assertEqual(report["source_observations_sha256"], hashlib.sha256(raw).hexdigest())

    def test_rejects_malformed_nested_suite_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite_path, source, raw = make_fixture(Path(tmp))
            malformed_suites = [
                [],
                {"suite_id": "heldout-suite-v1", "cases": None},
                {"suite_id": "heldout-suite-v1", "cases": [{"id": "JC01"}, "JC02", {"id": ""}]},
            ]
            for suite in malformed_suites:
                with self.subTest(suite=suite):
                    suite_raw = json.dumps(suite).encode()
                    suite_path.write_bytes(suite_raw)
                    source["dataset"]["suite_sha256"] = hashlib.sha256(suite_raw).hexdigest()
                    with self.assertRaisesRegex(ValueError, "frozen suite"):
                        build_report(source, suite_path, raw)

    def test_rejects_suite_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite_path, source, raw = make_fixture(Path(tmp))
            source["dataset"]["suite_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "does not match frozen suite bytes"):
                build_report(source, suite_path, raw)

    def test_rejects_missing_or_duplicate_case_observations(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite_path, source, raw = make_fixture(Path(tmp))
            source["observations"].pop()
            with self.assertRaisesRegex(ValueError, "exactly one row per frozen suite"):
                build_report(source, suite_path, raw)
            source["observations"].append(dict(source["observations"][0]))
            with self.assertRaisesRegex(ValueError, "exactly one row per frozen suite"):
                build_report(source, suite_path, raw)

    def test_supports_preregistered_repeated_judge_runs_per_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite_path, source, _ = make_fixture(Path(tmp))
            source["protocol"]["repeats_per_case"] = 2
            repeated = []
            for item in source["observations"]:
                first = dict(item, repeat_index=1)
                second = dict(item, repeat_index=2)
                if item["case_id"] == "JC01":
                    second["judge_status"] = "FAIL"
                repeated.extend([first, second])
            source["observations"] = repeated
            raw = json.dumps(source, sort_keys=True, separators=(",", ":")).encode()
            report = build_report(source, suite_path, raw)
            self.assertEqual(len(report["results"]), 6)
            self.assertEqual(report["summary"]["case_count"], 3)
            self.assertEqual(report["summary"]["observation_count"], 6)
            self.assertEqual(report["summary"]["adjudicable_count"], 2)
            self.assertEqual(report["summary"]["false_passes"], 1)
            self.assertEqual(report["summary"]["false_fails"], 1)
            self.assertEqual(report["summary"]["abstentions"], 2)
            self.assertEqual(report["summary"]["accuracy"], 0.0)
            self.assertEqual(report["summary"]["repeat_disagreement_cases"], 1)
            self.assertAlmostEqual(report["summary"]["repeat_agreement_rate"], 2 / 3)

    def test_never_imports_empirical_gold_from_synthetic_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite_path, source, raw = make_fixture(Path(tmp))
            source["dataset"]["label_source"] = "synthetic_fixture"
            with self.assertRaisesRegex(ValueError, "cannot use Builder/synthetic labels as Gold"):
                build_report(source, suite_path, raw)

    def test_requires_case_level_evidence_and_adjudicator_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite_path, source, raw = make_fixture(Path(tmp))
            source["observations"][0]["judge_evidence_ref"] = None
            source["observations"][0]["adjudicator_id"] = None
            raw = json.dumps(source, sort_keys=True, separators=(",", ":")).encode()
            with self.assertRaisesRegex(ValueError, "lacks Judge evidence reference|lacks anonymous adjudicator_id"):
                build_report(source, suite_path, raw)


if __name__ == "__main__":
    unittest.main()


class StrictJsonInputTests(unittest.TestCase):
    def test_observation_loader_rejects_non_standard_numeric_constants(self):
        from scripts.import_judge_calibration_evidence import load_json
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observations.json"
            path.write_text('{"score":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid JSON numeric constant"):
                load_json(path)
