#!/usr/bin/env python3
"""Resolve one deterministic pilot case per Builder-produced dataset.

The Builder remains the sole producer of datasets and case IDs. This script only
selects existing cases for a small execution pilot; it never creates or edits cases.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def load_suite(output_root: Path) -> dict:
    root = output_root.resolve()
    manifest_path = root / "SUITE-MANIFEST.json"
    if not manifest_path.is_file():
        fail(f"missing suite manifest: {manifest_path}")
    try:
        suite = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read suite manifest: {exc}")

    datasets = suite.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        fail("SUITE-MANIFEST.json must contain a non-empty datasets array")

    include = []
    seen_dataset_ids = set()
    seen_case_ids = set()
    for dataset_index, dataset in enumerate(datasets):
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
        if not isinstance(relative_jsonl, str):
            fail(f"{dataset_id}: jsonl path must be a string")
        rel = PurePosixPath(relative_jsonl)
        if rel.is_absolute() or ".." in rel.parts:
            fail(f"{dataset_id}: unsafe jsonl path: {relative_jsonl}")
        jsonl_path = (root / Path(*rel.parts)).resolve()
        if root not in jsonl_path.parents or not jsonl_path.is_file():
            fail(f"{dataset_id}: dataset JSONL is missing or escapes output root: {relative_jsonl}")
        if not isinstance(expected_count, int) or isinstance(expected_count, bool) or expected_count < 1:
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
                if not isinstance(case_id, str) or not case_id.strip():
                    fail(f"{dataset_id}:{line_number}: missing case_id")
                if case_id in seen_case_ids:
                    fail(f"duplicate case_id across suite: {case_id}")
                seen_case_ids.add(case_id)
                cases.append(case)
        except OSError as exc:
            fail(f"{dataset_id}: cannot read dataset JSONL: {exc}")

        if len(cases) != expected_count:
            fail(f"{dataset_id}: manifest says {expected_count} cases, JSONL contains {len(cases)}")
        if not cases:
            fail(f"{dataset_id}: no cases available for pilot")

        # Stable, low-cost pilot selection: first case in Builder-authored JSONL order.
        # This is selection only; the case content and ID remain unchanged.
        selected = cases[0]
        # Apply a mutation only when the selected Builder case explicitly tests
        # description/search behavior. Keep all unrelated cases on the clean profile.
        test_data = (selected.get("execution_requirements") or {}).get("test_data") or []
        search_challenge = any(
            isinstance(item, dict)
            and item.get("kind") in {"description_queries", "search_queries"}
            for item in test_data
        )
        fixture_profile = "mutant" if search_challenge else "clean"
        fixture_mutations = ["search-case-sensitive"] if search_challenge else []
        include.append({
            "dataset_id": dataset_id,
            "dataset_path": relative_jsonl,
            "case_id": selected["case_id"],
            "fixture_profile": fixture_profile,
            "fixture_mutations": fixture_mutations,
        })

    if len(include) != len(datasets):
        fail("not every Builder dataset produced exactly one pilot selection")
    return {"include": include}


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "datasets").mkdir()
        (root / "datasets" / "D-A.jsonl").write_text(
            json.dumps({"dataset_id": "D-A", "case_id": "D-A-001"}) + "\n"
            + json.dumps({"dataset_id": "D-A", "case_id": "D-A-002"}) + "\n",
            encoding="utf-8",
        )
        (root / "datasets" / "D-B.jsonl").write_text(
            json.dumps({
                "dataset_id": "D-B",
                "case_id": "D-B-001",
                "execution_requirements": {"test_data": [{"kind": "description_queries"}]},
            }) + "\n",
            encoding="utf-8",
        )
        (root / "SUITE-MANIFEST.json").write_text(json.dumps({
            "datasets": [
                {"dataset_id": "D-A", "jsonl": "datasets/D-A.jsonl", "case_count": 2},
                {"dataset_id": "D-B", "jsonl": "datasets/D-B.jsonl", "case_count": 1},
            ]
        }), encoding="utf-8")
        matrix = load_suite(root)
        assert matrix == {"include": [
            {"dataset_id": "D-A", "dataset_path": "datasets/D-A.jsonl", "case_id": "D-A-001", "fixture_profile": "clean", "fixture_mutations": []},
            {"dataset_id": "D-B", "dataset_path": "datasets/D-B.jsonl", "case_id": "D-B-001", "fixture_profile": "mutant", "fixture_mutations": ["search-case-sensitive"]},
        ]}
        print("PASS: dynamic pilot matrix self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root")
    parser.add_argument("--write-output")
    parser.add_argument("--github-output", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.output_root:
        parser.error("--output-root is required unless --self-test is used")
    matrix = load_suite(Path(args.output_root))
    serialized = json.dumps(matrix, ensure_ascii=False, separators=(",", ":"))
    if args.write_output:
        Path(args.write_output).write_text(serialized + "\n", encoding="utf-8")
    if args.github_output:
        import os
        target = os.environ.get("GITHUB_OUTPUT")
        if not target:
            fail("GITHUB_OUTPUT is not set")
        with open(target, "a", encoding="utf-8") as stream:
            stream.write(f"matrix={serialized}\n")
    print(serialized)
    return 0


if __name__ == "__main__":
    sys.exit(main())
