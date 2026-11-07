"""Benchmark 契约、覆盖全集、多数据集归属和统计口径的离线回归测试。"""
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
        self.assertEqual(result["statistics"]["observation_detection_rate"], 1.0)
        self.assertEqual(result["statistics"]["instance_detection_any_rate"], 1.0)
        self.assertEqual(result["statistics"]["control_false_positive_rate"], 0.0)

    def test_unknown_capability_reference_fails(self):
        self.package["cases"][0]["capability_keys"] = ["CAP-DOES-NOT-EXIST"]
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any("UNRESOLVED_REFERENCE:case:CASE-001:capability" in e for e in result["errors"]))

    def test_coverage_tag_without_assertion_fails(self):
        self.package["cases"][0]["grading"]["criteria"][0]["coverage_item_refs"] = []
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("COVERAGE_ASSERTION_MISMATCH:COV-001:ASSERT-001") for e in result["errors"]))

    def test_coverage_validation_without_matching_case_tag_fails(self):
        self.package["cases"][0]["coverage_tags"] = []
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("COVERAGE_VALIDATION_WITHOUT_CASE_TAG:COV-001:CASE-001") for e in result["errors"]))

    def test_every_ground_truth_coverage_requirement_needs_disposition(self):
        self.package["ground_truth"]["coverage_requirements"].append({
            "coverage_item_id": "COV-002", "target_refs": ["CAP-001"],
            "description": "验证另一个能力点", "source_refs": ["SRC-001"],
            "criticality": "high", "dataset_refs": ["DS-REFUND-001"]
        })
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertTrue(any(e.startswith("INCONCLUSIVE:COVERAGE_DISPOSITION_MISSING:DS-REFUND-001:COV-002") for e in result["errors"]))

    def test_not_applicable_is_an_explicit_disposition(self):
        self.package["ground_truth"]["coverage_requirements"][0]["dataset_refs"] = ["DS-REFUND-001"]
        self.package["ground_truth"]["coverage_requirements"].append({
            "coverage_item_id": "COV-002", "target_refs": ["CAP-001"],
            "description": "验证保留的能力点", "source_refs": ["SRC-001"],
            "criticality": "medium", "dataset_refs": ["DS-REFUND-001"]
        })
        self.package["cases"][0]["coverage_tags"] = [{
            "dimension": "capability", "value": "retained", "coverage_item_id": "COV-002"
        }]
        self.package["cases"][0]["grading"]["criteria"][0]["coverage_item_refs"] = ["COV-002"]
        record = self.package["coverage_validations"][0]
        record["status"] = "NOT_APPLICABLE"
        record.pop("case_ref")
        record.pop("assertion_refs")
        record.pop("evidence_refs")
        record["rationale"] = "该数据集的范围不包含此项能力。"
        self.package["coverage_validations"].append({
            "coverage_item_ref": "COV-002", "dataset_ref": "DS-REFUND-001",
            "case_ref": "CASE-001", "assertion_refs": ["ASSERT-001"],
            "status": "VALID", "validation_method": "expert_review",
            "evidence_refs": ["REVIEW-EVIDENCE-002"], "reviewer": "reviewer-002"
        })
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "PASS", result["errors"])

    def test_conflicting_coverage_dispositions_fail(self):
        record = copy.deepcopy(self.package["coverage_validations"][0])
        record["status"] = "INVALID"
        record["rationale"] = "复核发现断言并未测量该能力。"
        self.package["coverage_validations"].append(record)
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any("CONFLICTING_COVERAGE_DISPOSITION" in e for e in result["errors"]))

    def test_duplicate_ground_truth_source_id_fails(self):
        self.package["ground_truth"]["sources"].append(copy.deepcopy(self.package["ground_truth"]["sources"][0]))
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("DUPLICATE_ID:source:SRC-001") for e in result["errors"]))

    def test_approved_ground_truth_rejects_provisional_rule(self):
        self.package["ground_truth"]["rules"][0]["status"] = "PROVISIONAL"
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("UNCONFIRMED_RULE_IN_APPROVED_GROUND_TRUTH:RULE-001") for e in result["errors"]))

    def test_failed_injection_is_not_counted_as_detected(self):
        experiment = self.package["runs"][0]["experiments"][0]
        experiment["injection_status"], experiment["detection_status"] = "FAILED", "DETECTED"
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("INVALID_DETECTION_DENOMINATOR") for e in result["errors"]))
        self.assertEqual(result["statistics"]["defect_instance_count"], 0)
        self.assertIsNone(result["statistics"]["instance_detection_any_rate"])

    def test_control_pass_without_independent_evidence_is_rejected(self):
        experiment = self.package["runs"][0]["experiments"][0]
        experiment["control_execution_run_ids"] = []
        experiment["control_evidence_refs"] = []
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any("MISSING_CONTROL_EXECUTION_EVIDENCE" in e or "control_execution_run_ids" in e for e in result["errors"]))
        self.assertEqual(result["statistics"]["defect_instance_count"], 0)

    def test_variable_repeat_counts_are_reported_without_calling_them_pass_at_k(self):
        second_instance = copy.deepcopy(self.package["defect_instances"][0])
        second_instance["defect_instance_id"] = "DEFECT-INSTANCE-002"
        self.package["defect_instances"].append(second_instance)
        repeated = copy.deepcopy(self.package["runs"][0])
        repeated["run_id"] = "RUN-002"
        repeated["experiments"][0]["detection_status"] = "MISSED"
        repeated["experiments"][0]["execution_run_ids"] = ["EXEC-002"]
        repeated["experiments"][0]["control_execution_run_ids"] = ["CTRL-EXEC-002"]
        repeated["experiments"][0]["control_evidence_refs"] = ["CTRL-TRACE-002"]
        second = copy.deepcopy(repeated["experiments"][0])
        second["defect_instance_ref"] = "DEFECT-INSTANCE-002"
        second["detection_status"] = "DETECTED"
        second["execution_run_ids"] = ["EXEC-003"]
        second["control_execution_run_ids"] = ["CTRL-EXEC-003"]
        second["control_evidence_refs"] = ["CTRL-TRACE-003"]
        repeated["experiments"].append(second)
        self.package["runs"].append(repeated)
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "PASS", result["errors"])
        stats = result["statistics"]
        self.assertEqual(stats["valid_repeat_count_distribution"], {"1": 1, "2": 1})
        self.assertAlmostEqual(stats["observation_detection_rate"], 2 / 3)
        self.assertEqual(stats["instance_detection_any_rate"], 1.0)
        self.assertEqual(stats["instance_detection_all_valid_runs_rate"], 0.5)

    def test_injection_valid_without_trace_evidence_is_rejected(self):
        experiment = self.package["runs"][0]["experiments"][0]
        experiment["evidence_refs"] = []
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any("MISSING_INJECTION_EXECUTION_EVIDENCE" in e for e in result["errors"]))
        self.assertEqual(result["statistics"]["defect_instance_count"], 0)

    def test_failed_normal_control_is_inconclusive_not_a_valid_observation(self):
        self.package["runs"][0]["experiments"][0]["control_status"] = "FAIL"
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertEqual(result["statistics"]["defect_instance_count"], 0)
        self.assertEqual(result["statistics"]["control_observation_count"], 0)

    def test_control_false_positive_rate_is_separately_reported(self):
        repeated = copy.deepcopy(self.package["runs"][0])
        repeated["run_id"] = "RUN-002"
        repeated["experiments"][0]["detection_status"] = "MISSED"
        repeated["experiments"][0]["execution_run_ids"] = ["EXEC-002"]
        repeated["experiments"][0]["control_execution_run_ids"] = ["CTRL-EXEC-002"]
        repeated["experiments"][0]["control_evidence_refs"] = ["CTRL-TRACE-002"]
        repeated["experiments"][0]["control_detection_status"] = "FALSE_POSITIVE"
        self.package["runs"].append(repeated)
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["statistics"]["control_false_positive_count"], 1)
        self.assertEqual(result["statistics"]["control_false_positive_rate"], 0.5)

    def test_multiple_manifests_and_dataset_case_ownership_pass(self):
        second_manifest = copy.deepcopy(self.package["dataset_manifests"][0])
        second_manifest["dataset_id"] = "DS-REFUND-002"
        second_manifest["case_count"] = 1
        second_case = copy.deepcopy(self.package["cases"][0])
        second_case["case_id"] = "CASE-002"
        second_case["dataset_id"] = "DS-REFUND-002"
        second_case["grading"]["criteria"][0]["criterion_id"] = "ASSERT-002"
        self.package["dataset_manifests"].append(second_manifest)
        self.package["cases"].append(second_case)
        self.package["task"]["expected_scope"]["expected_dataset_count"] = 2
        self.package["ground_truth"]["coverage_requirements"][0]["dataset_refs"].append("DS-REFUND-002")
        second_validation = copy.deepcopy(self.package["coverage_validations"][0])
        second_validation["dataset_ref"] = "DS-REFUND-002"
        second_validation["case_ref"] = "CASE-002"
        second_validation["assertion_refs"] = ["ASSERT-002"]
        self.package["coverage_validations"].append(second_validation)
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["statistics"]["dataset_coverage"]["DS-REFUND-002"]["valid_coverage_count"], 1)

    def test_expected_dataset_count_mismatch_fails(self):
        self.package["task"]["expected_scope"]["expected_dataset_count"] = 2
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any(e.startswith("EXPECTED_DATASET_COUNT_MISMATCH") for e in result["errors"]))

    def test_malformed_array_member_does_not_crash(self):
        self.package["cases"].append("not-an-object")
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.startswith("TYPE:cases[1]") for e in result["errors"]))

    def test_malformed_members_across_collections_do_not_crash(self):
        self.package["ground_truth"]["sources"].append("bad-source")
        self.package["ground_truth"]["coverage_requirements"].append(None)
        self.package["defect_specs"].append("bad-defect")
        self.package["defect_instances"].append(None)
        self.package["runs"].append("bad-run")
        self.package["coverage_validations"].append("bad-coverage-record")
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.startswith("TYPE:source[") for e in result["errors"]))
        self.assertTrue(any(e.startswith("TYPE:coverage[") for e in result["errors"]))

    def test_control_execution_must_be_independent_of_injected_execution(self):
        experiment = self.package["runs"][0]["experiments"][0]
        experiment["control_execution_run_ids"] = experiment["execution_run_ids"][:]
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any("CONTROL_EXECUTION_NOT_INDEPENDENT" in e for e in result["errors"]))
        self.assertEqual(result["statistics"]["control_observation_count"], 0)
        self.assertEqual(result["statistics"]["defect_instance_count"], 0)

    def test_normal_control_execution_cannot_be_reused_across_observations(self):
        repeated = copy.deepcopy(self.package["runs"][0])
        repeated["run_id"] = "RUN-002"
        repeated["experiments"][0]["execution_run_ids"] = ["EXEC-002"]
        repeated["experiments"][0]["evidence_refs"] = ["TRACE-002"]
        self.package["runs"].append(repeated)
        result = VALIDATOR.validate_package(self.package)
        self.assertTrue(any("DUPLICATE_CONTROL_EXECUTION_ID" in e for e in result["errors"]))
        self.assertEqual(result["statistics"]["control_observation_count"], 0)

    def test_missing_independent_coverage_review_is_inconclusive(self):
        self.package["coverage_validations"] = []
        result = VALIDATOR.validate_package(self.package)
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertTrue(any(e.startswith("INCONCLUSIVE:COVERAGE_DISPOSITION_MISSING") for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
