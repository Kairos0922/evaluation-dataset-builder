#!/usr/bin/env python3
"""Validate Harness-produced execution envelopes against an ERA Run Plan.

This is an import/contract adapter, not a Runner: it never starts an Agent or
creates evidence. The Harness owns execution, fresh-session isolation, run IDs,
and immutable trace/result artifacts.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
ENVELOPE_SCHEMA = ROOT / "schemas" / "v0.0.3" / "era-harness-envelope.schema.json"
RUNTIME_SCHEMA = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "runtime-record.schema.json"
CONFIGURATION_FIELDS = (
    "configuration_id", "target_revision", "target_type", "model",
    "harness", "environment", "tool_versions", "seed",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)


def _reject_constant(token: str):
    raise ValueError(f"invalid JSON numeric constant: {token}")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"blank execution JSONL line {line_number}")
        try:
            value = json.loads(line, parse_constant=_reject_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"invalid execution JSONL line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"execution JSONL line {line_number} must be an object")
        rows.append(value)
    return rows


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def _validate_runtime_record(record: dict, validator: Draft202012Validator, label: str) -> None:
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:20]
        )
        raise ValueError(f"{label} Runtime Record schema validation failed: {details}")
    if not isinstance(record.get("trace_ref"), str) or not record["trace_ref"].strip():
        raise ValueError(f"{label} must reference a newly produced runtime trace")
    if not isinstance(record.get("result_ref"), str) or not record["result_ref"].strip():
        raise ValueError(f"{label} must reference a newly produced runtime result")
    trace_hash = record.get("trace_sha256")
    if not isinstance(trace_hash, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", trace_hash):
        raise ValueError(f"{label} must include trace_sha256 for the new runtime trace")
    if record["outcomes"].get("gold_outcome") != "unknown" or record["outcomes"].get("gold_source") != "not_available":
        raise ValueError(
            f"{label} has no independent Oracle attachment in this adapter; gold_outcome must be unknown "
            "and gold_source must be not_available"
        )


def import_harness_executions(plan: dict, executions: list[dict]) -> list[dict]:
    if plan.get("plan_version") != "0.0.3" or plan.get("status") != "DRAFT_NOT_EXECUTED":
        raise ValueError("input must be an unmodified v0.0.3 DRAFT_NOT_EXECUTED ERA Run Plan")
    planned = plan.get("planned_cases")
    if not isinstance(planned, list) or not planned:
        raise ValueError("Run Plan has no planned_cases")
    expected = {item.get("case_id"): item for item in planned}
    if None in expected or len(expected) != len(planned):
        raise ValueError("Run Plan contains missing or duplicate case_id values")
    if len(executions) != len(expected):
        raise ValueError(f"expected exactly {len(expected)} execution envelope(s), got {len(executions)}")

    envelope_schema = json.loads(ENVELOPE_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(envelope_schema)
    envelope_validator = Draft202012Validator(envelope_schema, format_checker=FormatChecker())
    runtime_schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(runtime_schema)
    validator = Draft202012Validator(runtime_schema, format_checker=FormatChecker())
    seen_cases: set[str] = set()
    seen_runs: set[str] = set()
    seen_sessions: set[str] = set()
    imported = []

    for index, envelope in enumerate(executions, start=1):
        label = f"execution line {index}"
        envelope_errors = sorted(
            envelope_validator.iter_errors(envelope),
            key=lambda error: list(error.absolute_path),
        )
        if envelope_errors:
            details = "; ".join(
                f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
                for error in envelope_errors[:20]
            )
            raise ValueError(f"{label} Harness envelope schema validation failed: {details}")
        if envelope.get("plan_id") != plan.get("plan_id"):
            raise ValueError(f"{label} plan_id does not match Run Plan")
        case_id = envelope.get("case_id")
        if case_id not in expected:
            raise ValueError(f"{label} case_id is not present in Run Plan: {case_id!r}")
        if case_id in seen_cases:
            raise ValueError(f"duplicate execution for case_id: {case_id}")
        seen_cases.add(case_id)

        session_id = envelope.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError(f"{label} must include a non-empty fresh session_id")
        if session_id in seen_sessions:
            raise ValueError(f"session_id reused across Cases: {session_id}")
        seen_sessions.add(session_id)

        record = envelope.get("runtime_record")
        if not isinstance(record, dict):
            raise ValueError(f"{label} runtime_record must be an object")
        _validate_runtime_record(record, validator, label)

        if record.get("run_id") in seen_runs:
            raise ValueError(f"duplicate run_id: {record.get('run_id')}")
        seen_runs.add(record.get("run_id"))

        item = expected[case_id]
        dataset = plan["dataset"]
        identity = {
            "dataset_id": dataset["dataset_id"],
            "dataset_sha256": dataset["dataset_sha256"],
            "case_id": case_id,
        }
        for key, value in identity.items():
            if record.get(key) != value:
                raise ValueError(f"{label} Runtime Record {key} does not match Run Plan")
        configuration = plan["configuration"]
        for key in CONFIGURATION_FIELDS:
            if key in configuration and record.get(key) != configuration[key]:
                raise ValueError(f"{label} Runtime Record {key} does not match frozen plan configuration")
            if key not in configuration and key == "seed" and record.get(key) not in (None,):
                raise ValueError(f"{label} Runtime Record seed is not present in frozen plan configuration")

        historical = set(_strings(item.get("historical_source_refs", [])))
        if record["trace_ref"] in historical:
            raise ValueError(f"{label} runtime trace_ref reuses a historical source reference")
        if record["result_ref"] in historical:
            raise ValueError(f"{label} runtime result_ref reuses a historical source reference")

        imported.append(record)

    missing = sorted(set(expected) - seen_cases)
    if missing:
        raise ValueError("missing execution envelopes for Case(s): " + ", ".join(missing))
    return imported


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--executions", required=True, type=Path,
                        help="Harness-produced JSONL envelopes: plan_id, case_id, session_id, runtime_record")
    parser.add_argument("--output", required=True, type=Path,
                        help="Output JSONL containing only existing v0.0.2 Runtime Records")
    args = parser.parse_args()
    try:
        records = import_harness_executions(load_json(args.plan), load_jsonl(args.executions))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: imported {len(records)} Harness execution record(s) against the ERA Run Plan")
    print("NOTE: no Agent was executed; execution and artifact authenticity remain Harness responsibilities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
