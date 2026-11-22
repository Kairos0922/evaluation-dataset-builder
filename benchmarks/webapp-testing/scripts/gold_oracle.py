#!/usr/bin/env python3
"""Independent Oracle for dynamic Builder-generated Workboard pilot cases.

The Oracle runs after the target Skill exits. It consumes the immutable Builder
suite, the resolved semantic pilot matrix, DSH event trace, server audit and
target-produced evidence. It never edits or repairs target output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from html.parser import HTMLParser
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
REMAINING_ROLES = {
    "initial_board", "search_description", "search_empty", "status_filter",
    "search_filter_combo", "accessible_names", "visible_title_mapping",
    "create_success", "create_rejected", "create_boundary_80", "delete_cancel",
}


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


def verify_evidence_manifest(pilot: Path, runner: dict) -> tuple[bool | None, dict]:
    """Verify the Runner manifest without following links or escaping the pilot root."""
    entries = runner.get("evidence_files")
    if not isinstance(entries, list) or not entries:
        return None, {"reason": "evidence_files manifest is missing or empty"}

    errors = []
    declared = {}
    try:
        root = pilot.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        return False, {"reason": f"pilot evidence root cannot be resolved: {exc}"}
    if pilot.is_symlink() or not root.is_dir():
        return False, {"reason": "pilot evidence root must be a real directory, not a symlink"}

    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("manifest entry is not an object")
            continue
        relative = entry.get("path")
        digest = entry.get("sha256")
        size = entry.get("size_bytes")
        if (
            not isinstance(relative, str) or not relative
            or "\x00" in relative or "\\" in relative
            or relative.startswith("/")
        ):
            errors.append(f"invalid POSIX relative path: {relative!r}")
            continue
        candidate = Path(relative)
        if (
            candidate.is_absolute() or ".." in candidate.parts
            or candidate.as_posix() != relative or relative in declared
            or relative == "runner-result.json"
            or (candidate.parts and ":" in candidate.parts[0])
        ):
            errors.append(f"unsafe, non-canonical or duplicate path: {relative!r}")
            continue
        try:
            resolved = (root / candidate).resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            errors.append(f"path cannot be safely resolved: {relative!r}: {exc}")
            continue
        if not resolved.is_relative_to(root):
            errors.append(f"path resolves outside evidence root: {relative!r}")
            continue
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append(f"invalid SHA-256 for {relative}")
            continue
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            errors.append(f"invalid size for {relative}")
            continue
        declared[relative] = (digest, size)

    actual_paths = set()
    def walk_error(exc):
        errors.append(f"cannot enumerate evidence directory: {exc}")

    for current, dirnames, filenames in os.walk(
        root, topdown=True, onerror=walk_error, followlinks=False
    ):
        current_path = Path(current)
        for name in list(dirnames):
            child = current_path / name
            if child.is_symlink():
                errors.append(f"symlink directory is not allowed: {child.relative_to(root).as_posix()}")
                dirnames.remove(name)
        for name in filenames:
            child = current_path / name
            relative = child.relative_to(root).as_posix()
            if child.is_symlink():
                errors.append(f"symlink file is not allowed: {relative}")
                continue
            if not child.is_file():
                errors.append(f"non-regular evidence entry is not allowed: {relative}")
                continue
            if relative != "runner-result.json":
                actual_paths.add(relative)

    for relative in declared:
        candidate = root / relative
        ancestor = candidate
        while ancestor != root:
            if ancestor.is_symlink():
                errors.append(f"symlink path component is not allowed: {relative}")
                break
            ancestor = ancestor.parent
        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            errors.append(f"path cannot be safely resolved: {relative!r}: {exc}")
            continue
        if not resolved.is_relative_to(root):
            errors.append(f"path resolves outside evidence root: {relative!r}")

    unlisted_paths = actual_paths - set(declared)
    missing_paths = set(declared) - actual_paths
    if unlisted_paths:
        errors.append(f"unlisted files (possible cross-run contamination): {sorted(unlisted_paths)}")

    verified = 0
    for relative, (expected_digest, expected_size) in declared.items():
        path = root / relative
        if relative not in actual_paths:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            errors.append(f"cannot read evidence file {relative}: {exc}")
            continue
        actual_digest = hashlib.sha256(data).hexdigest()
        if actual_digest != expected_digest:
            errors.append(f"SHA-256 mismatch: {relative}")
        if len(data) != expected_size:
            errors.append(f"size mismatch: {relative}")
        if actual_digest == expected_digest and len(data) == expected_size:
            verified += 1

    status = False if errors else (None if missing_paths else True)
    return status, {
        "declared_file_count": len(declared),
        "verified_file_count": verified,
        "missing_files": sorted(missing_paths),
        "errors": errors,
    }


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
    canonical_by_id = {item["id"]: item for item in INITIAL}
    result = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        task_id = item.get("id") or item.get("data_id")
        canonical = canonical_by_id.get(task_id, {})
        result.append({
            "id": task_id,
            "title": item.get("title") or item.get("visible_title") or canonical.get("title"),
            "description": item.get("description") if item.get("description") is not None else canonical.get("description"),
            "priority": item.get("priority") if item.get("priority") is not None else canonical.get("priority"),
            "status": normalize_status(item.get("status") if item.get("status") is not None else canonical.get("status")),
        })
    return result


def task_summary(tasks: list[dict]) -> dict:
    return {
        "all": len(tasks),
        "open": sum(item.get("status") == "open" for item in tasks),
        "in_progress": sum(item.get("status") == "in_progress" for item in tasks),
        "done": sum(item.get("status") == "done" for item in tasks),
    }


def case_initial_state(case: dict) -> tuple[list[dict], dict]:
    declared = ((case.get("execution_requirements") or {}).get("initial_state") or {})
    tasks = normalized_tasks(declared)
    if not tasks:
        tasks = normalized_tasks({"items": INITIAL})
    summary = declared.get("summary") or declared.get("initial_summary")
    if not isinstance(summary, dict):
        summary = task_summary(tasks)
    return tasks, summary


def tasks_match_declared(actual: list[dict], declared: list[dict]) -> bool:
    """Compare only fields the Builder actually declared; omitted optional fields are not mismatches."""
    if len(actual) != len(declared):
        return False
    actual_by_id = {item.get("id"): item for item in actual}
    if len(actual_by_id) != len(actual):
        return False
    for expected in declared:
        observed = actual_by_id.get(expected.get("id"))
        if observed is None:
            return False
        for key in ("title", "description", "priority", "status"):
            value = expected.get(key)
            if value is not None and observed.get(key) != value:
                return False
    return True


def tasks_contain_declared(actual: list[dict], declared: list[dict]) -> bool:
    """Verify every declared baseline task remains unchanged when new items are allowed."""
    actual_by_id = {item.get("id"): item for item in actual}
    if len(actual_by_id) != len(actual):
        return False
    for expected in declared:
        observed = actual_by_id.get(expected.get("id"))
        if observed is None:
            return False
        for key in ("title", "description", "priority", "status"):
            value = expected.get(key)
            if value is not None and observed.get(key) != value:
                return False
    return True


def target_task(case: dict, tasks: list[dict]) -> dict | None:
    """Resolve a target from explicit Builder fields without guessing from task order."""
    outcome = case.get("reference_outcome") or {}
    rule_expected = outcome.get("rule_expected") or {}
    target = (
        rule_expected.get("target") or outcome.get("target") or outcome.get("task_id")
        or outcome.get("target_task") or outcome.get("target_id")
        or outcome.get("target_data_id")
    )
    if target is None:
        test_data = ((case.get("execution_requirements") or {}).get("test_data") or [])
        explicit_targets = []
        for item in test_data:
            if isinstance(item, dict):
                value = (
                    item.get("target_task") or item.get("task_id")
                    or item.get("target_id") or item.get("target_data_id")
                )
                name = str(item.get("name") or item.get("kind") or "").casefold()
                if value is None and name in {"target_task", "target", "target-task"}:
                    value = item.get("data_id") or item.get("id")
                visible_title = item.get("visible_title") or item.get("target_title")
                if value is not None:
                    if isinstance(value, dict):
                        explicit_targets.append(value)
                    elif visible_title:
                        explicit_targets.append({"id": value, "title": visible_title})
                    else:
                        explicit_targets.append(value)
                elif visible_title:
                    # Builder may identify the target only by its rendered title.
                    explicit_targets.append({"title": visible_title})
            elif isinstance(item, str) and any(
                marker in item.casefold() for marker in ("目标", "target", "删除任务")
            ):
                match = re.search(r"\b(WB-\d+)\b", item)
                if match:
                    explicit_targets.append(match.group(1))
        if explicit_targets:
            fingerprints = {
                json.dumps(value, ensure_ascii=False, sort_keys=True)
                if isinstance(value, dict) else str(value)
                for value in explicit_targets
            }
            if len(fingerprints) == 1:
                target = explicit_targets[0]
        if target is None:
            message_ids = list(dict.fromkeys(re.findall(r"\b(WB-\d+)\b", user_message(case))))
            if len(message_ids) == 1:
                target = message_ids[0]
        if target is None:
            # Backward compatibility for one concise test-data string.
            candidates = []
            for item in test_data:
                if isinstance(item, str):
                    ids = re.findall(r"\b(WB-\d+)\b", item)
                    if len(ids) == 1:
                        candidates.append(ids[0])
            if candidates and len(set(candidates)) == 1:
                target = candidates[0]
    if isinstance(target, dict):
        target_id = (
            target.get("id") or target.get("data_id")
            or target.get("target_id") or target.get("target_data_id")
        )
        target_title = (
            target.get("title") or target.get("visible_title")
            or target.get("target_title")
        )
    elif isinstance(target, str):
        target_id = target if any(item.get("id") == target for item in tasks) else None
        target_title = None if target_id else target
    else:
        return None
    matches = [
        item for item in tasks
        if (target_id and item.get("id") == target_id)
        or (target_title and item.get("title") == target_title)
    ]
    return matches[0] if len(matches) == 1 else None

def is_delete_cancel_case(case: dict) -> bool:
    requirements = case.get("execution_requirements") or {}
    if any(isinstance(item, dict) and item.get("kind") == "delete_cancel" for item in requirements.get("test_data") or []):
        return True
    test_data = requirements.get("test_data") or []
    for item in test_data:
        if not isinstance(item, dict):
            continue
        if item.get("kind") == "delete_cancel":
            return True
        expected = item.get("expected_rule_state") or {}
        if expected.get("cancel_closes") is True and expected.get("task_retained"):
            return True
    message = user_message(case).casefold()
    return (
        ("cancel" in message or "取消" in message)
        and ("不要点击 delete task" in message or "do not click delete task" in message)
    )


def normalize_status(value) -> str:
    return str(value or "").lower().replace(" ", "_")


def expected_status_transitions(case: dict, target: dict | None) -> list[tuple[str, str]]:
    """Derive the state cycle from the Builder-authored case contract."""
    expected: list[tuple[str, str]] = []
    rule_expected = ((case.get("reference_outcome") or {}).get("rule_expected") or {})
    steps = rule_expected.get("steps") or []
    if steps:
        # Builder contracts may encode a transition as {action, status, summary}
        # rather than explicit {from, to}. Derive the previous state from the
        # target's declared initial status, then advance through each declared
        # destination. Do not return empty ("", "") transitions for a valid
        # action/status contract.
        structured = []
        previous = normalize_status(target.get("status")) if target else ""
        for step in steps:
            if not isinstance(step, dict):
                continue
            from_status = step.get("from") or step.get("from_status")
            to_status = step.get("to") or step.get("to_status") or step.get("status")
            if from_status and to_status:
                source = normalize_status(from_status)
                destination = normalize_status(to_status)
            elif to_status and previous:
                source = previous
                destination = normalize_status(to_status)
            else:
                continue
            structured.append((source, destination))
            previous = destination
        if len(structured) == len(steps) and structured:
            return structured

    outcome = case.get("reference_outcome") or {}
    from_status = outcome.get("from_status") or outcome.get("from")
    to_status = outcome.get("to_status") or outcome.get("to")
    if from_status and to_status:
        return [(normalize_status(from_status), normalize_status(to_status))]

    execution = case.get("execution_requirements") or {}
    test_data = execution.get("test_data") or []
    test_sequence = []
    for item in test_data:
        if not isinstance(item, dict):
            continue
        cycle_steps = item.get("steps")
        item_name = str(item.get("name") or item.get("kind") or "").casefold()
        if isinstance(cycle_steps, list) and cycle_steps and (
            item_name in {"expected_cycle", "state_cycle", "expected_status_cycle"}
            or all(isinstance(step, dict) and "status" in step for step in cycle_steps)
        ):
            ordered_steps = sorted(
                enumerate(cycle_steps),
                key=lambda pair: (
                    pair[1].get("step") if isinstance(pair[1].get("step"), int) else pair[0],
                    pair[0],
                ),
            )
            test_sequence = [
                step.get("status") for _, step in ordered_steps
                if isinstance(step, dict) and step.get("status")
            ]
            if test_sequence:
                break
        test_sequence = (
            item.get("expected_sequence")
            or item.get("expected")
            or test_sequence
        )
        if test_sequence:
            break
    expected_behavior = case.get("expected_behavior") or {}
    conforming = ((case.get("reference_outcome") or {}).get("conforming_branch") or {})
    sequence = []
    if isinstance(expected_behavior, dict):
        sequence = expected_behavior.get("expected_status_sequence") or []
    elif isinstance(expected_behavior, list):
        ordinal_patterns = (
            r"(?:第一次|第\s*1\s*次|第一步)",
            r"(?:第二次|第\s*2\s*次|第二步)",
            r"(?:第三次|第\s*3\s*次|第三步)",
        )
        for ordinal in ordinal_patterns:
            matched_state = None
            for item in expected_behavior:
                text = str(item)
                ordinal_matches = list(re.finditer(ordinal, text))
                for ordinal_match in ordinal_matches:
                    # Limit state extraction to this ordinal's clause. A single
                    # Builder sentence may describe all three clicks in sequence.
                    later_ordinals = [
                        match.start()
                        for pattern in ordinal_patterns
                        for match in re.finditer(pattern, text)
                        if match.start() > ordinal_match.start()
                    ]
                    clause_end = min(later_ordinals, default=len(text))
                    clause = text[ordinal_match.end():clause_end]
                    match = re.search(
                        r"(?:变为|回到|状态(?:为|回到))\s*(Open|In progress|Done)",
                        clause, re.I,
                    ) or re.search(r"(Open|In progress|Done)", clause, re.I)
                    if match:
                        matched_state = match.group(1)
                        break
                if matched_state:
                    break
            if matched_state:
                sequence.append(matched_state)
        if not sequence:
            for item in expected_behavior:
                match = re.search(
                    r"从\s*(Open|In progress|Done)\s*(?:变为|回到)\s*(Open|In progress|Done)",
                    str(item), re.I,
                )
                if match:
                    sequence.append(match.group(2))
    rule_state = ((case.get("reference_outcome") or {}).get("rule_state") or "")
    rule_sequence = re.findall(r"(Open|In progress|Done)", str(rule_state), re.I)
    if not sequence and len(rule_sequence) >= 2:
        sequence = rule_sequence
    sequence = sequence or test_sequence or conforming.get("statuses") or []
    if not target or not isinstance(sequence, list) or not sequence:
        return []

    previous = normalize_status(target.get("status"))
    normalized_sequence = [normalize_status(value) for value in sequence]
    # Builder's expected field is a full state sequence and includes the
    # initial state. Drop that first state when it matches the fixture target.
    if normalized_sequence and normalized_sequence[0] == previous:
        normalized_sequence = normalized_sequence[1:]
    for normalized in normalized_sequence:
        next_status = normalized
        normalized = normalize_status(next_status)
        expected.append((previous, normalized))
        previous = normalized
    return expected

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


def dsh_turn_completed(runtime: dict) -> bool:
    trace = runtime.get("trace") or {}
    return (
        trace.get("final_reason") == "completed"
        and trace.get("turn_end_count") == runtime.get("expected_user_turns")
    )


def report_bundle(pilot: Path) -> tuple[str, list[Path]]:
    root = pilot / "skill-artifacts"
    reports = sorted(
        (
            path for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() == ".md"
        ),
        key=lambda path: path.as_posix(),
    ) if root.is_dir() else []
    # Raw/original run reports are diagnostic evidence, not the final report.
    # Prefer canonical reports when present; fall back only when none exist.
    canonical_reports = [
        path for path in reports
        if not re.search(r"(?:^|[_-])(?:raw|original|diagnostic)(?:[_-]|$)", path.stem, re.I)
    ]
    if canonical_reports:
        reports = canonical_reports
    images = [
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    ] if root.is_dir() else []
    text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in reports)
    return text, images


def report_has_search_finding(report_text: str, expected_tasks: list[dict], required_queries: list[str]) -> bool:
    """Check the case-declared finding, not a hard-coded business-rule label."""
    return (
        bool(report_text.strip())
        and bool(expected_tasks)
        and all(item.get("title") and item["title"] in report_text for item in expected_tasks)
        and all(query.casefold() in report_text.casefold() for query in required_queries)
        and re.search(r"VIOLATED|FAIL|违反|不符合|缺陷|遗漏", report_text, re.I) is not None
    )


def report_has_state_cycle_result(
    report_text: str,
    target_id: str | None,
    target_title: str | None,
    expected_verdict: str = "PASS",
) -> bool:
    """Check that the Skill report's explicit verdict matches the observed cycle."""
    normalized_report = re.sub(r"[*_]", "", report_text)
    label_match = re.search(r"(?:判定|结论|结果|verdict)", normalized_report, re.I)
    match = None
    if label_match:
        verdict_section = normalized_report[label_match.start():label_match.start() + 80]
        match = re.search(r"(PASS|FAIL|UNKNOWN)", verdict_section, re.I)
    if match is None:
        # Backward compatibility for earlier reports that label the result as
        # "BR-07 PASS" without a separate summary verdict line.
        match = re.search(r"\bBR-07\s+(PASS|FAIL|UNKNOWN)\b", report_text, re.I)
    observed_verdict = match.group(1).upper() if match else None
    return (
        bool(report_text.strip())
        and (
            (bool(target_id) and target_id in report_text)
            or (bool(target_title) and target_title in report_text)
        )
        and all(term in report_text for term in ("Open", "In progress", "Done"))
        and observed_verdict == expected_verdict.upper()
    )


def report_has_delete_result(report_text: str, target_id: str | None) -> bool:
    """Check the target, confirmation dialog and action in the final report."""
    return (
        bool(report_text.strip())
        and bool(target_id) and target_id in report_text
        and "Delete task" in report_text
        and re.search(r"Delete task\?|confirmation dialog|确认对话框", report_text, re.I) is not None
        and re.search(r"PASS|CONFORMS|通过", report_text, re.I) is not None
    )


def count_test_script_executions(events: list[dict], runner: dict) -> dict:
    """Count actual runs of Builder-relevant test scripts in DSH Bash calls.

    Counts direct Python script invocations. For a length-truncated command
    payload, a script heredoc plus its correlated execution output is counted
    only when the output has the test's distinctive runtime markers and exit
    status. Static -c compile checks, imports, edits and analysis snippets do
    not count as test-script executions.
    """
    evidence = runner.get("evidence_files") or []
    candidates = sorted({
        Path(item.get("path", "")).name
        for item in evidence
        if isinstance(item, dict)
        and isinstance(item.get("path"), str)
        and item["path"].casefold().endswith(".py")
        and "test" in Path(item["path"]).name.casefold()
        and "recon" not in Path(item["path"]).name.casefold()
    })
    if not candidates:
        return {"count": None, "scripts": [], "invocations": [], "reason": "no archived test-script path found"}

    result_by_call = {
        event.get("callId"): event
        for event in events
        if event.get("type") == "tool_result" and event.get("callId")
    }
    invocations = []
    for event_index, event in enumerate(events):
        if event.get("type") != "tool_call" or event.get("tool") != "bash":
            continue
        command = (event.get("input") or {}).get("command")
        if not isinstance(command, str):
            continue
        for script in candidates:
            # A command separator can follow the script immediately (e.g.
            # "python3 test_wc12.py; echo ..."), not only whitespace.
            direct_pattern = re.compile(
                r"(?:^|[\s;&|])(?:python(?:\d+(?:\.\d+)*)?)(?:\s+-u)?\s+"
                r"(?:[^\s;&|]+/)?" + re.escape(script) + r"(?=[\s;&|]|$)",
                re.M,
            )
            direct_count = len(direct_pattern.findall(command))
            for occurrence in range(direct_count):
                invocations.append({
                    "event_index": event_index,
                    "script": script,
                    "execution_evidence": "direct_python_invocation",
                    "occurrence_in_command": occurrence + 1,
                })

            # DSH may truncate long bash command input in its event trace.
            # When the retained prefix writes the exact archived test script
            # by heredoc and the matching tool result contains the runtime's
            # distinctive output, we can still verify its execution once.
            if direct_count == 0 and event.get("truncated") is True:
                escaped = re.escape(script)
                heredoc = re.search(
                    r"(?:cat|tee)\s+>+\s+[^\n]*" + escaped + r"\s+<<",
                    command,
                )
                result_event = result_by_call.get(event.get("callId")) or {}
                output = result_event.get("result")
                if isinstance(output, dict):
                    output = json.dumps(output, ensure_ascii=False)
                output = output if isinstance(output, str) else ""
                has_runtime_result = (
                    "EXIT_CODE=" in output
                    and ("[step]" in output or "=== SUMMARY ===" in output)
                    and ("verdict" in output.casefold() or "FINAL STATUS" in output)
                )
                if heredoc and has_runtime_result:
                    invocations.append({
                        "event_index": event_index,
                        "script": script,
                        "execution_evidence": "truncated_heredoc_with_correlated_runtime_output",
                        "call_id": event.get("callId"),
                    })

    return {
        "count": len(invocations),
        "scripts": candidates,
        "invocations": invocations,
        "reason": "direct test-script calls plus verified truncated heredoc executions; static checks/imports excluded",
    }


def base_checks(case: dict, pilot: Path, checks: list[dict]) -> tuple[dict, list[dict], dict]:
    runner_path = pilot / "runner-result.json"
    trace_path = pilot / "dsh-events.jsonl"
    audit_path = pilot / "server-audit.jsonl"
    if not runner_path.is_file():
        add_check(checks, "Runner result archived", None, "runner-result.json is missing")
        return {}, [], {"trace": {}, "expected_user_turns": None}
    runner = load_json(runner_path)
    manifest_ok, manifest_detail = verify_evidence_manifest(pilot, runner)
    add_check(
        checks, "Archived evidence files match the Runner SHA-256 manifest",
        manifest_ok, json.dumps(manifest_detail, ensure_ascii=False),
    )
    trace_available = trace_path.is_file()
    audit_available = audit_path.is_file()
    trace = read_trace(trace_path) if trace_available else {}
    trace_events = load_jsonl(trace_path) if trace_available else []
    audit = load_jsonl(audit_path) if audit_available else []
    run_id = runner.get("run_id")
    execution_requirements = case.get("execution_requirements") or {}
    limits = execution_requirements.get("cost_and_rate_limits") or {}
    if "max_test_script_executions" in limits:
        maximum = limits.get("max_test_script_executions")
        script_detail = count_test_script_executions(trace_events, runner) if trace_available else {
            "count": None, "scripts": [], "invocations": [], "reason": "DSH Trace is missing"
        }
        count = script_detail.get("count")
        valid_limit = type(maximum) is int and maximum >= 0
        within_limit = count <= maximum if count is not None and valid_limit else None
        retry_policy = str(limits.get("retry_policy") or "").casefold()
        if within_limit is not None and retry_policy == "no_retry":
            within_limit = within_limit and count <= 1
        add_check(
            checks, "Test-script execution count complies with the Builder budget and retry policy",
            within_limit,
            json.dumps({
                "observed_count": count,
                "maximum": maximum,
                "retry_policy": retry_policy or None,
                **script_detail,
            }, ensure_ascii=False),
        )
    if "max_mutating_actions" in limits:
        maximum = limits.get("max_mutating_actions")
        observed_mutations = len(audit_writes(audit)) if audit_available else None
        valid_limit = type(maximum) is int and maximum >= 0
        within_limit = (
            observed_mutations <= maximum
            if observed_mutations is not None and valid_limit else None
        )
        add_check(
            checks, "Application mutation count complies with the Builder action budget",
            within_limit,
            json.dumps({
                "observed_mutating_actions": observed_mutations,
                "maximum": maximum,
                "mutations": audit_writes(audit) if audit_available else None,
            }, ensure_ascii=False),
        )

    context_path = pilot / "trace-run-context.json"
    context_error = None
    try:
        context = load_json(context_path) if context_path.is_file() else {}
    except (OSError, json.JSONDecodeError) as exc:
        context = {}
        context_error = str(exc)
    identity_status = None
    identity_detail = {
        "runner_run_id": run_id,
        "trace_context_run_id": context.get("run_id") if isinstance(context, dict) else None,
        "server_audit_event_count": len(audit),
        "trace_context_error": context_error,
    }
    if isinstance(run_id, str) and run_id.strip() and context_path.is_file() and audit_available and audit:
        if context_error is not None:
            identity_status = False
            identity_detail["reason"] = "trace run context is not valid JSON"
        elif not isinstance(context, dict):
            identity_status = False
            identity_detail["reason"] = "trace run context is not a JSON object"
        else:
            audit_ids = [item.get("run_id") if isinstance(item, dict) else None for item in audit]
            trace_digest = context.get("trace_sha256")
            expected_event_count = context.get("trace_event_count")
            actual_digest = (
                hashlib.sha256(trace_path.read_bytes()).hexdigest()
                if trace_available and trace_path.is_file() else None
            )
            actual_event_count = trace.get("event_count") if trace_available else None
            missing_fields = []
            if not context.get("run_id"):
                missing_fields.append("trace_context.run_id")
            if not isinstance(trace_digest, str) or not trace_digest:
                missing_fields.append("trace_context.trace_sha256")
            if isinstance(expected_event_count, bool) or not isinstance(expected_event_count, int):
                missing_fields.append("trace_context.trace_event_count")
            if not audit_ids or any(not isinstance(value, str) or not value for value in audit_ids):
                missing_fields.append("server_audit.run_id")
            if actual_digest is None:
                missing_fields.append("dsh_trace")
            if actual_event_count is None:
                missing_fields.append("dsh_trace.event_count")

            mismatches = []
            if context.get("run_id") and context.get("run_id") != run_id:
                mismatches.append("trace context run_id differs from Runner")
            if any(isinstance(value, str) and value and value != run_id for value in audit_ids):
                mismatches.append("server audit run_id differs from Runner")
            if trace_digest and actual_digest and trace_digest != actual_digest:
                mismatches.append("DSH Trace SHA-256 differs from sidecar")
            if isinstance(expected_event_count, int) and not isinstance(expected_event_count, bool) and actual_event_count is not None and expected_event_count != actual_event_count:
                mismatches.append("DSH Trace event count differs from sidecar")

            identity_status = False if mismatches else (None if missing_fields else True)
            identity_detail.update({
                "server_audit_run_ids": sorted({str(value) for value in audit_ids}),
                "trace_sha256_matches_context": (
                    actual_digest == trace_digest if actual_digest and trace_digest else None
                ),
                "trace_event_count_matches_context": (
                    actual_event_count == expected_event_count
                    if actual_event_count is not None and isinstance(expected_event_count, int)
                    and not isinstance(expected_event_count, bool) else None
                ),
                "missing_fields": missing_fields,
                "mismatches": mismatches,
            })
    add_check(
        checks, "Runner, server audit and DSH Trace belong to the same run",
        identity_status, json.dumps(identity_detail, ensure_ascii=False),
    )

    user_input = case.get("user_input")
    expected_turns = len(user_input) if isinstance(user_input, list) else 1
    add_check(
        checks, "DSH invocation completed",
        runner.get("dsh_exit_code") == 0 and runner.get("runner_status") == "INVOCATION_OK",
        f"exit={runner.get('dsh_exit_code')}; runner_status={runner.get('runner_status')}",
    )
    add_check(
        checks, "Target Skill invoked through an actual DSH tool call",
        (bool(trace) and trace.get("skill_calls", 0) > 0 and trace.get("completed_skill_calls", 0) > 0) if trace_available else None,
        f"calls={trace.get('skill_calls')}; completed={trace.get('completed_skill_calls')}",
    )
    add_check(checks, "DSH final reason is completed", trace.get("final_reason") == "completed" if trace_available and trace else None, str(trace.get("final_reason")))
    add_check(
        checks, "DSH turn count matches the Builder case",
        trace.get("turn_start_count") == expected_turns and trace.get("turn_end_count") == expected_turns if trace_available and trace else None,
        f"expected={expected_turns}; starts={trace.get('turn_start_count')}; ends={trace.get('turn_end_count')}",
    )
    add_check(checks, "One DSH session identity was used", len(trace.get("session_ids", [])) == 1 if trace_available and trace else None, str(trace.get("session_ids", [])))
    runner_turn_fields = "completed_user_turn_count" in runner and "session_turn_results" in runner
    add_check(checks, "Runner completed every submitted user turn", runner.get("completed_user_turn_count") == expected_turns and len(runner.get("session_turn_results") or []) == expected_turns if runner_turn_fields else None, f"expected={expected_turns}; completed={runner.get('completed_user_turn_count')}")
    add_check(checks, "Fixture server was closed after the run", runner.get("server_port_closed") is True if "server_port_closed" in runner else None, str(runner.get("server_port_closed")))
    required = runner.get("required_skill_evidence") or {}
    evidence_keys = ("markdown_report", "json_evidence_index", "screenshot")
    evidence_status = all(required.get(key) is True for key in evidence_keys) if all(key in required for key in evidence_keys) else None
    add_check(
        checks, "Required report, JSON evidence and screenshot exist",
        evidence_status,
        json.dumps(required, ensure_ascii=False),
    )
    paths = [event.get("path", "") for event in audit]
    audit_paths_ok = (
        bool(paths) and all(
            isinstance(value, str) and value.startswith("/") and not value.startswith("//") and "://" not in value
            for value in paths
        )
    ) if audit_available else None
    add_check(
        checks, "Server audit contains only origin-relative application paths",
        audit_paths_ok,
        f"audit_available={audit_available}; request_count={len(paths)}",
    )
    reset_events = [
        event for event in audit
        if event.get("method") == "POST" and event.get("path") == "/api/reset"
    ]
    add_check(
        checks, "Runner performed exactly one initial reset and target did not reset again",
        (len(reset_events) == 1 and bool(audit) and audit[0] is reset_events[0]) if audit_available else None,
        f"audit_available={audit_available}; reset_count={len(reset_events)}; first_event={audit[0] if audit else None}",
    )
    state_available = isinstance(runner.get("pre_state"), dict) and isinstance(runner.get("post_state"), dict)
    return runner, audit, {
        "trace": trace,
        "expected_user_turns": expected_turns,
        "trace_available": trace_available,
        "audit_available": audit_available,
        "state_available": state_available,
    }


def audit_writes(audit: list[dict]) -> list[dict]:
    return [
        event for event in audit
        if event.get("method") in {"PUT", "PATCH", "DELETE"}
        or (event.get("method") == "POST" and event.get("path") != "/api/reset")
    ]


def user_message(case: dict) -> str:
    """Return Builder-authored user input without assuming a single-turn shape."""
    value = case.get("user_input")
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\\n".join(str(item) for item in value if item is not None)
    return ""


def extract_search_queries(case: dict, tasks: list[dict]) -> list[str]:
    """Extract only explicitly requested search probes; never infer probes from task titles."""
    message = user_message(case)
    outcome = case.get("reference_outcome") or {}
    queries = [outcome["query"]] if isinstance(outcome.get("query"), str) and outcome.get("query") else []
    expected_behavior = case.get("expected_behavior") or {}
    if not queries and isinstance(expected_behavior, dict):
        required = expected_behavior.get("required_queries") or []
        if isinstance(required, list):
            queries = [str(item) for item in required if isinstance(item, str) and item.strip()]

    # Explicitly quoted queries following a search/input verb are authoritative.
    # This handles Builder prose such as: 搜索大写 'PASSWORD'，再搜索小写 'screenshots'。
    if not queries:
        quoted_probe = re.compile(
            r"(?:搜索|查询|输入|键入)\s*(?:大写|小写)?\s*['\"“‘\x60]([^'\"”’\x60]+)['\"”’\x60]"
        )
        queries = [match.strip() for match in quoted_probe.findall(message) if match.strip()]

    searchable_text = [
        " ".join(str(task.get(field) or "") for field in ("title", "description"))
        for task in tasks
    ]

    def retain_probe_tokens(segment: str) -> list[str]:
        candidates = re.findall(r"[A-Za-z][A-Za-z0-9-]*", segment)
        return [
            token for token in candidates
            if re.match(r"^z{3,}-", token.casefold())
            or any(
                re.search(rf"\b{re.escape(token)}\b", text, re.I)
                for text in searchable_text
            )
        ]

    if not queries:
        sequence = re.search(r"(?:依次输入|依次键入)(.*?)(?:。|$)", message, re.S)
        if sequence:
            queries = retain_probe_tokens(sequence.group(1))
    if not queries:
        test_data = ((case.get("execution_requirements") or {}).get("test_data") or [])
        for item in test_data:
            if isinstance(item, dict):
                kind = str(item.get("kind") or item.get("name") or "").casefold()
                value = item.get("query") or item.get("queries")
                if kind in {"search_queries", "query_list", "required_queries"}:
                    value = item.get("values") or item.get("value") or value
                if isinstance(value, str):
                    queries = retain_probe_tokens(value)
                elif isinstance(value, list):
                    queries = [str(part) for part in value if isinstance(part, str) and part.strip()]
                if queries:
                    break
            elif isinstance(item, str):
                query_list = re.search(r"查询[:：]\s*(.*?)(?:。|$)", item)
                if query_list:
                    queries = retain_probe_tokens(query_list.group(1))
                    if queries:
                        break
    if not queries and isinstance(expected_behavior, list):
        explicit_probe = re.compile(
            r"(?:输入|查询|搜索)\s*(?:大写|小写)?\s*['\"“‘]?([A-Za-z][A-Za-z0-9-]*)"
        )
        for item in expected_behavior:
            match = explicit_probe.search(str(item))
            if match:
                queries.append(match.group(1))
    return list(dict.fromkeys(query for query in queries if query and not query.startswith("<")))

def expected_search_task_titles(case: dict, tasks: list[dict]) -> list[str]:
    """Resolve Builder-authored expected title examples without relying on legacy fields."""
    test_data = ((case.get("execution_requirements") or {}).get("test_data") or [])
    titles = []
    for item in test_data:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").casefold()
        if kind in {"expected_match_example", "expected_title", "expected_task"}:
            value = item.get("value") or item.get("title") or item.get("visible_title")
            if isinstance(value, str):
                titles.extend(task["title"] for task in tasks if task.get("title") and task["title"] in value)
    message = user_message(case)
    for task in tasks:
        title = task.get("title")
        if title and title in message:
            titles.append(title)
    return list(dict.fromkeys(titles))


def expected_search_counts(queries: list[str], tasks: list[dict], branch_name: str) -> dict[str, int]:
    """Model the independently specified fixture branch, not target-reported counts."""
    counts = {}
    for query in queries:
        if branch_name == "case_sensitive_title_only":
            counts[query] = sum(query in str(task.get("title") or "") for task in tasks)
        else:
            counts[query] = sum(
                query.casefold() in (
                    str(task.get("title") or "") + " " + str(task.get("description") or "")
                ).casefold()
                for task in tasks
            )
    return counts



class DOMSnapshotParser(HTMLParser):
    """Parse archived rendered DOM snapshots without trusting Skill summaries."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.nodes = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        index = len(self.nodes)
        self.nodes.append({"tag": tag.lower(), "attrs": dict(attrs), "parent": self.stack[-1] if self.stack else None, "text": ""})
        if tag.lower() not in self.VOID:
            self.stack.append(index)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in self.VOID and self.stack:
            self.stack.pop()

    def handle_endtag(self, tag):
        for position in range(len(self.stack) - 1, -1, -1):
            if self.nodes[self.stack[position]]["tag"] == tag.lower():
                del self.stack[position:]
                break

    def handle_data(self, data):
        for index in self.stack:
            self.nodes[index]["text"] += data


def _clean_text(value) -> str:
    return " ".join(str(value or "").split())


def parse_dom_snapshots(pilot: Path) -> list[dict]:
    root = pilot / "skill-artifacts"
    result = []
    if root.is_dir():
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".html", ".htm"}:
                parser = DOMSnapshotParser()
                parser.feed(path.read_text(encoding="utf-8", errors="replace"))
                result.append({"path": path, "nodes": parser.nodes})
    return result


def _visible(node: dict, nodes: list[dict]) -> bool:
    current = node
    while current is not None:
        attrs = current.get("attrs") or {}
        if "hidden" in attrs or str(attrs.get("aria-hidden", "")).lower() == "true":
            return False
        if current.get("tag") == "dialog" and "open" not in attrs:
            return False
        parent = current.get("parent")
        current = nodes[parent] if parent is not None else None
    return True


def _role(node: dict) -> str | None:
    attrs, tag = node.get("attrs") or {}, node.get("tag")
    if attrs.get("role"):
        return attrs["role"]
    if tag == "button": return "button"
    if tag == "dialog": return "dialog"
    if tag == "select": return "combobox"
    if tag == "textarea": return "textbox"
    if tag == "input":
        return {"search": "searchbox", "submit": "button", "button": "button"}.get(str(attrs.get("type", "text")).lower(), "textbox")
    return None


def _name(node: dict, nodes: list[dict]) -> str:
    attrs = node.get("attrs") or {}
    if attrs.get("aria-label"):
        return _clean_text(attrs["aria-label"])
    ids = {item.get("attrs", {}).get("id"): item for item in nodes if item.get("attrs", {}).get("id")}
    labelledby = attrs.get("aria-labelledby")
    if labelledby:
        values = [_clean_text(ids[key].get("text")) for key in labelledby.split() if key in ids]
        if values: return _clean_text(" ".join(values))
    identifier = attrs.get("id")
    if identifier:
        labels = [item for item in nodes if item.get("tag") == "label" and item.get("attrs", {}).get("for") == identifier]
        if labels: return _clean_text(labels[0].get("text"))
    return _clean_text(node.get("text"))


def dom_controls(snapshots: list[dict]) -> list[dict]:
    controls = []
    for snap in snapshots:
        for node in snap["nodes"]:
            role = _role(node)
            if role and _visible(node, snap["nodes"]):
                controls.append({"role": role, "name": _name(node, snap["nodes"]), "attrs": node.get("attrs") or "", "snapshot": snap["path"].name})
    return controls


def dom_rows(snapshots: list[dict]) -> list[str]:
    return [
        _clean_text(node.get("text"))
        for snap in snapshots for node in snap["nodes"]
        if node.get("tag") == "tr" and _visible(node, snap["nodes"]) and _clean_text(node.get("text"))
    ]


def dom_snapshot_task_state(snapshot: dict) -> dict:
    rows = [
        _clean_text(node.get("text"))
        for node in snapshot["nodes"]
        if node.get("tag") == "tr" and _visible(node, snapshot["nodes"]) and _clean_text(node.get("text"))
    ]
    known_titles = [item["title"] for item in INITIAL]
    visible_titles = [
        title for title in known_titles
        for row in rows if title in row
    ]
    empty_visible = any(
        item["visible"] and item["text"] == "No tasks match the current filters."
        for item in dom_by_id([snapshot], "empty-state")
    )
    return {"titles": visible_titles, "rows": rows, "empty_visible": empty_visible, "snapshot": snapshot["path"].name}


def dom_has_exact_task_titles(snapshots: list[dict], expected_titles: list[str], require_empty: bool = False) -> bool:
    expected = list(expected_titles)
    for snapshot in snapshots:
        state = dom_snapshot_task_state(snapshot)
        exact_titles = len(state["rows"]) == len(expected) and sorted(state["titles"]) == sorted(expected)
        if exact_titles and (expected or (require_empty and state["empty_visible"])):
            return True
    return False


def dom_by_id(snapshots: list[dict], identifier: str) -> list[dict]:
    result = []
    for snap in snapshots:
        for node in snap["nodes"]:
            attrs = node.get("attrs") or {}
            if attrs.get("id") == identifier:
                result.append({"text": _clean_text(node.get("text")), "visible": _visible(node, snap["nodes"]), "attrs": attrs, "snapshot": snap["path"].name})
    return result


def dom_summary_ok(snapshots: list[dict], summary: dict) -> bool:
    ids = {"all": "count-all", "open": "count-open", "in_progress": "count-in-progress", "done": "count-done"}
    for snap in snapshots:
        if all(
            any(item["visible"] and item["text"] == str(summary[key]) for item in dom_by_id([snap], identifier))
            for key, identifier in ids.items() if key in summary
        ):
            return True
    return False


def _test_data(case: dict) -> dict:
    values = (case.get("execution_requirements") or {}).get("test_data") or []
    return values[0] if len(values) == 1 and isinstance(values[0], dict) else {}


def _query_events(audit: list[dict]) -> list[dict]:
    output = []
    for event in audit:
        if event.get("method") == "GET" and event.get("path") == "/api/tasks":
            params = parse_qs(event.get("query", ""), keep_blank_values=True)
            output.append({**event, "q": (params.get("q") or [""])[0], "status_filter": (params.get("status") or ["all"])[0]})
    return output


def adjudicate_remaining_case(case: dict, pilot: Path, role: str) -> dict:
    checks = []
    runner, audit, runtime = base_checks(case, pilot, checks)
    report_text, screenshots = report_bundle(pilot)
    if not runner:
        return {
            "case_id": case["case_id"], "dataset_id": case.get("dataset_id"), "pilot_role": role,
            "execution_valid": False, "contract_verdict": "UNKNOWN",
            "oracle_verdict": "UNKNOWN", "business_behavior_verdict": "UNKNOWN",
            "checks": checks, "target_report_excerpt": [], "limitations": ["Runner result evidence is missing."],
        }
    td, snaps = _test_data(case), parse_dom_snapshots(pilot)
    rows = dom_rows(snaps)
    pre, post = runner.get("pre_state") or {}, runner.get("post_state") or {}
    initial_tasks, initial_summary = case_initial_state(case)
    pre_tasks, post_tasks = normalized_tasks(pre), normalized_tasks(post)
    state_available = runtime.get("state_available", False)
    audit_available = runtime.get("audit_available", False)
    no_writes = None if not audit_available else not audit_writes(audit)
    pre_ok = (tasks_match_declared(pre_tasks, initial_tasks) and pre.get("summary") == initial_summary) if state_available else None
    writes = audit_writes(audit)
    report_ok = bool(report_text.strip()) if report_text.strip() else None

    def add(name, condition, evidence):
        add_check(checks, name, condition, evidence if isinstance(evidence, str) else json.dumps(evidence, ensure_ascii=False))

    add("Canonical target report is archived", report_ok, "A target-produced Markdown report is required as evidence.")

    if role == "initial_board":
        expected = normalized_tasks({"tasks": td.get("expected_tasks") or []})
        summary = td.get("expected_summary") or initial_summary
        state_ok = None if not state_available else bool(expected) and pre_ok and tasks_match_declared(post_tasks, expected) and post.get("summary") == summary
        dom_ok = None if not snaps else dom_has_exact_task_titles(snaps, [item["title"] for item in expected]) and dom_summary_ok(snaps, summary)
        add("Builder baseline rows and summary match server-side initial and final states", state_ok, {"expected": expected, "post": post_tasks, "summary": post.get("summary")})
        add("Rendered DOM contains all baseline rows and summary values", dom_ok, {"rows": rows, "expected_summary": summary})
        add("Initial-state inspection performed no application writes", no_writes, writes)

    elif role in {"search_description", "search_empty"}:
        query = td.get("query")
        events = [event for event in _query_events(audit) if event["q"] == query]
        count = 0 if role == "search_empty" else len(td.get("expected_rows") or [])
        count_ok = (bool(events) and events[-1].get("result_count") == count) if audit_available else None
        expected_titles = [item.get("title") for item in td.get("expected_rows") or []]
        if not snaps:
            dom_ok = None
        elif role == "search_empty":
            empty = dom_by_id(snaps, "empty-state")
            dom_ok = dom_has_exact_task_titles(snaps, [], require_empty=True) and any(
                item["visible"] and item["text"] == td.get("expected_empty_text")
                for item in empty
            )
        else:
            dom_ok = dom_has_exact_task_titles(snaps, expected_titles)
        summary = td.get("expected_summary") or initial_summary
        state_ok = (pre_ok and tasks_match_declared(post_tasks, initial_tasks) and post.get("summary") == summary) if state_available else None
        add("Builder-declared query reached the server and result count matches", count_ok, {"query": query, "count": count, "observed": [item.get("result_count") for item in events]})
        add("Rendered DOM contains the expected row or visible empty state", dom_ok, {"expected_titles": expected_titles, "rows": rows, "empty": dom_by_id(snaps, "empty-state")})
        add("Search remained read-only and preserved tasks and summary", no_writes and state_ok, {"writes": writes, "summary": post.get("summary")})

    elif role == "status_filter":
        events = _query_events(audit)
        filter_value, restore = td.get("filter_value"), td.get("restore_value", "all")
        filtered = [item for item in events if item["status_filter"] == filter_value]
        restored = [item for item in events if item["status_filter"] == restore]
        expected_titles = td.get("expected_titles") or []
        counts_ok = (bool(filtered) and filtered[-1].get("result_count") == len(expected_titles) and bool(restored) and restored[-1].get("result_count") == td.get("expected_restored_count")) if audit_available else None
        dom_filter_ok = None if not snaps else dom_has_exact_task_titles(snaps, expected_titles)
        dom_restore_ok = None if not snaps else dom_has_exact_task_titles(snaps, [item["title"] for item in INITIAL])
        dom_summary = None if not snaps else dom_summary_ok(snaps, td.get("expected_summary") or initial_summary)
        dom_ok = None if not snaps else bool(dom_filter_ok and dom_restore_ok and dom_summary)
        state_ok = (pre_ok and tasks_match_declared(post_tasks, initial_tasks)) if state_available else None
        add("Selected status and restored All queries match Builder-declared counts", counts_ok, {"filtered": filtered, "restored": restored})
        add("Rendered DOM shows the selected filter and the restored All task set with unchanged summary", dom_ok, {"filtered_titles": expected_titles, "restored_titles": [item["title"] for item in INITIAL], "rows": rows, "summary": td.get("expected_summary") or initial_summary})
        add("Status filtering is read-only and preserves state", no_writes and state_ok, writes)

    elif role == "search_filter_combo":
        events, query = _query_events(audit), td.get("query")
        observations = []
        for state in td.get("states") or []:
            matched = [item for item in events if item["q"] == query and item["status_filter"] == state.get("status")]
            observations.append({"status": state.get("status"), "expected": state.get("expected_count"), "observed": matched[-1].get("result_count") if matched else None, "seen": bool(matched)})
        counts_ok = (bool(observations) and all(item["seen"] and item["observed"] == item["expected"] for item in observations)) if audit_available else None
        dom_states = [
            {
                "status": state.get("status"),
                "expected_titles": state.get("expected_titles") or [],
                "dom_match": dom_has_exact_task_titles(
                    snaps, state.get("expected_titles") or [],
                    require_empty=not bool(state.get("expected_titles")),
                ) if snaps else None,
            }
            for state in td.get("states") or []
        ]
        dom_ok = None if not snaps else bool(dom_states) and all(item["dom_match"] for item in dom_states) and dom_summary_ok(snaps, td.get("expected_summary") or initial_summary)
        state_ok = (pre_ok and tasks_match_declared(post_tasks, initial_tasks)) if state_available else None
        add("Combined query/filter states match all Builder-declared result counts", counts_ok, observations)
        add("Rendered DOM contains each expected query/filter state and unchanged summary", dom_ok, {"states": dom_states, "rows": rows})
        add("Combined search/filter remained read-only", no_writes and state_ok, writes)

    elif role == "accessible_names":
        expected = td.get("expected_controls") or []
        controls = dom_controls(snaps)
        missing = [item for item in expected if not any(control["role"] == item.get("role") and control["name"] == item.get("name") for control in controls)]
        dom_available = bool(snaps)
        names_ok = (bool(expected) and not missing) if dom_available else None
        dialog_ok = any(item["role"] == "dialog" and item["name"] == "Delete task?" for item in controls) if dom_available else None
        actions_ok = (any(item["role"] == "button" and item["name"] == "Cancel" for item in controls) and any(item["role"] == "button" and item["name"] == "Delete task" for item in controls)) if dom_available else None
        target_title = td.get("dialog_target_visible_title")
        target_dom_ok = any(target_title and target_title in row for row in rows) if dom_available else None
        # WB-CORE-07 is an open-then-Cancel workflow. A single open-dialog
        # snapshot proves control names, but cannot prove that Cancel closed it.
        open_dialog_snapshots = [
            snap for snap in snaps
            if any(node.get("tag") == "dialog" and "open" in (node.get("attrs") or {}) for node in snap["nodes"])
        ]
        closed_dialog_snapshots = [
            snap for snap in snaps
            if any(node.get("tag") == "dialog" and "open" not in (node.get("attrs") or {}) for node in snap["nodes"])
        ]
        post_cancel_target_ok = (
            any(target_title and target_title in row for row in dom_rows(closed_dialog_snapshots))
            if closed_dialog_snapshots else None
        )
        cancel_lifecycle_ok = (
            (bool(open_dialog_snapshots) and post_cancel_target_ok)
            if closed_dialog_snapshots else None
        ) if dom_available else None
        state_ok = (pre_ok and tasks_match_declared(post_tasks, initial_tasks) and post.get("summary") == initial_summary) if state_available else None
        add("Every Builder-declared role/accessibility-name pair exists in rendered DOM", names_ok, {"missing": missing, "observed": controls})
        add("Delete dialog exposes its semantic name and safe action names", (dialog_ok and actions_ok) if dom_available else None, {"dialog": dialog_ok, "actions": actions_ok})
        add("Builder-declared delete target remains identifiable by its visible title", target_dom_ok, {"target_title": target_title, "rows": rows})
        add("Cancel closes the previously open dialog and the target remains visible afterward", cancel_lifecycle_ok, {"open_dialog_snapshots": len(open_dialog_snapshots), "closed_dialog_snapshots": len(closed_dialog_snapshots), "target_visible_after_cancel": post_cancel_target_ok})
        add("Accessibility inspection and Cancel caused no application mutation", no_writes and state_ok, writes)

    elif role == "visible_title_mapping":
        target, title = td.get("target_data_id"), td.get("target_visible_title")
        matching = [
            row for snap in snaps for row in dom_rows([snap])
            if title and title in row and td.get("expected_status") in row and td.get("expected_button") in row
        ]
        data_id_as_text = any(target and target in row for row in rows)
        state_ok = (pre_ok and any(item.get("id") == target and item.get("title") == title and item.get("status") == normalize_status(td.get("expected_status")) for item in pre_tasks) and tasks_match_declared(post_tasks, initial_tasks)) if state_available else None
        matching_ok = None if not snaps else any(
            sum(1 for row in dom_rows([snap]) if title and title in row and td.get("expected_status") in row and td.get("expected_button") in row) == 1
            for snap in snaps
        )
        add("Public visible title identifies exactly one row with expected status and action", matching_ok, matching)
        add("Opaque data ID is absent from rendered row text", None if not snaps else not data_id_as_text, rows)
        add("Title mapping remained read-only and preserved state", no_writes and state_ok, {"writes": writes, "pre_matches": pre_ok})
        behavior = "PASS" if matching_ok and not data_id_as_text and not writes and state_ok and report_ok else "FAIL"

    elif role in {"create_success", "create_boundary_80"}:
        title = td.get("expected_stored_title") if role == "create_success" else td.get("title_input")
        priority = td.get("expected_priority") if role == "create_success" else td.get("priority")
        status = normalize_status(td.get("expected_status", "Open"))
        events = [item for item in audit if item.get("method") == "POST" and item.get("path") == "/api/tasks"]
        successful = [item for item in events if item.get("status") == 201 and item.get("action") == "created"]
        created = successful[0].get("item") if len(successful) == 1 else {}
        new_items = [item for item in post_tasks if item.get("id") not in {old.get("id") for old in initial_tasks}]
        expected_description = td.get("description")
        title_length_ok = role != "create_boundary_80" or (isinstance(title, str) and len(title) == td.get("title_length") == 80)
        server_ok = (
            len(events) == 1 and len(successful) == 1
            and created.get("title") == title and created.get("priority") == priority
            and normalize_status(created.get("status")) == status and bool(created.get("id"))
            and (expected_description is None or created.get("description") == expected_description)
        ) if audit_available else None
        allowed_create_only = (len(writes) == 1 and writes[0].get("method") == "POST" and writes[0].get("path") == "/api/tasks" and writes[0].get("status") == 201 and writes[0].get("action") == "created") if audit_available else None
        preserves_initial = tasks_contain_declared(post_tasks, initial_tasks) if state_available else None
        state_ok = (len(new_items) == 1 and new_items[0].get("title") == title and new_items[0].get("priority") == priority and new_items[0].get("status") == status and post.get("summary") == (td.get("expected_summary") or {}) and pre_ok and preserves_initial) if state_available else None
        messages = dom_by_id(snaps, "status-message")
        dom_ok = (any(title and title in row for row in rows) and any(created.get("id") and created.get("id") in item["text"] for item in messages) and dom_summary_ok(snaps, td.get("expected_summary") or {})) if snaps else None
        add("Exactly one server-audited create matches title, priority, status and declared description", server_ok, {"events": events, "created": created, "expected_title": title})
        if role == "create_boundary_80":
            add("Eighty-character boundary input is exactly the declared length", title_length_ok, {"declared_length": td.get("title_length"), "observed_length": len(title) if isinstance(title, str) else None})
        else:
            trimmed_title_ok = (title_length_ok and created.get("title") == td.get("expected_stored_title")) if audit_available else None
            add("Trimmed title matches the Builder-declared stored title", trimmed_title_ok, {"observed": created.get("title"), "expected": td.get("expected_stored_title")})
        one_create_and_preserved = (allowed_create_only and preserves_initial) if allowed_create_only is not None and preserves_initial is not None else None
        add("Only one successful create write occurred; the initial tasks were preserved", one_create_and_preserved, {"writes": writes, "preserves_initial": preserves_initial})
        add("Post-state has exactly one new item and expected summary", state_ok, {"new_items": new_items, "summary": post.get("summary")})
        add("Rendered DOM shows the created item, returned ID and summary", dom_ok, {"rows": rows, "status_message": messages})

    elif role == "create_rejected":
        events = [item for item in audit if item.get("method") == "POST" and item.get("path") == "/api/tasks"]
        rejected = [item for item in events if item.get("status") == 400 and item.get("action") == "create-rejected"]
        success = [item for item in events if item.get("status") == 201]
        messages = dom_by_id(snaps, "status-message")
        message_ok = (any(item["visible"] and td.get("expected_error_contains", "Title").casefold() in item["text"].casefold() and item["attrs"].get("data-state") == "error" for item in messages)) if snaps else None
        unexpected_writes = [item for item in writes if not (item.get("method") == "POST" and item.get("path") == "/api/tasks" and item.get("status") == 400 and item.get("action") == "create-rejected")]
        state_ok = (len(events) == 1 and len(rejected) == 1 and not success and pre_ok and tasks_match_declared(post_tasks, initial_tasks) and len(post_tasks) == td.get("expected_row_count") and post.get("summary") == (td.get("expected_summary") or initial_summary) and not unexpected_writes) if audit_available and state_available else None
        no_false_success = (not any("Created " in item["text"] for item in messages)) if snaps else None
        rejection_ok = (len(events) == 1 and len(rejected) == 1 and not success) if audit_available else None
        add("Whitespace-only create was rejected once and no successful response occurred", rejection_ok, events)
        add("Rendered status region communicates an error without false success", (message_ok and no_false_success) if snaps else None, messages)
        add("Rejected create preserved all rows and summary without unexpected writes", state_ok, {"row_count": len(post_tasks), "summary": post.get("summary"), "write_attempts": writes, "unexpected_writes": unexpected_writes})

    else:
        add("Unsupported remaining semantic role", False, role)
        behavior = "FAIL"

    failed = [item for item in checks if item["status"] == "FAIL"]
    unknown = [item for item in checks if item["status"] == "UNKNOWN"]
    verdict = "FAIL" if failed else ("UNKNOWN" if unknown else "PASS")
    behavior = "FAIL" if failed else ("UNKNOWN" if unknown else "PASS")
    return {
        "case_id": case["case_id"], "dataset_id": case.get("dataset_id"), "pilot_role": role,
        "fixture_profile": runner.get("fixture_profile"),
        "execution_valid": runtime.get("trace", {}).get("turn_start_count") == runtime.get("expected_user_turns") and runtime.get("trace", {}).get("turn_end_count") == runtime.get("expected_user_turns") and len(runtime.get("trace", {}).get("session_ids", [])) == 1,
        "expected_user_turns": runtime.get("expected_user_turns"), "observed_dsh_turns": runtime.get("trace", {}).get("turn_start_count"),
        "contract_verdict": verdict, "oracle_verdict": verdict, "business_behavior_verdict": behavior,
        "checks": checks,
        "target_report_excerpt": [line.strip() for line in report_text.splitlines() if re.search(r"PASS|FAIL|CONFORMS|VIOLATES|BR-0[1-9]", line, re.I)][:12],
        "limitations": (["DOM snapshots are target-produced files copied from the Skill workspace; they are corroborative evidence, not independent browser instrumentation."] if parse_dom_snapshots(pilot) else []),
    }


def provider_quota_blocker(pilot: Path, runner: dict) -> str | None:
    """Recognize an external provider quota blocker from immutable execution evidence."""
    trace_path = pilot / "dsh-events.jsonl"
    stderr_path = pilot / "dsh-stderr.log"
    trace_text = trace_path.read_text(encoding="utf-8", errors="replace") if trace_path.is_file() else ""
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.is_file() else ""
    evidence = (trace_text + "\\n" + stderr_text + "\\n" + str(runner.get("runner_error") or "")).casefold()
    if runner.get("runner_status") == "BLOCKED" and (
        "quota" in evidence or "insufficient balance" in evidence or "status\\\":402" in evidence or "http 402" in evidence
    ):
        return "External model-provider quota/balance block (QUOTA / HTTP 402); target behavior was not executed to completion."
    return None


def adjudicate(case: dict, pilot: Path, role: str) -> dict:
    checks: list[dict] = []
    runner, audit, runtime = base_checks(case, pilot, checks)
    case_id = case["case_id"]
    if not runner:
        return {
            "case_id": case_id, "dataset_id": case.get("dataset_id"), "pilot_role": role,
            "execution_valid": False, "contract_verdict": "UNKNOWN",
            "oracle_verdict": "UNKNOWN", "business_behavior_verdict": "UNKNOWN",
            "checks": checks, "target_report_excerpt": [],
            "limitations": ["Runner result evidence is missing."],
        }
    quota_block = provider_quota_blocker(pilot, runner)
    if quota_block:
        # External provider failure is not evidence of target-Skill behavior.
        checks = [
            {**item, "status": "UNKNOWN"} if item.get("status") == "FAIL" else item
            for item in checks
        ]
        checks.append({
            "check": "External provider quota blocker",
            "status": "UNKNOWN",
            "evidence": quota_block,
        })
        return {
            "case_id": case_id, "dataset_id": case.get("dataset_id"), "pilot_role": role,
            "execution_valid": False, "execution_status": "BLOCKED",
            "contract_verdict": "UNKNOWN", "oracle_verdict": "UNKNOWN",
            "business_behavior_verdict": "UNKNOWN", "checks": checks,
            "target_report_excerpt": [],
            "limitations": [quota_block, "No target behavior verdict is assigned because the invocation was blocked externally."],
        }
    if role in REMAINING_ROLES and role != "delete_cancel":
        return adjudicate_remaining_case(case, pilot, role)
    report_text, screenshots = report_bundle(pilot)
    pre = runner.get("pre_state") or {}
    post = runner.get("post_state") or {}
    pre_tasks = normalized_tasks(pre)
    post_tasks = normalized_tasks(post)
    initial_tasks, initial_summary = case_initial_state(case)
    declared_initial = (((case.get("execution_requirements") or {}).get("initial_state") or {}).get("tasks") or [])
    if not declared_initial:
        declared_initial = INITIAL
    pre_is_initial = tasks_match_declared(pre_tasks, initial_tasks) and pre.get("summary") == initial_summary
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
        expected_behavior = case.get("expected_behavior") or {}
        if not isinstance(expected_behavior, dict):
            expected_behavior = {}
        required_queries = expected_behavior.get("required_queries") or []
        possible = expected_behavior.get("possible_observations") or {}
        reference_queries = ((case.get("reference_outcome") or {}).get("queries") or [])
        legacy_contract = not required_queries and not possible
        branch_name = "case_sensitive_title_only" if is_mutant else "conforming"
        expected_branch = possible.get(branch_name) or {}
        if legacy_contract:
            # Builder cases may encode expected behavior as prose/list rather
            # than the older structured search contract. Derive concrete probes
            # from quoted query literals in the authored request and reference
            # outcomes, excluding descriptive placeholders.
            reference_query_map = {
                item["query"]: len(item.get("expected_matches") or [])
                for item in reference_queries
                if isinstance(item, dict)
                and isinstance(item.get("query"), str)
                and not item["query"].startswith("<")
            }
            required_queries = extract_search_queries(case, initial_tasks)
            if not required_queries:
                required_queries = list(reference_query_map)
            expected_counts = expected_search_counts(required_queries, initial_tasks, branch_name)
        else:
            expected_counts = {
                query: len(expected_branch.get(query, []))
                for query in required_queries
            }
        observed: dict[str, list[int]] = {}
        for event in query_events:
            values = parse_qs(event.get("query", ""), keep_blank_values=True).get("q", [""])
            query = unquote_plus(values[0]) if values else ""
            if query in expected_counts:
                observed.setdefault(query, []).append(event.get("result_count"))
        all_seen = bool(required_queries) and all(query in observed for query in required_queries)
        all_match = all(
            query in observed and all(value == expected for value in observed[query])
            for query, expected in expected_counts.items()
        )
        add_check(checks, "All Builder-required search probes reached the application", all_seen, json.dumps(observed, ensure_ascii=False))
        add_check(checks, "Observed search results match the independently derived fixture branch", all_match, json.dumps({"branch": branch_name, "expected": expected_counts, "observed": observed}, ensure_ascii=False))
        add_check(checks, "Search did not mutate the task set", not audit_writes(audit), json.dumps(audit_writes(audit), ensure_ascii=False))
        add_check(checks, "Search preserved the initial task set and summary", pre_is_initial and tasks_match_declared(post_tasks, initial_tasks) and post.get("summary") == initial_summary, f"pre_initial={pre_is_initial}; post_ids={[item['id'] for item in post_tasks]}; summary={post.get('summary')}")
        reference_branch = possible.get("conforming") or expected_branch
        expected_ids = {
            item_id
            for values in reference_branch.values() if isinstance(values, list)
            for item_id in values
        }
        expected_tasks = [item for item in initial_tasks if item.get("id") in expected_ids]
        if legacy_contract:
            expected_tasks = [
                task for task in initial_tasks
                if any(
                    query.casefold() in (
                        str(task.get("title") or "") + " " + str(task.get("description") or "")
                    ).casefold()
                    for query in required_queries
                )
            ]
        example_titles = expected_search_task_titles(case, initial_tasks)
        if example_titles:
            expected_tasks = [{"title": title} for title in example_titles]
        declared_expected = ((case.get("reference_outcome") or {}).get("expected") or {})
        declared_titles = list(dict.fromkeys(
            title for values in declared_expected.values() if isinstance(values, list)
            for title in values if isinstance(title, str)
        ))
        if declared_titles:
            expected_tasks = [{"title": title} for title in declared_titles]
        report_mentions_expected_tasks = bool(expected_tasks) and all(
            item.get("title") and item["title"] in report_text for item in expected_tasks
        )
        report_mentions_queries = all(query.casefold() in report_text.casefold() for query in required_queries)
        # The case contract requires query/task/observation evidence, not a literal BR-02 label.
        report_ok = report_has_search_finding(report_text, expected_tasks, required_queries)
        add_check(checks, "Target report correctly identifies and supports the BR-02 violation", report_ok, json.dumps({
            "expected_titles": [item.get("title") for item in expected_tasks],
            "report_mentions_expected_tasks": report_mentions_expected_tasks,
            "required_queries": required_queries,
            "report_mentions_queries": report_mentions_queries,
            "mentions_BR02": "BR-02" in report_text,
            "mentions_violation": bool(re.search(r"VIOLATED|FAIL|违反|不符合|缺陷|遗漏", report_text, re.I)),
        }, ensure_ascii=False))
        trace_complete = dsh_turn_completed(runtime)
        behavior = (
            "EXPECTED_VIOLATION_DETECTED"
            if trace_complete and all_match and report_ok
            else "UNKNOWN"
        )

    elif role == "state_cycle":
        mutations = runner.get("fixture_mutations") or []
        add_check(checks, "Clean fixture was selected", runner.get("fixture_profile") == "clean" and not mutations, f"profile={runner.get('fixture_profile')}; mutations={mutations}")
        target = target_task(case, initial_tasks)
        target_id = target.get("id") if target else None
        target_title = target.get("title") if target else None
        expected = expected_status_transitions(case, target)
        updates = [
            event for event in audit
            if event.get("method") == "PATCH" and event.get("path", "").startswith("/api/tasks/")
        ]
        observed = [
            (normalize_status(event.get("old_status")), normalize_status(event.get("new_status")))
            for event in updates
        ]
        correct_target = target_id is not None and all(
            event.get("path") == f"/api/tasks/{target_id}" for event in updates
        )
        add_check(
            checks, "Builder-declared target completed the exact BR-07 state cycle",
            target is not None and bool(expected) and observed == expected and correct_target,
            json.dumps({
                "target": target,
                "expected": expected,
                "observed": observed,
                "paths": [event.get("path") for event in updates],
            }, ensure_ascii=False),
        )
        writes = audit_writes(audit)
        add_check(
            checks, "No unrelated task write occurred",
            target_id is not None and all(
                event.get("method") == "PATCH" and event.get("path") == f"/api/tasks/{target_id}"
                for event in writes
            ),
            json.dumps({"expected_target": target_id, "write_count": len(writes), "writes": writes}, ensure_ascii=False),
        )
        expected_after = [dict(item) for item in initial_tasks]
        if target_id and expected:
            final_status = expected[-1][1]
            for item in expected_after:
                if item.get("id") == target_id:
                    item["status"] = final_status
                    break
        expected_after_summary = task_summary(expected_after)
        state_matches = (
            pre_is_initial
            and bool(expected)
            and target_id is not None
            and tasks_match_declared(post_tasks, expected_after)
            and post.get("summary") == expected_after_summary
        )
        add_check(
            checks, "Task rows and summary match the Builder-declared transition outcome",
            state_matches,
            f"pre_initial={pre_is_initial}; expected_target={target_id}; expected_final_status={expected[-1][1] if expected else None}; post_ids={[item['id'] for item in post_tasks]}; summary={post.get('summary')}; expected_summary={expected_after_summary}",
        )
        trace_complete = runner.get("dsh_exit_code") == 0 and dsh_turn_completed(runtime)
        cycle_matches = (
            target is not None and bool(expected) and observed == expected
            and correct_target and state_matches
        )
        expected_report_verdict = (
            "UNKNOWN" if not trace_complete else ("PASS" if cycle_matches else "FAIL")
        )
        report_ok = report_has_state_cycle_result(
            report_text, target_id, target_title, expected_report_verdict
        )
        add_check(
            checks, "Target report verdict matches the independently observed BR-07 result",
            report_ok,
            f"expected_report_verdict={expected_report_verdict}; target={target_id} ({target_title}); expected={expected}; observed={observed}",
        )
        if not trace_complete:
            behavior = "UNKNOWN"
        else:
            behavior = "PASS" if cycle_matches and report_ok else "FAIL"

    elif role in {"delete_confirmation", "delete_cancel"}:
        mutations = runner.get("fixture_mutations") or []
        add_check(checks, "Clean fixture was selected", runner.get("fixture_profile") == "clean" and not mutations, f"profile={runner.get('fixture_profile')}; mutations={mutations}")
        target = target_task(case, initial_tasks)
        target_id = target.get("id") if target else None
        target_title = target.get("title") if target else None
        deletes = [event for event in audit if event.get("method") == "DELETE"]
        writes = audit_writes(audit)
        cancel_scenario = is_delete_cancel_case(case)

        if cancel_scenario:
            expected_retained = None
            expected_summary = initial_summary
            requirements = case.get("execution_requirements") or {}
            for item in requirements.get("test_data") or []:
                if isinstance(item, dict):
                    state = item.get("expected_rule_state") or {}
                    expected_retained = state.get("task_retained") or expected_retained
            retained_matches = target_id is not None and (expected_retained in (None, target_id))
            no_delete_or_write = (not deletes and not writes) if runtime.get("audit_available") else None
            state_matches = (
                target_id is not None
                and retained_matches
                and pre_is_initial
                and tasks_match_declared(post_tasks, initial_tasks)
                and post.get("summary") == expected_summary
            ) if runtime.get("state_available") else None
            dom_snapshots = parse_dom_snapshots(pilot)
            dialog_snapshots = [
                snap for snap in dom_snapshots
                if any(node.get("tag") == "dialog" and "open" in (node.get("attrs") or {}) for node in snap["nodes"])
            ]
            post_cancel_snapshots = [
                snap for snap in dom_snapshots
                if any(node.get("tag") == "dialog" and "open" not in (node.get("attrs") or {}) for node in snap["nodes"])
            ]
            dom_controls_seen = dom_controls(dialog_snapshots)
            dialog_dom_ok = any(item["role"] == "dialog" and item["name"] == "Delete task?" for item in dom_controls_seen) if dom_snapshots else None
            cancel_dom_ok = any(item["role"] == "button" and item["name"] == "Cancel" for item in dom_controls_seen) if dom_snapshots else None
            delete_dom_ok = any(item["role"] == "button" and item["name"] == "Delete task" for item in dom_controls_seen) if dom_snapshots else None
            closed_after_cancel_ok = bool(post_cancel_snapshots) if dom_snapshots else None
            target_dom_ok = any(target_title and target_title in row for row in dom_rows(post_cancel_snapshots)) if dom_snapshots else None
            dom_ok = (dialog_dom_ok and cancel_dom_ok and delete_dom_ok and closed_after_cancel_ok and target_dom_ok) if dom_snapshots else None
            report_ok = None if not skill_report_exists else (
                skill_report_exists
                and bool(target_title) and target_title in report_text
                and (bool(target_id) and target_id in report_text or bool(target_title))
                and "Cancel" in report_text and "Delete task" in report_text
                and re.search(r"dialog|对话框", report_text, re.I) is not None
                and re.search(r"未点击|未发出|没有.*DELETE|not clicked", report_text, re.I) is not None
                and re.search(r"PASS|CONFORMS|通过", report_text, re.I) is not None
            )
            add_check(
                checks, "Cancel scenario did not issue a delete or other mutation",
                no_delete_or_write,
                json.dumps({"target": target, "deletes": deletes, "writes": writes}, ensure_ascii=False),
            )
            add_check(
                checks, "Cancel preserved the Builder-declared target, full task set and summary",
                state_matches,
                f"pre_initial={pre_is_initial}; retained={expected_retained}; target_id={target_id}; post_ids={[item['id'] for item in post_tasks]}; summary={post.get('summary')}; expected_summary={expected_summary}",
            )
            add_check(
                checks, "Target-produced DOM snapshots show the open dialog, Cancel/Delete actions and visible target",
                dom_ok,
                json.dumps({"dialog": dialog_dom_ok, "cancel": cancel_dom_ok, "delete": delete_dom_ok, "closed_after_cancel": closed_after_cancel_ok, "target_retained_after_cancel": target_dom_ok}, ensure_ascii=False),
            )
            add_check(
                checks, "Target report documents the dialog, Cancel choice and safe outcome",
                report_ok,
                f"BR-08 cancel scenario, target {target_id} ({target_title}), dialog, Cancel, no deletion and PASS inspected",
            )
            add_check(
                checks, "Evidence contains screenshots for the dialog and post-Cancel workflow",
                len(screenshots) >= 3,
                f"screenshot_count={len(screenshots)}",
            )
            behavior = "FAIL" if any(item["status"] == "FAIL" for item in checks) else ("UNKNOWN" if any(item["status"] == "UNKNOWN" for item in checks) else "PASS")
        else:
            expected_after = [
                item for item in initial_tasks
                if target_id is not None and item.get("id") != target_id
            ]
            expected_summary = task_summary(expected_after) if target_id else {}
            delete_matches = (
                target_id is not None
                and len(deletes) == 1
                and deletes[0].get("path") == f"/api/tasks/{target_id}"
                and (deletes[0].get("item") or {}).get("id") == target_id
            )
            add_check(
                checks, "Only the Builder-declared target was deleted once",
                delete_matches,
                json.dumps({"target": target, "deletes": deletes}, ensure_ascii=False),
            )
            add_check(
                checks, "No create, status mutation or unrelated delete occurred",
                target_id is not None and len(writes) == 1 and writes[0].get("method") == "DELETE"
                and writes[0].get("path") == f"/api/tasks/{target_id}",
                json.dumps(writes, ensure_ascii=False),
            )
            state_matches = (
                target_id is not None
                and pre_is_initial
                and tasks_match_declared(post_tasks, expected_after)
                and post.get("summary") == expected_summary
            )
            add_check(
                checks, "Pre/post state matches initial and confirmed-delete result",
                state_matches,
                f"pre_initial={pre_is_initial}; target_id={target_id}; post_ids={[item['id'] for item in post_tasks]}; summary={post.get('summary')}; expected_summary={expected_summary}",
            )
            # BR-08 is the case's authority, not a required literal report token.
            report_ok = report_has_delete_result(report_text, target_id)
            add_check(checks, "Target report documents the confirmation dialog and chosen Delete task action", report_ok, f"BR-08, target ID {target_id}, confirmation dialog, Delete task and PASS verdict inspected")
            add_check(checks, "Evidence contains screenshots for the dialog workflow", len(screenshots) >= 3, f"screenshot_count={len(screenshots)}")
            behavior = "PASS" if delete_matches and state_matches and report_ok and len(screenshots) >= 3 else "FAIL"

    else:
        add_check(checks, "Pilot role has a supported Oracle", False, role)
        behavior = "UNKNOWN"

    failed = [item for item in checks if item["status"] == "FAIL"]
    unknown = [item for item in checks if item["status"] == "UNKNOWN"]
    verdict = "FAIL" if failed else ("UNKNOWN" if unknown else "PASS")
    if role == "delete_cancel":
        behavior = "FAIL" if failed else ("UNKNOWN" if unknown else "PASS")
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
        "limitations": (["DOM snapshots are target-produced files copied from the Skill workspace; they are corroborative evidence, not independent browser instrumentation."] if parse_dom_snapshots(pilot) else []),
    }



def build_report(suite: dict, entries: list[dict], results: list[dict]) -> dict:
    verdicts = [item.get("oracle_verdict", "UNKNOWN") for item in results]
    passed = sum(value == "PASS" for value in verdicts)
    if passed == len(results) and len(results) in {3, 11}:
        status = "PASS"
        completion_status = "COMPLETED"
    elif "FAIL" in verdicts:
        status = "FAIL"
        completion_status = "COMPLETED_WITH_FAIL"
    else:
        status = "UNKNOWN"
        completion_status = "COMPLETED_WITH_UNKNOWN"
    cases = [
        {**item, "adjudication_status": item.get("oracle_verdict", "UNKNOWN")}
        for item in results
    ]
    return {
        "status": status,
        "completion_status": completion_status,
        "scope": "independent_three_case_pilot_adjudication" if len(entries) == 3 else "independent_remaining_eleven_case_adjudication",
        "formal_cases_created_or_modified": False,
        "oracle_exposed_to_builder_or_target_skill": False,
        "builder_suite_id": suite.get("suite_id"),
        "builder_version": suite.get("version"),
        "case_count": len(results),
        "passed_cases": passed,
        "failed_cases": sum(value == "FAIL" for value in verdicts),
        "required_pilot_roles": [item.get("pilot_role") for item in entries],
        "required_case_ids": [item.get("case_id") for item in entries],
        "observed_case_ids": [
            item["case_id"] for item in results if item.get("execution_valid")
        ],
        "verdict_counts": dict(Counter(verdicts)),
        "business_behavior_verdict_counts": dict(
            Counter(item.get("business_behavior_verdict", "UNKNOWN") for item in results)
        ),
        "cases": cases,
        "results": results,
        "limitations": ([
            "Only the three selected pilot cases are adjudicated; the other generated cases are not all executed.",
            "The search mutation is a controlled synthetic defect, not a production defect.",
            "A PASS applies to the selected pilot cases, not to the full generated suite or the 0.0.1 release gates.",
        ] if len(entries) == 3 else [
            "Only the eleven selected remaining cases are adjudicated; the three original pilot cases are outside this report.",
            "A PASS applies only to these eleven cases and archived execution evidence, not to the full generated suite or release gates.",
        ]),
    }


def self_test() -> int:
    assert dsh_turn_completed({
        "trace": {"final_reason": "completed", "turn_end_count": 1},
        "expected_user_turns": 1,
    })
    assert not dsh_turn_completed({
        "trace": {"final_reason": None, "turn_end_count": 0},
        "expected_user_turns": 1,
    })

    production_style_case = {
        "user_input": "请依次输入 reset、RESET、一个只出现在某条任务描述中的英文词（例如 CSV），以及 zzz-no-match。",
    }
    extracted = extract_search_queries(production_style_case, INITIAL)
    assert extracted == ["reset", "RESET", "CSV", "zzz-no-match"], extracted

    builder_search_case = {
        "user_input": "在页面上验证 BR-02。依次输入 reset、SCREENSHOTS、email 和 zzzz-no-match，等待列表更新并记录每次结果中的任务 ID。",
        "expected_behavior": [
            "输入 reset 应命中 WB-101。",
            "输入 SCREENSHOTS 应命中 WB-102。",
            "输入 email 应命中 WB-101 与 WB-104。",
            "输入 zzzz-no-match 应无结果。",
        ],
        "execution_requirements": {"test_data": ["查询：reset、SCREENSHOTS、email、zzzz-no-match"]},
    }
    assert extract_search_queries(builder_search_case, INITIAL) == [
        "reset", "SCREENSHOTS", "email", "zzzz-no-match",
    ], extract_search_queries(builder_search_case, INITIAL)

    builder_actual_search_case = {
        "user_input": (
            "验证 Workboard Lite 的搜索行为：先搜索大写 'PASSWORD'，再搜索小写 'screenshots'。"
            "确认 'PASSWORD' 能匹配标题 'Reset password flow'，"
            "'screenshots' 能匹配描述中包含该词的 'Update onboarding guide'。"
        ),
        "expected_behavior": [
            "搜索 'PASSWORD' 后只显示标题匹配的 Reset password flow。",
            "搜索 'screenshots' 后只显示描述匹配的 Update onboarding guide。",
            "每次查询后的摘要必须仍为 all=5、open=2、in_progress=2、done=1。",
        ],
    }
    assert extract_search_queries(builder_actual_search_case, INITIAL) == [
        "PASSWORD", "screenshots",
    ], extract_search_queries(builder_actual_search_case, INITIAL)

    builder_state_case = {
        "user_input": "定位初始状态为 Open 的 WB-101，预期顺序为 Open → In progress → Done → Open。",
        "expected_behavior": [
            "第一次点击后 WB-101 从 Open 变为 In progress。",
            "第二次点击后 WB-101 从 In progress 变为 Done。",
            "第三次点击后 WB-101 从 Done 回到 Open。",
        ],
        "execution_requirements": {"test_data": ["WB-101 Reset password flow，初始 Open"]},
    }
    state_target = target_task(builder_state_case, INITIAL)
    assert state_target and state_target["id"] == "WB-101", state_target
    assert expected_status_transitions(builder_state_case, state_target) == [
        ("open", "in_progress"), ("in_progress", "done"), ("done", "open"),
    ]
    builder_expected_cycle_steps_case = {
        "execution_requirements": {"test_data": [
            {"name": "target_task", "data_id": "WB-101", "visible_title": "Reset password flow", "initial_status": "Open"},
            {"name": "expected_cycle", "steps": [
                {"step": 1, "status": "In progress"},
                {"step": 2, "status": "Done"},
                {"step": 3, "status": "Open"},
            ]},
        ]},
    }
    cycle_target = target_task(builder_expected_cycle_steps_case, INITIAL)
    assert cycle_target and cycle_target["id"] == "WB-101", cycle_target
    assert expected_status_transitions(builder_expected_cycle_steps_case, cycle_target) == [
        ("open", "in_progress"), ("in_progress", "done"), ("done", "open"),
    ]

    builder_actual_state_case = {
        "user_input": "定位 WB-101（初始 Open），依次点击状态按钮三次。预期：第 1 次 In progress，第 2 次 Done，第 3 次 Open。",
        "expected_behavior": [
            "第一次点击后 WB-101 状态为 In progress。",
            "第二次点击后状态为 Done。",
            "第三次点击后状态回到 Open。",
        ],
        "execution_requirements": {"test_data": [
            "初始任务：WB-101 Open、WB-102 In progress、WB-103 Done、WB-104 Open、WB-105 In progress",
            "目标任务：WB-101 Reset password flow",
        ]},
        "reference_outcome": {"rule_state": "WB-101：Open→In progress→Done→Open"},
    }
    actual_state_target = target_task(builder_actual_state_case, INITIAL)
    assert actual_state_target and actual_state_target["id"] == "WB-101", actual_state_target
    assert expected_status_transitions(builder_actual_state_case, actual_state_target) == [
        ("open", "in_progress"), ("in_progress", "done"), ("done", "open"),
    ]
    # Actual Builder output can place all three ordinal clauses in one list item.
    builder_single_string_state_case = {
        "user_input": "测试 WB-101 的状态流转。点击状态按钮三次。",
        "expected_behavior": [
            "第一次点击后状态为 In progress，摘要为 5/1/3/1，按钮变为 Move to Done；"
            "第二次点击后状态为 Done，摘要为 5/1/2/2，按钮变为 Move to Open；"
            "第三次点击后状态为 Open，摘要为 5/2/2/1，按钮变为 Move to In progress。"
        ],
    }
    single_string_target = target_task(builder_single_string_state_case, INITIAL)
    assert single_string_target and single_string_target["id"] == "WB-101"
    assert expected_status_transitions(builder_single_string_state_case, single_string_target) == [
        ("open", "in_progress"), ("in_progress", "done"), ("done", "open"),
    ], expected_status_transitions(builder_single_string_state_case, single_string_target)

    builder_rule_state_only = {
        "execution_requirements": {"test_data": ["目标任务：WB-101 Reset password flow"]},
        "reference_outcome": {"rule_state": "WB-101：Open→In progress→Done→Open"},
    }
    rule_state_target = target_task(builder_rule_state_only, INITIAL)
    assert rule_state_target and rule_state_target["id"] == "WB-101", rule_state_target
    assert expected_status_transitions(builder_rule_state_only, rule_state_target) == [
        ("open", "in_progress"), ("in_progress", "done"), ("done", "open"),
    ]

    builder_contract_state_case = {
        "execution_requirements": {"test_data": [{
            "task_id": "WB-101",
            "expected": ["open", "in_progress", "done", "open"],
        }]},
    }
    contract_state_target = target_task(builder_contract_state_case, INITIAL)
    assert contract_state_target and contract_state_target["id"] == "WB-101", contract_state_target
    assert expected_status_transitions(builder_contract_state_case, contract_state_target) == [
        ("open", "in_progress"), ("in_progress", "done"), ("done", "open"),
    ]
    builder_contract_delete_case = {
        "execution_requirements": {"test_data": [{
            "task_id": "WB-102",
            "expected_remaining": ["WB-101", "WB-103", "WB-104", "WB-105"],
        }]},
    }
    contract_delete_target = target_task(builder_contract_delete_case, INITIAL)
    assert contract_delete_target and contract_delete_target["id"] == "WB-102", contract_delete_target

    # Regression: real Builder outputs use data_id in initial_state and task_id
    # plus direct from_status/to_status and reference_outcome.query fields.
    builder_real_shape = {
        "user_input": "操作 WB-104 Verify email notification 从 Open 变为 In progress。",
        "reference_outcome": {"task_id": "WB-104", "from_status": "Open", "to_status": "In progress"},
        "execution_requirements": {
            "initial_state": {"tasks": [{"data_id": item["id"], "title": item["title"], "status": item["status"]} for item in INITIAL]},
            "test_data": [{"kind": "ui_only_status_transition", "task_id": "WB-104"}],
        },
    }
    real_tasks = normalized_tasks(builder_real_shape["execution_requirements"]["initial_state"])
    assert [item["id"] for item in real_tasks] == [item["id"] for item in INITIAL]
    real_target = target_task(builder_real_shape, real_tasks)
    assert real_target and real_target["id"] == "WB-104", real_target
    assert expected_status_transitions(builder_real_shape, real_target) == [("open", "in_progress")]
    builder_search_shape_real = {"reference_outcome": {"query": "review"}}
    assert extract_search_queries(builder_search_shape_real, INITIAL) == ["review"]
    builder_visible_title_shape = {"execution_requirements": {"initial_state": {"tasks": [
        {"data_id": "WB-105", "visible_title": "Review accessibility", "status": "In progress"}
    ]}}}
    normalized_visible = normalized_tasks(builder_visible_title_shape["execution_requirements"]["initial_state"])
    assert normalized_visible == [{
        "id": "WB-105", "title": "Review accessibility",
        "description": "Check labels, keyboard order, and status messages.",
        "priority": "Medium", "status": "in_progress",
    }], normalized_visible
    builder_delete_case = {
        "execution_requirements": {"test_data": ["WB-103 Fix export timeout，初始 Done"]},
    }
    delete_target = target_task(builder_delete_case, INITIAL)
    assert delete_target and delete_target["id"] == "WB-103", delete_target
    builder_actual_delete_case = {
        "user_input": "在 WB-104 行点击 Delete，确认对话框后点击 Delete task。",
        "execution_requirements": {"test_data": [
            "初始任务：WB-101 Open、WB-102 In progress、WB-103 Done、WB-104 Open、WB-105 In progress",
            "目标删除任务：WB-104 Verify email notification",
        ]},
        "reference_outcome": {"rule_state": "确认删除后 WB-104 消失"},
    }
    actual_delete_target = target_task(builder_actual_delete_case, INITIAL)
    assert actual_delete_target and actual_delete_target["id"] == "WB-104", actual_delete_target

    assert expected_search_counts(extracted, INITIAL, "case_sensitive_title_only") == {
        "reset": 0, "RESET": 0, "CSV": 0, "zzz-no-match": 0,
    }
    assert expected_search_counts(extracted, INITIAL, "conforming") == {
        "reset": 1, "RESET": 1, "CSV": 1, "zzz-no-match": 0,
    }

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        uppercase_report = root / "case-insensitive-report" / "skill-artifacts" / "REPORT.md"
        uppercase_report.parent.mkdir(parents=True)
        uppercase_report.write_text("Uppercase report extension is discoverable.", encoding="utf-8")
        uppercase_text, uppercase_files = report_bundle(uppercase_report.parent.parent)
        assert "Uppercase report extension is discoverable." in uppercase_text
        assert uppercase_files == []
        roles = {
            "search_mutation": {
                "case_id": "DYNAMIC-SEARCH-01",
                "target_title": "Reset password flow",
                "report": "BR-02: ONBOARDING returned 0 while WB-102 Update onboarding guide was expected. screenshots returned 0 while WB-102 description contained screenshots. 搜索大小写敏感，描述未参与匹配；VIOLATED.",
                "profile": "mutant",
                "mutations": ["search-case-sensitive"],
                "rule_expected": {
                    "PASSWORD": "Reset password flow",
                    "password": "Reset password flow",
                    "SCREENSHOTS": "Update onboarding guide",
                },
            },
            "state_cycle": {
                "case_id": "DYNAMIC-STATE-02",
                "target_title": "Reset password flow",
                "report": "BR-07 PASS: WB-101 Reset password flow moved Open, In progress, Done, Open. Summary counts returned to 5/2/2/1.",
                "profile": "clean",
                "mutations": [],
                "rule_expected": {
                    "target": "Reset password flow",
                    "steps": [
                        {"from": "Open", "to": "In progress"},
                        {"from": "In progress", "to": "Done"},
                        {"from": "Done", "to": "Open"},
                    ],
                },
            },
            "delete_confirmation": {
                "case_id": "DYNAMIC-DELETE-03",
                "target_title": "Verify email notification",
                "report": "BR-08 PASS: WB-104 Verify email notification. Delete task? dialog opened; Delete task removed WB-104 after confirmation.",
                "profile": "clean",
                "mutations": [],
                "rule_expected": {"target": "Update onboarding guide"},
            },
        }
        cases = {}
        for role, spec in roles.items():
            pilot = root / role
            artifacts = pilot / "skill-artifacts"
            artifacts.mkdir(parents=True)
            (artifacts / "report.md").write_text(spec["report"], encoding="utf-8")
            (artifacts / "evidence.json").write_text("{}", encoding="utf-8")
            for index in range(3 if role == "delete_confirmation" else 1):
                (artifacts / f"step-{index}.png").write_bytes(b"test-image")
            trace_events = [
                {"type": "session", "sessionId": "S-1"},
                {"type": "status", "phase": "turn_start", "turn": 1},
                {"type": "tool_call", "tool": "skill", "input": {"name": "webapp-testing"}, "callId": "C-1"},
                {"type": "tool_result", "callId": "C-1", "status": "completed"},
                {"type": "status", "phase": "turn_end", "turn": 1},
                {"type": "final", "reason": {"kind": "completed"}},
            ]
            (pilot / "dsh-events.jsonl").write_text(
                "".join(json.dumps(item) + "\n" for item in trace_events), encoding="utf-8"
            )
            target = next(item for item in INITIAL if item["title"] == spec["target_title"])
            audit = [{"method": "POST", "path": "/api/reset", "status": 200, "action": "reset"}]
            if role == "search_mutation":
                for query, count in {
                    "ONBOARDING": 0, "screenshots": 0,
                }.items():
                    audit.append({
                        "method": "GET", "path": "/api/tasks", "query": "q=" + query,
                        "status": 200, "result_count": count,
                    })
                post_state = {"items": INITIAL, "summary": INITIAL_SUMMARY}
            elif role == "state_cycle":
                for old_status, new_status in [
                    ("open", "in_progress"), ("in_progress", "done"), ("done", "open")
                ]:
                    audit.append({
                        "method": "PATCH", "path": f"/api/tasks/{target['id']}", "status": 200,
                        "action": "status-changed", "old_status": old_status, "new_status": new_status,
                    })
                post_state = {"items": INITIAL, "summary": INITIAL_SUMMARY}
            else:
                audit.append({
                    "method": "DELETE", "path": f"/api/tasks/{target['id']}", "status": 200,
                    "action": "deleted", "item": target,
                })
                post_items = [item for item in INITIAL if item["id"] != target["id"]]
                post_state = {"items": post_items, "summary": task_summary(normalized_tasks({"items": post_items}))}
            run_id = "oracle-self-test-" + role
            audit = [{**item, "run_id": run_id} for item in audit]
            (pilot / "server-audit.jsonl").write_text(
                "".join(json.dumps(item) + "\n" for item in audit), encoding="utf-8"
            )
            trace_path = pilot / "dsh-events.jsonl"
            (pilot / "trace-run-context.json").write_text(json.dumps({
                "run_id": run_id,
                "trace_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
                "trace_event_count": len(trace_events),
            }), encoding="utf-8")
            runner = {
                "case_id": spec["case_id"],
                "run_id": run_id,
                "runner_status": "INVOCATION_OK",
                "dsh_exit_code": 0,
                "completed_user_turn_count": 1,
                "session_turn_results": [{"turn_id": "T1", "dsh_exit_code": 0, "final_reason": "completed"}],
                "server_port_closed": True,
                "required_skill_evidence": {
                    "markdown_report": True, "json_evidence_index": True, "screenshot": True,
                },
                "fixture_profile": spec["profile"],
                "fixture_mutations": spec["mutations"],
                "pre_state": {"items": INITIAL, "summary": INITIAL_SUMMARY},
                "post_state": post_state,
            }
            runner["evidence_files"] = [
                {"path": path.relative_to(pilot).as_posix(),
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                 "size_bytes": path.stat().st_size}
                for path in sorted(pilot.rglob("*"))
                if path.is_file() and path.name != "runner-result.json"
            ]
            (pilot / "runner-result.json").write_text(
                json.dumps(runner, ensure_ascii=False), encoding="utf-8"
            )
            cases[spec["case_id"]] = {
                "case_id": spec["case_id"],
                "dataset_id": "generated",
                "user_input": "single turn",
                "reference_outcome": {"rule_expected": spec["rule_expected"]},
                "execution_requirements": {
                    "initial_state": {"tasks": INITIAL, "summary": INITIAL_SUMMARY},
                },
            }
            if role == "search_mutation":
                cases[spec["case_id"]]["expected_behavior"] = {
                    "required_queries": ["ONBOARDING", "screenshots"],
                    "possible_observations": {
                        "conforming": {"ONBOARDING": ["WB-102"], "screenshots": ["WB-102"]},
                        "case_sensitive_title_only": {"ONBOARDING": [], "screenshots": []},
                    },
                }
                cases[spec["case_id"]]["reference_outcome"] = {
                    "conforming_branch": {"ONBOARDING": ["WB-102"], "screenshots": ["WB-102"]}
                }
                cases[spec["case_id"]]["execution_requirements"]["test_data"] = [{
                    "target_task": "WB-102",
                }]
            elif role == "state_cycle":
                cases[spec["case_id"]]["reference_outcome"] = {
                    "conforming_branch": {"statuses": ["In progress", "Done", "Open"]}
                }
                cases[spec["case_id"]]["execution_requirements"]["test_data"] = [{
                    "target_task": "WB-101",
                    "expected_sequence": ["In progress", "Done", "Open"],
                }]
            elif role == "delete_confirmation":
                cases[spec["case_id"]]["reference_outcome"] = {
                    "conforming": {
                        "dialog_shown": True,
                        "cancel_keeps_all": True,
                        "confirm_removes_only": "WB-104",
                    }
                }
                cases[spec["case_id"]]["execution_requirements"]["test_data"] = [{
                    "target_task": "WB-104",
                }]

        verdicts = {}
        results = []
        entries = []
        for role, spec in roles.items():
            result = adjudicate(cases[spec["case_id"]], root / role, role)
            results.append(result)
            entries.append({
                "case_id": spec["case_id"],
                "dataset_id": "generated",
                "pilot_role": role,
            })
            verdicts[role] = result["oracle_verdict"]
            assert result["business_behavior_verdict"] == (
                "EXPECTED_VIOLATION_DETECTED" if role == "search_mutation" else "PASS"
            ), (role, result)
        assert verdicts == {role: "PASS" for role in roles}, verdicts
        # Regression: Builder-authored delete-cancel cases must be adjudicated
        # as cancellation, not as a confirmed-delete scenario. This mirrors
        # WB-C10's actual schema and verifies no DELETE is required.
        cancel_case = {
            "case_id": "DYNAMIC-DELETE-CANCEL-04",
            "dataset_id": "generated",
            "user_input": "点击 WB-103 行的 Delete，确认对话框出现后点击 Cancel；不要点击 Delete task。",
            "reference_outcome": {
                "rule_expected": {
                    "dialog_shown": True,
                    "cancel_closes": True,
                    "task_retained": "WB-103",
                    "summary_unchanged": INITIAL_SUMMARY,
                },
            },
            "execution_requirements": {
                "initial_state": {"tasks": INITIAL, "summary": INITIAL_SUMMARY},
                "test_data": [{
                    "kind": "delete_cancel",
                    "task_id": "WB-103",
                    "expected_rule_state": {
                        "dialog_shown": True,
                        "cancel_closes": True,
                        "task_retained": "WB-103",
                        "summary_unchanged": INITIAL_SUMMARY,
                    },
                }],
            },
        }
        assert is_delete_cancel_case(cancel_case)
        cancel_pilot = root / "delete_cancel_regression"
        cancel_artifacts = cancel_pilot / "skill-artifacts"
        cancel_artifacts.mkdir(parents=True)
        cancel_report = (
            "# BR-08 PASS: WB-103 Fix export timeout. Delete button opened the confirmation dialog. "
            "Clicked Cancel; dialog closed and WB-103 remained. The task set and summary were unchanged. "
            "Delete task was not clicked and no DELETE request was issued. PASS."
        )
        (cancel_artifacts / "report.md").write_text(cancel_report, encoding="utf-8")
        (cancel_artifacts / "evidence.json").write_text("{}", encoding="utf-8")
        cancel_rows = "".join(
            f'<tr><td>{item["title"]}</td><td>{item["priority"]}</td><td>{item["status"]}</td></tr>'
            for item in INITIAL
        )
        cancel_table = f"<table><tbody>{cancel_rows}</tbody></table>"
        cancel_dialog = (
            '<dialog id="delete-dialog" aria-labelledby="delete-heading">'
            '<h2 id="delete-heading">Delete task?</h2>'
            '<button>Cancel</button><button>Delete task</button></dialog>'
        )
        (cancel_artifacts / "dialog-open.html").write_text(
            cancel_table + cancel_dialog.replace('<dialog id="delete-dialog"', '<dialog id="delete-dialog" open'),
            encoding="utf-8",
        )
        (cancel_artifacts / "after-cancel.html").write_text(cancel_table + cancel_dialog, encoding="utf-8")
        for index in range(3):
            (cancel_artifacts / f"cancel-step-{index}.png").write_bytes(b"test-image")
        (cancel_pilot / "dsh-events.jsonl").write_text(
            "".join(json.dumps(item) + "\n" for item in trace_events), encoding="utf-8"
        )
        cancel_run_id = "oracle-self-test-delete-cancel"
        cancel_audit = [
            {"method": "POST", "path": "/api/reset", "status": 200, "action": "reset", "run_id": cancel_run_id},
        ]
        (cancel_pilot / "server-audit.jsonl").write_text(
            "".join(json.dumps(item) + "\n" for item in cancel_audit), encoding="utf-8"
        )
        cancel_trace_path = cancel_pilot / "dsh-events.jsonl"
        (cancel_pilot / "trace-run-context.json").write_text(json.dumps({
            "run_id": cancel_run_id,
            "trace_sha256": hashlib.sha256(cancel_trace_path.read_bytes()).hexdigest(),
            "trace_event_count": len(trace_events),
        }), encoding="utf-8")
        cancel_runner = {
            "case_id": cancel_case["case_id"],
            "run_id": cancel_run_id,
            "runner_status": "INVOCATION_OK",
            "dsh_exit_code": 0,
            "completed_user_turn_count": 1,
            "session_turn_results": [{"turn_id": "T1", "dsh_exit_code": 0, "final_reason": "completed"}],
            "server_port_closed": True,
            "required_skill_evidence": {
                "markdown_report": True, "json_evidence_index": True, "screenshot": True,
            },
            "fixture_profile": "clean",
            "fixture_mutations": [],
            "pre_state": {"items": INITIAL, "summary": INITIAL_SUMMARY},
            "post_state": {"items": INITIAL, "summary": INITIAL_SUMMARY},
        }
        cancel_runner["evidence_files"] = [
            {"path": path.relative_to(cancel_pilot).as_posix(),
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
             "size_bytes": path.stat().st_size}
            for path in sorted(cancel_pilot.rglob("*"))
            if path.is_file() and path.name != "runner-result.json"
        ]
        (cancel_pilot / "runner-result.json").write_text(
            json.dumps(cancel_runner, ensure_ascii=False), encoding="utf-8"
        )
        cancel_result = adjudicate(cancel_case, cancel_pilot, "delete_confirmation")
        assert cancel_result["oracle_verdict"] == "PASS", cancel_result
        assert cancel_result["business_behavior_verdict"] == "PASS", cancel_result
        assert all(check["status"] == "PASS" for check in cancel_result["checks"]), cancel_result

        contract = build_report({"suite_id": "self-test", "version": "0.0.1"}, entries, results)
        assert contract["status"] == "PASS"
        assert contract["scope"] == "independent_three_case_pilot_adjudication"
        assert contract["passed_cases"] == 3 and contract["failed_cases"] == 0
        assert contract["formal_cases_created_or_modified"] is False
        assert contract["oracle_exposed_to_builder_or_target_skill"] is False
        assert {item["pilot_role"] for item in contract["cases"]} == {
            "search_mutation", "state_cycle", "delete_confirmation"
        }
    print("PASS: independent Oracle derives targets from Builder cases and accepts reproduced synthetic violations.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--builder-output")
    parser.add_argument("--pilots-root")
    parser.add_argument("--pilot-matrix")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    missing = [name for name in ("builder_output", "pilots_root", "pilot_matrix", "output") if not getattr(args, name)]
    if missing:
        parser.error("missing required arguments: " + ", ".join("--" + name.replace("_", "-") for name in missing))

    builder_output = Path(args.builder_output).resolve()
    pilots_root = Path(args.pilots_root).resolve()
    matrix = load_json(Path(args.pilot_matrix).resolve())
    cases = case_index(builder_output)
    entries = matrix.get("include")
    if not isinstance(entries, list) or len(entries) not in {3, 11}:
        raise SystemExit("pilot matrix must contain exactly three original-pilot entries or eleven remaining-case entries")
    roles = [item.get("pilot_role") for item in entries]
    expected_roles = EXPECTED_ROLES if len(entries) == 3 else REMAINING_ROLES
    if set(roles) != expected_roles or len(set(roles)) != len(expected_roles):
        raise SystemExit(f"pilot roles must be exactly {sorted(expected_roles)}")
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

    suite = load_json(builder_output / "SUITE-MANIFEST.json")
    output = build_report(suite, entries, results)
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": output["status"],
        "completion_status": output["completion_status"],
        "case_count": output["case_count"],
        "passed_cases": output["passed_cases"],
        "failed_cases": output["failed_cases"],
        "verdict_counts": output["verdict_counts"],
        "output": str(output_path),
    }, ensure_ascii=False))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
