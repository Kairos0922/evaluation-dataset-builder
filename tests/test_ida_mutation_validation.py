import unittest

from scripts.run_ida_mutation_validation import run_validation, validate_report


class IDAMutationValidationTests(unittest.TestCase):
    def test_deterministic_mutations_and_negative_controls_are_reported(self):
        report = run_validation()
        self.assertEqual(validate_report(report), [])
        summary = report["summary"]
        self.assertEqual(summary["deterministic_mutation_count"], 8)
        self.assertEqual(summary["detected_mutation_count"], 8)
        self.assertEqual(summary["missed_mutation_count"], 0)
        self.assertEqual(summary["deterministic_detection_rate"], 1.0)
        self.assertEqual(summary["negative_control_count"], 4)
        self.assertEqual(summary["false_positive_control_count"], 0)
        self.assertEqual(summary["negative_control_false_positive_rate"], 0.0)
        self.assertEqual(summary["non_deterministic_not_assessed_count"], 4)
        self.assertTrue(all(item["status"] == "PASS" for item in report["deterministic_mutations"]))
        self.assertTrue(all(item["status"] == "PASS" for item in report["negative_controls"]))
        self.assertTrue(all(item["status"] == "NOT_ASSESSED" for item in report["non_deterministic_mutations"]))

    def test_report_identity_is_reproducible_for_fixed_mutations(self):
        first = run_validation()
        second = run_validation()
        self.assertEqual(first["report_id"], second["report_id"])
        self.assertEqual(first["summary"], second["summary"])


if __name__ == "__main__":
    unittest.main()
