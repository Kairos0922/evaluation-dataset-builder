"""Offline contract tests for execution-evaluation rubric integration."""
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
