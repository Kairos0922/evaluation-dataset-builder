import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "benchmarks" / "webapp-testing" / "scripts" / "validate_builder_output.py"
SPEC = importlib.util.spec_from_file_location("validate_builder_output", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


RESOLVER_PATH = ROOT / "benchmarks" / "webapp-testing" / "scripts" / "resolve_pilot_matrix.py"
RESOLVER_SPEC = importlib.util.spec_from_file_location("resolve_pilot_matrix", RESOLVER_PATH)
RESOLVER = importlib.util.module_from_spec(RESOLVER_SPEC)
RESOLVER_SPEC.loader.exec_module(RESOLVER)

class BuilderExecutionTimeoutTests(unittest.TestCase):
    def test_contract_level_timeout_is_accepted(self):
        self.assertEqual(
            VALIDATOR.validate_case_timeout_seconds("CASE-01", {"case_timeout_seconds": 300}),
            300,
        )

    def test_pilot_resolver_accepts_contract_level_timeout(self):
        self.assertEqual(
            RESOLVER.validate_case_timeout_seconds("CASE-01", {"case_timeout_seconds": 300}),
            300,
        )

    def test_pilot_resolver_rejects_missing_timeout_contract(self):
        with self.assertRaisesRegex(SystemExit, "execution_requirements.case_timeout_seconds"):
            RESOLVER.validate_case_timeout_seconds("CASE-01", {})

    def test_environment_timeout_is_not_a_substitute_for_required_contract_field(self):
        with self.assertRaisesRegex(SystemExit, "execution_requirements.case_timeout_seconds"):
            VALIDATOR.validate_case_timeout_seconds("CASE-01", {})

    def test_timeout_must_be_between_one_and_nine_hundred(self):
        for value in (0, 901, -1):
            with self.subTest(value=value):
                with self.assertRaisesRegex(SystemExit, "integer from 1 to 900"):
                    VALIDATOR.validate_case_timeout_seconds("CASE-01", {"case_timeout_seconds": value})

    def test_boolean_is_not_accepted_as_integer_timeout(self):
        with self.assertRaisesRegex(SystemExit, "integer from 1 to 900"):
            VALIDATOR.validate_case_timeout_seconds("CASE-01", {"case_timeout_seconds": True})


if __name__ == "__main__":
    unittest.main()
