#!/usr/bin/env python3
"""Independent Gold Oracle for the three-case Workboard Lite pilot.

Reads Builder-authored cases, runner-owned application state/audit evidence, and
the target Skill's evidence package. Never creates or modifies formal cases.
This file is not mounted into either Skill workspace.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    if not path.is_file():
        raise ValueError(f"missing evidence file: {path}")
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{n}: invalid JSON: {exc}") from exc
            if isinstance(item, dict):
                rows.append(item)
    return rows


def check(checks, name, ok, expected, observed, detail=""):
    checks.append({
        "check_id": name, "status": "PASS" if ok else "FAIL",
        "expected": expected, "observed": observed, "detail": detail,
    })


def find_case(root: Path, entry: dict) -> dict:
    manifest = load_json(root / "SUITE-MANIFEST.json")
    dataset = next((d for d in manifest["datasets"] if d.get("dataset_id") == entry["dataset_id"]), None)
    if not dataset:
        raise ValueError(f"missing dataset {entry['dataset_id']}")
    path = (root / dataset["jsonl"]).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        raise ValueError(f"unsafe or missing JSONL path: {dataset.get('jsonl')}")
    matches = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
               if line.strip() and json.loads(line).get("case_id") == entry["case_id"]]
    if len(matches) != 1:
        raise ValueError(f"expected one case {entry['case_id']}; found {len(matches)}")
    if matches[0].get("quality_status") != "candidate":
        raise ValueError(f"selected case {entry['case_id']} is not candidate")
    if matches[0].get("execution_requirements", {}).get("status") != "NOT_RUN":
        raise ValueError(f"selected case {entry['case_id']} was not NOT_RUN before execution")
    return matches[0]


def case_dir_for(root: Path, case_id: str) -> Path:
    found = []
    for path in root.rglob("runner-result.json"):
        try:
            data = load_json(path)
        except Exception:
            continue
        if data.get("case_id") == case_id:
            found.append(path.parent)
    if len(found) != 1:
        raise ValueError(f"expected one runner-result for {case_id}; found {len(found)}")
    return found[0]


def query_results(events: list[dict]) -> dict[str, list[int]]:
    result = {}
    for event in events:
        if event.get("method") == "GET" and event.get("path") == "/api/tasks":
            query = parse_qs(event.get("query", ""), keep_blank_values=True).get("q", [""])[0]
            count = event.get("result_count")
            if query and type(count) is int:
                result.setdefault(query, []).append(count)
    return result


def adjudicate_one(suite: Path, pilot: Path, entry: dict) -> dict:
    cid, role = entry["case_id"], entry["pilot_role"]
    case = find_case(suite, entry)
    folder = case_dir_for(pilot, cid)
    runner = load_json(folder / "runner-result.json")
    audit = load_jsonl(folder / "server-audit.jsonl")
    skill = folder / "skill-artifacts"
    if not skill.is_dir():
        raise ValueError(f"{cid}: missing skill-artifacts")
    result_files = sorted(skill.rglob("result.json"))
    scripts = sorted(skill.rglob("*.py"))
    images = sorted(p for p in skill.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
    reports = sorted(skill.rglob("*.md"))
    result = load_json(result_files[0]) if len(result_files) == 1 else {}
    assertions = result.get("assertions") if isinstance(result.get("assertions"), list) else []
    verdicts = [a.get("verdict") for a in assertions if isinstance(a, dict)]
    result_text = json.dumps(result, ensure_ascii=False).casefold()
    pre, post = runner.get("pre_state") or {}, runner.get("post_state") or {}
    observed_queries = query_results(audit)
    checks = []

    check(checks, "runner_invocation", runner.get("runner_status") == "INVOCATION_OK",
          "INVOCATION_OK", runner.get("runner_status"))
    trace = runner.get("trace") or {}
    check(checks, "actual_skill_call",
          trace.get("webapp_testing_skill_calls", 0) > 0 and trace.get("completed_skill_calls", 0) > 0,
          "completed webapp-testing Skill call", trace)
    check(checks, "server_cleanup", runner.get("server_port_closed") is True, True, runner.get("server_port_closed"))
    check(checks, "one_result_json", len(result_files) == 1, "one result.json", len(result_files))
    check(checks, "playwright_script", bool(scripts), "at least one Python script", [p.name for p in scripts])
    min_images = {"search_mutation": 3, "multi_turn": 4, "delete_confirmation": 3}[role]
    check(checks, "screenshots", len(images) >= min_images, f">={min_images}", len(images))
    check(checks, "markdown_report", bool(reports), "at least one Markdown report", [p.name for p in reports])
    check(checks, "result_case_id", result.get("case_id") == cid, cid, result.get("case_id"))
    check(checks, "assertion_contract",
          bool(verdicts) and all(v in {"PASS", "FAIL", "UNKNOWN"} for v in verdicts),
          "non-empty PASS/FAIL/UNKNOWN assertions", verdicts)

    if role == "search_mutation":
        gold = {"EXPORT": 1, "token expiry": 1, "zzz-no-such-task": 0}
        mutant = {"EXPORT": 0, "token expiry": 0, "zzz-no-such-task": 0}
        observed = {q: rows[-1] for q, rows in observed_queries.items() if q in gold and rows}
        mutations = runner.get("fixture_mutations") or []
        check(checks, "correct_mutant", runner.get("fixture_profile") == "mutant"
              and mutations == ["search-case-sensitive"],
              {"profile": "mutant", "mutations": ["search-case-sensitive"]},
              {"profile": runner.get("fixture_profile"), "mutations": mutations})
        check(checks, "all_three_queries", set(observed) == set(gold), sorted(gold), sorted(observed))
        check(checks, "mutant_behavior_confirmed", observed == mutant,
              {"mutant_signature": mutant, "business_rule_expected": gold}, observed)
        check(checks, "defect_identified", result.get("overall") == "VIOLATION" and "FAIL" in verdicts,
              "VIOLATION with at least one FAIL", {"overall": result.get("overall"), "verdicts": verdicts})
        required = ["export", "token expiry", "zzz-no-such-task", "wb-103", "wb-101"]
        check(checks, "expected_vs_observed_reported", all(x in result_text for x in required),
              required, [x for x in required if x in result_text])
        check(checks, "no_task_mutation", pre.get("items") == post.get("items")
              and pre.get("summary") == post.get("summary"), "pre_state == post_state",
              {"pre": pre, "post": post})

    elif role == "multi_turn":
        created = [e for e in audit if e.get("method") == "POST" and e.get("action") == "created"]
        patches = [e for e in audit if e.get("method") == "PATCH" and e.get("action") == "status-changed"]
        deleted = [e for e in audit if e.get("method") == "DELETE" and e.get("action") == "deleted"]
        turns = case.get("user_input") if isinstance(case.get("user_input"), list) else []
        item = created[0].get("item", {}) if len(created) == 1 else {}
        task_id = item.get("id")
        session_results = runner.get("session_turn_results") or []
        check(checks, "four_turn_continuity", len(turns) == 4
              and runner.get("user_turn_count") == 4
              and runner.get("completed_user_turn_count") == 4
              and len(session_results) == 4
              and len({x.get("session_id_argument") or runner.get("session_id") for x in session_results}) == 1,
              "4 turns in one DSH session", {"input": len(turns),
              "completed": runner.get("completed_user_turn_count"), "session": runner.get("session_id")})
        check(checks, "created_task", len(created) == 1 and item.get("title") == "Sprint retro prep"
              and item.get("priority") == "High" and item.get("status") == "open",
              "one High/Open Sprint retro prep task", created)
        counts = observed_queries.get("action items", [])
        check(checks, "description_search", bool(counts) and counts[-1] == 1,
              "description search returns 1 result", counts)
        transitions = [(e.get("old_status"), e.get("new_status")) for e in patches]
        ids = [e.get("path", "").rsplit("/", 1)[-1] for e in patches]
        check(checks, "status_cycle", transitions == [("open", "in_progress"), ("in_progress", "done")]
              and len(ids) == 2 and len(set(ids)) == 1 and ids[0] == task_id,
              [("open", "in_progress"), ("in_progress", "done")], transitions)
        check(checks, "delete_created_task", len(deleted) == 1
              and deleted[0].get("item", {}).get("id") == task_id,
              f"delete only created task {task_id}", deleted)
        check(checks, "restore_initial_state", pre.get("items") == post.get("items")
              and pre.get("summary") == post.get("summary"), "post_state equals pre_state",
              {"pre": pre, "post": post})
        check(checks, "target_skill_conclusion", result.get("overall") == "CONFORMS"
              and verdicts and all(v == "PASS" for v in verdicts),
              "CONFORMS and all assertions PASS", {"overall": result.get("overall"), "verdicts": verdicts})

    elif role == "delete_confirmation":
        delete_requests = [e for e in audit if e.get("method") == "DELETE"]
        reset_requests = [e for e in audit if e.get("method") == "POST" and e.get("path") == "/api/reset"]
        other_mutations = [e for e in audit if e.get("method") in {"POST", "PATCH", "DELETE"}
                           and not (e.get("method") == "POST" and e.get("path") == "/api/reset")]
        deleted = [e for e in delete_requests if e.get("action") == "deleted" and e.get("status") == 200]
        before_items = pre.get("items") or []
        after_items = post.get("items") or []
        before = {x.get("id") for x in before_items}
        after = {x.get("id") for x in after_items}
        test_data = (case.get("execution_requirements") or {}).get("test_data") or []
        target_spec = next((x for x in test_data if x.get("kind") == "target_task"), {})
        remaining_spec = next((x for x in test_data if x.get("kind") == "expected_remaining_tasks"), {})
        summary_spec = next((x for x in test_data if x.get("kind") == "expected_summary"), {})
        target_title = target_spec.get("visible_title")
        target_items = [x for x in before_items if x.get("title") == target_title]
        target_id = target_items[0].get("id") if len(target_items) == 1 else None
        expected_remaining_titles = set(remaining_spec.get("values") or [])
        expected_summary_text = str(summary_spec.get("value") or "")
        import re
        summary_values = re.findall(r"(All|Open|In progress|Done)\s*=\s*(\d+)", expected_summary_text)
        summary_keys = {"All": "all", "Open": "open", "In progress": "in_progress", "Done": "done"}
        expected_summary = {summary_keys[k]: int(v) for k, v in summary_values}
        mutations = runner.get("fixture_mutations") or []
        check(checks, "clean_fixture", runner.get("fixture_profile") == "clean" and not mutations,
              {"profile": "clean", "mutations": []},
              {"profile": runner.get("fixture_profile"), "mutations": mutations})
        guard_events = load_jsonl(folder / "delete-guard-audit.jsonl") if (folder / "delete-guard-audit.jsonl").is_file() else []
        check(checks, "delete_guard_enabled", runner.get("delete_guard_enabled") is True,
              True, runner.get("delete_guard_enabled"))
        check(checks, "delete_guard_single_allowed_attempt",
              len(guard_events) == 1 and guard_events[0].get("attempt") == 1
              and guard_events[0].get("path") == "/api/tasks/WB-104"
              and guard_events[0].get("allowed") is True and guard_events[0].get("status") == 200,
              "one allowed successful DELETE to WB-104, no other attempts", guard_events)
        check(checks, "runner_only_reset", len(reset_requests) == 1 and reset_requests[0].get("status") == 200,
              "exactly one successful pre-run reset by Runner", reset_requests)
        check(checks, "no_other_mutations", len(other_mutations) == 1 and other_mutations[0] in delete_requests,
              "only the single intended DELETE mutation", other_mutations)
        check(checks, "one_delete_request", len(delete_requests) == 1 and len(deleted) == 1,
              "exactly one DELETE request, successful", delete_requests)
        check(checks, "delete_target", target_id is not None and deleted[0].get("item", {}).get("id") == target_id
              and delete_requests[0].get("path", "").endswith("/" + str(target_id)),
              {"target_title": target_title, "target_id": target_id},
              {"request": delete_requests, "deleted": deleted})
        remaining_titles = {x.get("title") for x in after_items}
        check(checks, "only_target_removed", target_id in before and after == before - {target_id}
              and remaining_titles == expected_remaining_titles and len(after_items) == len(expected_remaining_titles),
              sorted(expected_remaining_titles), sorted(remaining_titles))
        check(checks, "summary_after_delete", bool(expected_summary) and post.get("summary") == expected_summary,
              expected_summary, post.get("summary"))
        check(checks, "target_skill_conclusion", result.get("overall") == "CONFORMS"
              and verdicts and all(v == "PASS" for v in verdicts),
              "CONFORMS and all assertions PASS", {"overall": result.get("overall"), "verdicts": verdicts})
        required = [str(target_title or "").casefold(), "delete task"]
        check(checks, "dialog_result_reported", all(x in result_text for x in required),
              required, [x for x in required if x in result_text])

    status = "PASS" if all(x["status"] == "PASS" for x in checks) else "FAIL"
    return {"case_id": cid, "dataset_id": entry["dataset_id"], "pilot_role": role,
            "adjudication_status": status, "checks": checks,
            "runner_result": str(folder / "runner-result.json"),
            "skill_result": str(result_files[0]) if len(result_files) == 1 else None}


def adjudicate(suite: Path, pilot: Path, matrix: dict) -> dict:
    entries = matrix.get("include")
    if not isinstance(entries, list) or len(entries) != 3:
        raise ValueError("pilot matrix must contain exactly three cases")
    ids = [x.get("case_id") for x in entries]
    roles = [x.get("pilot_role") for x in entries]
    if len(set(ids)) != 3 or set(roles) != {"search_mutation", "multi_turn", "delete_confirmation"}:
        raise ValueError("pilot matrix must contain three unique cases with the three required roles")
    cases = [adjudicate_one(suite, pilot, entry) for entry in entries]
    passed = sum(x["adjudication_status"] == "PASS" for x in cases)
    return {"status": "PASS" if passed == 3 else "FAIL",
            "scope": "independent_three_case_pilot_adjudication",
            "formal_cases_created_or_modified": False,
            "oracle_exposed_to_builder_or_target_skill": False,
            "case_count": 3, "passed_cases": passed, "failed_cases": 3 - passed,
            "cases": cases,
            "limitations": ["This is a three-case pilot result, not a full-suite quality score or release approval.",
                            "Screenshot presence is checked automatically; semantic screenshot review remains a human review item."]}


def self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        suite, pilot = root / "suite", root / "pilot"
        (suite / "datasets").mkdir(parents=True)
        (pilot / "C-SEARCH" / "skill-artifacts").mkdir(parents=True)
        case = {"case_id": "C-SEARCH", "dataset_id": "D-1", "quality_status": "candidate",
                "execution_requirements": {"status": "NOT_RUN"}, "coverage_tags": [{"coverage_item_id": "BR-02"}]}
        (suite / "datasets" / "D-1.jsonl").write_text(json.dumps(case) + "\n", encoding="utf-8")
        (suite / "SUITE-MANIFEST.json").write_text(json.dumps({"datasets": [{"dataset_id": "D-1", "jsonl": "datasets/D-1.jsonl"}]}), encoding="utf-8")
        folder = pilot / "C-SEARCH"
        (folder / "runner-result.json").write_text(json.dumps({
            "case_id": "C-SEARCH", "runner_status": "INVOCATION_OK", "fixture_profile": "mutant",
            "fixture_mutations": ["search-case-sensitive"], "server_port_closed": True,
            "trace": {"webapp_testing_skill_calls": 1, "completed_skill_calls": 1},
            "pre_state": {"items": [1], "summary": {"all": 5}}, "post_state": {"items": [1], "summary": {"all": 5}},
        }), encoding="utf-8")
        audit = [{"method": "GET", "path": "/api/tasks", "query": "q=EXPORT", "result_count": 0},
                 {"method": "GET", "path": "/api/tasks", "query": "q=token+expiry", "result_count": 0},
                 {"method": "GET", "path": "/api/tasks", "query": "q=zzz-no-such-task", "result_count": 0}]
        (folder / "server-audit.jsonl").write_text("".join(json.dumps(x) + "\n" for x in audit), encoding="utf-8")
        skill = folder / "skill-artifacts"
        (skill / "result.json").write_text(json.dumps({
            "case_id": "C-SEARCH", "overall": "VIOLATION",
            "assertions": [{"verdict": "FAIL", "expected": "WB-103 for EXPORT, WB-101 for token expiry; zzz-no-such-task expects no rows",
                            "observed": "0 rows for EXPORT, token expiry, and zzz-no-such-task"}]}), encoding="utf-8")
        (skill / "test.py").write_text("print('test')\n", encoding="utf-8")
        for i in range(3):
            (skill / f"step-{i}.png").write_bytes(b"png")
        (skill / "report.md").write_text("report\n", encoding="utf-8")
        entry = {"dataset_id": "D-1", "case_id": "C-SEARCH", "pilot_role": "search_mutation"}
        report = adjudicate_one(suite, pilot, entry)
        assert report["adjudication_status"] == "PASS", report

        # Regression test: delete-confirmation must derive the target from
        # Builder test_data, not a historical hard-coded task ID.
        delete_case = {
            "case_id": "C-DELETE", "dataset_id": "D-1", "quality_status": "candidate",
            "execution_requirements": {"status": "NOT_RUN", "test_data": [
                {"kind": "target_task", "visible_title": "Verify email notification"},
                {"kind": "expected_remaining_tasks", "values": [
                    "Reset password flow", "Update onboarding guide", "Fix export timeout", "Review accessibility"]},
                {"kind": "expected_summary", "value": "All=4, Open=1, In progress=2, Done=1"}]},
        }
        (suite / "datasets" / "D-1.jsonl").write_text(
            json.dumps(case) + "\n" + json.dumps(delete_case) + "\n", encoding="utf-8")
        manifest = load_json(suite / "SUITE-MANIFEST.json")
        manifest["datasets"][0]["case_count"] = 2
        (suite / "SUITE-MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        delete_folder = pilot / "C-DELETE"
        skill_delete = delete_folder / "skill-artifacts"
        skill_delete.mkdir(parents=True)
        before_items = [
            {"id": "WB-101", "title": "Reset password flow", "status": "open"},
            {"id": "WB-102", "title": "Update onboarding guide", "status": "in_progress"},
            {"id": "WB-103", "title": "Fix export timeout", "status": "done"},
            {"id": "WB-104", "title": "Verify email notification", "status": "open"},
            {"id": "WB-105", "title": "Review accessibility", "status": "in_progress"},
        ]
        after_items = [x for x in before_items if x["id"] != "WB-104"]
        runner_delete = {
            "case_id": "C-DELETE", "runner_status": "INVOCATION_OK",
            "fixture_profile": "clean", "fixture_mutations": [],
            "server_port_closed": True,
            "trace": {"webapp_testing_skill_calls": 1, "completed_skill_calls": 1},
            "pre_state": {"items": before_items, "summary": {"all": 5, "open": 2, "in_progress": 2, "done": 1}},
            "post_state": {"items": after_items, "summary": {"all": 4, "open": 1, "in_progress": 2, "done": 1}},
        }
        (delete_folder / "runner-result.json").write_text(json.dumps(runner_delete), encoding="utf-8")
        delete_audit = [
            {"method": "POST", "path": "/api/reset", "status": 200, "action": "reset"},
            {"method": "DELETE", "path": "/api/tasks/WB-104", "status": 200,
             "action": "deleted", "item": before_items[3]},
        ]
        (delete_folder / "delete-guard-audit.jsonl").write_text(json.dumps({
            "attempt": 1, "method": "DELETE", "path": "/api/tasks/WB-104",
            "allowed": True, "status": 200
        }) + "\n", encoding="utf-8")
        runner_delete["delete_guard_enabled"] = True
        (delete_folder / "runner-result.json").write_text(json.dumps(runner_delete), encoding="utf-8")
        (delete_folder / "server-audit.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in delete_audit), encoding="utf-8")
        (skill_delete / "result.json").write_text(json.dumps({
            "case_id": "C-DELETE", "overall": "CONFORMS",
            "assertions": [{"verdict": "PASS"}],
            "summary": "Verify email notification deleted once; Delete task confirmed",
        }), encoding="utf-8")
        (skill_delete / "test.py").write_text("print('test')\n", encoding="utf-8")
        (skill_delete / "report.md").write_text("Verify email notification deleted; Delete task confirmed\n", encoding="utf-8")
        for i in range(3):
            (skill_delete / f"delete-{i}.png").write_bytes(b"png")
        delete_entry = {"dataset_id": "D-1", "case_id": "C-DELETE", "pilot_role": "delete_confirmation"}
        delete_report = adjudicate_one(suite, pilot, delete_entry)
        assert delete_report["adjudication_status"] == "PASS", delete_report
        (delete_folder / "server-audit.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in delete_audit + [delete_audit[1]]), encoding="utf-8")
        duplicate_delete_report = adjudicate_one(suite, pilot, delete_entry)
        assert duplicate_delete_report["adjudication_status"] == "FAIL", duplicate_delete_report
    print("PASS: independent Gold Oracle self-test")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--suite-root")
    p.add_argument("--pilot-root")
    p.add_argument("--matrix")
    p.add_argument("--output")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        return self_test()
    if not all((args.suite_root, args.pilot_root, args.matrix, args.output)):
        p.error("suite-root, pilot-root, matrix, and output are required")
    report = adjudicate(Path(args.suite_root), Path(args.pilot_root), load_json(Path(args.matrix)))
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "passed_cases", "failed_cases")}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
