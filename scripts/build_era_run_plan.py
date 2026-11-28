#!/usr/bin/env python3
"""Build a reviewable ERA run-plan draft from the existing Dataset Manifest and Cases.

This creates no run IDs and starts no Agent. A concrete harness must consume the
plan, execute each case in a fresh session, and emit the existing Runtime Record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA = ROOT / "skills" / "evaluation-dataset-builder" / "references" / "dataset-manifest-schema.json"
CASE_SCHEMA = ROOT / "skills" / "evaluation-dataset-builder" / "references" / "dataset-schema.json"
RUNTIME_SCHEMA = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "runtime-record.schema.json"


def reject_constant(token: str):
    raise ValueError(f"invalid JSON numeric constant: {token}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def load_jsonl_bytes(raw: bytes) -> list[dict]:
    cases = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"blank Case JSONL line {line_number}")
        try:
            value = json.loads(line.decode("utf-8"), parse_constant=reject_constant)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"invalid Case JSONL at line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"Case JSONL line {line_number} is not an object")
        cases.append(value)
    return cases


def _validate(schema_path: Path, value: Any, label: str) -> None:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:20]
        )
        raise ValueError(f"{label} schema validation failed: {details}")


def dataset_digest(manifest_bytes: bytes, cases_bytes: bytes) -> str:
    """Match the digest convention already used by import_dsh_pilot_records.py."""
    digest = hashlib.sha256()
    digest.update(b"evaluation-dataset-builder-ida-v0.0.2\\0")
    digest.update(manifest_bytes)
    digest.update(b"\\0")
    digest.update(cases_bytes)
    return digest.hexdigest()


def _validate_configuration(configuration: dict) -> None:
    if not isinstance(configuration, dict):
        raise ValueError("configuration must be a JSON object")
    runtime_schema = load_json(RUNTIME_SCHEMA)
    required = ("configuration_id", "target_revision", "target_type", "model", "harness", "environment", "tool_versions")
    missing = [key for key in required if key not in configuration]
    if missing:
        raise ValueError("configuration missing required Runtime Record identity fields: " + ", ".join(missing))
    for key in required:
        field_schema = runtime_schema["properties"][key]
        errors = list(Draft202012Validator(field_schema, format_checker=FormatChecker()).iter_errors(configuration[key]))
        if errors:
            raise ValueError(f"configuration.{key} is invalid: " + "; ".join(error.message for error in errors))
    if "seed" in configuration:
        errors = list(Draft202012Validator(runtime_schema["properties"]["seed"]).iter_errors(configuration["seed"]))
        if errors:
            raise ValueError("configuration.seed is invalid: " + "; ".join(error.message for error in errors))


def build_era_run_plan(
    manifest: dict,
    manifest_bytes: bytes,
    cases: list[dict],
    cases_bytes: bytes,
    configuration: dict,
    selected_case_ids: list[str] | None = None,
) -> dict:
    """Create a deterministic, non-executing plan over existing Case objects."""
    _validate(MANIFEST_SCHEMA, manifest, "Dataset Manifest")
    _validate_configuration(configuration)
    if manifest.get("case_count") != len(cases):
        raise ValueError("Manifest case_count does not match Case JSONL line count")
    if not cases:
        raise ValueError("Case JSONL contains no cases")

    seen = set()
    for index, case in enumerate(cases, start=1):
        _validate(CASE_SCHEMA, case, f"Case line {index}")
        case_id = case["case_id"]
        if case_id in seen:
            raise ValueError(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        if case["dataset_id"] != manifest["dataset_id"]:
            raise ValueError(f"Case {case_id} dataset_id does not match Manifest")
    if selected_case_ids is None:
        selected = [case["case_id"] for case in cases]
    else:
        if not selected_case_ids or len(selected_case_ids) != len(set(selected_case_ids)):
            raise ValueError("selected_case_ids must be non-empty and unique")
        unknown = sorted(set(selected_case_ids) - seen)
        if unknown:
            raise ValueError("selected case_id not found in dataset: " + ", ".join(unknown))
        selected = selected_case_ids

    by_id = {case["case_id"]: case for case in cases}
    planned_cases = []
    for ordinal, case_id in enumerate(selected, start=1):
        case = by_id[case_id]
        requirements = case["execution_requirements"]
        if requirements.get("status") != "READY_TO_RUN":
            raise ValueError(
                f"Case {case_id} is not READY_TO_RUN (status={requirements.get('status')!r}); "
                "resolve its execution requirements before planning"
            )
        planned_cases.append({
            "ordinal": ordinal,
            "case_id": case_id,
            "case_sha256": hashlib.sha256(
                json.dumps(case, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "case": case,
            "execution_requirements": requirements,
            "historical_source_refs": case.get("source_refs", []),
            "historical_source_refs_are_not_runtime_trace_refs": True,
        })

    digest = dataset_digest(manifest_bytes, cases_bytes)
    dataset = {
        "dataset_id": manifest["dataset_id"],
        "version": manifest["version"],
        "case_count": len(cases),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "cases_jsonl_sha256": hashlib.sha256(cases_bytes).hexdigest(),
        "dataset_sha256": digest,
    }
    identity = {
        "dataset": dataset,
        "configuration": configuration,
        "selected_case_ids": selected,
    }
    plan_id = "era-plan-" + hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "plan_version": "0.0.3",
        "plan_id": plan_id,
        "status": "DRAFT_NOT_EXECUTED",
        "execution_protocol": {
            "session_policy": "fresh_session_per_case",
            "historical_source_trace_reuse": "prohibited",
            "runtime_record_version": "0.0.2",
            "run_id_allocation": "runner_only_after_execution_starts",
            "oracle_policy": "independent_oracle_or_unknown",
        },
        "dataset": dataset,
        "configuration": configuration,
        "planned_cases": planned_cases,
        "execution_count": len(planned_cases),
        "limitations": [
            "This plan is derived from the existing Manifest and Case JSONL; it is not a second Dataset Manifest.",
            "Plan generation does not execute an Agent, allocate run_id values, or create Runtime Records.",
            "A harness must create a new trace_ref/result_ref for each actual run and preserve the dataset_sha256 and case_id bindings.",
            "Missing independent Oracle evidence must remain UNKNOWN; historical source traces are provenance only.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--configuration", required=True, type=Path,
                        help="Frozen Runtime Record identity fields as JSON")
    parser.add_argument("--case-id", action="append", dest="case_ids",
                        help="Optional Case ID to include; repeat for multiple cases")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        manifest_bytes = args.manifest.read_bytes()
        cases_bytes = args.cases.read_bytes()
        plan = build_era_run_plan(
            load_json(args.manifest),
            manifest_bytes,
            load_jsonl_bytes(cases_bytes),
            cases_bytes,
            load_json(args.configuration),
            args.case_ids,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: created non-executing ERA run-plan draft {plan['plan_id']} for {plan['execution_count']} Case(s)")
    print(f"Dataset SHA-256: {plan['dataset']['dataset_sha256']}")
    print("NOTE: no Agent was executed and no Runtime Record was created")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
