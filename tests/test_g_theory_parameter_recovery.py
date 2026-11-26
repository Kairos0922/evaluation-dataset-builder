import unittest

from scripts.run_g_theory_parameter_recovery import run_experiment, validate_report


class GTheoryParameterRecoveryTests(unittest.TestCase):
    def test_simulation_report_is_schema_valid_and_simulation_only(self):
        report = run_experiment(
            replications=5, persons=12, items=8, reference_draws=250, seed=1234
        )
        self.assertEqual(report["evidence_level"], "SIMULATION_ONLY")
        self.assertEqual(len(report["scenarios"]), 4)
        self.assertEqual(validate_report(report), [])
        for scenario in report["scenarios"]:
            self.assertGreaterEqual(scenario["valid_replications"], 1)
            self.assertGreaterEqual(scenario["reference"]["relative_G_coefficient"], 0.0)
            self.assertLessEqual(scenario["reference"]["relative_G_coefficient"], 1.0)

    def test_fixed_seed_is_reproducible(self):
        kwargs = dict(replications=3, persons=10, items=7, reference_draws=200, seed=77)
        first = run_experiment(**kwargs)
        second = run_experiment(**kwargs)
        self.assertEqual(first["report_id"], second["report_id"])
        self.assertEqual(first["scenarios"], second["scenarios"])

    def test_invalid_design_sizes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "replications>=2"):
            run_experiment(replications=1)


if __name__ == "__main__":
    unittest.main()
