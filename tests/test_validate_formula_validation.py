import copy
import unittest

from scripts.validate_formula_validation import validate_formula_validation_report


def stat_result(name, sample_count=20):
    return {
        "name": name,
        "value": 0.8,
        "interval": {"lower": 0.7, "upper": 0.9, "level": 0.95},
        "method": "pre-registered bootstrap",
        "sample_count": sample_count,
        "interpretation": "Illustrative evidence result for validator contract testing.",
        "evidence_ref": "artifact://validation-evidence"
    }


def split(family, letter):
    return {
        "datasets": [{
            "dataset_family": family,
            "source_ref": f"dataset://{family}",
            "sha256": letter * 64,
            "notes": "Independent family for schema contract test."
        }],
        "sample_count": 20
    }


def validated_report():
    return {
        "schema_version": "0.0.2",
        "validation_id": "FORMULA-VALIDATION-001",
        "model_id": "candidate-composite-v1",
        "status": "VALIDATED_FOR_SCOPE",
        "created_at": "2026-11-25T00:00:00Z",
        "scope": {
            "evaluation_purposes": ["capability"],
            "target_types": ["agent"],
            "domains": ["browser"],
            "models": ["model-a"],
            "environments": ["sandbox"],
            "validity_boundary": "Only the declared browser-agent capability scope."
        },
        "candidate_model": {
            "family": "weighted_arithmetic",
            "scalar_score_enabled": True,
            "formula_spec": "S = 0.4 * coverage + 0.6 * ground_truth_validity, subject to non-compensatory gates.",
            "weights_source": "empirical",
            "weights": {"coverage": 0.4, "ground_truth_validity": 0.6},
            "hard_gates": ["critical_ground_truth", "judge_validity"],
            "thresholds": {"validated_scope_threshold": 0.5},
            "normalization": "pre-registered min-max anchors",
            "missing_data_policy": "do not impute critical evidence",
            "aggregation_policy": "weighted arithmetic after hard gates"
        },
        "data_splits": {
            "development": split("dev-family", "a"),
            "calibration": split("cal-family", "b"),
            "validation": split("validation-family", "c"),
            "external": split("external-family", "d"),
            "grouping_unit": "dataset_family",
            "leakage_audit": {
                "status": "PASS",
                "method": "dataset-family grouped split and exact/semantic overlap audit",
                "evidence_ref": "artifact://leakage-audit",
                "limitations": []
            }
        },
        "expert_validation": {
            "status": "PASS",
            "reviewer_count": 2,
            "reviewer_profiles": ["Agent evaluation researcher", "Software testing researcher"],
            "blinded": True,
            "independent": True,
            "content_validity": {
                "cvi": 0.9,
                "cvr": 0.8,
                "aikens_v": 0.85,
                "method": "independent expert relevance and necessity ratings"
            },
            "agreement_metrics": [stat_result("ICC(2,k)")],
            "raw_data_ref": "artifact://expert-ratings",
            "limitations": []
        },
        "mutation_validation": {
            "status": "PASS",
            "catalog_version": "0.0.2",
            "mutation_count": 8,
            "detected_count": 8,
            "false_positive_count": 0,
            "false_negative_count": 0,
            "per_defect_results": [stat_result("mutation detection")],
            "results_ref": "artifact://mutation-results",
            "limitations": []
        },
        "external_criterion_validation": {
            "status": "PASS",
            "criteria": [{
                "criterion": "independent expert quality assessment",
                "source_ref": "dataset://external-quality-criterion",
                "sample_count": 40,
                "method": "grouped external validation with Spearman association",
                "result": stat_result("Spearman rho", 40),
                "status": "PASS"
            }],
            "limitations": []
        },
        "robustness": {
            "status": "PASS",
            "weight_sensitivity": stat_result("weight sensitivity"),
            "normalization_sensitivity": stat_result("normalization sensitivity"),
            "aggregation_sensitivity": stat_result("aggregation sensitivity"),
            "leave_one_dimension_out": stat_result("leave-one-dimension-out"),
            "rank_or_grade_instability": stat_result("rank instability"),
            "limitations": []
        },
        "threshold_validation": {
            "status": "PASS",
            "decision_context": "Use as a scoped release decision aid, not universal ranking.",
            "loss_model": {
                "false_pass_cost": 10,
                "false_fail_cost": 2,
                "source": "documented stakeholder loss elicitation"
            },
            "selection_method": "pre-registered cost-sensitive ROC and decision analysis",
            "candidate_thresholds": [0.4, 0.5, 0.6],
            "selected_threshold": 0.5,
            "validation_results": [stat_result("threshold decision performance", 40)],
            "limitations": []
        },
        "uncertainty": {
            "methods": ["grouped bootstrap"],
            "confidence_level": 0.95,
            "reported_intervals": [stat_result("score interval", 40)],
            "limitations": []
        },
        "reproducibility": {
            "analysis_code_ref": "scripts/validate_formula_validation.py",
            "commit_sha": "abcdef1234567",
            "random_seed": 2026,
            "environment": "Python 3.x with locked requirements",
            "reproduction_instructions": "Run the pre-registered validation workflow."
        },
        "conclusion": {
            "decision": "VALIDATED_FOR_SCOPE",
            "scope_statement": "Validated only for the declared browser-agent capability evaluation scope.",
            "limitations": ["Do not generalize to other task domains without external validation."],
            "evidence_refs": ["artifact://complete-validation-package"]
        }
    }


def not_validated_report():
    report = validated_report()
    report["status"] = "NOT_VALIDATED"
    report["candidate_model"]["scalar_score_enabled"] = False
    report["candidate_model"]["weights"] = None
    report["candidate_model"]["thresholds"] = None
    report["candidate_model"]["weights_source"] = "none"
    report["data_splits"] = {
        "development": {"datasets": [], "sample_count": 0},
        "calibration": {"datasets": [], "sample_count": 0},
        "validation": {"datasets": [], "sample_count": 0},
        "external": {"datasets": [], "sample_count": 0},
        "grouping_unit": "dataset_family",
        "leakage_audit": {"status": "UNKNOWN", "method": "not run", "evidence_ref": None, "limitations": []}
    }
    report["expert_validation"] = {
        "status": "NOT_RUN", "reviewer_count": 0, "reviewer_profiles": [],
        "blinded": False, "independent": False,
        "content_validity": {"cvi": None, "cvr": None, "aikens_v": None, "method": None},
        "agreement_metrics": [], "raw_data_ref": None, "limitations": ["Not yet assessed."]
    }
    report["mutation_validation"] = {
        "status": "NOT_RUN", "catalog_version": "0.0.2", "mutation_count": 0,
        "detected_count": 0, "false_positive_count": 0, "false_negative_count": 0,
        "per_defect_results": [], "results_ref": None, "limitations": ["Not yet assessed."]
    }
    report["external_criterion_validation"] = {
        "status": "NOT_RUN", "criteria": [], "limitations": ["No external criterion data yet."]
    }
    report["robustness"] = {
        "status": "NOT_RUN",
        "weight_sensitivity": stat_result("not run", 0),
        "normalization_sensitivity": stat_result("not run", 0),
        "aggregation_sensitivity": stat_result("not run", 0),
        "leave_one_dimension_out": stat_result("not run", 0),
        "rank_or_grade_instability": stat_result("not run", 0),
        "limitations": ["Not yet assessed."]
    }
    report["threshold_validation"] = {
        "status": "NOT_APPLICABLE",
        "decision_context": "No scalar score is enabled.",
        "loss_model": {"false_pass_cost": "not applicable", "false_fail_cost": "not applicable", "source": "no scalar decision threshold"},
        "selection_method": "not applicable",
        "candidate_thresholds": [],
        "selected_threshold": None,
        "validation_results": [],
        "limitations": ["Thresholds must not be set before formula validation."]
    }
    report["uncertainty"] = {
        "methods": [], "confidence_level": None, "reported_intervals": [],
        "limitations": ["No validation estimates exist."]
    }
    report["conclusion"] = {
        "decision": "NOT_VALIDATED",
        "scope_statement": "No validated scope has been established.",
        "limitations": ["Formula validation has not been completed."],
        "evidence_refs": []
    }
    return report


class FormulaValidationTests(unittest.TestCase):
    def test_not_validated_report_is_valid_when_scalar_is_disabled(self):
        self.assertEqual(validate_formula_validation_report(not_validated_report()), [])

    def test_validated_scalar_requires_complete_independent_evidence(self):
        report = validated_report()
        self.assertEqual(validate_formula_validation_report(report), [])

    def test_validated_scalar_is_rejected_when_external_criterion_is_missing(self):
        report = validated_report()
        report["external_criterion_validation"]["status"] = "NOT_RUN"
        report["external_criterion_validation"]["criteria"] = []
        errors = validate_formula_validation_report(report)
        self.assertTrue(any("external_criterion_validation" in error for error in errors))

    def test_validated_split_requires_at_least_one_dataset_source(self):
        report = validated_report()
        report["data_splits"]["development"]["datasets"] = []
        errors = validate_formula_validation_report(report)
        self.assertTrue(any("development.datasets must include at least one source dataset" in error for error in errors))

    def test_dataset_entries_follow_schema_without_per_dataset_sample_count(self):
        report = validated_report()
        self.assertEqual(validate_formula_validation_report(report), [])
        for split_name in ("development", "calibration", "validation", "external"):
            self.assertNotIn("sample_count", report["data_splits"][split_name]["datasets"][0])

    def test_dataset_family_overlap_is_detected(self):
        report = validated_report()
        report["data_splits"]["external"] = copy.deepcopy(report["data_splits"]["development"])
        errors = validate_formula_validation_report(report)
        self.assertTrue(any("dataset_family leakage" in error for error in errors))

    def test_unvalidated_model_cannot_enable_scalar_score(self):
        report = not_validated_report()
        report["candidate_model"]["scalar_score_enabled"] = True
        errors = validate_formula_validation_report(report)
        self.assertTrue(any("scalar_score_enabled" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
