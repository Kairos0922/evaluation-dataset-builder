import unittest

from scripts.analyze_capability_measurement import analyze_records, validate_report


MATRIX = [
    [1, 1, 1, 0, 0],
    [1, 1, 0, 1, 0],
    [1, 0, 1, 0, 1],
    [0, 1, 0, 1, 1],
    [0, 0, 1, 1, 0],
    [0, 0, 0, 1, 1],
]


def make_records(matrix=MATRIX, *, gold_source="independent_oracle"):
    records = []
    for person_index, row in enumerate(matrix):
        for item_index, passed in enumerate(row):
            records.append({
                "run_id": f"run-{person_index}-{item_index}",
                "dataset_id": "capability-fixture",
                "dataset_sha256": "a" * 64,
                "configuration_id": f"agent-config-{person_index}",
                "case_id": f"case-{item_index}",
                "status": "valid",
                "outcomes": {
                    "agent_outcome": "pass" if passed else "fail",
                    "gold_outcome": "pass",
                    "gold_source": gold_source,
                },
            })
    return records


class CapabilityMeasurementTests(unittest.TestCase):
    def test_rasch_and_g_theory_estimate_balanced_independent_gold_design(self):
        report = analyze_records(make_records())
        self.assertEqual(report["irt"]["status"], "ESTIMATED_EXPLORATORY")
        self.assertEqual(report["irt"]["model"], "Rasch_1PL_joint_maximum_likelihood")
        self.assertTrue(report["irt"]["converged"])
        self.assertEqual(len(report["irt"]["persons"]), 6)
        self.assertEqual(len(report["irt"]["items"]), 5)
        self.assertEqual(report["g_theory"]["status"], "ESTIMATED_EXPLORATORY")
        self.assertEqual(report["g_theory"]["person_count"], 6)
        self.assertEqual(report["g_theory"]["item_count"], 5)
        self.assertEqual(len(report["g_theory"]["d_study"]), 5)
        self.assertEqual(report["overall_status"], "ESTIMATED_EXPLORATORY")
        self.assertEqual(validate_report(report), [])

    def test_no_independent_gold_returns_not_assessed_not_zero(self):
        report = analyze_records(make_records(gold_source="not_available"))
        self.assertEqual(report["irt"]["status"], "NOT_ASSESSED")
        self.assertEqual(report["g_theory"]["status"], "NOT_ASSESSED")
        self.assertIsNone(report["irt"].get("persons"))
        self.assertEqual(report["evidence"]["eligible_observation_count"], 0)
        self.assertEqual(report["overall_status"], "NOT_ASSESSED")
        self.assertEqual(validate_report(report), [])

    def test_unbalanced_person_item_design_is_rejected(self):
        records = make_records()
        records.pop()
        with self.assertRaisesRegex(ValueError, "unbalanced person-item design"):
            analyze_records(records)

    def test_duplicate_person_item_cell_is_rejected(self):
        records = make_records()
        records.append(dict(records[0], run_id="duplicate-run"))
        with self.assertRaisesRegex(ValueError, "duplicate person-item cell"):
            analyze_records(records)

    def test_complete_person_separation_disables_rasch_estimates(self):
        separated = [
            [1, 1, 1, 0, 0],
            [1, 1, 0, 1, 0],
            [1, 0, 1, 0, 1],
            [0, 1, 0, 1, 1],
            [0, 0, 1, 1, 0],
            [1, 1, 1, 1, 1],
        ]
        report = analyze_records(make_records(separated))
        self.assertEqual(report["irt"]["status"], "NOT_ASSESSED")
        self.assertIn("separation", report["irt"]["reason"])
        self.assertEqual(report["g_theory"]["status"], "ESTIMATED_EXPLORATORY")
        self.assertEqual(validate_report(report), [])


if __name__ == "__main__":
    unittest.main()
