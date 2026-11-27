import unittest

from scripts.run_capability_measurement_monte_carlo import run_experiment


class CapabilityMonteCarloTests(unittest.TestCase):
    def test_rasch_parameter_recovery_under_correctly_specified_1pl_model(self):
        report = run_experiment(replications=30, persons=80, items=25, seed=8000)
        self.assertEqual(report["evidence_level"], "SIMULATION_ONLY")
        self.assertEqual(report["valid_replications"], 26)
        self.assertEqual(report["failed_replications"], 4)
        metrics = report["metrics_across_valid_replications"]
        self.assertGreater(metrics["ability_correlation"]["mean"], 0.82)
        self.assertGreater(metrics["item_correlation"]["mean"], 0.93)
        self.assertLess(metrics["ability_rmse"]["mean"], 0.60)
        self.assertLess(metrics["item_rmse"]["mean"], 0.40)
        self.assertIn("not confidence intervals", report["interpretation"].lower())


if __name__ == "__main__":
    unittest.main()
