"""Regression tests for case-contract-aligned Gold Oracle reporting."""
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORACLE_PATH = ROOT / "benchmarks" / "webapp-testing" / "scripts" / "gold_oracle.py"
SPEC = importlib.util.spec_from_file_location("webapp_testing_gold_oracle", ORACLE_PATH)
ORACLE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ORACLE)


class GoldOracleReportingTests(unittest.TestCase):
    def test_search_finding_does_not_require_literal_business_rule_id(self):
        report = (
            "Queries RESET and reset returned no rows. "
            "Expected Reset password flow; observed an empty list. "
            "This violates the case-insensitive search requirement. Final verdict: FAIL."
        )
        self.assertTrue(
            ORACLE.report_has_search_finding(
                report, [{"title": "Reset password flow"}], ["RESET", "reset"]
            )
        )
        self.assertNotIn("BR-02", report)

    def test_state_cycle_result_does_not_require_literal_business_rule_id(self):
        report = (
            "WB-101 / Reset password flow: Open -> In progress -> Done -> Open. "
            "The final summary is restored. Final verdict: PASS."
        )
        self.assertTrue(
            ORACLE.report_has_state_cycle_result(report, "WB-101", "Reset password flow")
        )
        self.assertNotIn("BR-07", report)

    def test_delete_result_does_not_require_literal_business_rule_id(self):
        report = (
            "WB-105 Review accessibility: confirmation dialog title Delete task?; "
            "clicked Delete task once; final verdict PASS."
        )
        self.assertTrue(ORACLE.report_has_delete_result(report, "WB-105"))
        self.assertNotIn("BR-08", report)

    def test_builder_action_status_steps_derive_exact_state_cycle(self):
        case = {
            "reference_outcome": {
                "rule_expected": {
                    "steps": [
                        {"action": "Move to In progress", "status": "In progress", "summary": {"open": 1, "in_progress": 3}},
                        {"action": "Move to Done", "status": "Done", "summary": {"open": 1, "in_progress": 2, "done": 2}},
                        {"action": "Move to Open", "status": "Open", "summary": {"open": 2, "in_progress": 2, "done": 1}},
                    ]
                }
            }
        }
        target = {"id": "WB-101", "title": "Reset password flow", "status": "Open"}
        self.assertEqual(
            ORACLE.expected_status_transitions(case, target),
            [("open", "in_progress"), ("in_progress", "done"), ("done", "open")],
        )

    def test_canonical_report_excludes_raw_diagnostic_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "pilot" / "skill-artifacts"
            root.mkdir(parents=True)
            (root / "report.md").write_text("Final verdict: PASS", encoding="utf-8")
            (root / "report_raw_run.md").write_text("Original verdict: FAIL", encoding="utf-8")
            (root / "dialog.png").write_bytes(b"image")
            report_text, images = ORACLE.report_bundle(root.parent)
            self.assertEqual(report_text, "Final verdict: PASS")
            self.assertEqual(len(images), 1)

    def test_raw_report_is_fallback_only_when_no_canonical_report_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "pilot" / "skill-artifacts"
            root.mkdir(parents=True)
            (root / "report_raw_run.md").write_text("Raw diagnostic report", encoding="utf-8")
            report_text, _ = ORACLE.report_bundle(root.parent)
            self.assertEqual(report_text, "Raw diagnostic report")


if __name__ == "__main__":
    unittest.main()
