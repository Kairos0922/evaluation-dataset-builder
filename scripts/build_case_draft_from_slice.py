#!/usr/bin/env python3
"""Convert a reviewed trajectory task slice into a draft of the existing Builder Case format."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

try:
    from scripts.validate_trajectory_assets import validate_assets
except ModuleNotFoundError:
    from validate_trajectory_assets import validate_assets

ROOT = Path(__file__).resolve().parents[1]
CASE_SCHEMA = ROOT / "skills" / "evaluation-dataset-builder" / "references" / "dataset-schema.json"


def reject_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant: {token}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def build_case_draft(
    source: dict,
    candidate: dict,
    qualification: dict,
    task_slice: dict,
    case_fields: dict,
    source_title: str,
    source_authority: str,
) -> dict:
    """Build an existing-format Case without inventing expected behavior or grading."""
    errors = validate_assets(
        source=source, candidate=candidate,
        qualification=qualification, task_slice=task_slice,
    )
    if errors:
        raise ValueError("trajectory evidence chain is invalid: " + "; ".join(errors))
    if task_slice.get("status") != "ready_for_reconstruction":
        raise ValueError("slice must be ready_for_reconstruction before Case conversion")
    if task_slice.get("initial_context", {}).get("closure_review") != "complete":
        raise ValueError("slice context closure must be complete")
    if task_slice.get("leakage_review") != "passed":
        raise ValueError("slice leakage review must pass")
    if not source_title.strip() or not source_authority.strip():
        raise ValueError("source title and source authority must be explicitly supplied")

    forbidden = {"source_refs", "case_origin"} & set(case_fields)
    if forbidden:
        raise ValueError("case-fields must not override provenance fields: " + ", ".join(sorted(forbidden)))

    required = {
        "case_id", "dataset_id", "title", "evaluation_target", "objective",
        "user_input", "expected_behavior", "grading", "quality_status",
        "scenario_bucket", "coverage_tags", "execution_requirements",
    }
    missing = sorted(required - set(case_fields))
    if missing:
        raise ValueError("case-fields missing required reviewed fields: " + ", ".join(missing))

    # The trace supports provenance and task discovery only. It does not establish a gold answer.
    locator = (
        f"{source['artifact']['uri']}#sha256={source['artifact']['sha256']}"
        f";events={task_slice['trace_boundary']['start_event_ref']}"
        f"..{task_slice['trace_boundary']['end_event_ref']}"
    )
    case = dict(case_fields)
    case["case_origin"] = "execution_trace"
    case["source_refs"] = [{
        "source_id": source["source_id"],
        "source_type": "trace_log",
        "title": source_title,
        "version": source.get("agent_revision"),
        "effective_date": None,
        "authority": source_authority,
        "locator": locator,
        "quoted_evidence": "",
    }]

    schema = load_json(CASE_SCHEMA)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_errors = sorted(validator.iter_errors(case), key=lambda e: list(e.absolute_path))
    if schema_errors:
        details = "; ".join(
            f"{'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in schema_errors
        )
        raise ValueError("generated Case does not satisfy existing dataset-schema.json: " + details)
    return case


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--qualification", required=True, type=Path)
    parser.add_argument("--slice", required=True, type=Path)
    parser.add_argument("--case-fields", required=True, type=Path,
                        help="Human-reviewed existing Case fields, excluding source_refs and case_origin")
    parser.add_argument("--source-title", required=True)
    parser.add_argument("--source-authority", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        case = build_case_draft(
            source=load_json(args.source),
            candidate=load_json(args.candidate),
            qualification=load_json(args.qualification),
            task_slice=load_json(args.slice),
            case_fields=load_json(args.case_fields),
            source_title=args.source_title,
            source_authority=args.source_authority,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(case, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print("PASS: produced a draft in the existing Evaluation Dataset Builder Case format")
    print("NOTE: this is a candidate Case; it is not validated, approved, or execution-verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
