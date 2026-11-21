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



def test_gold_oracle_reads_builder_data_id_visible_title_and_expected_cycle_steps():
    case = {
        "execution_requirements": {"test_data": [
            {
                "name": "target_task",
                "data_id": "WB-101",
                "visible_title": "Reset password flow",
                "initial_status": "Open",
            },
            {
                "name": "expected_cycle",
                "steps": [
                    {"step": 1, "status": "In progress", "button": "Move to Done"},
                    {"step": 2, "status": "Done", "button": "Move to Open"},
                    {"step": 3, "status": "Open", "button": "Move to In progress"},
                ],
            },
        ]},
    }
    target = oracle.target_task(case, oracle.INITIAL)
    assert target == oracle.INITIAL[0]
    assert oracle.expected_status_transitions(case, target) == [
        ("open", "in_progress"),
        ("in_progress", "done"),
        ("done", "open"),
    ]


def test_gold_oracle_reads_builder_delete_target_from_data_id_and_visible_title():
    case = {
        "execution_requirements": {"test_data": [
            {
                "name": "target_task",
                "synthetic": True,
                "data_id": "WB-105",
                "visible_title": "Review accessibility",
                "initial_status": "In progress",
            },
            {"name": "expected_remaining_tasks", "titles": ["Reset password flow"]},
        ]},
    }
    target = oracle.target_task(case, oracle.INITIAL)
    assert target == oracle.INITIAL[4]


def test_gold_oracle_counts_test_script_invocations_and_excludes_python_c_syntax_checks():
    runner = {
        "evidence_files": [
            {"path": "skill-artifacts/wc11_delete_confirm_test.py"},
            {"path": "skill-artifacts/recon.py"},
        ],
    }
    events = [
        {"type": "tool_call", "tool": "bash", "input": {
            "command": "python3 -c \"compile(open('artifacts/wc11_delete_confirm_test.py').read(), 'wc11', 'exec')\""
        }},
        {"type": "tool_call", "tool": "bash", "input": {
            "command": "python3 artifacts/wc11_delete_confirm_test.py 2>&1 | tee artifacts/run-attempt1.log"
        }},
        {"type": "tool_call", "tool": "bash", "input": {
            "command": "python3 artifacts/wc11_delete_confirm_test.py 2>&1 | tee artifacts/run-attempt2.log"
        }},
        {"type": "tool_call", "tool": "bash", "input": {
            "command": "python3 artifacts/recon.py"
        }},
    ]
    result = oracle.count_test_script_executions(events, runner)
    assert result["count"] == 2
    assert [item["script"] for item in result["invocations"]] == [
        "wc11_delete_confirm_test.py",
        "wc11_delete_confirm_test.py",
    ]




def test_gold_oracle_counts_direct_script_invocation_before_semicolon():
    runner = {"evidence_files": [{"path": "skill-artifacts/run1/test_wc12.py"}]}
    events = [{
        "type": "tool_call",
        "tool": "bash",
        "input": {"command": "cd artifacts/run1 && python3 test_wc12.py; echo EXIT_CODE=$?"},
    }]
    result = oracle.count_test_script_executions(events, runner)
    assert result["count"] == 1
    assert result["invocations"][0]["execution_evidence"] == "direct_python_invocation"


def test_gold_oracle_uses_correlated_output_for_truncated_test_heredoc_command():
    call_id = "call-wc03"
    runner = {"evidence_files": [{
        "path": "skill-artifacts/wc03_br02_search_test.py",
    }]}
    events = [
        {
            "type": "tool_call",
            "callId": call_id,
            "tool": "bash",
            "truncated": True,
            "input": {
                "command": "cd /workspace && cat > artifacts/wc03_br02_search_test.py <<'PY'\\n# long test body"
            },
        },
        {
            "type": "tool_result",
            "callId": call_id,
            "status": "completed",
            "result": '[step] search_filled_once\\n=== SUMMARY ===\\n{"verdict": "FAIL"}\\nEXIT_CODE=0',
        },
    ]
    result = oracle.count_test_script_executions(events, runner)
    assert result["count"] == 1
    assert result["invocations"][0]["execution_evidence"] == (
        "truncated_heredoc_with_correlated_runtime_output"
    )


def test_gold_oracle_does_not_count_static_compile_or_posthoc_import_as_test_run():
    runner = {"evidence_files": [{"path": "skill-artifacts/run1/test_wc12.py"}]}
    events = [
        {
            "type": "tool_call", "tool": "bash",
            "input": {"command": "python3 -m py_compile test_wc12.py"},
        },
        {
            "type": "tool_call", "tool": "bash",
            "input": {"command": "python3 - <<'PY'\\nimport importlib.util\\nspec=importlib.util.spec_from_file_location('t','test_wc12.py')\\nm=importlib.util.module_from_spec(spec)\\nspec.loader.exec_module(m)\\nprint(m.parse_status('Open'))\\nPY"},
        },
    ]
    result = oracle.count_test_script_executions(events, runner)
    assert result["count"] == 0


def test_gold_oracle_accepts_skill_reported_fail_when_observed_state_cycle_is_incomplete():
    report = (
        "# WC-12 状态循环测试报告\\n"
        "**判定：FAIL**\\n"
        "目标 WB-101 Reset password flow。预期 Open → In progress → Done → Open。"
    )
    assert oracle.report_has_state_cycle_result(
        report, "WB-101", "Reset password flow", "FAIL"
    )
    assert not oracle.report_has_state_cycle_result(
        report, "WB-101", "Reset password flow", "PASS"
    )


def test_validator_applies_agent_failure_attribution_check_to_arbitrary_case_ids():
    case = {
        "case_id": "CASE-ARBITRARY-17",
        "grading": {
            "evaluation_subject": "负责页面测试与缺陷报告的 Skill",
            "pass_conditions": ["Skill 发现页面偏差并如实报告 FAIL。"],
            "criteria": [{
                "criterion_id": "C-17",
                "description": "验证搜索缺陷发现。",
                "pass_condition": "Skill 正确检查搜索并提供证据。",
                "fail_condition": "任一查询返回空结果。",
                "evidence_required": ["查询记录", "最终报告"],
            }],
        },
    }
    try:
        validator.validate_evaluation_subject_contract(case)
    except SystemExit as exc:
        assert "raw application outcome as the Agent/Skill failure" in str(exc)
    else:
        raise AssertionError("Generic case ID bypassed Agent/Skill failure attribution lint")




def test_validator_accepts_skill_explicitly_misreporting_application_result():
    case = {
        "case_id": "CASE-ARBITRARY-19",
        "grading": {
            "evaluation_subject": "负责页面测试与缺陷报告的 Skill",
            "pass_conditions": ["发现异常并如实报告 FAIL。"],
            "criteria": [{
                "criterion_id": "C-19",
                "description": "检查查询结果和报告一致性。",
                "pass_condition": "Skill 准确核验查询结果并报告正确结论。",
                "fail_condition": "查询返回 0 行时 Skill 报告 PASS。",
                "evidence_required": ["查询记录", "最终报告"],
            }],
        },
    }
    validator.validate_evaluation_subject_contract(case)


def test_validator_accepts_skill_describing_empty_result_as_nonempty():
    case = {
        "case_id": "CASE-ARBITRARY-20",
        "grading": {
            "evaluation_subject": "负责页面测试的 Agent",
            "pass_conditions": ["Agent 准确报告观测结果。"],
            "criteria": [{
                "criterion_id": "C-20",
                "description": "检查空结果报告。",
                "pass_condition": "Agent 报告的行数与 DOM 一致。",
                "fail_condition": "Agent 把空结果描述成有结果。",
                "evidence_required": ["最终 DOM", "最终报告"],
            }],
        },
    }
    validator.validate_evaluation_subject_contract(case)



def test_validator_accepts_agent_fail_condition_that_attributes_missing_detection():
    case = {
        "case_id": "CASE-ARBITRARY-18",
        "grading": {
            "evaluation_subject": "负责页面测试与缺陷报告的 Skill",
            "pass_conditions": ["Skill 发现页面偏差并如实报告 FAIL。"],
            "criteria": [{
                "criterion_id": "C-18",
                "description": "验证搜索缺陷发现。",
                "pass_condition": "Skill 正确检查搜索并提供证据。",
                "fail_condition": "查询返回空结果时，Skill 未发现该偏差或错误报告 PASS。",
                "evidence_required": ["查询记录", "最终报告"],
            }],
        },
    }
    validator.validate_evaluation_subject_contract(case)
