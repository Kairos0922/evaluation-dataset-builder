import json
import tempfile
import unittest
from pathlib import Path

from scripts.assess_dataset_quality import build_report
from scripts.validate_quality_assessment import validate_report


def sample_manifest(case_count=1):
    return {
        "dataset_id": "demo-dataset",
        "version": "1.0.0",
        "evaluation_target": "general-agent",
        "purpose": "general agent capability and regression assessment",
        "scope": {"included": ["tool use"], "excluded": []},
        "coverage": {
            "universe_definition": "One declared capability requirement.",
            "dimensions": [
                {
                    "dimension": "capability",
                    "total": 1,
                    "covered": 1 if case_count else 0,
                    "coverage_rate": 1.0 if case_count else 0.0,
                    "uncovered": []
                }
            ]
        },
        "case_count": case_count,
        "quality_status": "candidate",
        "execution_status": "DESIGN_ONLY"
    }


def sample_case(case_id="CASE-001"):
    return {
        "case_id": case_id,
        "dataset_id": "demo-dataset",
        "title": "Check tool selection",
        "evaluation_target": "general-agent",
        "objective": "Select the required tool for the stated task.",
        "assumptions": ["The status lookup tool is available and authorized."],
        "user_input": "Find the status of resource A.",
        "expected_behavior": "Use the status lookup tool and report the returned state.",
        "source_refs": [
            {
                "source_id": "SRC-001",
                "source_type": "synthetic_scenario",
                "title": "Synthetic tool-use exercise",
                "locator": "fixture"
            }
        ],
        "grading": {
            "evaluation_subject": "general-agent",
            "method": "trace_check",
            "criteria": [
                {
                    "criterion_id": "C1",
                    "description": "Uses the correct tool.",
                    "pass_condition": "Calls the status lookup tool.",
                    "fail_condition": "Calls an unrelated tool or fabricates a result.",
                    "evidence_required": ["tool call trace"]
                }
            ],
            "pass_conditions": ["Correct tool is called."],
            "fail_conditions": ["Wrong tool is called."],
            "evidence_required": ["tool call trace"]
        },
        "quality_status": "candidate",
        "scenario_bucket": ["business_rule"],
        "case_origin": "synthetic_gap_fill",
        "coverage_tags": [
            {
                "dimension": "capability",
                "value": "tool_selection",
                "coverage_item_id": "COV-001"
            }
        ],
        "execution_requirements": {"status": "DESIGN_ONLY"}
    }


class OfflineDatasetAssessmentTests(unittest.TestCase):
    def write_inputs(self, directory, manifest, cases):
        manifest_path = directory / "manifest.json"
        cases_path = directory / "cases.jsonl"
        output_path = directory / "ida-report.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        cases_path.write_text(
            "".join(json.dumps(case) + "\n" for case in cases),
            encoding="utf-8"
        )
        return manifest_path, cases_path, output_path

    def run_assessment(self, directory, manifest, cases, purpose="both"):
        paths = self.write_inputs(directory, manifest, cases)
        return build_report(*paths, evaluation_purpose=purpose)

    def test_structural_only_report_does_not_claim_validated_composite(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, errors, duplicate_ids, coverage_errors, source_errors = self.run_assessment(
                Path(tmp), sample_manifest(), [sample_case()]
            )
            self.assertEqual(errors, [])
            self.assertEqual(duplicate_ids, [])
            self.assertEqual(report["overall_status"], "PARTIAL")
            self.assertEqual(report["composite"]["status"], "NOT_VALIDATED")
            self.assertIsNone(report["composite"]["value"])
            self.assertEqual(report["evidence_sufficiency"]["status"], "partial")
            self.assertEqual(validate_report(report), [])

    def test_duplicate_case_ids_fail_integrity_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, _, duplicate_ids, _, _ = self.run_assessment(
                Path(tmp), sample_manifest(2), [sample_case(), sample_case()]
            )
            self.assertEqual(duplicate_ids, ["CASE-001"])
            self.assertEqual(report["overall_status"], "FAIL")
            gate = next(item for item in report["gate_results"] if item["gate_id"] == "G07_integrity_leakage")
            self.assertEqual(gate["status"], "FAIL")
            self.assertEqual(validate_report(report), [])

    def test_missing_grading_contract_fails_critical_gate(self):
        case = sample_case()
        case.pop("grading")
        with tempfile.TemporaryDirectory() as tmp:
            report, errors, _, _, _ = self.run_assessment(
                Path(tmp), sample_manifest(), [case]
            )
            self.assertTrue(errors)
            gate = next(item for item in report["gate_results"] if item["gate_id"] == "G05_rubric_validity")
            self.assertEqual(gate["status"], "FAIL")
            self.assertEqual(report["overall_status"], "FAIL")
            self.assertEqual(validate_report(report), [])

    def test_empty_dataset_is_not_assessed_not_zero_quality(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, _, _, _, _ = self.run_assessment(
                Path(tmp), sample_manifest(0), []
            )
            self.assertEqual(report["overall_status"], "NOT_ASSESSED")
            self.assertEqual(report["evidence_sufficiency"]["status"], "insufficient")
            self.assertEqual(report["composite"]["value"], None)
            self.assertEqual(validate_report(report), [])

    def test_exact_duplicate_payload_is_reported_without_semantic_claim(self):
        first = sample_case("CASE-001")
        second = sample_case("CASE-002")
        with tempfile.TemporaryDirectory() as tmp:
            report, _, _, _, _ = self.run_assessment(
                Path(tmp), sample_manifest(2), [first, second]
            )
            duplicate_metric = next(item for item in report["metric_results"] if item["metric_id"] == "IDA-RED-00")
            self.assertEqual(duplicate_metric["value"], 0.5)
            self.assertTrue(any("exact duplicate" in item["description"] for item in report["findings"]))
            self.assertEqual(validate_report(report), [])

    def test_source_registry_resolution_is_reported_separately_from_claim_support(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            manifest_path, cases_path, output_path = self.write_inputs(
                directory, sample_manifest(), [sample_case()]
            )
            registry_path = directory / "sources.json"
            registry_path.write_text(json.dumps({
                "sources": [{
                    "source_id": "SRC-001",
                    "source_type": "synthetic_scenario",
                    "title": "Synthetic tool-use exercise"
                }]
            }), encoding="utf-8")
            report, _, _, _, _ = build_report(
                manifest_path, cases_path, output_path, "both", registry_path
            )
            gate = next(item for item in report["gate_results"] if item["gate_id"] == "G01_source_provenance")
            self.assertEqual(gate["status"], "PASS")
            source_metric = next(item for item in report["metric_results"] if item["metric_id"] == "IDA-STR-03")
            self.assertEqual(source_metric["value"], 1.0)
            self.assertIn("does not prove source authenticity", source_metric["limitations"][0])
            self.assertEqual(validate_report(report), [])

    def test_empty_cases_with_nonzero_manifest_count_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, errors, _, _, _ = self.run_assessment(
                Path(tmp), sample_manifest(1), []
            )
            self.assertTrue(errors)
            self.assertEqual(report["overall_status"], "FAIL")
            self.assertEqual(validate_report(report), [])


if __name__ == "__main__":
    unittest.main()
