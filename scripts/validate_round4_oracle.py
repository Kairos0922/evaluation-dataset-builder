#!/usr/bin/env python3
"""Validate frozen Round 4 independent Oracle records against dataset and plan hashes."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "docs/quality-assessment-v0.0.2/schemas/round4-oracle-record.schema.json"
EXPECTED_DATASET_SHA256 = "000d38b110b60eae902f86737ea6bd1368f98c6632c42a47bb9470a4a08bfc45"
EXPECTED_CASE_IDS = {
    "WB-01", "WB-03", "WB-04", "WB-05", "WB-06", "WB-07",
    "WB-08", "WB-09", "WB-11", "WB-13", "WB-14", "WB-15",
}


def _reject_json_constant(value: str):
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def _non_finite_number_paths(value, path: str = "$"):
    if isinstance(value, float) and not math.isfinite(value):
        yield path
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _non_finite_number_paths(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _non_finite_number_paths(child, f"{path}[{index}]")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_dataset_case_hashes(path: Path) -> tuple[str, dict[str, str]]:
    raw = path.read_bytes()
    dataset_sha256 = sha256_bytes(raw)
    cases: dict[str, str] = {}
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line, parse_constant=_reject_json_constant)
        except json.JSONDecodeError as exc:
            raise ValueError(f"dataset JSONL line {line_number} is invalid: {exc}") from exc
        case_id = item.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"dataset JSONL line {line_number} has no case_id")
        if case_id in cases:
            raise ValueError(f"duplicate case_id in frozen dataset: {case_id}")
        cases[case_id] = sha256_bytes(line)
    return dataset_sha256, cases


def load_jsonl_records(path: Path) -> list[dict]:
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line, parse_constant=_reject_json_constant)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Oracle JSONL line {line_number} is invalid: {exc}") from exc
        non_finite = list(_non_finite_number_paths(record))
        if non_finite:
            raise ValueError(f"Oracle JSONL line {line_number} contains non-finite values: {', '.join(non_finite[:10])}")
        if not isinstance(record, dict):
            raise ValueError(f"Oracle JSONL line {line_number} must be a JSON object")
        records.append(record)
    return records


def validate_records(
    records: list[dict],
    *,
    dataset_sha256: str,
    case_hashes: dict[str, str],
    plan_sha256: str,
    schema: dict,
    require_complete: bool = False,
) -> list[str]:
    errors: list[str] = []
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    seen_cases: set[str] = set()
    seen_record_ids: set[str] = set()

    for index, record in enumerate(records, start=1):
        prefix = f"record[{index}]"
        for error in validator.iter_errors(record):
            location = ".".join(str(part) for part in error.absolute_path)
            errors.append(f"{prefix}.{location}: {error.message}")

        case_id = record.get("case_id")
        record_id = record.get("record_id")
        if isinstance(case_id, str):
            if case_id not in EXPECTED_CASE_IDS:
                errors.append(f"{prefix}: case_id {case_id} is outside the 12-case Oracle scope")
            if case_id in seen_cases:
                errors.append(f"{prefix}: duplicate Oracle record for {case_id}")
            seen_cases.add(case_id)
            expected_case_hash = case_hashes.get(case_id)
            if expected_case_hash is None:
                errors.append(f"{prefix}: case_id {case_id} does not exist in the frozen dataset")
            elif record.get("case_sha256") != expected_case_hash:
                errors.append(f"{prefix}: case_sha256 does not match the frozen Builder case")
        if isinstance(record_id, str):
            if record_id in seen_record_ids:
                errors.append(f"{prefix}: duplicate record_id {record_id}")
            seen_record_ids.add(record_id)

        if record.get("dataset_sha256") != dataset_sha256:
            errors.append(f"{prefix}: dataset_sha256 does not match the supplied frozen JSONL")
        if record.get("oracle_plan_sha256") != plan_sha256:
            errors.append(f"{prefix}: oracle_plan_sha256 does not match the supplied plan")

        adjudication = record.get("adjudication", {})
        reviewer_ids = adjudication.get("reviewer_ids", [])
        decisions = adjudication.get("independent_decisions", [])
        decision_ids = [item.get("reviewer_id") for item in decisions if isinstance(item, dict)]
        if set(reviewer_ids) != set(decision_ids) or len(decision_ids) != len(set(decision_ids)):
            errors.append(f"{prefix}: reviewer_ids must exactly match distinct independent_decisions")

        consensus = adjudication.get("consensus_status")
        if consensus in {"agreed", "adjudicated"}:
            if not {"final_application_outcome", "final_skill_outcome"}.issubset(adjudication):
                errors.append(f"{prefix}: finalized consensus requires both final outcomes")
            else:
                if record.get("application_outcome") != adjudication.get("final_application_outcome"):
                    errors.append(f"{prefix}: application_outcome differs from finalized adjudication")
                if record.get("skill_outcome") != adjudication.get("final_skill_outcome"):
                    errors.append(f"{prefix}: skill_outcome differs from finalized adjudication")

        budget = record.get("action_budget", {})
        max_scripts = budget.get("max_script_runs")
        observed_scripts = budget.get("observed_script_runs")
        max_writes = budget.get("max_write_actions")
        observed_writes = budget.get("observed_write_actions")
        if all(isinstance(value, int) for value in (max_scripts, observed_scripts, max_writes, observed_writes)):
            actual_exceeded = observed_scripts > max_scripts or observed_writes > max_writes
            if budget.get("budget_exceeded") is not actual_exceeded:
                errors.append(f"{prefix}: budget_exceeded does not match observed action counts")

        if record.get("record_status") == "accepted":
            run = record.get("run", {})
            if consensus not in {"agreed", "adjudicated"}:
                errors.append(f"{prefix}: accepted record requires agreed or adjudicated consensus")
            if run.get("execution_status") != "completed" or run.get("reset_verified") is not True:
                errors.append(f"{prefix}: accepted record requires completed execution and verified clean reset")

    if require_complete:
        missing = EXPECTED_CASE_IDS - seen_cases
        if missing:
            errors.append("missing Oracle records: " + ", ".join(sorted(missing)))
        unaccepted = sorted(
            record.get("case_id", "<missing>")
            for record in records
            if record.get("record_status") != "accepted"
        )
        if unaccepted:
            errors.append("records not accepted: " + ", ".join(unaccepted))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True, help="JSONL containing independent Oracle records")
    parser.add_argument("--dataset-jsonl", type=Path, required=True, help="Frozen Builder-authored case JSONL")
    parser.add_argument("--oracle-plan", type=Path, required=True, help="Frozen independent Oracle plan")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="Oracle record JSON Schema")
    parser.add_argument("--require-complete", action="store_true", help="Require all 12 cases to have accepted records")
    args = parser.parse_args()

    try:
        dataset_sha256, case_hashes = load_dataset_case_hashes(args.dataset_jsonl)
        if dataset_sha256 != EXPECTED_DATASET_SHA256:
            raise ValueError(
                "dataset JSONL SHA-256 mismatch: "
                f"expected {EXPECTED_DATASET_SHA256}, got {dataset_sha256}"
            )
        plan_sha256 = sha256_bytes(args.oracle_plan.read_bytes())
        schema = json.loads(args.schema.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)
        Draft202012Validator.check_schema(schema)
        records = load_jsonl_records(args.records)
        errors = validate_records(
            records,
            dataset_sha256=dataset_sha256,
            case_hashes=case_hashes,
            plan_sha256=plan_sha256,
            schema=schema,
            require_complete=args.require_complete,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if errors:
        print("Oracle validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Oracle validation PASS: "
        f"{len(records)} record(s), {len({r.get('case_id') for r in records})} distinct cases; "
        f"dataset={dataset_sha256}; plan={plan_sha256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
