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






def test_validator_rejects_bare_sut_outcome_even_when_another_clause_is_agent_attributed():
    case = {
        "case_id": "CASE-ARBITRARY-21",
        "grading": {
            "evaluation_subject": "web page testing Skill",
            "pass_conditions": ["Skill correctly reports observed defects."],
            "criteria": [{
                "criterion_id": "C-21",
                "description": "Checks summary consistency.",
                "pass_condition": "Skill reads each summary and reports deviations.",
                "fail_condition": "Skill does not compare each step, summary value differs from the DOM.",
                "evidence_required": ["step summaries", "DOM"],
            }],
        },
    }
    try:
        validator.validate_evaluation_subject_contract(case)
    except SystemExit as exc:
        assert "raw application outcome" in str(exc)
    else:
        raise AssertionError("A bare SUT mismatch clause was masked by a neighboring agent-behavior clause")


def test_validator_accepts_each_clause_when_it_attributes_the_failure_to_agent_behavior():
    case = {
        "case_id": "CASE-ARBITRARY-22",
        "grading": {
            "evaluation_subject": "web page testing Skill",
            "pass_conditions": ["Skill correctly reports observed defects."],
            "criteria": [{
                "criterion_id": "C-22",
                "description": "Checks summary consistency.",
                "pass_condition": "Skill reads each summary and reports deviations.",
                "fail_condition": "Skill does not compare each step; Skill ignores a summary that is out of sync.",
                "evidence_required": ["step summaries", "DOM"],
            }],
        },
    }
    validator.validate_evaluation_subject_contract(case)





def test_validator_rejects_raw_summary_mismatch_clause_in_multi_clause_criterion():
    case = {
        "case_id": "WC-12-LIKE",
        "grading": {
            "evaluation_subject": "webapp-testing Skill",
            "criteria": [{
                "criterion_id": "C-SUMMARY",
                "description": "The Skill reports every intermediate summary.",
                "pass_condition": "The Skill reports actual values and identifies any desynchronization.",
                "fail_condition": "只读取最终摘要、未逐步对照、摘要值与 DOM 不一致，或忽略摘要未同步。",
                "evidence_required": ["intermediate summary snapshots"],
            }],
        },
    }
    try:
        validator.validate_evaluation_subject_contract(case)
    except SystemExit as exc:
        assert "摘要值与 DOM 不一致" in str(exc)
    else:
        raise AssertionError("A raw application-summary mismatch clause was accepted")


def test_validator_rejects_ambiguous_priority_status_mismatch_clause():
    case = {
        "case_id": "WC-09-LIKE",
        "grading": {
            "evaluation_subject": "webapp-testing Skill",
            "criteria": [{
                "criterion_id": "C-OBSERVE",
                "description": "The Skill reads the created task fields.",
                "pass_condition": "The Skill reports actual priority and status from DOM and response.",
                "fail_condition": "报告长度不是 80，或优先级/状态不一致。",
                "evidence_required": ["DOM snapshot", "POST response"],
            }],
        },
    }
    try:
        validator.validate_evaluation_subject_contract(case)
    except SystemExit as exc:
        assert "优先级/状态不一致" in str(exc)
    else:
        raise AssertionError("An ambiguous priority/status mismatch clause was accepted")


def test_validator_accepts_report_to_dom_mismatch_as_agent_error():
    case = {
        "case_id": "CASE-ARBITRARY-23",
        "grading": {
            "evaluation_subject": "webapp-testing Skill",
            "criteria": [{
                "criterion_id": "C-REPORT",
                "description": "The Skill reports actual DOM values.",
                "pass_condition": "The Skill's report matches the observed DOM.",
                "fail_condition": "报告与实际 DOM 不一致。",
                "evidence_required": ["DOM", "report"],
            }],
        },
    }
    validator.validate_evaluation_subject_contract(case)





def test_validator_collects_wc12_like_state_and_summary_contract_issues():
    case = {
        "case_id": "CASE-WC12-LIKE",
        "grading": {
            "evaluation_subject": "webapp-testing Skill",
            "criteria": [
                {
                    "criterion_id": "C3-STATUS",
                    "description": "Skill reports each status and button step.",
                    "pass_condition": "Skill reports each step from the observed DOM and flags deviations from the expected cycle.",
                    "fail_condition": "缺少某一步、状态/按钮序列与 DOM 不一致、或只报告最终状态。",
                    "evidence_required": ["step DOM", "PATCH trace"],
                },
                {
                    "criterion_id": "C4-SUMMARY",
                    "description": "Skill reports each summary value.",
                    "pass_condition": "Skill reports actual summary values and identifies any desynchronization.",
                    "fail_condition": "只读取最终摘要、未逐步对照、摘要值与 DOM 不一致，或忽略摘要未同步。",
                    "evidence_required": ["summary DOM snapshots"],
                },
            ],
        },
    }
    issues = validator.evaluation_subject_contract_issues(case)
    assert len(issues) == 2
    assert any("C3-STATUS" in issue and "状态/按钮序列与 DOM 不一致" in issue for issue in issues)
    assert any("C4-SUMMARY" in issue and "摘要值与 DOM 不一致" in issue for issue in issues)


def test_validator_flags_ambiguous_priority_and_status_condition_for_arbitrary_case():
    case = {
        "case_id": "CASE-WC09-LIKE",
        "grading": {
            "evaluation_subject": "webapp-testing Skill",
            "criteria": [{
                "criterion_id": "C3-OBSERVE",
                "description": "Skill reports title length, priority and status from actual evidence.",
                "pass_condition": "Skill reports actual values and flags deviations from expected business behavior.",
                "fail_condition": "只读取视觉截断文本、未计算字符长度、报告长度不是 80，或优先级/状态不一致。",
                "evidence_required": ["DOM", "POST response"],
            }],
        },
    }
    issues = validator.evaluation_subject_contract_issues(case)
    assert len(issues) == 1
    assert "优先级/状态不一致" in issues[0]



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
                "fail_condition": "查询返回空结果时 Skill 未发现该偏差或错误报告 PASS.",
                "evidence_required": ["查询记录", "最终报告"],
            }],
        },
    }
    validator.validate_evaluation_subject_contract(case)


def test_semantic_contract_lint_failure_is_machine_readable():
    issues = [
        "Case WC-09 criterion C3 has an ambiguous priority/status mismatch condition.",
        "Case WC-12 criterion C3 has a bare status/DOM mismatch condition.",
        "Case WC-12 criterion C4 has a bare summary/DOM mismatch condition.",
    ]
    report = validator.semantic_contract_failure_report(issues)
    assert report["status"] == "FAIL"
    assert report["scope"] == "agent_skill_grading_subject_semantics"
    assert report["issue_count"] == 3
    assert report["issues"] == issues
    assert "immutable output was not modified" in report["interpretation"]


def test_validator_accepts_agent_attribution_phrases_in_round3_builder_output():
    cases = [
        "Skill 在摘要与任务集合不一致时仍报告 BR-01 PASS",
        "把应用偏差写成 Skill 失败",
        "在摘要未更新时仍称同步符合",
        "Skill 在应用错误接受时仍报 PASS",
        "在摘要未同步时仍称符合",
        "在摘要未同步时称符合",
    ]
    for index, clause in enumerate(cases, start=1):
        case = {
            "case_id": f"ROUND3-FALSE-POSITIVE-{index}",
            "grading": {
                "evaluation_subject": "webapp-testing Skill 的测试与缺陷识别表现",
                "criteria": [{
                    "criterion_id": f"C-{index}",
                    "pass_condition": "Skill 根据实际证据准确报告应用偏差。",
                    "fail_condition": clause,
                }],
            },
        }
        assert validator.evaluation_subject_contract_issues(case) == [], clause


def test_validator_still_rejects_unattributed_application_outcome_clauses():
    cases = [
        "应用摘要未同步",
        "查询返回空结果",
        "页面状态与预期不一致",
        "应用错误接受空白标题",
    ]
    for index, clause in enumerate(cases, start=1):
        case = {
            "case_id": f"RAW-SUT-OUTCOME-{index}",
            "grading": {
                "evaluation_subject": "webapp-testing Skill 的测试与缺陷识别表现",
                "criteria": [{
                    "criterion_id": f"C-{index}",
                    "pass_condition": "Skill准确报告观察结果。",
                    "fail_condition": clause,
                }],
            },
        }
        assert validator.evaluation_subject_contract_issues(case), clause


def test_validator_accepts_round4_builder_fail_conditions_with_explicit_skill_attribution():
    cases = [
        ("WB-03-C3", "Skill 漏报描述字段未匹配、空状态缺失或摘要变化，或把应用偏差直接写成Skill失败。"),
        ("WB-04-C2", "Skill 遗漏某个筛选值的结果，或报告数量/标题/摘要与 DOM/截图不一致。"),
        ("WB-14-C2", "Skill 遗漏任务、报告状态/标签与 DOM 不一致，或把期望标签写成已观察值。"),
    ]
    for case_id, fail_condition in cases:
        case = {
            "case_id": case_id,
            "grading": {
                "evaluation_subject": "webapp-testing Skill 的测试与缺陷识别表现",
                "criteria": [{
                    "criterion_id": case_id,
                    "pass_condition": "Skill 根据实际证据准确报告偏差。",
                    "fail_condition": fail_condition,
                }],
            },
        }
        assert validator.evaluation_subject_contract_issues(case) == [], fail_condition


def test_validator_still_flags_raw_sut_clause_after_agent_clause_boundary():
    case = {
        "case_id": "CASE-ROUND4-INDEPENDENT-RAW",
        "grading": {
            "evaluation_subject": "webapp-testing Skill",
            "criteria": [{
                "criterion_id": "C-1",
                "pass_condition": "Skill accurately reports observations.",
                "fail_condition": "Skill 漏报一个字段；页面状态与预期不一致。",
            }],
        },
    }
    issues = validator.evaluation_subject_contract_issues(case)
    assert len(issues) == 1
    assert "页面状态与预期不一致" in issues[0]


def test_validator_accepts_round4_wb15_explicit_agent_fail_condition():
    case = {
        "case_id": "WB-15-C2",
        "grading": {
            "evaluation_subject": "webapp-testing Skill 的测试与缺陷识别表现",
            "criteria": [{
                "criterion_id": "WB-15-C2",
                "pass_condition": "Skill 报告 BR-09 请求失败分支无法权威验证，不把合成网络拦截结果当作权威结论。",
                "fail_condition": "Skill 在无受控注入时强行判 BR-09 PASS/FAIL，或把自行 route.abort 的合成结果当作应用符合/不符合的权威证据。",
            }],
        },
    }
    assert validator.evaluation_subject_contract_issues(case) == []


def test_validator_preserves_chinese_omission_scope_over_enumerated_outcomes():
    cases = [
        ("CASE-WB03", "Skill 漏报描述字段未匹配、空状态缺失或摘要变化"),
        ("CASE-WB04", "Skill 遗漏某个筛选值的结果，或报告数量/标题/摘要与 DOM/截图不一致"),
        ("CASE-WB14", "Skill 遗漏任务，报告状态/标签与 DOM 不一致，或把期望标签写成已观察值"),
    ]
    for case_id, fail_condition in cases:
        case = {
            "case_id": case_id,
            "grading": {
                "evaluation_subject": "webapp-testing Skill 的测试与缺陷识别表现",
                "criteria": [{
                    "criterion_id": "C-1",
                    "pass_condition": "Skill 根据实际证据准确报告偏差。",
                    "fail_condition": fail_condition,
                }],
            },
        }
        assert validator.evaluation_subject_contract_issues(case) == [], fail_condition


def test_validator_still_rejects_independent_raw_outcome_after_omission_clause():
    case = {
        "case_id": "CASE-INDEPENDENT-RAW",
        "grading": {
            "evaluation_subject": "webapp-testing Skill",
            "criteria": [{
                "criterion_id": "C-1",
                "pass_condition": "Skill accurately reports observations.",
                "fail_condition": "Skill 漏报一个字段；页面状态与预期不一致。",
            }],
        },
    }
    issues = validator.evaluation_subject_contract_issues(case)
    assert len(issues) == 1
    assert "页面状态与预期不一致" in issues[0]
