#!/usr/bin/env python3
"""Independently validate Evaluation Dataset Builder's generated webapp-testing suite.

This script validates only. It must never create, edit, repair, or select cases.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path("artifacts/webapp-testing-builder-output")
CASE_SCHEMA_PATH = ROOT / "skills/evaluation-dataset-builder/references/dataset-schema.json"
MANIFEST_SCHEMA_PATH = ROOT / "skills/evaluation-dataset-builder/references/dataset-manifest-schema.json"
ALLOWED_QUALITY = {"candidate", "needs_info"}
ALLOWED_EXECUTION = {"NOT_RUN"}


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_nonempty_text(value, location: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{location} must be a non-empty string")


def require_nonempty_collection(value, location: str) -> None:
    if not isinstance(value, (list, dict)) or not value:
        raise SystemExit(f"{location} must be a non-empty list or object")


def require_nonempty_value(value, location: str) -> None:
    if value is None:
        raise SystemExit(f"{location} is required")
    if isinstance(value, str) and not value.strip():
        raise SystemExit(f"{location} must not be blank")
    if isinstance(value, (list, dict)) and not value:
        raise SystemExit(f"{location} must not be empty")


def main() -> int:
    if not OUTPUT.is_dir():
        raise SystemExit(f"Builder output directory not found: {OUTPUT}")

    case_schema = load_schema(CASE_SCHEMA_PATH)
    manifest_schema = load_schema(MANIFEST_SCHEMA_PATH)
    case_validator = jsonschema.Draft202012Validator(
        case_schema, format_checker=jsonschema.FormatChecker()
    )
    manifest_validator = jsonschema.Draft202012Validator(
        manifest_schema, format_checker=jsonschema.FormatChecker()
    )

    dataset_files = sorted(OUTPUT.rglob("*.jsonl"))
    if not dataset_files:
        raise SystemExit("Builder did not produce any JSONL dataset files")

    all_cases: dict[str, dict] = {}
    datasets: dict[str, list[dict]] = defaultdict(list)
    coverage_counts: dict[str, int] = defaultdict(int)
    case_file_count = {}
    file_dataset_ids: dict[str, set[str]] = defaultdict(set)

    for path in dataset_files:
        file_count = 0
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc

            errors = sorted(case_validator.iter_errors(case), key=lambda e: list(e.path))
            if errors:
                details = "; ".join(
                    f"{'/'.join(map(str, error.path)) or '$'}: {error.message}"
                    for error in errors[:8]
                )
                raise SystemExit(f"{path}:{line_no}: Dataset Schema validation failed: {details}")

            case_id = case["case_id"]
            if case_id in all_cases:
                raise SystemExit(f"Duplicate case_id across datasets: {case_id}")
            if case["quality_status"] not in ALLOWED_QUALITY:
                raise SystemExit(
                    f"Case {case_id} quality_status must remain candidate/needs_info, "
                    f"got {case['quality_status']}"
                )
            execution_status = case["execution_requirements"]["status"]
            if execution_status not in ALLOWED_EXECUTION:
                raise SystemExit(
                    f"Case {case_id} has unsupported execution_status {execution_status}"
                )

            require_nonempty_value(case.get("user_input"), f"{case_id}.user_input")
            require_nonempty_value(case.get("expected_behavior"), f"{case_id}.expected_behavior")
            require_nonempty_collection(case.get("preconditions"), f"{case_id}.preconditions")
            if "forbidden_behavior" not in case or not isinstance(case["forbidden_behavior"], list):
                raise SystemExit(f"Case {case_id} must declare forbidden_behavior as a list")
            require_nonempty_collection(case.get("source_refs"), f"{case_id}.source_refs")

            execution = case["execution_requirements"]
            for field in ("required_permissions", "allowed_actions", "steps",
                          "observable_assertions", "forbidden_side_effects"):
                require_nonempty_collection(execution.get(field), f"{case_id}.execution_requirements.{field}")
            require_nonempty_collection(execution.get("environment"), f"{case_id}.execution_requirements.environment")
            require_nonempty_value(execution.get("initial_state"), f"{case_id}.execution_requirements.initial_state")
            for field in ("expected_end_state", "reset_plan", "cleanup_plan", "failure_cleanup"):
                require_nonempty_value(execution.get(field), f"{case_id}.execution_requirements.{field}")

            grading = case["grading"]
            if not grading.get("uncertainty_policy"):
                raise SystemExit(f"Case {case_id} grading lacks an explicit UNKNOWN policy")
            if not grading.get("pass_conditions") or not grading.get("fail_conditions"):
                raise SystemExit(f"Case {case_id} grading lacks PASS/FAIL conditions")
            if not grading.get("evidence_required"):
                raise SystemExit(f"Case {case_id} grading lacks required evidence")
            for criterion in grading.get("criteria", []):
                for field in ("criterion_id", "description", "pass_condition", "fail_condition", "evidence_required"):
                    if not criterion.get(field):
                        raise SystemExit(f"Case {case_id} grading criterion lacks {field}")

            for source in case.get("source_refs", []):
                require_nonempty_text(source.get("title"), f"{case_id}.source_refs.title")
                require_nonempty_text(source.get("locator"), f"{case_id}.source_refs.locator")

            all_cases[case_id] = case
            datasets[case["dataset_id"]].append(case)
            file_dataset_ids[path.relative_to(OUTPUT).as_posix()].add(case["dataset_id"])
            for tag in case.get("coverage_tags", []):
                coverage_counts[tag["coverage_item_id"]] += 1
            file_count += 1

        if file_count == 0:
            raise SystemExit(f"Dataset file contains no cases: {path}")
        relative_dataset_path = path.relative_to(OUTPUT).as_posix()
        if len(file_dataset_ids[relative_dataset_path]) != 1:
            raise SystemExit(f"Dataset file must contain cases from exactly one dataset: {relative_dataset_path}")
        case_file_count[relative_dataset_path] = file_count

    manifest_files = sorted(
        path for path in OUTPUT.rglob("*.json")
        if path.name.casefold().endswith(".manifest.json")
    )
    if not manifest_files:
        raise SystemExit("Builder did not produce a dataset Manifest JSON file")

    manifests: dict[str, dict] = {}
    manifest_path_by_id: dict[str, str] = {}
    for path in manifest_files:
        manifest = load_json(path)
        errors = sorted(manifest_validator.iter_errors(manifest), key=lambda e: list(e.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(map(str, error.path)) or '$'}: {error.message}"
                for error in errors[:8]
            )
            raise SystemExit(f"{path}: Manifest Schema validation failed: {details}")

        dataset_id = manifest["dataset_id"]
        if dataset_id in manifests:
            raise SystemExit(f"Duplicate Manifest dataset_id: {dataset_id}")
        if manifest["quality_status"] not in ALLOWED_QUALITY:
            raise SystemExit(
                f"Manifest {dataset_id} quality_status must remain candidate/needs_info"
            )
        if manifest["execution_status"] not in ALLOWED_EXECUTION:
            raise SystemExit(
                f"Manifest {dataset_id} execution_status must be NOT_RUN before any real execution"
            )

        owned_cases = datasets.get(dataset_id, [])
        if not owned_cases:
            raise SystemExit(f"Manifest {dataset_id} has no corresponding generated cases")
        if manifest["case_count"] != len(owned_cases):
            raise SystemExit(
                f"Manifest {dataset_id} case_count={manifest['case_count']} "
                f"but found {len(owned_cases)} generated cases"
            )
        manifests[dataset_id] = manifest
        manifest_path_by_id[dataset_id] = path.relative_to(OUTPUT).as_posix()

    suite_manifest_path = OUTPUT / "SUITE-MANIFEST.json"
    if not suite_manifest_path.is_file():
        raise SystemExit("Builder output lacks SUITE-MANIFEST.json")
    suite_manifest = load_json(suite_manifest_path)
    for field in ("suite_id", "version", "built_at", "evaluation_target"):
        require_nonempty_text(suite_manifest.get(field), f"SUITE-MANIFEST.json.{field}")
    suite_coverage = suite_manifest.get("coverage")
    require_nonempty_collection(suite_coverage, "SUITE-MANIFEST.json.coverage")
    require_nonempty_collection(suite_coverage.get("dimensions"), "SUITE-MANIFEST.json.coverage.dimensions")
    suite_entries = suite_manifest.get("datasets")
    if not isinstance(suite_entries, list) or not suite_entries:
        raise SystemExit("SUITE-MANIFEST.json must contain a non-empty datasets array")
    if suite_manifest.get("case_count") != len(all_cases):
        raise SystemExit(
            f"Suite Manifest case_count={suite_manifest.get('case_count')} "
            f"but found {len(all_cases)} generated cases"
        )
    if suite_manifest.get("quality_status") not in ALLOWED_QUALITY:
        raise SystemExit("Suite Manifest quality_status must remain candidate/needs_info")
    if suite_manifest.get("execution_status") not in ALLOWED_EXECUTION:
        raise SystemExit("Suite Manifest execution_status must be NOT_RUN before any real execution")

    suite_dataset_ids = set()
    for entry in suite_entries:
        if not isinstance(entry, dict):
            raise SystemExit("Each Suite Manifest dataset entry must be an object")
        dataset_id = entry.get("dataset_id")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise SystemExit("Suite Manifest dataset entry has an invalid dataset_id")
        if dataset_id in suite_dataset_ids:
            raise SystemExit(f"Duplicate dataset_id in Suite Manifest: {dataset_id}")
        suite_dataset_ids.add(dataset_id)
        require_nonempty_text(entry.get("purpose"), f"SUITE-MANIFEST.json.datasets[{dataset_id}].purpose")
        if entry.get("quality_status") not in ALLOWED_QUALITY:
            raise SystemExit(f"Suite Manifest dataset {dataset_id} quality_status must remain candidate/needs_info")
        if entry.get("execution_status") not in ALLOWED_EXECUTION:
            raise SystemExit(f"Suite Manifest dataset {dataset_id} execution_status must be NOT_RUN")
        jsonl_relative = entry.get("jsonl")
        manifest_relative = entry.get("manifest")
        if not isinstance(jsonl_relative, str) or not isinstance(manifest_relative, str):
            raise SystemExit(f"Suite Manifest {dataset_id} must reference JSONL and Manifest paths")
        jsonl_path = Path(jsonl_relative)
        manifest_path = Path(manifest_relative)
        for relative, label in ((jsonl_path, "jsonl"), (manifest_path, "manifest")):
            if relative.is_absolute() or ".." in relative.parts:
                raise SystemExit(f"Suite Manifest {dataset_id} has unsafe {label} path: {relative}")
        jsonl_key = jsonl_path.as_posix()
        manifest_key = manifest_path.as_posix()
        if jsonl_key not in case_file_count:
            raise SystemExit(f"Suite Manifest {dataset_id} references missing JSONL: {jsonl_key}")
        if file_dataset_ids[jsonl_key] != {dataset_id}:
            raise SystemExit(f"Suite Manifest {dataset_id} JSONL contains different dataset IDs")
        if entry.get("case_count") != case_file_count[jsonl_key]:
            raise SystemExit(f"Suite Manifest {dataset_id} case_count does not match JSONL")
        if manifest_path_by_id.get(dataset_id) != manifest_key:
            raise SystemExit(f"Suite Manifest {dataset_id} references the wrong dataset Manifest")
        if manifests[dataset_id]["case_count"] != case_file_count[jsonl_key]:
            raise SystemExit(f"Dataset Manifest {dataset_id} case_count does not match JSONL")

    if suite_dataset_ids != set(datasets):
        raise SystemExit(
            f"Suite Manifest dataset IDs do not match generated datasets: "
            f"suite={sorted(suite_dataset_ids)}, generated={sorted(datasets)}"
        )

    if set(datasets) != set(manifests):
        missing = sorted(set(datasets) - set(manifests))
        orphaned = sorted(set(manifests) - set(datasets))
        raise SystemExit(
            f"Dataset/Manifest IDs do not match; missing_manifests={missing}; "
            f"manifests_without_cases={orphaned}"
        )

    coverage_files = [p for p in OUTPUT.rglob("*") if p.is_file() and "coverage" in p.name.casefold()]
    coverage_matrix_files = [p for p in coverage_files if p.name.casefold() == "coverage-matrix.json"]
    if len(coverage_matrix_files) != 1:
        raise SystemExit("Builder output must contain exactly one coverage-matrix.json")
    coverage_matrix = load_json(coverage_matrix_files[0])
    coverage_items = coverage_matrix.get("items")
    if not isinstance(coverage_items, list) or not coverage_items:
        raise SystemExit("coverage-matrix.json must contain a non-empty items array")
    coverage_item_by_id = {}
    for item in coverage_items:
        if not isinstance(item, dict):
            raise SystemExit("Coverage matrix items must be objects")
        item_id = item.get("coverage_item_id")
        if not isinstance(item_id, str) or not item_id.strip() or item_id in coverage_item_by_id:
            raise SystemExit(f"Invalid or duplicate coverage_item_id: {item_id!r}")
        if item.get("applicability") not in {"applicable", "not_applicable", "needs_info"}:
            raise SystemExit(f"{item_id}: invalid applicability value")
        if item["applicability"] != "applicable":
            require_nonempty_text(item.get("notes"), f"{item_id}.notes")
        coverage_item_by_id[item_id] = item

    unknown_coverage_tags = sorted(set(coverage_counts) - set(coverage_item_by_id))
    if unknown_coverage_tags:
        raise SystemExit(f"Cases reference unknown coverage items: {unknown_coverage_tags}")
    gap_priorities = suite_manifest["coverage"].get("gap_priorities") or []
    gap_by_id = {
        gap.get("gap_id"): gap
        for gap in gap_priorities
        if isinstance(gap, dict) and isinstance(gap.get("gap_id"), str)
    }
    if len(gap_by_id) != len(gap_priorities):
        raise SystemExit("Suite Manifest gap_priorities contains invalid or duplicate gap IDs")

    matrix_dimensions = {
        item.get("dimension"): item
        for item in coverage_matrix.get("dimensions", [])
        if isinstance(item, dict) and isinstance(item.get("dimension"), str)
    }
    suite_dimensions = {
        item.get("dimension"): item
        for item in suite_manifest["coverage"].get("dimensions", [])
        if isinstance(item, dict) and isinstance(item.get("dimension"), str)
    }
    if set(matrix_dimensions) != set(suite_dimensions):
        raise SystemExit("Coverage matrix and Suite Manifest dimensions do not match")

    for dimension, matrix_summary in matrix_dimensions.items():
        applicable_items = [
            item for item in coverage_items
            if item.get("dimension") == dimension and item.get("applicability") == "applicable"
        ]
        covered_items = [
            item for item in applicable_items
            if coverage_counts.get(item["coverage_item_id"], 0) > 0
        ]
        uncovered_items = [
            item for item in applicable_items
            if coverage_counts.get(item["coverage_item_id"], 0) == 0
        ]
        expected_uncovered = {
            f"{item['coverage_item_id']} {item.get('value', '')}".strip()
            for item in uncovered_items
        }
        for summary in (matrix_summary, suite_dimensions[dimension]):
            if summary.get("total") != len(applicable_items):
                raise SystemExit(f"{dimension}: coverage total does not match applicable items")
            if summary.get("covered") != len(covered_items):
                raise SystemExit(f"{dimension}: covered count does not match case coverage tags")
            if set(summary.get("uncovered", [])) != expected_uncovered:
                raise SystemExit(f"{dimension}: uncovered list does not match coverage items")
            expected_rate = (len(covered_items) / len(applicable_items)) if applicable_items else None
            actual_rate = summary.get("coverage_rate")
            if expected_rate is None:
                if actual_rate is not None:
                    raise SystemExit(f"{dimension}: coverage_rate must be null when total is zero")
            elif not isinstance(actual_rate, (int, float)) or abs(actual_rate - expected_rate) > 0.0001:
                raise SystemExit(f"{dimension}: coverage_rate does not match covered/total")

        for item in uncovered_items:
            gap = gap_by_id.get(item["coverage_item_id"])
            if gap is None:
                raise SystemExit(
                    f"Applicable coverage gap lacks a Suite Manifest gap_priority: {item['coverage_item_id']}"
                )
            require_nonempty_text(gap.get("reason"), f"{item['coverage_item_id']}.gap_priority.reason")
            require_nonempty_text(gap.get("planned_action"), f"{item['coverage_item_id']}.gap_priority.planned_action")

    source_files = [p for p in OUTPUT.rglob("*") if p.is_file() and "source" in p.name.casefold()]
    quality_reports = [
        p for p in OUTPUT.rglob("*")
        if p.is_file() and "quality" in p.name.casefold()
        and p.suffix.lower() in {".md", ".json"}
    ]
    if not coverage_files:
        raise SystemExit("Builder output lacks a coverage matrix or coverage report")
    if not source_files:
        raise SystemExit("Builder output lacks a source map or source traceability file")
    if not quality_reports:
        raise SystemExit("Builder output lacks a quality report")
    report_templates = [
        p for p in OUTPUT.rglob("*")
        if p.is_file() and "template" in p.name.casefold()
        and p.suffix.lower() in {".md", ".json"}
    ]
    if not report_templates:
        raise SystemExit("Builder output lacks the requested report template")

    transient_files = [
        path.relative_to(OUTPUT).as_posix()
        for path in OUTPUT.rglob("*")
        if path.is_file() and (path.suffix.lower() == ".pyc" or "__pycache__" in path.parts)
    ]
    if transient_files:
        raise SystemExit(
            "Builder output contains Python cache artifacts: " + ", ".join(transient_files[:10])
        )

    summary = {
        "status": "PASS",
        "scope": "builder_output_validation_only",
        "formal_evaluation_cases_created_by_validator": False,
        "dataset_count": len(datasets),
        "case_count": len(all_cases),
        "case_files": case_file_count,
        "manifest_files": [p.relative_to(OUTPUT).as_posix() for p in manifest_files],
        "datasets": {
            dataset_id: {
                "case_count": len(cases),
                "manifest_quality_status": manifests[dataset_id]["quality_status"],
                "execution_status": manifests[dataset_id]["execution_status"],
            }
            for dataset_id, cases in sorted(datasets.items())
        },
        "coverage_item_counts": dict(sorted(coverage_counts.items())),
        "schema_errors": 0,
        "quality_status_gate": "candidate/needs_info",
        "execution_status_gate": "NOT_RUN",
        "unknown_policy_gate": "present_in_every_case",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except jsonschema.SchemaError as exc:
        print(f"Invalid repository schema: {exc}", file=sys.stderr)
        raise SystemExit(2)
