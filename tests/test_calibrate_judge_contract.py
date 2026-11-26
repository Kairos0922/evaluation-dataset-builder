import json
import unittest
from pathlib import Path

from calibrate_judge import build_contract_report
from scripts.validate_judge_calibration import validate_report


ROOT = Path(__file__).resolve().parents[1]


class JudgeCalibrationRunnerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite_path = ROOT / "tests" / "judge-calibration-cases.json"
        cls.fixture = json.loads(cls.suite_path.read_text(encoding="utf-8"))

    def _results(self):
        return [
            {
                "case_id": case["id"],
                "gold_status": case["expected_status"],
                "judge_status": case["expected_status"],
                "evidence_validated": True,
                "output_sha256": "a" * 64,
                "gold_evidence_ref": "synthetic-fixture://" + case["id"],
            }
            for case in self.fixture["cases"]
        ]

    def test_runner_emits_schema_valid_synthetic_not_validated_report(self):
        report = build_contract_report(
            self.fixture, self._results(),
            base_url="https://judge.example/v1",
            model="judge-model",
            candidate_sha="1" * 40,
            run_id="12345",
        )
        self.assertEqual(report["calibration_kind"], "synthetic_smoke")
        self.assertEqual(report["status"], "NOT_VALIDATED")
        self.assertFalse(report["dataset"]["independent_gold"])
        self.assertEqual(
            validate_report(report, self.suite_path), []
        )

    def test_runner_recomputes_false_pass_false_fail_and_abstention(self):
        results = self._results()
        results[0]["gold_status"] = "FAIL"
        results[0]["judge_status"] = "PASS"
        results[1]["gold_status"] = "PASS"
        results[1]["judge_status"] = "FAIL"
        results[2]["gold_status"] = "UNKNOWN"
        results[2]["judge_status"] = "UNKNOWN"
        report = build_contract_report(
            self.fixture, results,
            base_url="https://judge.example/v1",
            model="judge-model",
            candidate_sha="2" * 40,
        )
        self.assertEqual(report["summary"]["false_passes"], 1)
        self.assertEqual(report["summary"]["false_fails"], 1)
        self.assertEqual(report["summary"]["abstentions"], 1)
        self.assertEqual(report["summary"]["adjudicable_count"], len(results) - 1)
        self.assertEqual(validate_report(report, self.suite_path), [])

    def test_runner_records_hashes_and_execution_identity(self):
        report = build_contract_report(
            self.fixture, self._results(),
            base_url="https://judge.example/v1",
            model="judge-model",
            candidate_sha="3" * 40,
            run_id="workflow-987",
        )
        self.assertEqual(len(report["dataset"]["suite_sha256"]), 64)
        self.assertEqual(len(report["judge"]["prompt_sha256"]), 64)
        self.assertEqual(len(report["judge"]["implementation_sha256"]), 64)
        self.assertEqual(report["protocol"]["commit_sha"], "3" * 40)
        self.assertEqual(report["protocol"]["run_id"], "workflow-987")


if __name__ == "__main__":
    unittest.main()
