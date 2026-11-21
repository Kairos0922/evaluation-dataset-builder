#!/usr/bin/env python3
"""Select three semantic pilots from Builder-authored cases.

The selector uses only the generated suite. It does not invent or modify cases.
The current source corpus supports a single-turn diagnostic search test, a
within-session state cycle, and a delete-confirmation workflow. It does not
justify labelling a case multi_turn merely because one user message contains
several UI steps.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath

PILOT_ROLES = ("search_mutation", "state_cycle", "delete_confirmation")
# The default selector remains the already-accepted three-case pilot. This
# opt-in list contains only the eleven unexecuted Builder-authored cases.
REMAINING_ROLES = (
    "initial_board",
    "search_description",
    "search_empty",
    "status_filter",
    "search_filter_combo",
    "accessible_names",
    "visible_title_mapping",
    "create_success",
    "create_rejected",
    "create_boundary_80",
    "delete_cancel",
)
ALLOWED_QUALITY = {"candidate", "needs_info"}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def user_message(case: dict) -> str:
    value = case.get("user_input")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(
            str(item.get("content") or item.get("message") or item.get("prompt") or "")
            if isinstance(item, dict) else str(item)
            for item in value
        )
    return ""


def case_text(case: dict) -> str:
    keys = (
        "title", "objective", "evaluation_target", "expected_behavior",
        "forbidden_behavior", "capability_keys", "scenario_bucket",
        "business_rule_refs", "workflow_refs", "coverage_tags",
    )
    return " ".join(str(case.get(key, "")) for key in keys) + " " + user_message(case)


def role_score(case: dict, role: str) -> int:
    text = case_text(case).casefold()
    message = user_message(case).casefold()
    rules = set(case.get("business_rule_refs") or [])
    workflows = set(case.get("workflow_refs") or [])
    buckets = set(case.get("scenario_bucket") or [])
    has_rule = lambda prefix: any(isinstance(rule, str) and rule.startswith(prefix) for rule in rules)

    if role == "search_mutation":
        # Require the user request itself to challenge a case-sensitivity
        # claim. Metadata alone must not turn a broad audit into this pilot.
        has_search = any(term in message for term in ("search", "搜索"))
        is_focused_search_case = not any(term in message for term in ("分诊", "连续操作", "回归"))
        # Builder-generated requests may express the probe as "大写形式查询 TOKEN"
        # rather than the exact phrase "大写查询". BR-02 is authoritative,
        # and an uppercase token is sufficient evidence of the case-sensitivity probe.
        has_uppercase_probe = bool(re.search(r"\b[A-Z]{2,}\b", user_message(case)))
        # Builder output may state this contract in the case title/objective
        # while the user request demonstrates it with an uppercase query.
        search_contract_text = " ".join(
            str(case.get(key, "")) for key in ("title", "objective", "expected_behavior")
        ).casefold() + " " + message
        explicitly_tests_case_sensitivity = any(
            phrase in search_contract_text
            for phrase in ("不区分大小写", "大小写不敏感", "大小写敏感", "case-insensitive", "case sensitive")
        )
        if (
            has_rule("BR-02")
            and (not workflows or any(ref.startswith(("WF-SEARCH", "WF-02")) for ref in workflows))
            and has_search
            and is_focused_search_case
            and has_uppercase_probe
            and explicitly_tests_case_sensitivity
        ):
            return 300 + len(message)

    elif role == "state_cycle":
        # Builder cases may express the cycle through three explicit workflow
        # refs and a three-click instruction rather than a literal arrow string.
        # Require the complete transition coverage plus a three-step request,
        # and reject cases explicitly marked multi-turn.
        normalized_message = re.sub(r"\s+", "", message).replace("->", "→")
        explicit_cycle = "open→inprogress→done→open" in normalized_message
        complete_workflow_refs = {"WF-01", "WF-02", "WF-03"}.issubset(workflows)
        compact_message = "".join(message.casefold().split())
        three_click_request = (
            ("三次" in compact_message or "3次" in compact_message)
            and ("点击" in message or "click" in message)
            and ("状态按钮" in message or "status button" in message)
        )
        expected_contract = "".join(
            (message + " " + " ".join(
                str(item) for item in (case.get("expected_behavior") or [])
            )).casefold().split()
        )
        expected_transitions = all(
            state in text for state in ("open", "in progress", "done")
        )
        ordered_expected_steps = True
        previous_position = -1
        for number, chinese_ordinal, state in (
            (1, "第一次", "inprogress"),
            (2, "第二次", "done"),
            (3, "第三次", "open"),
        ):
            ordinal_candidates = (
                expected_contract.find(f"第{number}次"),
                expected_contract.find(chinese_ordinal),
            )
            step_position = min((p for p in ordinal_candidates if p >= 0), default=-1)
            state_position = expected_contract.find(state, step_position + 1)
            if step_position <= previous_position or state_position <= step_position:
                ordered_expected_steps = False
                break
            previous_position = state_position
        builder_status_cycle = (
            has_rule("BR-07")
            and (
                not workflows
                or any(ref.startswith(("WF-STATUS", "WF-05")) for ref in workflows)
            )
            and three_click_request
            and expected_transitions
            and ordered_expected_steps
        )
        has_cycle = explicit_cycle or (
            complete_workflow_refs and three_click_request and expected_transitions
        ) or builder_status_cycle
        if (
            has_rule("BR-07")
            and (not workflows or any(ref.startswith(("WF-STATUS", "WF-05", "WF-01")) for ref in workflows))
            and has_cycle
            and "multi_turn" not in buckets
        ):
            return 200 + len(message)

    elif role == "delete_confirmation":
        has_confirmation = any(
            term in message for term in ("delete task", "confirm delete", "点击确认删除按钮")
        )
        has_delete_action = any(term in message for term in ("点击 delete", "click delete", "删除"))
        if (
            has_rule("BR-08")
            and (not workflows or any(ref.startswith(("WF-DELETE", "WF-07", "WF-08")) for ref in workflows))
            and has_confirmation
            and has_delete_action
        ):
            return 100 + len(message)

    remaining_specs = {
        "initial_board": ("initial_board", ("BR-01",), ("WF-INITIAL",)),
        "search_description": ("search_description", ("BR-02",), ("WF-SEARCH",)),
        "search_empty": ("search_empty", ("BR-02",), ("WF-SEARCH",)),
        "status_filter": ("status_filter", ("BR-03",), ("WF-FILTER",)),
        "search_filter_combo": ("search_filter_combo", ("BR-02", "BR-03"), ("WF-SEARCH", "WF-FILTER")),
        "accessible_names": ("accessible_names", ("BR-10",), ("WF-INITIAL",)),
        "visible_title_mapping": ("recon_only", ("BR-07",), ("WF-INITIAL",)),
        "create_success": ("create_task", ("BR-01", "BR-04", "BR-05", "BR-06"), ("WF-CREATE-DEFAULT",)),
        "create_rejected": ("invalid_create", ("BR-04",), ("WF-CREATE-BOUNDARY",)),
        "create_boundary_80": ("boundary_create", ("BR-01", "BR-04", "BR-05", "BR-06"), ("WF-CREATE-BOUNDARY",)),
        "delete_cancel": ("delete_cancel", ("BR-08",), ("WF-DELETE-CANCEL",)),
    }
    if role in remaining_specs:
        expected_kind, required_rules, required_workflows = remaining_specs[role]
        test_data = ((case.get("execution_requirements") or {}).get("test_data") or [])
        kinds = {
            item.get("kind") for item in test_data
            if isinstance(item, dict) and isinstance(item.get("kind"), str)
        }
        # The Builder's structured test-data kind is the primary semantic
        # discriminator. Rules and workflow refs are corroborating evidence;
        # titles or user prose alone never make a case eligible.
        if (
            expected_kind in kinds
            and all(has_rule(rule) for rule in required_rules)
            and all(
                any(isinstance(ref, str) and ref.startswith(prefix) for ref in workflows)
                for prefix in required_workflows
            )
        ):
            return 1000 + len(message)

    return 0


def validate_case_timeout_seconds(case_id: str, execution: dict) -> int:
    environment = execution.get("environment") or {}
    timeout = environment.get("case_timeout_seconds")
    if timeout is None:
        timeout = execution.get("case_timeout_seconds")
    if type(timeout) is not int or not 1 <= timeout <= 900:
        fail(f"{case_id}: execution_requirements.case_timeout_seconds must be 1..900")
    return timeout


def validate_case(case: dict, dataset_id: str) -> None:
    case_id = case.get("case_id", "<missing>")
    if case.get("quality_status") != "candidate":
        fail(f"{dataset_id}/{case_id}: pilot requires quality_status=candidate")
    if case.get("execution_requirements", {}).get("status") != "NOT_RUN":
        fail(f"{dataset_id}/{case_id}: execution status must remain NOT_RUN")
    execution = case.get("execution_requirements") or {}
    environment = execution.get("environment")
    if not isinstance(environment, dict):
        fail(f"{dataset_id}/{case_id}: execution environment is missing")
    if environment.get("app_url") != "http://127.0.0.1:4173":
        fail(f"{dataset_id}/{case_id}: app_url must target the local fixture")
    validate_case_timeout_seconds(case_id, execution)
    if environment.get("server_state_at_start", "running") != "running":
        fail(f"{dataset_id}/{case_id}: server_state_at_start must be running")
    gaps = case.get("information_gaps") or []
    if any(isinstance(g, dict) and g.get("status") in {"OPEN", "IN_PROGRESS"} for g in gaps):
        fail(f"{dataset_id}/{case_id}: unresolved information gaps block pilot execution")


def load_suite(root: Path, roles: tuple[str, ...] = PILOT_ROLES) -> dict:
    root = root.resolve()
    manifest_path = root / "SUITE-MANIFEST.json"
    if not manifest_path.is_file():
        fail("SUITE-MANIFEST.json is missing")
    suite = json.loads(manifest_path.read_text(encoding="utf-8"))
    if suite.get("quality_status") not in ALLOWED_QUALITY:
        fail("suite quality_status must be candidate or needs_info")
    if suite.get("execution_status") != "NOT_RUN":
        fail("suite execution_status must be NOT_RUN")
    datasets = suite.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        fail("suite datasets must be a non-empty array")

    all_cases: list[dict] = []
    seen: set[str] = set()
    for dataset in datasets:
        dataset_id = dataset.get("dataset_id")
        relative = dataset.get("jsonl")
        if not isinstance(dataset_id, str) or not dataset_id:
            fail("dataset_id must be a non-empty string")
        if dataset.get("quality_status") not in ALLOWED_QUALITY:
            fail(f"{dataset_id}: invalid quality status")
        if dataset.get("execution_status") != "NOT_RUN":
            fail(f"{dataset_id}: dataset execution_status must be NOT_RUN")
        rel = PurePosixPath(str(relative or ""))
        if rel.is_absolute() or ".." in rel.parts:
            fail(f"{dataset_id}: unsafe JSONL path")
        jsonl = (root / Path(*rel.parts)).resolve()
        if root not in jsonl.parents or not jsonl.is_file():
            fail(f"{dataset_id}: JSONL does not resolve inside suite output")
        count = 0
        for number, line in enumerate(jsonl.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            count += 1
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(f"{dataset_id}:{number}: invalid JSON: {exc}")
            case_id = case.get("case_id")
            if not isinstance(case_id, str) or not case_id or case_id in seen:
                fail(f"{dataset_id}:{number}: missing or duplicate case_id")
            seen.add(case_id)
            if case.get("dataset_id") != dataset_id:
                fail(f"{dataset_id}/{case_id}: dataset_id mismatch")
            if case.get("quality_status") not in ALLOWED_QUALITY:
                fail(f"{dataset_id}/{case_id}: invalid quality_status")
            if case.get("quality_status") == "candidate":
                validate_case(case, dataset_id)
                all_cases.append(case)
        if type(dataset.get("case_count")) is not int or count != dataset["case_count"]:
            fail(f"{dataset_id}: manifest case_count differs from JSONL")

    selected: list[tuple[dict, str]] = []
    used: set[str] = set()
    for role in roles:
        scored = [(role_score(case, role), case) for case in all_cases if case["case_id"] not in used]
        scored = [(score, case) for score, case in scored if score > 0]
        if not scored:
            fail(f"no candidate case matches pilot role {role}; do not fabricate a replacement")
        best_score = max(score for score, _ in scored)
        best = [case for score, case in scored if score == best_score]
        if len(best) != 1:
            fail(f"pilot role {role} is ambiguous: {[c['case_id'] for c in best]}")
        case = best[0]
        selected.append((case, role))
        used.add(case["case_id"])

    entries = []
    for case, role in selected:
        dataset_id = case["dataset_id"]
        dataset = next(item for item in datasets if item["dataset_id"] == dataset_id)
        mutant = role == "search_mutation"
        entries.append({
            "dataset_id": dataset_id,
            "dataset_path": dataset["jsonl"],
            "case_id": case["case_id"],
            "pilot_role": role,
            "fixture_profile": "mutant" if mutant else "clean",
            "fixture_mutations": ["search-case-sensitive"] if mutant else [],
        })
    return {"include": entries}


def self_test() -> int:
    # Regression: every remaining case is classified only when its structured
    # test-data kind and source-backed rule/workflow references agree.
    remaining_examples = {
        "initial_board": ("initial_board", ["BR-01"], ["WF-INITIAL"]),
        "search_description": ("search_description", ["BR-02"], ["WF-SEARCH"]),
        "search_empty": ("search_empty", ["BR-02"], ["WF-SEARCH"]),
        "status_filter": ("status_filter", ["BR-03"], ["WF-FILTER"]),
        "search_filter_combo": ("search_filter_combo", ["BR-02", "BR-03"], ["WF-SEARCH", "WF-FILTER"]),
        "accessible_names": ("accessible_names", ["BR-10"], ["WF-INITIAL"]),
        "visible_title_mapping": ("recon_only", ["BR-07"], ["WF-INITIAL"]),
        "create_success": ("create_task", ["BR-01", "BR-04", "BR-05", "BR-06"], ["WF-CREATE-DEFAULT"]),
        "create_rejected": ("invalid_create", ["BR-04"], ["WF-CREATE-BOUNDARY"]),
        "create_boundary_80": ("boundary_create", ["BR-01", "BR-04", "BR-05", "BR-06"], ["WF-CREATE-BOUNDARY"]),
        "delete_cancel": ("delete_cancel", ["BR-08"], ["WF-DELETE-CANCEL"]),
    }
    for role, (kind, rules, workflows) in remaining_examples.items():
        example = {
            "business_rule_refs": rules,
            "workflow_refs": workflows,
            "user_input": "Run the structured Builder-authored case once.",
            "execution_requirements": {"test_data": [{"kind": kind}]},
        }
        if role_score(example, role) <= 0:
            fail(f"remaining Builder case shape did not resolve: {role}")
        wrong_kind = {
            **example,
            "execution_requirements": {"test_data": [{"kind": "unrelated"}]},
        }
        if role_score(wrong_kind, role) != 0:
            fail(f"selector accepted unrelated test-data kind for {role}")

    # Regression: Builder-authored BR-02 cases may put "大小写不敏感" in the
    # title and demonstrate it through an uppercase query, without repeating
    # that exact phrase in user_input.
    builder_search_shape = {
        "title": "搜索大小写不敏感且同时匹配标题与描述",
        "objective": "验证搜索大小写不敏感，并匹配标题与描述。",
        "business_rule_refs": ["BR-02"],
        "workflow_refs": ["WF-SEARCH"],
        "scenario_bucket": ["normal", "business_rule"],
        "user_input": "验证搜索：依次输入 reset、SCREENSHOTS、email，记录结果；预期 SCREENSHOTS 命中 WB-102。",
        "expected_behavior": ["SCREENSHOTS 命中 WB-102，证明大小写不敏感。"],
    }
    if role_score(builder_search_shape, "search_mutation") <= 0:
        fail("Builder-shaped BR-02 search case did not resolve to search_mutation")

    # Regression: Builder may use WF-STATUS and ordered per-click expectations
    # instead of WF-01/WF-02/WF-03 or a literal transition arrow.
    builder_state_shape = {
        "title": "状态按钮三轮推进与摘要同步",
        "business_rule_refs": ["BR-07", "BR-01"],
        "workflow_refs": ["WF-STATUS"],
        "scenario_bucket": ["normal", "business_rule"],
        "user_input": "定位 WB-101（初始 Open），依次点击状态按钮三次。预期：第 1 次 In progress，第 2 次 Done，第 3 次 Open。",
        "expected_behavior": ["Open", "In progress", "Done"],
    }
    if role_score(builder_state_shape, "state_cycle") <= 0:
        fail("Builder-shaped BR-07 three-click state cycle did not resolve")

    # Regression: actual Builder output uses Chinese ordinal words
    # ("第一次/第二次/第三次") and omits optional workflow_refs.
    actual_builder_state_shape = {
        "title": "WB-101 可见标题定位与三次状态循环",
        "business_rule_refs": ["BR-07"],
        "scenario_bucket": ["business_rule", "state_anomaly", "tool_interaction", "negative"],
        "user_input": (
            "测试 WB-101 的状态流转。先等待页面稳定，确认初始状态为 Open；"
            "然后通过渲染后的页面定位任务行，点击状态按钮三次，验证状态依次变为 "
            "In progress、Done、Open，并在每次变化后核对四项摘要。"
        ),
        "expected_behavior": [
            "第一次点击后状态为 In progress。",
            "第二次点击后状态为 Done。",
            "第三次点击后状态为 Open。",
        ],
    }
    if role_score(actual_builder_state_shape, "state_cycle") <= 0:
        fail("Actual Builder-shaped Chinese-ordinal state cycle did not resolve")

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "datasets").mkdir()
        cases = [
            {
                "dataset_id": "D-SEARCH",
                "case_id": "WB-CORE-02",
                "title": "搜索大小写与描述匹配",
                "objective": "验证搜索不区分大小写并匹配描述",
                "expected_behavior": {"expected": "ONBOARDING matches Update onboarding guide"},
                "business_rule_refs": ["BR-02A"],
                "workflow_refs": ["WF-SEARCH"],
                "scenario_bucket": ["boundary", "business_rule"],
                "user_input": "验证 BR-02：搜索不区分大小写，并同时匹配任务标题和描述；搜索结果必须符合查询文本，并覆盖无结果状态。依次使用搜索词 RESET、screenshots、EMAIL、no-such-task-xyz，记录每次返回的任务 ID 集合和空状态。",
            },
            {
                "dataset_id": "D-CORE",
                "case_id": "WB-CORE-07",
                "title": "[SYNTHETIC] 状态完整循环与摘要同步",
                "business_rule_refs": ["BR-07A", "BR-07B"],
                "workflow_refs": ["WF-01", "WF-02", "WF-03"],
                "scenario_bucket": ["state_anomaly", "business_rule"],
                "user_input": "验证 BR-07：对同一任务连续点击状态按钮，预期状态依次为 Open→In progress→Done→Open，且每次状态和摘要同步更新。定位 WB-101（Reset password flow），连续点击其状态按钮三次，每次记录状态、按钮文本和摘要。",
            },
            {
                "dataset_id": "D-CORE",
                "case_id": "WB-CORE-09",
                "title": "[SYNTHETIC] 删除确认 Cancel 与 Delete task",
                "business_rule_refs": ["BR-08B"],
                "workflow_refs": ["WF-DELETE"],
                "scenario_bucket": ["negative", "business_rule"],
                "user_input": "验证 BR-08 的确认删除分支：只有点击 Delete task 才删除所选任务，并验证任务列表和摘要同步更新。定位 WB-105（Review accessibility），点击其 Delete 按钮，在确认对话框中点击 Delete task，记录剩余任务和摘要。",
            },
            {
                "dataset_id": "D-CORE",
                "case_id": "WB-CORE-08",
                "title": "[SYNTHETIC] 仅取消删除",
                "business_rule_refs": ["BR-08"],
                "scenario_bucket": ["negative", "business_rule"],
                "user_input": "验证 BR-08 的 Cancel 分支：点击 Delete 必须显示确认对话框；点击 Cancel 必须关闭对话框并保持任务集合与摘要不变。定位 WB-104，点击 Delete 按钮，在确认对话框中点击 Cancel。",
            },
        ]

        datasets = {}
        for case in cases:
            case["quality_status"] = "candidate"
            case["execution_requirements"] = {
                "status": "NOT_RUN",
                "case_timeout_seconds": 120,
                "environment": {
                    "app_url": "http://127.0.0.1:4173",
                    "server_state_at_start": "running",
                },
            }
            datasets.setdefault(case["dataset_id"], []).append(case)

        entries = []
        for dataset_id, dataset_cases in datasets.items():
            path = root / "datasets" / f"{dataset_id}.jsonl"
            path.write_text(
                "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in dataset_cases),
                encoding="utf-8",
            )
            entries.append({
                "dataset_id": dataset_id,
                "jsonl": f"datasets/{dataset_id}.jsonl",
                "case_count": len(dataset_cases),
                "quality_status": "candidate",
                "execution_status": "NOT_RUN",
            })

        (root / "SUITE-MANIFEST.json").write_text(json.dumps({
            "quality_status": "candidate",
            "execution_status": "NOT_RUN",
            "datasets": entries,
        }), encoding="utf-8")

        matrix = load_suite(root)
        assert [item["pilot_role"] for item in matrix["include"]] == list(PILOT_ROLES)
        assert [item["case_id"] for item in matrix["include"]] == [
            "WB-CORE-02", "WB-CORE-07", "WB-CORE-09"
        ]
        assert [item["fixture_profile"] for item in matrix["include"]] == [
            "mutant", "clean", "clean"
        ]
        assert matrix["include"][1]["fixture_mutations"] == []
        assert "WB-CORE-08" not in {
            item["case_id"] for item in matrix["include"]
        }

        # End-to-end opt-in resolution for the eleven additional semantic
        # roles. These are isolated selector fixtures, not Builder output and
        # never treated as execution or evaluation evidence.
        remaining_root = root / "remaining-role-fixture"
        (remaining_root / "datasets").mkdir(parents=True)
        remaining_specs = {
            "initial_board": ("initial_board", ["BR-01"], ["WF-INITIAL"]),
            "search_description": ("search_description", ["BR-02"], ["WF-SEARCH"]),
            "search_empty": ("search_empty", ["BR-02"], ["WF-SEARCH"]),
            "status_filter": ("status_filter", ["BR-03"], ["WF-FILTER"]),
            "search_filter_combo": ("search_filter_combo", ["BR-02", "BR-03"], ["WF-SEARCH", "WF-FILTER"]),
            "accessible_names": ("accessible_names", ["BR-10"], ["WF-INITIAL"]),
            "visible_title_mapping": ("recon_only", ["BR-07"], ["WF-INITIAL"]),
            "create_success": ("create_task", ["BR-01", "BR-04", "BR-05", "BR-06"], ["WF-CREATE-DEFAULT"]),
            "create_rejected": ("invalid_create", ["BR-04"], ["WF-CREATE-BOUNDARY"]),
            "create_boundary_80": ("boundary_create", ["BR-01", "BR-04", "BR-05", "BR-06"], ["WF-CREATE-BOUNDARY"]),
            "delete_cancel": ("delete_cancel", ["BR-08"], ["WF-DELETE-CANCEL"]),
        }
        remaining_cases = []
        for index, role in enumerate(REMAINING_ROLES, start=1):
            kind, rules, workflows = remaining_specs[role]
            remaining_cases.append({
                "case_id": f"REMAINING-{index:02d}",
                "dataset_id": "D-REMAINING",
                "quality_status": "candidate",
                "business_rule_refs": rules,
                "workflow_refs": workflows,
                "user_input": "Resolve the Builder-authored semantic candidate without executing it.",
                "execution_requirements": {
                    "status": "NOT_RUN",
                    "environment": {"app_url": "http://127.0.0.1:4173", "case_timeout_seconds": 180},
                    "test_data": [{"kind": kind}],
                },
                "information_gaps": [],
            })
        remaining_dataset_path = remaining_root / "datasets" / "D-REMAINING.jsonl"
        remaining_dataset_path.write_text(
            "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in remaining_cases),
            encoding="utf-8",
        )
        (remaining_root / "SUITE-MANIFEST.json").write_text(json.dumps({
            "quality_status": "candidate",
            "execution_status": "NOT_RUN",
            "datasets": [{
                "dataset_id": "D-REMAINING",
                "jsonl": "datasets/D-REMAINING.jsonl",
                "case_count": len(remaining_cases),
                "quality_status": "candidate",
                "execution_status": "NOT_RUN",
            }],
        }), encoding="utf-8")
        remaining_matrix = load_suite(remaining_root, roles=REMAINING_ROLES)
        assert [item["pilot_role"] for item in remaining_matrix["include"]] == list(REMAINING_ROLES)
        assert len({item["case_id"] for item in remaining_matrix["include"]}) == 11
        assert all(case["execution_requirements"]["status"] == "NOT_RUN" for case in remaining_cases)

    print("PASS: Builder-authored search, state-cycle and delete-confirmation cases resolve semantically, including explicit workflow-ref state cycles.")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root")
    parser.add_argument("--write-output")
    parser.add_argument("--github-output", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--include-remaining-candidates", action="store_true", help="resolve only the eleven unexecuted semantic roles; does not run them")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.output_root:
        parser.error("--output-root is required unless --self-test is used")
    roles = REMAINING_ROLES if args.include_remaining_candidates else PILOT_ROLES
    matrix = load_suite(Path(args.output_root), roles=roles)
    serialized = json.dumps(matrix, ensure_ascii=False, separators=(",", ":"))
    if args.write_output:
        Path(args.write_output).write_text(serialized + "\n", encoding="utf-8")
    if args.github_output:
        target = os.environ.get("GITHUB_OUTPUT")
        if not target:
            fail("GITHUB_OUTPUT is not set")
        with open(target, "a", encoding="utf-8") as stream:
            stream.write(f"matrix={serialized}\n")
    print(serialized)
    return 0


if __name__ == "__main__":
    sys.exit(main())
