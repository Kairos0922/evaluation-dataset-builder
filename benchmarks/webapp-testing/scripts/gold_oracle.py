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
    check(checks, "Audit contains only local application paths", bool(paths) and all(
        isinstance(path, str) and path.startswith("/") and not path.startswith("//") and "://" not in path
        for path in paths
    ), f"audited request count={len(paths)}; all paths are origin-relative")
    return runner, audit, {"trace": trace, "audit_method_counts": dict(methods), "expected_user_turns": expected_turns}


def adjudicate(case: dict, pilot: Path) -> dict:
    checks: list[dict] = []
    runner, audit, runtime = base_checks(case, pilot, checks)
    case_id = case["case_id"]
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
        if runner.get("fixture_profile") == "mutant":
            expected_upper = 0
            expected_verdict = "VIOLATES"
        else:
            expected_upper = 1
            expected_verdict = "CONFORMS"
        query_events = [event for event in audit if event.get("method") == "GET" and "/api/tasks" in event.get("path", "") and "q=" in event.get("query", "")]
        lower_events = [event for event in query_events if "reset+password+flow" in event.get("query", "").lower()]
        upper_events = [event for event in query_events if "RESET+PASSWORD+FLOW" in event.get("query", "")]
        low_file = skill_root / "evidence" / "query-lowercase.json"
        up_file = skill_root / "evidence" / "query-uppercase.json"
        lower = load_json(low_file) if low_file.is_file() else {}
        upper = load_json(up_file) if up_file.is_file() else {}
        lower_count, upper_count = lower.get("count"), upper.get("count")
        check(checks, "Lowercase probe is present in server audit", bool(lower_events), str([e.get("query") for e in lower_events]))
        check(checks, "Uppercase probe is present in server audit", bool(upper_events), str([e.get("query") for e in upper_events]))
        check(checks, "Lowercase query returns WB-101", lower_count == 1 and [row.get("id") for row in lower.get("rows", [])] == ["WB-101"], json.dumps({"count": lower_count, "rows": [x.get("id") for x in lower.get("rows", [])]}))
        check(checks, "Uppercase query result matches fixture profile", upper_count == expected_upper and ([row.get("id") for row in upper.get("rows", [])] == (["WB-101"] if expected_upper else [])), f"profile={runner.get('fixture_profile')}, expected={expected_upper}, actual={upper_count}")
        result_path = skill_root / "evidence" / "result.json"
        result_evidence = load_json(result_path) if result_path.is_file() else {}
        if expected_verdict == "VIOLATES":
            result_signal = result_evidence.get("verdict") in {"FAIL", "VIOLATES"} and result_evidence.get("br02") in {"VIOLATES", "NONCOMPLIANT", "NON_COMPLIANT"}
        else:
            result_signal = result_evidence.get("verdict") in {"PASS", "CONFORMS"} and result_evidence.get("br02") in {"COMPLIANT", "CONFORMS"}
        report_has_expected = expected_verdict in report_text or (expected_verdict == "CONFORMS" and "PASS" in report_text) or result_signal
        check(checks, "Target report matches the observed search behavior", report_has_expected, f"expected_report_signal={expected_verdict}; result_signal={result_signal}")
        write_events = [event for event in audit if event.get("method") in {"PUT", "PATCH", "DELETE"} or (event.get("method") == "POST" and event.get("path") != "/api/reset")]
        check(checks, "Search probe does not mutate task data", not write_events, json.dumps(write_events, ensure_ascii=False))
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

    elif case_id == "WB-LIFE-01":
        # The Builder case defines three user turns. The first pilot bundled the
        # entire array into one DSH prompt, so its scripted sub-runs cannot prove
        # cross-turn memory. Check the app state sequence, but do not score target
        # capability until the runner replays the turns in one persisted session.
        events = audit
        last_reset = max((i for i, event in enumerate(events) if event.get("method") == "POST" and event.get("path") == "/api/reset"), default=-1)
        actions = events[last_reset + 1:]
        created = [event for event in actions if event.get("action") == "created"]
        changed = [event for event in actions if event.get("action") == "status-changed"]
        deleted = [event for event in actions if event.get("action") == "deleted"]
        same_id = bool(created and changed and deleted) and len({created[0].get("item", {}).get("id"), *(event.get("path", "").rsplit("/", 1)[-1] for event in changed), deleted[0].get("item", {}).get("id")}) == 1
        check(checks, "Application action sequence is create, two status changes, delete", len(created) == 1 and len(changed) == 2 and len(deleted) == 1, f"create={len(created)}, status_changes={len(changed)}, delete={len(deleted)}")
        check(checks, "Lifecycle actions target the same task ID", same_id, f"created={created[0].get('item', {}).get('id') if created else None}, delete={deleted[0].get('item', {}).get('id') if deleted else None}")
        check(checks, "Status sequence is Open to In progress to Done", [event.get("new_status") for event in changed] == ["in_progress", "done"], str([event.get("new_status") for event in changed]))
        check(checks, "Final application state is reset to the initial fixture", normalized_tasks(runner.get("post_state")) == INITIAL, "post-state compared with frozen initial task set")
        if runtime["trace"]["turn_start_count"] != runtime["expected_user_turns"]:
            contract = "UNKNOWN"
            oracle = "UNKNOWN"
        else:
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
    results = []
    for pilot in sorted(pilots_root.iterdir()):
        if not pilot.is_dir() or not (pilot / "runner-result.json").is_file():
            continue
        case_id = load_json(pilot / "runner-result.json").get("case_id")
        case = cases.get(case_id)
        if not case:
            raise SystemExit(f"pilot case {case_id!r} does not exist in Builder output")
        results.append(adjudicate(case, pilot))
    if not results:
        raise SystemExit("No pilot evidence directories found")
    output = {
        "status": "COMPLETED_WITH_UNKNOWN" if any(item["oracle_verdict"] == "UNKNOWN" for item in results) else "COMPLETED",
        "scope": "independent pilot adjudication only; does not approve the full 23-case suite",
        "builder_suite_id": load_json(builder_output / "SUITE-MANIFEST.json").get("suite_id"),
        "builder_version": load_json(builder_output / "SUITE-MANIFEST.json").get("version"),
        "case_count": len(results),
        "verdict_counts": dict(Counter(item["oracle_verdict"] for item in results)),
        "results": results,
        "limitations": [
            "Only selected pilot cases are adjudicated; 23 generated cases are not all executed.",
            "The clean WB-DEF-01 probe does not substitute for a mutant negative-control run.",
            "WB-LIFE-01 is UNKNOWN until the three user turns are delivered as separate DSH messages in one persisted session.",
            "This pilot Oracle does not complete the A0/A1 × B0/B1 regression matrix.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "case_count": len(results), "verdict_counts": output["verdict_counts"], "output": str(output_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
