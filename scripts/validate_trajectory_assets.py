#!/usr/bin/env python3
"""Validate v0.0.3 trajectory-derived evaluation assets and cross-record invariants."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "v0.0.3"
SCHEMAS = {
    "source": SCHEMA_DIR / "trajectory-source.schema.json",
    "candidate": SCHEMA_DIR / "task-candidate.schema.json",
    "qualification": SCHEMA_DIR / "failure-qualification.schema.json",
    "slice": SCHEMA_DIR / "task-slice.schema.json",
    "reconstruction": SCHEMA_DIR / "environment-reconstruction.schema.json",
}


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant: {token}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)


def _non_finite_paths(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, float) and not math.isfinite(value):
        return [path]
    if isinstance(value, dict):
        return [p for key, child in value.items() for p in _non_finite_paths(child, f"{path}.{key}")]
    if isinstance(value, list):
        return [p for i, child in enumerate(value) for p in _non_finite_paths(child, f"{path}[{i}]")]
    return []


def _schema_errors(kind: str, value: Any) -> list[str]:
    schema = _load_json(SCHEMAS[kind])
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{kind}: schema at {'.'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(value), key=lambda e: list(e.absolute_path))
    ]


def validate_assets(
    source: dict | None = None,
    candidate: dict | None = None,
    qualification: dict | None = None,
    task_slice: dict | None = None,
    reconstruction: dict | None = None,
) -> list[str]:
    """Return schema and cross-record errors. Missing records are allowed for staged validation."""
    supplied = {
        "source": source, "candidate": candidate, "qualification": qualification,
        "slice": task_slice, "reconstruction": reconstruction,
    }
    errors: list[str] = []
    for kind, value in supplied.items():
        if value is None:
            continue
        if not isinstance(value, dict):
            errors.append(f"{kind}: root must be an object")
            continue
        non_finite = _non_finite_paths(value)
        if non_finite:
            errors.extend(f"{kind}: non-finite number at {path}" for path in non_finite)
            continue
        try:
            errors.extend(_schema_errors(kind, value))
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"{kind}: cannot load or validate schema: {exc}")

    if isinstance(source, dict):
        auth = source.get("authorization", {})
        if auth.get("status") in {"not_authorized", "unknown"}:
            errors.append("source: explicit authorization or user-provided provenance is required")
        if source.get("redaction_status") in {"pending_review", "not_redacted", "unknown"}:
            errors.append("source: sensitive-content review must be completed before qualification")
        if source.get("source_kind") == "synthetic_fixture" and auth.get("status") != "synthetic_only":
            errors.append("source: synthetic_fixture requires synthetic_only authorization status")
        if source.get("source_kind") != "synthetic_fixture" and auth.get("status") == "synthetic_only":
            errors.append("source: synthetic_only authorization is valid only for synthetic_fixture")

    if isinstance(candidate, dict) and isinstance(source, dict):
        if candidate.get("source_id") != source.get("source_id"):
            errors.append("candidate: source_id does not match trajectory source")

    if isinstance(qualification, dict) and isinstance(candidate, dict):
        if qualification.get("candidate_id") != candidate.get("candidate_id"):
            errors.append("qualification: candidate_id does not match candidate")
        if qualification.get("review_status") == "qualified":
            decision = qualification.get("decision_context", {})
            contract = qualification.get("task_contract", {})
            if qualification.get("attribution") not in {"agent_decision", "mixed"}:
                errors.append("qualification: qualified status requires agent_decision or mixed attribution")
            if decision.get("could_reasonably_avoid_error") != "yes":
                errors.append("qualification: qualified status requires an avoidable decision error")
            if decision.get("post_hoc_requirement_added") is True:
                errors.append("qualification: post-hoc requirement cannot support a qualified capability gap")
            if not all(contract.get(key) is True for key in (
                "input_identifiable", "deliverable_identifiable", "quality_criteria_identifiable"
            )):
                errors.append("qualification: qualified status requires identifiable input, deliverable and quality criteria")
            if qualification.get("environment_health") != "healthy":
                errors.append("qualification: qualified status requires healthy observed environment")
            if qualification.get("evidence_sufficiency") != "sufficient_for_candidate":
                errors.append("qualification: qualified status requires sufficient evidence")

    if isinstance(task_slice, dict):
        if isinstance(candidate, dict) and task_slice.get("candidate_id") != candidate.get("candidate_id"):
            errors.append("slice: candidate_id does not match candidate")
        if isinstance(source, dict) and task_slice.get("source_id") != source.get("source_id"):
            errors.append("slice: source_id does not match trajectory source")
        if isinstance(qualification, dict):
            if task_slice.get("qualification_id") != qualification.get("qualification_id"):
                errors.append("slice: qualification_id does not match qualification")
            if task_slice.get("status") == "ready_for_reconstruction" and qualification.get("review_status") != "qualified":
                errors.append("slice: ready_for_reconstruction requires a qualified failure review")
        if task_slice.get("status") == "ready_for_reconstruction":
            if task_slice.get("initial_context", {}).get("closure_review") != "complete":
                errors.append("slice: ready_for_reconstruction requires complete context closure")
            if task_slice.get("leakage_review") != "passed":
                errors.append("slice: ready_for_reconstruction requires passed leakage review")

    if isinstance(reconstruction, dict) and isinstance(task_slice, dict):
        if reconstruction.get("slice_id") != task_slice.get("slice_id"):
            errors.append("reconstruction: slice_id does not match task slice")
        if reconstruction.get("readiness") == "ready_for_review":
            if task_slice.get("status") != "ready_for_reconstruction":
                errors.append("reconstruction: ready_for_review requires a ready task slice")
            if reconstruction.get("reset_and_cleanup", {}).get("side_effects_reviewed") is not True:
                errors.append("reconstruction: readiness requires reviewed side-effect and cleanup plan")
            if reconstruction.get("resource_limits", {}).get("network_policy") == "unrestricted_not_recommended":
                errors.append("reconstruction: unrestricted network policy cannot be marked ready_for_review")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for kind, flag in (
        ("source", "--source"), ("candidate", "--candidate"),
        ("qualification", "--qualification"), ("slice", "--slice"),
        ("reconstruction", "--reconstruction"),
    ):
        parser.add_argument(flag, type=Path, help=f"Path to {kind} JSON")
    args = parser.parse_args()
    paths = {
        "source": args.source, "candidate": args.candidate,
        "qualification": args.qualification, "slice": args.slice,
        "reconstruction": args.reconstruction,
    }
    if not any(paths.values()):
        parser.error("provide at least one asset file")
    loaded: dict[str, dict | None] = {}
    try:
        for kind, path in paths.items():
            loaded[kind] = _load_json(path) if path else None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read JSON: {exc}", file=sys.stderr)
        return 2
    errors = validate_assets(
        source=loaded["source"], candidate=loaded["candidate"],
        qualification=loaded["qualification"], task_slice=loaded["slice"],
        reconstruction=loaded["reconstruction"],
    )
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: supplied v0.0.3 trajectory assets satisfy schema and cross-record invariants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
