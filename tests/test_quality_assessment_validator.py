import copy
import unittest

from scripts.validate_quality_assessment import validate_report


def base_ida():
    return {
        "schema_version": "0.0.2",
        "assessment_id": "ida-demo-001",
        "assessment_type": "independent_dataset_assessment",
        "created_at": "2026-11-25T07:30:00Z",
        "dataset": {
            "dataset_id": "demo",
            "version": "1.0.0",
            "sha256": "a" * 64,
            "case_count": 2
        },
        "evaluation_purpose": "both",
        "assessor": {
            "name": "offline-validator",
            "version": "0.0.2",
            "independence": "independent",
            "review_protocol_ref": None
        },
        "overall_status": "PARTIAL",
        "gate_results": [
            {
                "gate_id": "G-EVIDENCE",
                "status": "PASS",
                "severity": "critical",
                "rationale": "All sampled references resolved.",
                "evidence_refs": ["evidence://source-a"]
            }
        ],
        "metric_results": [
            {
                "metric_id": "IDA-STR-01",
                "status": "PASS",
                "value": 1.0,
                "unit": "proportion",
                "numerator": 2,
                "denominator": 2,
                "interval": None,
                "evidence_refs": ["artifact://schema-report"],
                "limitations": ["Schema validity is not semantic validity."]
            }
        ],
        "evidence_sufficiency": {
            "status": "partial",
            "rationale": "Static checks completed; expert review is pending.",
            "missing_evidence": ["independent expert review"]
        },
        "composite": {
            "status": "NOT_VALIDATED",
            "value": None,
            "model_id": None,
            "scope": None,
            "validation_report_ref": None,
            "limitations": ["No validated aggregation model is available."]
        },
        "findings": [],
        "limitations": ["No runtime execution was performed."],
        "not_assessed": ["runtime reliability"],
        "not_applicable": []
    }


def base_era():
    return {
        "schema_version": "0.0.2",
        "assessment_id": "era-demo-001",
        "assessment_type": "empirical_runtime_assessment",
        "created_at": "2026-11-25T07:30:00Z",
        "dataset": {
            "dataset_id": "demo",
            "version": "1.0.0",
            "sha256": "b" * 64
        },
        "evaluation_purpose": "both",
        "target": {
            "target_type": "agent_with_skill",
            "name": "demo-agent",
            "version": "1.2.0",
            "revision": "abc123"
        },
        "runtime_protocol": {
            "protocol_id": "protocol-1",
            "model": {"provider": "example", "model_id": "model-x", "model_revision": None},
            "harness": {"name": "test-harness", "version": "1.0"},
            "environment": {"name": "sandbox", "version": "1", "digest": None, "region": None},
            "tool_versions": {"browser": "1"},
            "execution_parameters": {"temperature": 0},
            "protocol_ref": None
        },
        "runs": [
            {
                "run_id": "run-1",
                "status": "valid",
                "seed": 1,
                "started_at": "2026-11-25T07:00:00Z",
                "trace_ref": "trace://run-1",
                "result_ref": "result://run-1",
                "failure_class": None
            }
        ],
        "grader_validation": {
            "status": "NOT_RUN",
            "reference_standard": None,
            "sample_count": 0,
            "metric_results": [],
            "limitations": ["No independent gold-label comparison."]
        },
        "capability_analysis": {
            "status": "NOT_RUN",
            "method": "IRT planned; not executed",
            "agent_configurations": 0,
            "task_count": 0,
            "results_ref": None,
            "limitations": ["No response matrix."]
        },
        "regression_analysis": {
            "status": "NOT_RUN",
            "baseline_revision": "old",
            "candidate_revision": "new",
            "paired_case_count": 0,
            "historical_faults_replayed": 0,
            "mutants_replayed": 0,
            "results_ref": None,
            "limitations": ["No paired regression runs."]
        },
        "metric_results": [],
        "evidence_sufficiency": {
            "status": "insufficient",
            "rationale": "Only a contract smoke run exists.",
            "missing_evidence": ["grader calibration", "capability trials", "regression replay"]
        },
        "composite": {
            "status": "NOT_VALIDATED",
            "value": None,
            "model_id": None,
            "scope": None,
            "validation_report_ref": None,
            "limitations": ["No validated composite."]
        },
        "findings": [],
        "limitations": ["Illustrative contract fixture only."]
    }


class QualityAssessmentValidatorTests(unittest.TestCase):
    def test_valid_ida_report(self):
        self.assertEqual(validate_report(base_ida()), [])

    def test_ida_cannot_pass_with_critical_gate_failure(self):
        report = base_ida()
        report["overall_status"] = "PASS"
        report["gate_results"][0]["status"] = "FAIL"
        errors = validate_report(report)
        self.assertTrue(any("critical gate fails" in error for error in errors))

    def test_unassessed_metric_cannot_have_numeric_value(self):
        report = base_ida()
        report["metric_results"][0]["status"] = "NOT_ASSESSED"
        errors = validate_report(report)
        self.assertTrue(any("must not carry a measured value" in error for error in errors))

    def test_zero_denominator_is_not_applicable(self):
        report = base_ida()
        report["metric_results"][0]["denominator"] = 0
        report["metric_results"][0]["numerator"] = 0
        errors = validate_report(report)
        self.assertTrue(any("zero denominator" in error for error in errors))

    def test_ida_rejects_runtime_only_metrics(self):
        report = base_ida()
        metric = copy.deepcopy(report["metric_results"][0])
        metric["metric_id"] = "REG-01"
        report["metric_results"].append(metric)
        errors = validate_report(report)
        self.assertTrue(any("runtime-only metric" in error for error in errors))

    def test_duplicate_metric_ids_are_rejected(self):
        report = base_ida()
        report["metric_results"].append(copy.deepcopy(report["metric_results"][0]))
        errors = validate_report(report)
        self.assertTrue(any("duplicate metric_id" in error for error in errors))

    def test_valid_era_report(self):
        self.assertEqual(validate_report(base_era()), [])

    def test_non_finite_metric_value_is_rejected(self):
        report = base_ida()
        report["metric_results"][0]["value"] = float("nan")
        errors = validate_report(report)
        self.assertTrue(any("non-finite numeric value" in error for error in errors))

    def test_non_finite_nested_interval_bound_is_rejected(self):
        report = base_ida()
        report["metric_results"][0]["interval"] = {
            "lower": 0.1,
            "upper": float("inf"),
            "level": 0.95,
            "method": "test"
        }
        errors = validate_report(report)
        self.assertTrue(any("non-finite numeric value" in error for error in errors))

    def test_ida_pass_requires_sufficient_evidence(self):
        report = base_ida()
        report["overall_status"] = "PASS"
        report["evidence_sufficiency"]["status"] = "insufficient"
        errors = validate_report(report)
        self.assertTrue(any("evidence is insufficient" in error for error in errors))

    def test_grader_pass_requires_validation_metrics(self):
        report = base_era()
        report["grader_validation"]["status"] = "PASS"
        report["grader_validation"]["sample_count"] = 10
        errors = validate_report(report)
        self.assertTrue(any("at least one reported validation metric" in error for error in errors))

    def test_valid_era_run_requires_trace(self):
        report = base_era()
        report["runs"][0]["trace_ref"] = None
        errors = validate_report(report)
        self.assertTrue(any("valid run requires trace_ref" in error for error in errors))

    def test_era_rejects_offline_only_metrics(self):
        report = base_era()
        report["metric_results"] = [{
            "metric_id": "IDA-STR-01",
            "status": "PASS",
            "value": 1.0,
            "unit": "proportion",
            "numerator": 1,
            "denominator": 1,
            "interval": None,
            "evidence_refs": ["artifact://x"],
            "limitations": []
        }]
        errors = validate_report(report)
        self.assertTrue(any("offline-only metric" in error for error in errors))

    def test_composite_cannot_be_validated_without_sufficient_evidence(self):
        report = base_era()
        report["composite"] = {
            "status": "VALIDATED_FOR_SCOPE",
            "value": 0.9,
            "model_id": "model-1",
            "scope": "general agents",
            "validation_report_ref": "report://validation",
            "limitations": []
        }
        errors = validate_report(report)
        self.assertTrue(any("requires sufficient_for_scope" in error for error in errors))

    def test_era_composite_requires_runtime_and_grader_evidence(self):
        report = base_era()
        report["evidence_sufficiency"]["status"] = "sufficient_for_scope"
        report["composite"] = {
            "status": "VALIDATED_FOR_SCOPE",
            "value": 0.9,
            "model_id": "model-1",
            "scope": "general agents",
            "validation_report_ref": "report://validation",
            "limitations": []
        }
        errors = validate_report(report)
        self.assertTrue(any("requires validated grader evidence" in error for error in errors))
        self.assertTrue(any("completed capability analysis" in error for error in errors))
        self.assertTrue(any("completed regression analysis" in error for error in errors))


if __name__ == "__main__":
    unittest.main()


class StrictJsonConstantTests(unittest.TestCase):
    def test_rejects_non_standard_json_numeric_constants(self):
        from scripts.validate_quality_assessment import _reject_json_constant
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "invalid JSON numeric constant"):
                _reject_json_constant(token)
