"""Offline contract tests for the Skill self-evaluation rubric integration."""
import json
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))

import run_eval  # noqa: E402


def load_inputs():
    suite = json.loads((TESTS_DIR / "self-eval-cases.json").read_text(encoding="utf-8"))
    rubric = json.loads((TESTS_DIR / "self-eval-rubric.json").read_text(encoding="utf-8"))
    return suite, rubric


class SelfEvalRubricTests(unittest.TestCase):
    def test_rubric_covers_every_case_and_assertion(self):
        suite, rubric = load_inputs()
        indexed = run_eval.index_self_eval_rubric(suite, rubric)

        self.assertEqual(len(suite["cases"]), 13)
        self.assertEqual(sum(len(case["expected"]) for case in suite["cases"]), 64)
        self.assertEqual(set(indexed), {case["id"] for case in suite["cases"]})
        self.assertEqual(sum(len(case["assertions"]) for case in rubric["cases"]), 64)

    def test_rubric_annotation_preserves_judge_status_and_adds_severity(self):
        suite, rubric = load_inputs()
        indexed = run_eval.index_self_eval_rubric(suite, rubric)
        case = suite["cases"][-1]
        assertion = indexed[case["id"]]["assertions"][0]
        judge_check = {
            "criterion": case["expected"][0],
            "status": "FAIL",
            "rationale": "fixture rationale",
            "evidence": ["output excerpt"],
        }

        annotated = run_eval.annotate_checks_with_rubric(
            [judge_check],
            {"assertions": [assertion]},
        )

        self.assertEqual(annotated[0]["status"], "FAIL")
        self.assertEqual(annotated[0]["assertion_id"], assertion["assertion_id"])
        self.assertEqual(annotated[0]["severity"], "CRITICAL")

    def test_rubric_rejects_suite_criterion_drift(self):
        suite, rubric = load_inputs()
        suite["cases"][0]["expected"][0] = "changed criterion"

        with self.assertRaisesRegex(ValueError, "assertion text"):
            run_eval.index_self_eval_rubric(suite, rubric)

    def test_reference_navigation_manifest_matches_cases_and_package_files(self):
        navigation = json.loads(
            (TESTS_DIR / "reference-navigation-cases.json").read_text(encoding="utf-8")
        )
        dependency = json.loads(
            (TESTS_DIR / "reference-dependency-manifest.json").read_text(encoding="utf-8")
        )
        skill_dir = TESTS_DIR.parent / "skills" / "evaluation-dataset-builder"

        self.assertEqual(len(navigation["cases"]), 8)
        manifest_cases = {item["case_id"]: item for item in dependency["navigation_cases"]}
        self.assertEqual(
            {item["id"] for item in navigation["cases"]},
            set(manifest_cases),
        )
        for case in navigation["cases"]:
            manifest_item = manifest_cases[case["id"]]
            self.assertEqual(manifest_item["required"], case["required"])
            self.assertEqual(manifest_item["critical"], case["critical"])
            self.assertTrue(set(case["critical"]).issubset(case["required"]))
            referenced = (
                case["required"]
                + case["critical"]
                + case["conditionally_relevant"]
                + case["irrelevant_examples"]
            )
            for relative_path in referenced:
                self.assertTrue(
                    (skill_dir / relative_path).is_file(),
                    f"{case['id']} references missing Skill asset: {relative_path}",
                )

    def test_reference_read_event_schema_captures_delivery_and_preload_distinctions(self):
        schema = json.loads(
            (TESTS_DIR / "reference-read-event.schema.json").read_text(encoding="utf-8")
        )
        self.assertIn("event_type", schema["required"])
        self.assertIn("access_origin", schema["required"])
        self.assertIn("delivery_status", schema["required"])
        self.assertIn("evidence_ref", schema["required"])
        event_types = schema["properties"]["event_type"]["enum"]
        self.assertIn("CONTENT_DELIVERED", event_types)
        self.assertIn("PRELOADED_CONTEXT", event_types)
        self.assertIn("FILE_READ_FAILED", event_types)
        self.assertIn("FILE_READ_DENIED", event_types)

    def test_critical_rule_summary_keeps_failures_and_unknowns_visible(self):
        summary = run_eval.summarize_critical_rule_checks([
            {
                "id": "SE13",
                "checks": [
                    {"assertion_id": "SE13-A01", "severity": "CRITICAL", "status": "FAIL"},
                    {"assertion_id": "SE13-A02", "severity": "CRITICAL", "status": "UNKNOWN"},
                    {"assertion_id": "SE13-A03", "severity": "IMPORTANT", "status": "PASS"},
                ],
            }
        ])

        self.assertEqual(summary["opportunities"], 2)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["unknown"], 1)
        self.assertEqual(summary["failed_assertion_ids"], ["SE13-A01"])
        self.assertEqual(summary["failed_case_ids"], ["SE13"])
        self.assertEqual(
            summary["interpretation"],
            "descriptive_non_compensatory; no composite score or automatic release decision",
        )


if __name__ == "__main__":
    unittest.main()
