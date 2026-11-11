#!/usr/bin/env python3
"""Select three Builder-authored candidate cases for an isolated execution pilot.

This script validates and selects existing cases only. It never creates, edits,
repairs, or regrades formal evaluation cases.
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
PILOT_ROLES = (
    ("wb-defect", "WB-DEF-01", "BR-02", "search_mutation"),
    ("wb-lifecycle", "WB-LIFE-01", "SCN-MULTI-TURN", "multi_turn"),
    ("wb-core", "WB-CORE-08", "BR-08", "delete_confirmation"),
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def tags_for(case: dict) -> set[str]:
    tags = case.get("coverage_tags", [])
    if not isinstance(tags, list):
        fail(f"{case.get('case_id')}: coverage_tags must be a list")
    values = set()
    for tag in tags:
        if isinstance(tag, dict) and isinstance(tag.get("coverage_item_id"), str):
            values.add(tag["coverage_item_id"])
    return values


def load_suite(output_root: Path, pilot_count: int = 3) -> dict:
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
    if type(pilot_count) is not int or pilot_count < 1:
        fail("pilot_count must be a positive integer")

    all_candidate_cases: list[dict] = []
    seen_dataset_ids: set[str] = set()
    seen_case_ids: set[str] = set()

    for dataset in datasets:
        if not isinstance(dataset, dict):
            fail("each dataset manifest entry must be an object")
        dataset_id = dataset.get("dataset_id")
        relative_jsonl = dataset.get("jsonl")
        expected_count = dataset.get("case_count")
        if not isinstance(dataset_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", dataset_id):
            fail(f"invalid dataset_id: {dataset_id!r}")
        if dataset_id in seen_dataset_ids:
            fail(f"duplicate dataset_id: {dataset_id}")
        seen_dataset_ids.add(dataset_id)
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

        cases = []
        try:
            for line_number, line in enumerate(jsonl_path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
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
                    execution = case.get("execution_requirements")
                    if not isinstance(execution, dict) or execution.get("status") != "NOT_RUN":
                        fail(f"{dataset_id}/{case_id}: candidate case execution status must be NOT_RUN")
                    cases.append(case)
        except OSError as exc:
            fail(f"{dataset_id}: cannot read dataset JSONL: {exc}")

        actual_count = sum(1 for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip())
        if actual_count != expected_count:
            fail(f"{dataset_id}: manifest case_count does not match JSONL")
        # A dataset with zero candidate cases is allowed when its own quality is needs_info.
        all_candidate_cases.extend(cases)

    if len(all_candidate_cases) < pilot_count:
        fail(f"only {len(all_candidate_cases)} candidate cases are available; {pilot_count} required")

    selected: list[tuple[dict, str]] = []
    selected_ids: set[str] = set()
    for expected_dataset, expected_case_id, coverage_id, role in PILOT_ROLES:
        matches = [
            case for case in all_candidate_cases
            if case["dataset_id"] == expected_dataset
            and case["case_id"] == expected_case_id
            and coverage_id in tags_for(case)
        ]
        if len(matches) != 1:
            fail(
                f"required pilot role {role} must resolve to exactly one Builder candidate "
                f"({expected_dataset}/{expected_case_id}, tag {coverage_id}); found {len(matches)}"
            )
        match = matches[0]
        if match["case_id"] in selected_ids:
            fail(f"pilot roles resolve to duplicate case_id: {match['case_id']}")
        selected.append((match, role))
        selected_ids.add(match["case_id"])

    if pilot_count != len(PILOT_ROLES):
        fail(f"this benchmark requires exactly {len(PILOT_ROLES)} semantic pilot roles")
    if len(selected) != pilot_count:
        fail(f"expected {pilot_count} distinct semantic pilot cases; selected {len(selected)}")

    include = []
    for case, role in selected:
        dataset_id = case["dataset_id"]
        entry = next(item for item in datasets if item["dataset_id"] == dataset_id)
        relative_jsonl = entry["jsonl"]
        is_search_mutation = role == "search_mutation"
        include.append({
            "dataset_id": dataset_id,
            "dataset_path": relative_jsonl,
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
        pilot_cases = [
            ("wb-defect", "WB-DEF-01", "BR-02"),
            ("wb-lifecycle", "WB-LIFE-01", "SCN-MULTI-TURN"),
            ("wb-core", "WB-CORE-08", "BR-08"),
        ]
        datasets = []
        for dataset_id, case_id, coverage_id in pilot_cases:
            case = {
                "dataset_id": dataset_id,
                "case_id": case_id,
                "quality_status": "candidate",
                "execution_requirements": {"status": "NOT_RUN"},
                "coverage_tags": [{"coverage_item_id": coverage_id}],
            }
            jsonl = f"datasets/{dataset_id}.jsonl"
            (root / jsonl).write_text(json.dumps(case) + "\n", encoding="utf-8")
            datasets.append({
                "dataset_id": dataset_id,
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
        matrix = load_suite(root, pilot_count=3)
        assert [item["case_id"] for item in matrix["include"]] == [
            "WB-DEF-01", "WB-LIFE-01", "WB-CORE-08"
        ]
        assert [item["pilot_role"] for item in matrix["include"]] == [
            "search_mutation", "multi_turn", "delete_confirmation"
        ]
        assert [item["fixture_profile"] for item in matrix["include"]] == [
            "mutant", "clean", "clean"
        ]
        assert matrix["include"][0]["fixture_mutations"] == ["search-case-sensitive"]
        print("PASS: exact Builder-authored cases selected for mutant search, true multi-turn, and delete confirmation")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root")
    parser.add_argument("--pilot-count", type=int, default=3)
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
