#!/usr/bin/env python3
"""Select three Builder-authored cases for the isolated execution pilot.

Selection is semantic and data-driven. This module validates and selects
existing Builder cases only; it never creates, edits, repairs, or regrades them.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath

ALLOWED_QUALITY = {"candidate", "needs_info"}
PILOT_COUNT = 3
ROLE_PATTERNS = {
    "search_mutation": {
        "required_groups": [
            ("search", "搜索"),
            ("case-sensitive", "case sensitive", "case-insensitive", "case insensitive", "大小写", "不区分大小写"),
            ("defect", "bug", "incorrect", "mismatch", "regression", "failure", "缺陷", "错误", "不符合", "异常", "变异", "突变"),
        ],
    },
    "multi_turn": {
        "required_groups": [("multi_turn", "multi-turn", "multi turn")],
    },
    "delete_confirmation": {
        "required_groups": [
            ("delete", "remove", "deletion", "removal", "删除"),
            ("confirm", "confirmation", "confirming", "确认", "对话框"),
        ],
    },
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def case_text(case: dict) -> str:
    """Build a searchable view from authored case fields without changing them."""
    fields = (
        "title", "objective", "evaluation_target", "user_input",
        "expected_behavior", "forbidden_behavior", "capability_keys",
        "scenario_bucket", "business_rule_refs", "workflow_refs",
    )
    values = [str(case.get(key, "")) for key in fields]
    for tag in case.get("coverage_tags", []) if isinstance(case.get("coverage_tags"), list) else []:
        if isinstance(tag, dict):
            values.extend(str(tag.get(key, "")) for key in ("dimension", "value", "coverage_item_id"))
    return " ".join(values).casefold()


def role_score(case: dict, role: str) -> int:
    text = case_text(case)
    score = 0
    for alternatives in ROLE_PATTERNS[role]["required_groups"]:
        matched = [term for term in alternatives if term.casefold() in text]
        if not matched:
            return 0
        score += max(len(term) for term in matched)

    # Select the focused search-rule case for the case-sensitive mutant.
    # A case that only mentions search as one step of a larger workflow, or
    # that primarily tests evidence/adversarial claims, is not this pilot role.
    workflows = set(case.get("workflow_refs", []))
    business_rules = set(case.get("business_rule_refs", []))
    buckets = set(case.get("scenario_bucket", []))
    if role == "search_mutation":
        if workflows != {"WF-SEARCH"} or business_rules != {"BR-02"} or "normal" not in buckets:
            return 0
        score += 100

    # Prefer the richest genuinely multi-turn case. Turn count is derived
    # from the Builder-authored prompt structure; workflow breadth breaks a tie.
    elif role == "multi_turn":
        if "multi_turn" not in buckets:
            return 0
        user_input = case.get("user_input")
        turn_count = len(user_input) if isinstance(user_input, list) else 1
        score += 100 + min(turn_count, 9) * 10 + min(len(workflows), 9)

    # Keep the deletion pilot focused on a single UI workflow. Multi-turn
    # deletion scenarios remain eligible for the multi-turn role instead.
    elif role == "delete_confirmation":
        if workflows != {"WF-DELETE"} or "BR-08" not in business_rules or "multi_turn" in buckets:
            return 0
        score += 100

    return score


def validate_case_for_pilot(case: dict, dataset_id: str) -> None:
    case_id = case["case_id"]
    if case.get("quality_status") != "candidate":
        fail(f"{dataset_id}/{case_id}: pilot cases must have quality_status=candidate")
    execution = case.get("execution_requirements")
    if not isinstance(execution, dict) or execution.get("status") != "NOT_RUN":
        fail(f"{dataset_id}/{case_id}: candidate case execution status must be NOT_RUN")
    if case.get("information_gaps"):
        open_gaps = [
            gap for gap in case["information_gaps"]
            if isinstance(gap, dict) and gap.get("status") in {"OPEN", "IN_PROGRESS"}
        ]
        if open_gaps:
            fail(f"{dataset_id}/{case_id}: unresolved information gaps block pilot selection")
    environment = execution.get("environment")
    if not isinstance(environment, dict):
        fail(f"{dataset_id}/{case_id}: execution environment is missing")
    if environment.get("app_url") != "http://127.0.0.1:4173":
        fail(f"{dataset_id}/{case_id}: app_url must target the local Workboard fixture")
    timeout = environment.get("case_timeout_seconds")
    if type(timeout) is not int or not 1 <= timeout <= 900:
        fail(f"{dataset_id}/{case_id}: case_timeout_seconds must be an integer from 1 to 900")
    initial = execution.get("initial_state", {})
    state = initial.get("server_state") if isinstance(initial, dict) else None
    state = state or environment.get("server_state_at_start") or "running"
    if state != "running":
        fail(f"{dataset_id}/{case_id}: pilot runner supports server_state=running only")


def load_suite(output_root: Path, pilot_count: int = PILOT_COUNT) -> dict:
    root = output_root.resolve()
    manifest_path = root / "SUITE-MANIFEST.json"
    if not manifest_path.is_file():
        fail(f"missing suite manifest: {manifest_path}")
    try:
        suite = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read suite manifest: {exc}")

    if suite.get("quality_status") not in ALLOWED_QUALITY:
        fail("Suite quality_status must be candidate or needs_info before pilot selection")
    if suite.get("execution_status") != "NOT_RUN":
        fail("Suite execution_status must be NOT_RUN before pilot execution")
    datasets = suite.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        fail("SUITE-MANIFEST.json must contain a non-empty datasets array")
    if type(pilot_count) is not int or pilot_count != PILOT_COUNT:
        fail(f"this benchmark requires exactly {PILOT_COUNT} semantic pilot roles")

    all_candidate_cases: list[dict] = []
    dataset_entries: dict[str, dict] = {}
    seen_case_ids: set[str] = set()

    for dataset in datasets:
        if not isinstance(dataset, dict):
            fail("each dataset manifest entry must be an object")
        dataset_id = dataset.get("dataset_id")
        relative_jsonl = dataset.get("jsonl")
        expected_count = dataset.get("case_count")
        if not isinstance(dataset_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", dataset_id):
            fail(f"invalid dataset_id: {dataset_id!r}")
        if dataset_id in dataset_entries:
            fail(f"duplicate dataset_id: {dataset_id}")
        dataset_entries[dataset_id] = dataset
        if dataset.get("quality_status") not in ALLOWED_QUALITY:
            fail(f"{dataset_id}: dataset quality_status must be candidate or needs_info")
        if dataset.get("execution_status") != "NOT_RUN":
            fail(f"{dataset_id}: dataset execution_status must be NOT_RUN")
        if not isinstance(relative_jsonl, str):
            fail(f"{dataset_id}: jsonl path must be a string")
        rel = PurePosixPath(relative_jsonl)
        if rel.is_absolute() or ".." in rel.parts:
            fail(f"{dataset_id}: unsafe jsonl path: {relative_jsonl}")
        jsonl_path = (root / Path(*rel.parts)).resolve()
        if root not in jsonl_path.parents or not jsonl_path.is_file():
            fail(f"{dataset_id}: dataset JSONL is missing or escapes output root: {relative_jsonl}")
        if type(expected_count) is not int or expected_count < 1:
            fail(f"{dataset_id}: case_count must be a positive integer")

        actual_count = 0
        try:
            for line_number, line in enumerate(jsonl_path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                actual_count += 1
                try:
                    case = json.loads(line)
                except json.JSONDecodeError as exc:
                    fail(f"{dataset_id}:{line_number}: invalid JSON: {exc}")
                if not isinstance(case, dict):
                    fail(f"{dataset_id}:{line_number}: case must be a JSON object")
                if case.get("dataset_id") != dataset_id:
                    fail(f"{dataset_id}:{line_number}: case dataset_id mismatch")
                case_id = case.get("case_id")
                if not isinstance(case_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", case_id):
                    fail(f"{dataset_id}:{line_number}: invalid case_id: {case_id!r}")
                if case_id in seen_case_ids:
                    fail(f"duplicate case_id across suite: {case_id}")
                seen_case_ids.add(case_id)
                if case.get("quality_status") not in ALLOWED_QUALITY:
                    fail(f"{dataset_id}/{case_id}: unsupported quality_status")
                if case.get("quality_status") == "candidate":
                    validate_case_for_pilot(case, dataset_id)
                    all_candidate_cases.append(case)
        except OSError as exc:
            fail(f"{dataset_id}: cannot read dataset JSONL: {exc}")
        if actual_count != expected_count:
            fail(f"{dataset_id}: manifest case_count does not match JSONL")
        if actual_count == 0:
            fail(f"{dataset_id}: dataset JSONL contains no cases")

    if len(all_candidate_cases) < PILOT_COUNT:
        fail(f"only {len(all_candidate_cases)} candidate cases are available; {PILOT_COUNT} required")

    selected: list[tuple[dict, str]] = []
    selected_ids: set[str] = set()
    for role in ROLE_PATTERNS:
        scored = [
            (role_score(case, role), case)
            for case in all_candidate_cases
            if case["case_id"] not in selected_ids
        ]
        scored = [(score, case) for score, case in scored if score > 0]
        if not scored:
            fail(
                f"no Builder-authored candidate matches pilot role {role}; "
                "do not fabricate or rename a case to satisfy the pilot"
            )
        best_score = max(score for score, _ in scored)
        best = [case for score, case in scored if score == best_score]
        if len(best) != 1:
            ids = sorted(case["case_id"] for case in best)
            fail(f"pilot role {role} is ambiguous at score {best_score}: {ids}")
        match = best[0]
        selected.append((match, role))
        selected_ids.add(match["case_id"])

    include = []
    for case, role in selected:
        dataset_id = case["dataset_id"]
        entry = dataset_entries[dataset_id]
        is_search_mutation = role == "search_mutation"
        include.append({
            "dataset_id": dataset_id,
            "dataset_path": entry["jsonl"],
            "case_id": case["case_id"],
            "pilot_role": role,
            "fixture_profile": "mutant" if is_search_mutation else "clean",
            "fixture_mutations": ["search-case-sensitive"] if is_search_mutation else [],
        })
    return {"include": include}


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "datasets").mkdir()
        authored = [
            {
                "dataset_id": "dataset-alpha",
                "case_id": "CASE-SEARCH-17",
                "title": "搜索必须不区分大小写，并匹配标题和描述；检测大小写敏感缺陷",
                "objective": "验证 BR-02 搜索规则。",
                "scenario_bucket": ["normal", "business_rule"],
                "business_rule_refs": ["BR-02"],
                "workflow_refs": ["WF-SEARCH"],
                "user_input": "在页面验证大小写不敏感搜索。",
            },
            {
                "dataset_id": "dataset-search-evidence",
                "case_id": "CASE-SEARCH-EVIDENCE-18",
                "title": "核验未经验证的交接声明并裁决搜索大小写缺陷",
                "objective": "从证据独立核验搜索规则。",
                "scenario_bucket": ["adversarial", "business_rule"],
                "business_rule_refs": ["BR-02"],
                "workflow_refs": ["WF-SEARCH", "WF-EVIDENCE"],
                "user_input": "验证搜索并审查证据。",
            },
            {
                "dataset_id": "dataset-beta",
                "case_id": "CASE-CONTEXT-42",
                "title": "多轮任务应保留前序工作区上下文",
                "objective": "跨轮使用同一任务并验证状态连续性。",
                "scenario_bucket": ["multi_turn"],
                "business_rule_refs": ["BR-04", "BR-02", "BR-07", "BR-03"],
                "workflow_refs": ["WF-CREATE", "WF-SEARCH", "WF-STATUS-CYCLE", "WF-FILTER"],
                "user_input": [
                    {"turn": 1, "prompt": "创建任务并记录 ID X。"},
                    {"turn": 2, "prompt": "继续使用 X 并推进状态。"},
                    {"turn": 3, "prompt": "继续筛选并核对 X。"},
                ],
            },
            {
                "dataset_id": "dataset-multi-delete",
                "case_id": "CASE-MULTI-DELETE-43",
                "title": "多轮删除确认应保留前序上下文",
                "objective": "先取消，再重新打开确认删除。",
                "scenario_bucket": ["multi_turn", "negative"],
                "business_rule_refs": ["BR-08", "BR-01"],
                "workflow_refs": ["WF-DELETE"],
                "user_input": [
                    {"turn": 1, "prompt": "点击删除并取消。"},
                    {"turn": 2, "prompt": "继续并确认删除。"},
                ],
            },
            {
                "dataset_id": "dataset-gamma",
                "case_id": "CASE-DELETE-08",
                "title": "删除任务前必须显示确认对话框",
                "objective": "点击删除并验证确认对话框。",
                "scenario_bucket": ["normal", "negative", "business_rule"],
                "business_rule_refs": ["BR-08", "BR-01"],
                "workflow_refs": ["WF-DELETE"],
                "user_input": "通过页面删除选中任务并确认。",
            },
        ]
        datasets = []
        for item in authored:
            case = {
                **item,
                "quality_status": "candidate",
                "execution_requirements": {
                    "status": "NOT_RUN",
                    "environment": {
                        "app_url": "http://127.0.0.1:4173",
                        "case_timeout_seconds": 120,
                        "server_state_at_start": "running",
                    },
                    "initial_state": {"server_state": "running"},
                },
            }
            jsonl = f"datasets/{item['dataset_id']}.jsonl"
            (root / jsonl).write_text(json.dumps(case, ensure_ascii=False) + "\n", encoding="utf-8")
            datasets.append({
                "dataset_id": item["dataset_id"],
                "jsonl": jsonl,
                "case_count": 1,
                "quality_status": "candidate",
                "execution_status": "NOT_RUN",
            })
        (root / "SUITE-MANIFEST.json").write_text(json.dumps({
            "datasets": datasets,
            "quality_status": "candidate",
            "execution_status": "NOT_RUN",
        }), encoding="utf-8")

        matrix = load_suite(root)
        assert [item["case_id"] for item in matrix["include"]] == [
            "CASE-SEARCH-17", "CASE-CONTEXT-42", "CASE-DELETE-08"
        ]
        assert [item["dataset_id"] for item in matrix["include"]] == [
            "dataset-alpha", "dataset-beta", "dataset-gamma"
        ]
        assert [item["fixture_profile"] for item in matrix["include"]] == [
            "mutant", "clean", "clean"
        ]
        assert [item["fixture_mutations"] for item in matrix["include"]] == [
            ["search-case-sensitive"], [], []
        ]
        print("PASS: focused search, multi-turn and delete-confirmation pilots resolve from Builder-authored cases")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root")
    parser.add_argument("--pilot-count", type=int, default=PILOT_COUNT)
    parser.add_argument("--write-output")
    parser.add_argument("--github-output", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.output_root:
        parser.error("--output-root is required unless --self-test is used")
    matrix = load_suite(Path(args.output_root), pilot_count=args.pilot_count)
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
