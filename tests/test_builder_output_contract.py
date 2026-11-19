"""Contract regressions for Builder-authored nested execution requirements."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "benchmarks" / "webapp-testing" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_builder_output as validator
import resolve_pilot_matrix as pilot_selector
import gold_oracle as oracle


def test_timeout_is_read_from_nested_builder_environment_and_validated():
    nested = {"environment": {"case_timeout_seconds": 300}}
    direct_legacy = {"case_timeout_seconds": 120}
    assert validator.validate_case_timeout_seconds("WB-AUDIT-01", nested) == 300
    assert validator.validate_case_timeout_seconds("WB-CORE-02", direct_legacy) == 120
    assert pilot_selector.validate_case_timeout_seconds("WB-AUDIT-01", nested) == 300
    assert pilot_selector.validate_case_timeout_seconds("WB-CORE-02", direct_legacy) == 120


def test_nested_timeout_still_fails_closed_for_invalid_values():
    for value in (0, 901, "300", True, None):
        execution = {"environment": {"case_timeout_seconds": value}}
        try:
            validator.validate_case_timeout_seconds("BAD", execution)
        except SystemExit:
            pass
        else:
            raise AssertionError(f"Invalid timeout unexpectedly accepted: {value!r}")
        try:
            pilot_selector.validate_case_timeout_seconds("BAD", execution)
        except SystemExit:
            pass
        else:
            raise AssertionError(f"Pilot selector accepted invalid timeout: {value!r}")


def test_gold_oracle_reads_builder_task_id_and_expected_sequence_fields():
    case = {
        "execution_requirements": {"test_data": [{
            "task_id": "WB-101",
            "expected": ["open", "in_progress", "done", "open"],
        }]},
    }
    target = oracle.target_task(case, oracle.INITIAL)
    assert target and target["id"] == "WB-101"
    assert oracle.expected_status_transitions(case, target) == [
        ("open", "in_progress"),
        ("in_progress", "done"),
        ("done", "open"),
    ]


def test_gold_oracle_resolves_builder_delete_target_from_task_id():
    case = {
        "execution_requirements": {"test_data": [{
            "task_id": "WB-102",
            "expected_remaining": ["WB-101", "WB-103", "WB-104", "WB-105"],
        }]},
    }
    target = oracle.target_task(case, oracle.INITIAL)
    assert target and target["id"] == "WB-102"
