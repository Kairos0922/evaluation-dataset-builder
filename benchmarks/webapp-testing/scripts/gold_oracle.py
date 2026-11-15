#!/usr/bin/env python3
"""Independent Oracle for dynamic Builder-generated Workboard pilot cases.

The Oracle runs after the target Skill exits. It consumes the immutable Builder
suite, the resolved semantic pilot matrix, DSH event trace, server audit and
target-produced evidence. It never edits or repairs target output.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
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
INITIAL_SUMMARY = {"all": 5, "open": 2, "in_progress": 2, "done": 1}
EXPECTED_ROLES = {"search_mutation", "state_cycle", "delete_confirmation"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    values = []
    if not path.is_file():
        return values
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
    rows = state.get("items") or state.get("tasks") or []
    if not isinstance(rows, list):
        return []
    result = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        result.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "description": item.get("description"),
            "priority": item.get("priority"),
            "status": str(item.get("status", "")).lower().replace(" ", "_"),
        })
    return result


def read_trace(path: Path) -> dict:
    events = load_jsonl(path)
    sessions = [
        event.get("sessionId") for event in events
        if event.get("type") == "session" and event.get("sessionId")
    ]
    starts = [
        event for event in events
        if event.get("type") == "status" and event.get("phase") == "turn_start"
    ]
    ends = [
        event for event in events
        if event.get("type") == "status" and event.get("phase") == "turn_end"
    ]
    calls = [
        event for event in events
        if event.get("type") == "tool_call"
        and event.get("tool") == "skill"
        and (event.get("input") or {}).get("name") == "webapp-testing"
    ]
    results = {
        event.get("callId"): event for event in events
        if event.get("type") == "tool_result" and event.get("callId")
    }
    finals = [event for event in events if event.get("type") == "final"]
    return {
        "event_count": len(events),
        "session_ids": list(dict.fromkeys(sessions)),
        "turn_start_count": len(starts),
        "turn_end_count": len(ends),
        "skill_calls": len(calls),
        "completed_skill_calls": sum(
            results.get(call.get("callId"), {}).get("status") == "completed"
            for call in calls
        ),
        "final_reason": (finals[-1].get("reason") or {}).get("kind") if finals else None,
    }


def add_check(checks: list[dict], name: str, condition: bool | None, evidence: str) -> bool:
    status = "UNKNOWN" if condition is None else ("PASS" if condition else "FAIL")
    checks.append({"check": name, "status": status, "evidence": evidence})
    return status == "PASS"


def report_bundle(pilot: Path) -> tuple[str, list[Path]]:
    root = pilot / "skill-artifacts"
    reports = list(root.rglob("*.md")) if root.is_dir() else []
    images = [
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    ] if root.is_dir() else []
    text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in reports)
    return text, images


def base_checks(case: dict, pilot: Path, checks: list[dict]) -> tuple[dict, list[dict], dict]:
    runner_path = pilot / "runner-result.json"
    trace_path = pilot / "dsh-events.jsonl"
    audit_path = pilot / "server-audit.jsonl"
    if not runner_path.is_file():
        add_check(checks, "Runner result archived", None, "runner-result.json is missing")
        return {}, [], {"trace": {}, "expected_user_turns": None}
    runner = load_json(runner_path)
    trace = read_trace(trace_path) if trace_path.is_file() else {}
    audit = load_jsonl(audit_path)

    user_input = case.get("user_input")
    expected_turns = len(user_input) if isinstance(user_input, list) else 1
    add_check(
        checks, "DSH invocation completed",
        runner.get("dsh_exit_code") == 0 and runner.get("runner_status") == "INVOCATION_OK",
        f"exit={runner.get('dsh_exit_code')}; runner_status={runner.get('runner_status')}",
    )
    add_check(
        checks, "Target Skill invoked through an actual DSH tool call",
        bool(trace) and trace.get("skill_calls", 0) > 0 and trace.get("completed_skill_calls", 0) > 0,
        f"calls={trace.get('skill_calls')}; completed={trace.get('completed_skill_calls')}",
    )
    add_check(checks, "DSH final reason is completed", trace.get("final_reason") == "completed" if trace else None, str(trace.get("final_reason")))
    add_check(
        checks, "DSH turn count matches the Builder case",
        trace.get("turn_start_count") == expected_turns and trace.get("turn_end_count") == expected_turns if trace else None,
        f"expected={expected_turns}; starts={trace.get('turn_start_count')}; ends={trace.get('turn_end_count')}",
    )
    add_check(checks, "One DSH session identity was used", len(trace.get("session_ids", [])) == 1 if trace else None, str(trace.get("session_ids", [])))
    add_check(checks, "Runner completed every submitted user turn", runner.get("completed_user_turn_count") == expected_turns and len(runner.get("session_turn_results") or []) == expected_turns, f"expected={expected_turns}; completed={runner.get('completed_user_turn_count')}")
    add_check(checks, "Fixture server was closed after the run", runner.get("server_port_closed") is True, str(runner.get("server_port_closed")))
    required = runner.get("required_skill_evidence") or {}
    add_check(
        checks, "Required report, JSON evidence and screenshot exist",
        all(required.get(key) is True for key in ("markdown_report", "json_evidence_index", "screenshot")),
        json.dumps(required, ensure_ascii=False),
    )
    paths = [event.get("path", "") for event in audit]
    add_check(
        checks, "Server audit contains only origin-relative application paths",
        bool(paths) and all(
            isinstance(value, str) and value.startswith("/") and not value.startswith("//") and "://" not in value
            for value in paths
        ),
        f"request_count={len(paths)}",
    )
    reset_events = [
        event for event in audit
        if event.get("method") == "POST" and event.get("path") == "/api/reset"
    ]
    add_check(
        checks, "Runner performed exactly one initial reset and target did not reset again",
        len(reset_events) == 1 and bool(audit) and audit[0] is reset_events[0],
        f"reset_count={len(reset_events)}; first_event={audit[0] if audit else None}",
    )
    return runner, audit, {"trace": trace, "expected_user_turns": expected_turns}


def audit_writes(audit: list[dict]) -> list[dict]:
    return [
        event for event in audit
        if event.get("method") in {"PUT", "PATCH", "DELETE"}
        or (event.get("method") == "POST" and event.get("path") != "/api/reset")
    ]


def adjudicate(case: dict, pilot: Path, role: str) -> dict:
    checks: list[dict] = []
    runner, audit, runtime = base_checks(case, pilot, checks)
    case_id = case["case_id"]
    report_text, screenshots = report_bundle(pilot)
    pre = runner.get("pre_state") or {}
    post = runner.get("post_state") or {}
    pre_tasks = normalized_tasks(pre)
    post_tasks = normalized_tasks(post)
    pre_is_initial = pre_tasks == INITIAL and pre.get("summary") == INITIAL_SUMMARY
    skill_report_exists = bool(report_text.strip())

    if role == "search_mutation":
        mutations = runner.get("fixture_mutations") or []
        is_mutant = (
            runner.get("fixture_profile") == "mutant"
            and mutations == ["search-case-sensitive"]
        )
        add_check(checks, "Case-sensitive search defect mutant was selected", is_mutant, f"profile={runner.get('fixture_profile')}; mutations={mutations}")
        query_events = [
            event for event in audit
            if event.get("method") == "GET"
            and event.get("path") == "/api/tasks"
            and "q=" in event.get("query", "")
        ]
        expected_counts = {
            "RESET": 0,
            "Reset": 1,
            "reset": 0,
            "SCREENSHOTS": 0,
            "screenshots": 0,
        }
        observed: dict[str, list[int]] = {}
        for event in query_events:
            values = parse_qs(event.get("query", ""), keep_blank_values=True).get("q", [""])
            query = unquote_plus(values[0]) if values else ""
            if query in expected_counts:
                observed.setdefault(query, []).append(event.get("result_count"))
        all_seen = all(query in observed for query in expected_counts)
        all_match = all(
            query in observed and all(value == expected for value in observed[query])
            for query, expected in expected_counts.items()
        )
        add_check(checks, "All five case-variant title/description probes reached the application", all_seen, json.dumps(observed, ensure_ascii=False))
        add_check(checks, "Observed mutant results match the independently derived behavior", all_match, json.dumps({"expected": expected_counts, "observed": observed}, ensure_ascii=False))
        add_check(checks, "Search did not mutate the task set", not audit_writes(audit), json.dumps(audit_writes(audit), ensure_ascii=False))
        add_check(checks, "Search preserved the initial task set and summary", pre_is_initial and post_tasks == INITIAL and post.get("summary") == INITIAL_SUMMARY, f"pre_initial={pre_is_initial}; post_ids={[item['id'] for item in post_tasks]}; summary={post.get('summary')}")
        report_ok = (
            skill_report_exists
            and "BR-02" in report_text
            and "RESET" in report_text
            and "SCREENSHOTS" in report_text
            and "WB-101" in report_text
            and "WB-102" in report_text
            and re.search(r"大小写敏感|case-sensitive|case sensitive", report_text, re.I) is not None
            and re.search(r"成立|已复现|确认|reproduced", report_text, re.I) is not None
            and re.search(r"FAIL|违反|不符合|缺陷", report_text, re.I) is not None
        )
        add_check(checks, "Target report correctly identifies and supports the BR-02 violation", report_ok, "BR-02, query variants, affected task IDs and reproduced defect language inspected")
        behavior = "EXPECTED_VIOLATION_DETECTED" if all_match and report_ok else "UNKNOWN"

    elif role == "state_cycle":
        mutations = runner.get("fixture_mutations") or []
        add_check(checks, "Clean fixture was selected", runner.get("fixture_profile") == "clean" and not mutations, f"profile={runner.get('fixture_profile')}; mutations={mutations}")
        updates = [
            event for event in audit
            if event.get("method") == "PATCH" and event.get("path", "").startswith("/api/tasks/")
        ]
        expected = [
            ("open", "in_progress"),
            ("in_progress", "done"),
            ("done", "open"),
        ]
        observed = [
            (event.get("old_status"), event.get("new_status"))
            for event in updates
        ]
        correct_target = all(event.get("path") == "/api/tasks/WB-101" for event in updates)
        add_check(checks, "WB-101 completed the exact BR-07 state cycle", observed == expected and correct_target, json.dumps({"expected": expected, "observed": observed, "paths": [event.get("path") for event in updates]}, ensure_ascii=False))
        add_check(checks, "No unrelated task write occurred", len(audit_writes(audit)) == 3 and all(event.get("method") == "PATCH" and event.get("path") == "/api/tasks/WB-101" for event in audit_writes(audit)), json.dumps(audit_writes(audit), ensure_ascii=False))
        add_check(checks, "Task rows and summary returned to the initial state", pre_is_initial and post_tasks == INITIAL and post.get("summary") == INITIAL_SUMMARY, f"pre_initial={pre_is_initial}; post_ids={[item['id'] for item in post_tasks]}; summary={post.get('summary')}")
        report_ok = (
            skill_report_exists and "BR-07" in report_text
            and all(term in report_text for term in ("Open", "In progress", "Done"))
            and re.search(r"PASS|CONFORMS|通过", report_text, re.I) is not None
        )
        add_check(checks, "Target report agrees with the independently observed BR-07 cycle", report_ok, "BR-07, three transitions, resulting summary and PASS verdict inspected")
        behavior = "PASS" if observed == expected and report_ok else "FAIL"

    elif role == "delete_confirmation":
        mutations = runner.get("fixture_mutations") or []
        add_check(checks, "Clean fixture was selected", runner.get("fixture_profile") == "clean" and not mutations, f"profile={runner.get('fixture_profile')}; mutations={mutations}")
        deletes = [event for event in audit if event.get("method") == "DELETE"]
        expected_after = [item for item in INITIAL if item["id"] != "WB-104"]
        expected_summary = {"all": 4, "open": 1, "in_progress": 2, "done": 1}
        add_check(checks, "Only WB-104 was deleted once", len(deletes) == 1 and deletes[0].get("path") == "/api/tasks/WB-104" and (deletes[0].get("item") or {}).get("id") == "WB-104", json.dumps(deletes, ensure_ascii=False))
        writes = audit_writes(audit)
        add_check(checks, "No create, status mutation or unrelated delete occurred", len(writes) == 1 and writes[0].get("method") == "DELETE" and writes[0].get("path") == "/api/tasks/WB-104", json.dumps(writes, ensure_ascii=False))
        add_check(checks, "Pre/post state matches Cancel preservation and confirmed-delete result", pre_is_initial and post_tasks == expected_after and post.get("summary") == expected_summary, f"pre_initial={pre_is_initial}; post_ids={[item['id'] for item in post_tasks]}; summary={post.get('summary')}")
        report_ok = (
            skill_report_exists and "BR-08" in report_text and "WB-104" in report_text
            and "Cancel" in report_text and "Delete task" in report_text
            and re.search(r"PASS|CONFORMS|通过", report_text, re.I) is not None
        )
        add_check(checks, "Target report documents both the cancel and confirmation branches", report_ok, "BR-08, WB-104, Cancel, Delete task and PASS verdict inspected")
        add_check(checks, "Evidence contains screenshots for the dialog workflow", len(screenshots) >= 3, f"screenshot_count={len(screenshots)}")
        behavior = "PASS" if deletes and report_ok and post_tasks == expected_after else "FAIL"

    else:
        add_check(checks, "Pilot role has a supported Oracle", False, role)
        behavior = "UNKNOWN"

    failed = [item for item in checks if item["status"] == "FAIL"]
    unknown = [item for item in checks if item["status"] == "UNKNOWN"]
    verdict = "FAIL" if failed else ("UNKNOWN" if unknown else "PASS")
    return {
        "case_id": case_id,
        "dataset_id": case.get("dataset_id"),
        "pilot_role": role,
        "fixture_profile": runner.get("fixture_profile"),
        "execution_valid": (
            runtime.get("trace", {}).get("turn_start_count") == runtime.get("expected_user_turns")
            and runtime.get("trace", {}).get("turn_end_count") == runtime.get("expected_user_turns")
            and len(runtime.get("trace", {}).get("session_ids", [])) == 1
        ),
        "expected_user_turns": runtime.get("expected_user_turns"),
        "observed_dsh_turns": runtime.get("trace", {}).get("turn_start_count"),
        "contract_verdict": verdict,
        "oracle_verdict": verdict,
        "business_behavior_verdict": behavior,
        "checks": checks,
        "target_report_excerpt": [
            line.strip() for line in report_text.splitlines()
            if re.search(r"PASS|FAIL|CONFORMS|VIOLATES|BR-0[278]", line, re.I)
        ][:12],
        "limitations": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--builder-output", required=True)
    parser.add_argument("--pilots-root", required=True)
    parser.add_argument("--pilot-matrix", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    builder_output = Path(args.builder_output).resolve()
    pilots_root = Path(args.pilots_root).resolve()
    matrix = load_json(Path(args.pilot_matrix).resolve())
    cases = case_index(builder_output)
    entries = matrix.get("include")
    if not isinstance(entries, list) or len(entries) != 3:
        raise SystemExit("pilot matrix must contain exactly three entries")
    roles = [item.get("pilot_role") for item in entries]
    if set(roles) != EXPECTED_ROLES or len(set(roles)) != 3:
        raise SystemExit(f"pilot roles must be exactly {sorted(EXPECTED_ROLES)}")
    if len({item.get("case_id") for item in entries}) != 3:
        raise SystemExit("pilot matrix must contain three distinct case IDs")

    pilot_dirs = {}
    for role_entry in entries:
        case_id = role_entry["case_id"]
        dataset_id = role_entry["dataset_id"]
        case = cases.get(case_id)
        if not case or case.get("dataset_id") != dataset_id:
            raise SystemExit(f"Builder-authored pilot case missing or dataset mismatch: {case_id}")
        matches = [
            path for path in pilots_root.rglob("runner-result.json")
            if load_json(path).get("case_id") == case_id
        ]
        if len(matches) > 1:
            raise SystemExit(f"duplicate runner evidence for case {case_id}")
        pilot_dirs[case_id] = matches[0].parent if matches else None

    results = []
    for entry in entries:
        case = cases[entry["case_id"]]
        pilot = pilot_dirs[entry["case_id"]]
        if pilot is None:
            results.append({
                "case_id": entry["case_id"],
                "dataset_id": entry["dataset_id"],
                "pilot_role": entry["pilot_role"],
                "execution_valid": False,
                "contract_verdict": "UNKNOWN",
                "oracle_verdict": "UNKNOWN",
                "business_behavior_verdict": "UNKNOWN",
                "checks": [{
                    "check": "Archived target execution evidence is present",
                    "status": "UNKNOWN",
                    "evidence": "No runner-result.json exists for this pilot case.",
                }],
                "target_report_excerpt": [],
                "limitations": ["No execution evidence was archived; behavior cannot be adjudicated."],
            })
        else:
            results.append(adjudicate(case, pilot, entry["pilot_role"]))

    verdicts = [item["oracle_verdict"] for item in results]
    overall = (
        "COMPLETED_WITH_FAIL" if "FAIL" in verdicts
        else "COMPLETED_WITH_UNKNOWN" if "UNKNOWN" in verdicts
        else "COMPLETED"
    )
    suite = load_json(builder_output / "SUITE-MANIFEST.json")
    output = {
        "status": overall,
        "scope": "independent adjudication of three semantic Builder-authored pilots; not approval of the full suite",
        "builder_suite_id": suite.get("suite_id"),
        "builder_version": suite.get("version"),
        "case_count": len(results),
        "required_pilot_roles": list(roles),
        "required_case_ids": [item["case_id"] for item in entries],
        "observed_case_ids": [item["case_id"] for item in results if item.get("execution_valid")],
        "verdict_counts": dict(Counter(verdicts)),
        "business_behavior_verdict_counts": dict(Counter(item["business_behavior_verdict"] for item in results)),
        "results": results,
        "limitations": [
            "Only the three selected pilot cases are adjudicated; the other generated cases are not all executed.",
            "The search mutation is a controlled synthetic defect, not a production defect.",
        ],
    }
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": output["status"],
        "case_count": output["case_count"],
        "verdict_counts": output["verdict_counts"],
        "output": str(output_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
