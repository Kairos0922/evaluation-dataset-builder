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
        deleted = [e for e in audit if e.get("method") == "DELETE" and e.get("action") == "deleted"]
        before = {x.get("id") for x in pre.get("items", [])}
        after = {x.get("id") for x in post.get("items", [])}
        expected_ids = before - {"WB-102"}
        expected_summary = {"all": 4, "open": 2, "in_progress": 1, "done": 1}
        mutations = runner.get("fixture_mutations") or []
        check(checks, "clean_fixture", runner.get("fixture_profile") == "clean" and not mutations,
              {"profile": "clean", "mutations": []},
              {"profile": runner.get("fixture_profile"), "mutations": mutations})
        check(checks, "cancel_then_confirm", len(deleted) == 1
              and deleted[0].get("item", {}).get("id") == "WB-102",
              "one DELETE of WB-102 after cancel preserved it", deleted)
        check(checks, "only_target_removed", "WB-102" in before and after == expected_ids
              and len(after) == 4, sorted(expected_ids), sorted(after))
        check(checks, "summary_after_delete", post.get("summary") == expected_summary,
              expected_summary, post.get("summary"))
        check(checks, "target_skill_conclusion", result.get("overall") == "CONFORMS"
              and verdicts and all(v == "PASS" for v in verdicts),
              "CONFORMS and all assertions PASS", {"overall": result.get("overall"), "verdicts": verdicts})
        required = ["wb-102", "cancel", "delete task"]
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
