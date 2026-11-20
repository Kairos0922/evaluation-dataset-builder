import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "remaining_plan", ROOT / "benchmarks" / "webapp-testing" / "scripts" / "plan_remaining_pilots.py"
)
PLAN = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(PLAN)

MATRIX = {"include": [
    {"pilot_role": role, "case_id": f"WB-CORE-{i:02}", "dataset_id": "D-WB"}
    for i, role in enumerate(PLAN.ORDER, 1)
]}


class RemainingExecutionPlanTests(unittest.TestCase):
    def test_plan_is_sequential_and_never_authorizes_execution(self):
        result = PLAN.build_plan(MATRIX)
        self.assertEqual(result["case_count"], 11)
        self.assertEqual([step["pilot_role"] for step in result["steps"]], list(PLAN.ORDER))
        self.assertTrue(result["sequential_policy"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["execution_started"])
        self.assertEqual(result["status"], "DRY_RUN_PLAN_ONLY")
        self.assertTrue(all(step["execution"] == "NOT_AUTHORIZED" for step in result["steps"]))

    def test_read_only_cases_precede_dialog_and_write_cases(self):
        result = PLAN.build_plan(MATRIX)
        classes = [step["side_effect_class"] for step in result["steps"]]
        self.assertEqual(classes[:6], ["read_only"] * 6)
        self.assertEqual(classes[6:8], ["dialog_cancel"] * 2)
        self.assertEqual(classes[8:], ["rejected_write", "successful_write", "successful_write"])

    def test_duplicate_role_rejected(self):
        matrix = {"include": MATRIX["include"] + [MATRIX["include"][0]]}
        with self.assertRaisesRegex(ValueError, "duplicate role"):
            PLAN.build_plan(matrix)

    def test_missing_role_rejected(self):
        matrix = {"include": MATRIX["include"][:-1]}
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            PLAN.build_plan(matrix)

    def test_duplicate_case_ids_rejected(self):
        matrix = {"include": [dict(item) for item in MATRIX["include"]]}
        matrix["include"][1]["case_id"] = matrix["include"][0]["case_id"]
        with self.assertRaisesRegex(ValueError, "case IDs must be unique"):
            PLAN.build_plan(matrix)

    def test_missing_dataset_id_rejected(self):
        matrix = {"include": [dict(item) for item in MATRIX["include"]]}
        del matrix["include"][0]["dataset_id"]
        with self.assertRaisesRegex(ValueError, "dataset_id missing"):
            PLAN.build_plan(matrix)


if __name__ == "__main__":
    unittest.main()
