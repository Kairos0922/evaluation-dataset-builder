#!/usr/bin/env python3
"""Independent, deterministic Oracle for Builder-generated Workboard pilot cases.

This program is deliberately outside the DSH workspace. It consumes archived run
evidence after the target Skill has exited. It never edits Builder cases and does
not trust the target Skill's final prose as the source of application truth.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, unquote_plus

INITIAL = [
    {"id": "WB-101", "title": "Reset password flow", "description": "Review password reset email and token expiry.", "priority": "High", "status": "open"},
    {"id": "WB-102", "title": "Update onboarding guide", "description": "Add screenshots for the first project setup.", "priority": "Low", "status": "in_progress"},
    {"id": "WB-103", "title": "Fix export timeout", "description": "CSV export stops after a large result set.", "priority": "High", "status": "done"},
    {"id": "WB-104", "title": "Verify email notification", "description": "Check delivery after a task status change.", "priority": "Medium", "status": "open"},
    {"id": "WB-105", "title": "Review accessibility", "description": "Check labels, keyboard order, and status messages.", "priority": "Medium", "status": "in_progress"},
]
SUMMARY = {"all": 5, "open": 2, "in_progress": 2, "done": 1}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    values = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                values.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
    return values


def case_index(root: Path) -> dict:
    result = {}
    for path in sorted(root.glob("*.jsonl")):
        for case in load_jsonl(path):
            case_id = case.get("case_id")
            if not case_id or case_id in result:
                raise ValueError(f"missing/duplicate Builder case_id: {case_id!r}")
            result[case_id] = case
    return result


def normalized_tasks(state: dict | None) -> list[dict]:
    if not isinstance(state, dict):
        return []
    tasks = state.get("items") or state.get("tasks") or []
    if not isinstance(tasks, list):
        return []
    normalized = []
    for item in tasks:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "description": item.get("description"),
            "priority": item.get("priority"),
            "status": str(item.get("status", "")).lower().replace(" ", "_"),
        })
    return normalized


def read_audit(path: Path) -> list[dict]:
    return load_jsonl(path) if path.is_file() else []


def read_trace(path: Path) -> dict:
    events = load_jsonl(path) if path.is_file() else []
    sessions = [event.get("sessionId") for event in events if event.get("type") == "session" and event.get("sessionId")]
    starts = [event for event in events if event.get("type") == "status" and event.get("phase") == "turn_start"]
    ends = [event for event in events if event.get("type") == "status" and event.get("phase") == "turn_end"]
    calls = [event for event in events if event.get("type") == "tool_call" and event.get("tool") == "skill" and (event.get("input") or {}).get("name") == "webapp-testing"]
    results = {event.get("callId"): event for event in events if event.get("type") == "tool_result" and event.get("callId")}
    finals = [event for event in events if event.get("type") == "final"]
    return {
        "event_count": len(events),
        "session_ids": list(dict.fromkeys(sessions)),
        "turn_start_count": len(starts),
        "turn_end_count": len(ends),
        "turn_numbers": [event.get("turn") for event in starts],
        "skill_calls": len(calls),
        "completed_skill_calls": sum(results.get(call.get("callId"), {}).get("status") == "completed" for call in calls),
        "final_reason": (finals[-1].get("reason") or {}).get("kind") if finals else None,
    }


def check(checks: list[dict], name: str, condition: bool, evidence: str):
    checks.append({"check": name, "status": "PASS" if condition else "FAIL", "evidence": evidence})
    return condition


def base_checks(case: dict, pilot: Path, checks: list[dict]) -> tuple[dict, list[dict], dict]:
    runner = load_json(pilot / "runner-result.json")
    trace = read_trace(pilot / "dsh-events.jsonl")
    audit = read_audit(pilot / "server-audit.jsonl")
    expected_turns = len(case.get("user_input")) if isinstance(case.get("user_input"), list) else 1
    check(checks, "DSH invocation completed", runner.get("dsh_exit_code") == 0 and runner.get("runner_status") == "INVOCATION_OK", f"exit={runner.get('dsh_exit_code')}, runner_status={runner.get('runner_status')}")
    check(checks, "Target Skill invoked by actual DSH tool call", trace["skill_calls"] > 0 and trace["completed_skill_calls"] > 0, f"skill_calls={trace['skill_calls']}, completed={trace['completed_skill_calls']}")
    check(checks, "DSH final reason completed", trace["final_reason"] == "completed", str(trace["final_reason"]))
    check(checks, "DSH user-turn count matches Builder case", trace["turn_start_count"] == expected_turns and trace["turn_end_count"] == expected_turns, f"expected={expected_turns}, starts={trace['turn_start_count']}, ends={trace['turn_end_count']}")
    check(checks, "Single DSH session identity", len(trace["session_ids"]) == 1, str(trace["session_ids"]))
    check(checks, "Fixture process cleaned up", runner.get("server_port_closed") is True, str(runner.get("server_port_closed")))
    check(checks, "Skill supplied required evidence types", all(runner.get("required_skill_evidence", {}).values()), json.dumps(runner.get("required_skill_evidence"), ensure_ascii=False))
    methods = Counter(event.get("method") for event in audit)
    paths = [event.get("path", "") for event in audit]
    reset_events = [event for event in audit if event.get("method") == "POST" and event.get("path") == "/api/reset"]
    check(checks, "Only the runner performs the single initial reset", len(reset_events) == 1, f"reset_count={len(reset_events)}; timestamps={[event.get('timestamp') for event in reset_events]}")
    check(checks, "Initial reset completes before task interactions", bool(reset_events) and (not audit or audit.index(reset_events[0]) == 0), f"first_audit_event={audit[0] if audit else None}")
    check(checks, "Audit contains only local application paths", bool(paths) and all(
        isinstance(path, str) and path.startswith("/") and not path.startswith("//") and "://" not in path
        for path in paths
    ), f"audited request count={len(paths)}; all paths are origin-relative")
    return runner, audit, {"trace": trace, "audit_method_counts": dict(methods), "expected_user_turns": expected_turns}


def adjudicate(case: dict, pilot: Path) -> dict:
    checks: list[dict] = []
    runner, audit, runtime = base_checks(case, pilot, checks)
    case_id = case["case_id"]
    business_behavior_verdict = "UNKNOWN"
    skill_root = pilot / "skill-artifacts"
    report_files = list(skill_root.glob("*.md"))
    report_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in report_files)
    execution_valid = runtime["trace"]["turn_start_count"] == runtime["expected_user_turns"] and runtime["trace"]["turn_end_count"] == runtime["expected_user_turns"] and len(runtime["trace"]["session_ids"]) == 1

    if case_id == "WB-CORE-01":
        pre = runner.get("pre_state") or {}
        post = runner.get("post_state") or {}
        pre_tasks = normalized_tasks(pre)
        check(checks, "Independent initial task state matches frozen fixture", pre_tasks == INITIAL, f"IDs={[x['id'] for x in pre_tasks]}, count={len(pre_tasks)}")
        check(checks, "Read-only run leaves application state unchanged", pre == post, f"pre/post state equal={pre == post}")
        check(checks, "Expected summary is 5/2/2/1", (pre.get("summary") or {}) == SUMMARY, json.dumps(pre.get("summary"), ensure_ascii=False))
        evidence_path = skill_root / "evidence" / "run_result.json"
        evidence = load_json(evidence_path) if evidence_path.is_file() else {}
        checks_list = evidence.get("checks") or []
        check(checks, "Browser evidence independently records a stable ready sample", evidence.get("pre_ready_sample", {}).get("loadingVisible") is True and evidence.get("ready_sample", {}).get("taskRowCount") == 5 and evidence.get("final_sample", {}).get("counts") == {"all": "5", "open": "2", "inProgress": "2", "done": "1"}, "pre-ready loading state, 5 ready rows, expected final counts")
        check(checks, "All recorded browser assertions passed", len(checks_list) == 16 and all(item.get("pass") is True for item in checks_list), f"{sum(item.get('pass') is True for item in checks_list)}/{len(checks_list)}")
        check(checks, "Target report accurately says CONFORMS", "CONFORMS" in report_text and "16/16" in report_text, "target report inspected against machine evidence")
        write_events = [event for event in audit if event.get("method") in {"PUT", "PATCH", "DELETE"} or (event.get("method") == "POST" and event.get("path") != "/api/reset")]
        check(checks, "Application audit shows no task mutations", not write_events, json.dumps(write_events, ensure_ascii=False))
        contract = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
        oracle = contract

    elif case_id == "WB-DEF-01":
        mutations = runner.get("fixture_mutations") or []
        is_mutant = runner.get("fixture_profile") == "mutant" and "search-case-sensitive" in mutations
        expected_count = 0 if is_mutant else 1
        expected_eval = "FAIL" if is_mutant else "PASS"

        def query_value(event):
            values = parse_qs(event.get("query", ""), keep_blank_values=True).get("q", [""])
            return unquote_plus(values[0]) if values else ""

        query_events = [
            event for event in audit
            if event.get("method") == "GET" and event.get("path") == "/api/tasks" and "q=" in event.get("query", "")
        ]
        lower_events = [event for event in query_events if query_value(event) == "reset password flow"]
        upper_events = [event for event in query_events if query_value(event) == "RESET PASSWORD FLOW"]
        exact_events = [event for event in query_events if query_value(event) == "Reset password flow"]

        lower_file = skill_root / "snapshots" / "query_lowercase_rows.json"
        upper_file = skill_root / "snapshots" / "query_uppercase_rows.json"
        exact_file = skill_root / "snapshots" / "query_exact_rows.json"
        lower = load_json(lower_file) if lower_file.is_file() else {}
        upper = load_json(upper_file) if upper_file.is_file() else {}
        exact = load_json(exact_file) if exact_file.is_file() else {}

        def row_ids(value):
            return [row.get("task_id") or row.get("id") for row in value.get("rows", []) if isinstance(row, dict)]

        lower_count = lower.get("result_count")
        upper_count = upper.get("result_count")
        exact_count = exact.get("result_count")
        expected_rows = [] if is_mutant else ["WB-101"]
        check(checks, "Expected search fixture mutation is explicitly selected", is_mutant and mutations == ["search-case-sensitive"], f"profile={runner.get('fixture_profile')}, mutations={mutations}")
        check(checks, "Lowercase probe is present in independent server audit", bool(lower_events), str([event.get("query") for event in lower_events]))
        check(checks, "Uppercase probe is present in independent server audit", bool(upper_events), str([event.get("query") for event in upper_events]))
        check(checks, "Exact-case diagnostic probe is present in independent server audit", bool(exact_events), str([event.get("query") for event in exact_events]))
        check(checks, "Lowercase result matches the selected fixture profile", lower_count == expected_count and row_ids(lower) == expected_rows, json.dumps({"count": lower_count, "ids": row_ids(lower), "expected_count": expected_count, "expected_ids": expected_rows}, ensure_ascii=False))
        check(checks, "Uppercase result matches the selected fixture profile", upper_count == expected_count and row_ids(upper) == expected_rows, json.dumps({"count": upper_count, "ids": row_ids(upper), "expected_count": expected_count, "expected_ids": expected_rows}, ensure_ascii=False))
        check(checks, "Exact-case diagnostic control returns WB-101", exact_count == 1 and row_ids(exact) == ["WB-101"], json.dumps({"count": exact_count, "ids": row_ids(exact)}, ensure_ascii=False))
        check(checks, "Server audit counts agree with all three saved query snapshots", all(event.get("result_count") == expected_count for event in lower_events + upper_events) and all(event.get("result_count") == 1 for event in exact_events), json.dumps({"lower": [event.get("result_count") for event in lower_events], "upper": [event.get("result_count") for event in upper_events], "exact": [event.get("result_count") for event in exact_events]}, ensure_ascii=False))

        test_run_path = skill_root / "logs" / "test_run.json"
        test_run = load_json(test_run_path) if test_run_path.is_file() else {}
        evaluation = test_run.get("evaluation") or {}
        evaluation_matches = (
            evaluation.get("verdict") == expected_eval
            and (not is_mutant or evaluation.get("defect_type") == "case_sensitive_search")
            and (not is_mutant or evaluation.get("br") == "BR-02")
        )
        check(checks, "Target's machine-readable verdict matches the observed search behavior", evaluation_matches, json.dumps({"expected": expected_eval, "evaluation": evaluation}, ensure_ascii=False))
        report_has_expected = (
            ("FAIL" in report_text.upper() and "BR-02" in report_text)
            if is_mutant else
            ("PASS" in report_text.upper() or "CONFORMS" in report_text.upper())
        )
        check(checks, "Target report communicates the expected BR-02 result", report_has_expected, f"mutant={is_mutant}; report_has_FAIL={'FAIL' in report_text.upper()}; report_has_BR02={'BR-02' in report_text}")
        write_events = [
            event for event in audit
            if event.get("method") in {"PUT", "PATCH", "DELETE"}
            or (event.get("method") == "POST" and event.get("path") != "/api/reset")
        ]
        check(checks, "Search probes do not mutate task data", not write_events, json.dumps(write_events, ensure_ascii=False))
        check(checks, "Application state is unchanged by search probes", runner.get("pre_state") == runner.get("post_state") and normalized_tasks(runner.get("post_state")) == INITIAL, "runner pre/post snapshots independently compared")
        business_behavior_verdict = "EXPECTED_VIOLATION_DETECTED" if is_mutant and evaluation_matches and report_has_expected else ("PASS" if evaluation_matches and report_has_expected else "FAIL")
        contract = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
        oracle = contract

    elif case_id == "WB-PROC-01":
        pre = runner.get("pre_state") or {}
        post = runner.get("post_state") or {}
        assertions_path = skill_root / "evidence" / "assertions.json"
        summary_path = skill_root / "evidence" / "run_summary.json"
        assertions = load_json(assertions_path) if assertions_path.is_file() else []
        summary = load_json(summary_path) if summary_path.is_file() else {}
        if isinstance(assertions, dict):
            assertions = assertions.get("assertions", [])
        network = summary.get("network_summary") or {}
        recon_manifest_path = skill_root / "recon" / "recon_manifest.json"
        recon = load_json(recon_manifest_path) if recon_manifest_path.is_file() else {}
        action = summary.get("action_done") or {}
        all_action = summary.get("action_all") or {}
        check(checks, "Application state remains unchanged", pre == post and normalized_tasks(pre) == INITIAL, "runner pre/post state and frozen fixture compared")
        check(checks, "All 22 agent-produced assertions passed", len(assertions) == 22 and all(item.get("passed") is True for item in assertions), f"{sum(item.get('passed') is True for item in assertions)}/{len(assertions)}")
        check(checks, "Recon evidence timestamp precedes action phase", bool(recon) and recon.get("recon_completed_utc") and recon.get("action_started_utc") and recon["recon_completed_utc"] < recon["action_started_utc"], json.dumps({"recon": recon.get("recon_completed_utc"), "action": recon.get("action_started_utc")}))
        check(checks, "Done filter returns only WB-103", action.get("row_count") == 1 and [row.get("id") for row in action.get("rows", [])] == ["WB-103"], json.dumps({"row_count": action.get("row_count"), "ids": [row.get("id") for row in action.get("rows", [])]}))
        check(checks, "All filter restores the five baseline task IDs", all_action.get("row_count") == 5 and {row.get("id") for row in all_action.get("rows", [])} == {item["id"] for item in INITIAL}, json.dumps({"row_count": all_action.get("row_count"), "ids": [row.get("id") for row in all_action.get("rows", [])]}))
        write_events = [event for event in audit if event.get("method") in {"PUT", "PATCH", "DELETE"} or (event.get("method") == "POST" and event.get("path") != "/api/reset")]
        check(checks, "Server audit shows no application writes", not write_events, json.dumps(write_events, ensure_ascii=False))
        check(checks, "Target report matches independent evidence", "22/22" in report_text and "PASS" in report_text, "report claim is supported by the external audit and evidence files")
        contract = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
        oracle = contract

    elif case_id == "WB-CORE-08":
        pre = runner.get("pre_state") or {}
        post = runner.get("post_state") or {}
        expected_after = [item for item in INITIAL if item["id"] != "WB-104"]
        check(checks, "Independent initial state matches the five-task fixture", normalized_tasks(pre) == INITIAL, f"initial IDs={[item.get('id') for item in normalized_tasks(pre)]}")
        check(checks, "Final state contains exactly the four retained tasks", normalized_tasks(post) == expected_after, f"final IDs={[item.get('id') for item in normalized_tasks(post)]}")
        check(checks, "Final summary is 4/1/2/1", (post.get("summary") or {}) == {"all": 4, "open": 1, "in_progress": 2, "done": 1}, json.dumps(post.get("summary"), ensure_ascii=False))

        snapshots_path = skill_root / "data" / "br08_snapshots.json"
        result_path = skill_root / "data" / "br08_result.json"
        steps_path = skill_root / "logs" / "br08_steps.jsonl"
        snapshots = load_json(snapshots_path) if snapshots_path.is_file() else {}
        br08_result = load_json(result_path) if result_path.is_file() else {}
        step_events = load_jsonl(steps_path) if steps_path.is_file() else []

        baseline = snapshots.get("01_baseline") or {}
        dialog_open = snapshots.get("02_dialog_open_cancel_pending") or {}
        after_cancel = snapshots.get("03_after_cancel") or {}
        dialog_reopened = snapshots.get("04_dialog_reopened_confirm_pending") or {}
        after_confirm = snapshots.get("05_after_confirm_delete") or {}
        ids = lambda state: [row.get("task_id") or row.get("id") for row in state.get("rows", []) if isinstance(row, dict)]
        initial_ids = [item["id"] for item in INITIAL]
        final_ids = [item["id"] for item in expected_after]

        check(checks, "Baseline snapshot contains exactly the five initial tasks", baseline.get("row_count") == 5 and ids(baseline) == initial_ids, json.dumps({"row_count": baseline.get("row_count"), "ids": ids(baseline)}, ensure_ascii=False))
        check(checks, "First confirmation dialog is visible and modal", (dialog_open.get("dialog") or {}).get("open") is True and (dialog_open.get("dialog") or {}).get("modal") is True, json.dumps(dialog_open.get("dialog"), ensure_ascii=False))
        check(checks, "Cancel closes dialog and preserves the exact five-task set", after_cancel.get("row_count") == 5 and ids(after_cancel) == initial_ids and (after_cancel.get("dialog") or {}).get("open") is False, json.dumps({"row_count": after_cancel.get("row_count"), "ids": ids(after_cancel), "dialog": after_cancel.get("dialog")}, ensure_ascii=False))
        check(checks, "Second confirmation dialog is visible and modal", (dialog_reopened.get("dialog") or {}).get("open") is True and (dialog_reopened.get("dialog") or {}).get("modal") is True, json.dumps(dialog_reopened.get("dialog"), ensure_ascii=False))
        check(checks, "Delete confirmation leaves exactly the four expected tasks", after_confirm.get("row_count") == 4 and ids(after_confirm) == final_ids and (after_confirm.get("dialog") or {}).get("open") is False, json.dumps({"row_count": after_confirm.get("row_count"), "ids": ids(after_confirm), "dialog": after_confirm.get("dialog")}, ensure_ascii=False))

        required_screenshots = [
            "screenshots/br08_02_dialog_open_cancel_pending.png",
            "screenshots/br08_03_after_cancel_list.png",
            "screenshots/br08_05_after_confirm_delete_list.png",
        ]
        screenshot_presence = {name: (skill_root / name).is_file() and (skill_root / name).stat().st_size > 0 for name in required_screenshots}
        check(checks, "Dialog, Cancel, and confirmed-delete screenshots are archived", all(screenshot_presence.values()), json.dumps(screenshot_presence, ensure_ascii=False))

        click_events = [event for event in step_events if event.get("action") == "click"]
        click_targets = [event.get("target", "") for event in click_events]
        cancel_pos = next((i for i, value in enumerate(click_targets) if "Cancel" in value), -1)
        confirm_pos = next((i for i, value in enumerate(click_targets) if "Delete task confirmation" in value), -1)
        initial_delete_clicks = [event for event in click_events if str(event.get("target", "")).startswith("row Delete button") and event.get("task_id") == "WB-104"]
        check(checks, "Step log records Cancel before confirmed Delete task", cancel_pos >= 0 and confirm_pos > cancel_pos, str(click_targets))
        check(checks, "Both Delete launches target WB-104", len(initial_delete_clicks) == 2, json.dumps(initial_delete_clicks, ensure_ascii=False))

        delete_events = [event for event in audit if event.get("method") == "DELETE"]
        all_task_writes = [
            event for event in audit
            if event.get("method") in {"PUT", "PATCH", "DELETE"}
            or (event.get("method") == "POST" and event.get("path") != "/api/reset")
        ]
        correct_delete_events = all(
            event.get("path") == "/api/tasks/WB-104" and event.get("status") == 200
            and (event.get("item") or {}).get("id") == "WB-104"
            for event in delete_events
        )
        check(checks, "Only one confirmed DELETE was issued for WB-104", len(delete_events) == 1 and correct_delete_events, json.dumps(delete_events, ensure_ascii=False))
        create_or_status_events = [
            event for event in audit
            if event.get("action") in {"created", "status-changed"}
            or event.get("method") in {"PUT", "PATCH"}
            or (event.get("method") == "POST" and event.get("path") != "/api/reset")
        ]
        check(checks, "No task creation or status mutation occurred", not create_or_status_events, json.dumps(create_or_status_events, ensure_ascii=False))

        result_checks = br08_result.get("checks") or []
        failed_result_checks = [item for item in result_checks if item.get("result") != "PASS"]
        check(checks, "Skill's structured BR-08 checks are all PASS", len(result_checks) >= 13 and not failed_result_checks, json.dumps({"check_count": len(result_checks), "failed": failed_result_checks}, ensure_ascii=False))
        report_has_conforms = ("PASS" in report_text.upper() or "CONFORMS" in report_text.upper()) and "BR-08" in report_text
        report_has_violates = "VIOLATES" in report_text.upper() or "违反 BR-08" in report_text
        check(checks, "Target report agrees with the observed BR-08 UI behavior", report_has_conforms and not report_has_violates, f"conforms={report_has_conforms}, violates={report_has_violates}")

        business_behavior_verdict = "PASS" if (
            baseline.get("row_count") == 5
            and after_cancel.get("row_count") == 5
            and ids(after_cancel) == initial_ids
            and after_confirm.get("row_count") == 4
            and ids(after_confirm) == final_ids
            and (dialog_open.get("dialog") or {}).get("open") is True
            and (dialog_reopened.get("dialog") or {}).get("open") is True
        ) else "FAIL"
        contract = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
        oracle = contract

    elif case_id == "WB-LIFE-01":
        events = audit
        reset_indices = [i for i, event in enumerate(events) if event.get("method") == "POST" and event.get("path") == "/api/reset"]
        first_reset = reset_indices[0] if reset_indices else -1
        actions = events[first_reset + 1:] if first_reset >= 0 else events
        lifecycle_sequence = [
            event.get("action") for event in actions
            if event.get("action") in {"created", "status-changed", "deleted"}
        ]
        created = [event for event in actions if event.get("action") == "created"]
        changed = [event for event in actions if event.get("action") == "status-changed"]
        deleted = [event for event in actions if event.get("action") == "deleted"]
        task_ids = {
            created_event.get("item", {}).get("id")
            for created_event in created
        } | {
            event.get("path", "").rsplit("/", 1)[-1]
            for event in changed
        } | {
            event.get("item", {}).get("id")
            for event in deleted
        }
        same_id = len(task_ids) == 1 and None not in task_ids
        reset_count = len(reset_indices)
        one_creation = len(created) == 1
        state_carry_valid = reset_count == 1 and one_creation and lifecycle_sequence == ["created", "status-changed", "status-changed", "deleted"]

        check(checks, "Lifecycle action sequence is one create, two status changes, one delete", lifecycle_sequence == ["created", "status-changed", "status-changed", "deleted"], str(lifecycle_sequence))
        check(checks, "The task was created only once across all three turns", one_creation, f"create_events={len(created)}; ids={[event.get('item', {}).get('id') for event in created]}")
        check(checks, "No extra application reset interrupted cross-turn state", reset_count == 1, f"reset_events={[event.get('timestamp') for event in events if event.get('method') == 'POST' and event.get('path') == '/api/reset']}")
        check(checks, "All lifecycle actions target one task ID", same_id, f"task_ids={sorted(str(value) for value in task_ids)}")
        check(checks, "Status sequence is Open to In progress to Done", [event.get("new_status") for event in changed] == ["in_progress", "done"], str([event.get("new_status") for event in changed]))
        check(checks, "Final application state is restored to the initial fixture", normalized_tasks(runner.get("post_state")) == INITIAL, "post-state compared with frozen initial task set")

        turn_results = runner.get("session_turn_results") or []
        expected_turn_ids = ["T1", "T2", "T3"]
        continuation_valid = (
            [item.get("turn_id") for item in turn_results] == expected_turn_ids
            and len(turn_results) == 3
            and all(item.get("dsh_exit_code") == 0 and item.get("final_reason") == "completed" for item in turn_results)
            and all(item.get("session_id_argument") == runner.get("session_id") for item in turn_results[1:])
            and bool(runner.get("session_id"))
        )
        check(checks, "Three separate DSH messages continue one persisted session", continuation_valid, json.dumps(turn_results, ensure_ascii=False))
        report_has_conforms = "CONFORMS" in report_text.upper() or re.search(r"\bPASS\b", report_text, re.I) is not None
        report_has_violates = "VIOLATES" in report_text.upper() or "FAIL" in report_text.upper()
        report_consistent = report_has_conforms and not report_has_violates if state_carry_valid else report_has_violates
        check(checks, "Target report agrees with independently observed cross-turn state", report_consistent, f"state_carry_valid={state_carry_valid}; report_conforms={report_has_conforms}; report_violates={report_has_violates}")

        business_behavior_verdict = "PASS" if state_carry_valid and continuation_valid else "FAIL"
        contract = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
        oracle = contract

    else:
        contract = "UNKNOWN"
        oracle = "UNKNOWN"
        checks.append({"check": "Case-specific Oracle implementation", "status": "UNKNOWN", "evidence": "No adjudicator is defined for this case ID in the pilot Oracle."})

    failed = [item for item in checks if item["status"] == "FAIL"]
    unknown = [item for item in checks if item["status"] == "UNKNOWN"]
    if failed and oracle != "UNKNOWN":
        oracle = "FAIL"
        contract = "FAIL"
    elif unknown and oracle == "PASS":
        oracle = "UNKNOWN"
        contract = "UNKNOWN"
    return {
        "case_id": case_id,
        "dataset_id": case.get("dataset_id"),
        "fixture_profile": runner.get("fixture_profile"),
        "execution_valid": execution_valid,
        "expected_user_turns": runtime["expected_user_turns"],
        "observed_dsh_turns": runtime["trace"]["turn_start_count"],
        "session_ids": runtime["trace"]["session_ids"],
        "contract_verdict": contract,
        "oracle_verdict": oracle,
        "business_behavior_verdict": business_behavior_verdict,
        "checks": checks,
        "target_report_excerpt": [line.strip() for line in report_text.splitlines() if re.search(r"PASS|FAIL|CONFORMS|VIOLATES", line, re.I)][:8],
        "limitations": (
            ["Search negative-control mutant not executed in this artifact; this is a clean-fixture conformance probe."]
            if case_id == "WB-DEF-01" and runner.get("fixture_profile") == "clean" else []
        ) + (
            ["The three Builder user turns were delivered to DSH as one user turn; no multi-turn memory claim is supported."]
            if case_id == "WB-LIFE-01" and not execution_valid else []
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--builder-output", required=True)
    parser.add_argument("--pilots-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    builder_output = Path(args.builder_output).resolve()
    pilots_root = Path(args.pilots_root).resolve()
    output_path = Path(args.output).resolve()
    cases = case_index(builder_output)
    expected_pilots = {
        "WB-DEF-01": ("wb-defect", "mutant"),
        "WB-LIFE-01": ("wb-lifecycle", "clean"),
        "WB-CORE-08": ("wb-core", "clean"),
    }
    pilot_dirs = {}
    for pilot in sorted(pilots_root.iterdir()):
        if not pilot.is_dir() or not (pilot / "runner-result.json").is_file():
            continue
        case_id = load_json(pilot / "runner-result.json").get("case_id")
        if case_id not in expected_pilots:
            raise SystemExit(f"unexpected pilot case artifact: {case_id!r}")
        if case_id in pilot_dirs:
            raise SystemExit(f"duplicate pilot evidence for case: {case_id}")
        pilot_dirs[case_id] = pilot

    results = []
    for case_id, (dataset_id, expected_profile) in expected_pilots.items():
        case = cases.get(case_id)
        if not case or case.get("dataset_id") != dataset_id:
            raise SystemExit(f"required Builder case is missing or in the wrong dataset: {case_id}")
        pilot = pilot_dirs.get(case_id)
        if pilot is None:
            expected_turns = len(case.get("user_input")) if isinstance(case.get("user_input"), list) else 1
            results.append({
                "case_id": case_id,
                "dataset_id": dataset_id,
                "fixture_profile": expected_profile,
                "execution_valid": False,
                "expected_user_turns": expected_turns,
                "observed_dsh_turns": 0,
                "session_ids": [],
                "contract_verdict": "UNKNOWN",
                "oracle_verdict": "UNKNOWN",
                "checks": [{
                    "check": "Archived target execution evidence is present",
                    "status": "UNKNOWN",
                    "evidence": "No runner-result.json was archived for this required pilot case.",
                }],
                "target_report_excerpt": [],
                "limitations": ["The target pilot did not produce an evidence artifact; no behavior verdict is possible."],
            })
        else:
            results.append(adjudicate(case, pilot))
    verdicts = [item["oracle_verdict"] for item in results]
    overall_status = (
        "COMPLETED_WITH_FAIL" if "FAIL" in verdicts
        else "COMPLETED_WITH_UNKNOWN" if "UNKNOWN" in verdicts
        else "COMPLETED"
    )
    output = {
        "status": overall_status,
        "scope": "independent pilot adjudication only; does not approve the full 23-case suite",
        "builder_suite_id": load_json(builder_output / "SUITE-MANIFEST.json").get("suite_id"),
        "builder_version": load_json(builder_output / "SUITE-MANIFEST.json").get("version"),
        "case_count": len(results),
        "required_case_ids": list(expected_pilots),
        "observed_case_ids": [item["case_id"] for item in results if item["execution_valid"]],
        "verdict_counts": dict(Counter(item["oracle_verdict"] for item in results)),
        "business_behavior_verdict_counts": dict(Counter(item["business_behavior_verdict"] for item in results)),
        "results": results,
        "limitations": [
            "Only selected pilot cases are adjudicated; 23 generated cases are not all executed.",
            "This pilot Oracle does not complete the A0/A1 × B0/B1 regression matrix.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "case_count": len(results), "verdict_counts": output["verdict_counts"], "output": str(output_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
