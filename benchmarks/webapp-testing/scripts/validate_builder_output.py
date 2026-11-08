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
ALLOWED_EXECUTION = {"NOT_RUN", "DESIGN_ONLY"}


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
            for tag in case.get("coverage_tags", []):
                coverage_counts[tag["coverage_item_id"]] += 1
            file_count += 1

        if file_count == 0:
            raise SystemExit(f"Dataset file contains no cases: {path}")
        case_file_count[path.relative_to(OUTPUT).as_posix()] = file_count

    manifest_files = sorted(
        path for path in OUTPUT.rglob("*.json")
        if "manifest" in path.name.casefold()
    )
    if not manifest_files:
        raise SystemExit("Builder did not produce a dataset Manifest JSON file")

    manifests: dict[str, dict] = {}
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
                f"Manifest {dataset_id} execution_status must remain NOT_RUN/DESIGN_ONLY"
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

    if set(datasets) != set(manifests):
        missing = sorted(set(datasets) - set(manifests))
        orphaned = sorted(set(manifests) - set(datasets))
        raise SystemExit(
            f"Dataset/Manifest IDs do not match; missing_manifests={missing}; "
            f"manifests_without_cases={orphaned}"
        )

    json_files = {
        path.name: path for path in OUTPUT.rglob("*.json")
    }
    coverage_files = [p for p in OUTPUT.rglob("*") if p.is_file() and "coverage" in p.name.casefold()]
    source_files = [p for p in OUTPUT.rglob("*") if p.is_file() and "source" in p.name.casefold()]
    quality_reports = [
        p for p in OUTPUT.rglob("*.md")
        if "quality" in p.name.casefold()
    ]
    if not coverage_files:
        raise SystemExit("Builder output lacks a coverage matrix or coverage report")
    if not source_files:
        raise SystemExit("Builder output lacks a source map or source traceability file")
    if not quality_reports:
        raise SystemExit("Builder output lacks a quality report")
    report_templates = [
        p for p in OUTPUT.rglob("*.md")
        if "template" in p.name.casefold()
    ]
    if not report_templates:
        raise SystemExit("Builder output lacks the requested report template")

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
        "execution_status_gate": "NOT_RUN/DESIGN_ONLY",
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
