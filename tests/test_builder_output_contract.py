"""Contract regressions for Builder-authored nested execution requirements."""
from pathlib import Path
import json
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


def test_gold_oracle_detects_builder_declared_delete_cancel_scenario():
    case = {
        "user_input": "点击 Delete 打开对话框，然后点击 Cancel。不要点击 Delete task。",
        "execution_requirements": {"test_data": [{
            "kind": "delete_cancel",
            "task_id": "WB-103",
            "expected_rule_state": {
                "dialog_shown": True,
                "cancel_closes": True,
                "task_retained": "WB-103",
            },
        }]},
    }
    assert oracle.is_delete_cancel_case(case)


def test_gold_oracle_does_not_classify_confirmed_delete_as_cancel():
    case = {
        "user_input": "点击 Delete 打开对话框，然后点击 Delete task 确认删除。",
        "execution_requirements": {"test_data": [{
            "kind": "delete_confirm",
            "task_id": "WB-103",
        }]},
    }
    assert not oracle.is_delete_cancel_case(case)



def test_validator_rejects_sut_failure_as_agent_failure():
    contradictory = {
        "case_id": "WBT-CORE-02-SEARCH-MATCH",
        "grading": {
            "evaluation_subject": "webapp-testing Skill 的测试与缺陷识别表现",
            "pass_conditions": ["若结果不符合规则，Skill 如实报告 FAIL 并提供证据。"],
            "criteria": [{
                "criterion_id": "WBT-CORE-02-G2",
                "pass_condition": "查询结果恰好符合业务规则。",
                "fail_condition": "任一查询返回空或返回多余任务。",
            }],
        },
    }
    try:
        validator.validate_evaluation_subject_contract(contradictory)
    except SystemExit as exc:
        assert "application defect as the Skill's failure" in str(exc)
    else:
        raise AssertionError("Contradictory grading contract was accepted")


def test_validator_accepts_truthful_defect_detection_by_test_skill():
    coherent = {
        "case_id": "WBT-CORE-02-SEARCH-MATCH",
        "grading": {
            "evaluation_subject": "webapp-testing Skill 的测试与缺陷识别表现",
            "pass_conditions": ["若结果不符合规则，Skill 如实报告 FAIL 并提供证据。"],
            "criteria": [{
                "criterion_id": "WBT-CORE-02-G2",
                "pass_condition": "Skill 准确识别查询结果与 BR-02 的差异，并如实报告 FAIL。",
                "fail_condition": "Skill 未发现差异、错误报告 PASS，或证据不足却作出确定结论。",
            }],
        },
    }
    validator.validate_evaluation_subject_contract(coherent)


def test_dataset_schema_requires_explicit_grading_evaluation_subject():
    schema_path = ROOT / "skills" / "evaluation-dataset-builder" / "references" / "dataset-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    grading = schema["properties"]["grading"]
    assert "evaluation_subject" in grading["required"]
    assert grading["properties"]["evaluation_subject"]["type"] == "string"
    assert grading["properties"]["evaluation_subject"]["minLength"] == 1
