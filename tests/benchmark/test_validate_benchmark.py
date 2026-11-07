"""Benchmark 契约、引用完整性和统计单位的离线回归测试。"""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("validate_benchmark", ROOT / "tests/benchmark/validate_benchmark.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
FIXTURE = json.loads((ROOT / "tests/benchmark/fixtures/refund-valid.json").read_text(encoding="utf-8"))


class BenchmarkValidationTests(unittest.TestCase):
    def setUp(self):
        self.package = copy.deepcopy(FIXTURE)

    def test_valid_refund_package_passes(self):
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["statistics"]["defect_instance_count"], 1)
        self.assertEqual(result["statistics"]["detection_rate_any_run"], 1.0)
        self.assertEqual(result["statistics"]["detection_rate_all_runs"], 1.0)

    def test_n01_unknown_capability_reference_fails(self):
        self.package["cases"][0]["capability_keys"] = ["CAP-DOES-NOT-EXIST"]
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any("UNRESOLVED_REFERENCE:case:CASE-001:capability" in e for e in result["errors"]))

    def test_n02_coverage_tag_without_assertion_fails(self):
        self.package["cases"][0]["grading"]["criteria"][0]["coverage_item_refs"] = []
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("COVERAGE_WITHOUT_ASSERTION:CASE-001:COV-001") for e in result["errors"]))

    def test_n03_assertion_without_evidence_fails_schema(self):
        self.package["cases"][0]["grading"]["criteria"][0]["evidence_required"] = []
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any("CASE_SCHEMA:cases[0]" in e and "evidence_required" in e for e in result["errors"]))

    def test_n04_failed_injection_is_not_counted_as_detected(self):
        experiment = self.package["runs"][0]["experiments"][0]
        experiment["injection_status"], experiment["detection_status"] = "FAILED", "DETECTED"
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("INVALID_DETECTION_DENOMINATOR") for e in result["errors"]))
        self.assertEqual(result["statistics"]["defect_instance_count"], 0)
        self.assertIsNone(result["statistics"]["detection_rate_any_run"])
        self.assertIsNone(result["statistics"]["detection_rate_all_runs"])

    def test_n05_failed_control_blocks_valid_detection_claim(self):
        self.package["runs"][0]["experiments"][0]["control_status"] = "FAIL"
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("CONTROL_EXPERIMENT_FAILED") for e in result["errors"]))
        self.assertEqual(result["statistics"]["detected_defect_instance_count"], 0)

    def test_n06_repeated_runs_do_not_inflate_defect_instance_count(self):
        repeated = copy.deepcopy(self.package["runs"][0])
        repeated["run_id"] = "RUN-002"
        repeated["experiments"][0]["execution_run_ids"] = ["EXEC-002"]
        self.package["runs"].append(repeated)
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["statistics"]["run_count"], 2)
        self.assertEqual(result["statistics"]["experiment_observation_count"], 2)
        self.assertEqual(result["statistics"]["defect_instance_count"], 1)
        self.assertEqual(result["statistics"]["detection_rate_any_run"], 1.0)
        self.assertEqual(result["statistics"]["detection_rate_all_runs"], 1.0)

    def test_repeated_runs_report_pass_at_k_and_pass_all_runs_separately(self):
        repeated = copy.deepcopy(self.package["runs"][0])
        repeated["run_id"] = "RUN-002"
        repeated["experiments"][0]["detection_status"] = "MISSED"
        repeated["experiments"][0]["execution_run_ids"] = ["EXEC-002"]
        self.package["runs"].append(repeated)
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["statistics"]["defect_instance_count"], 1)
        self.assertEqual(result["statistics"]["detection_rate_any_run"], 1.0)
        self.assertEqual(result["statistics"]["detection_rate_all_runs"], 0.0)

    def test_n07_conflicted_ground_truth_cannot_be_approved(self):
        self.package["ground_truth"]["adjudication"]["status"] = "CONFLICTED"
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("UNRESOLVED_RULE_CONFLICT") for e in result["errors"]))

    def test_n08_semantically_invalid_coverage_is_rejected(self):
        self.package["coverage_validations"][0]["status"] = "INVALID"
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("INVALID_COVERAGE_CLAIM") for e in result["errors"]))

    def test_missing_independent_coverage_review_is_inconclusive(self):
        self.package["coverage_validations"] = []
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertTrue(any(e.startswith("INCONCLUSIVE:COVERAGE_VALIDATION_MISSING") for e in result["errors"]))

    def test_valid_coverage_requires_independent_evidence(self):
        self.package["coverage_validations"][0]["evidence_refs"] = []
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any("MISSING_COVERAGE_EVIDENCE" in e or "coverage_validation[0]" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
