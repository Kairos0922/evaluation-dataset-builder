#!/usr/bin/env python3
"""Validate v0.0.2 independent and runtime quality assessment reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas"
SCHEMAS = {
    "independent_dataset_assessment": SCHEMA_DIR / "ida-report.schema.json",
    "empirical_runtime_assessment": SCHEMA_DIR / "era-report.schema.json",
}
NON_NUMERIC_STATUSES = {
    "UNKNOWN", "NOT_RUN", "NOT_ASSESSED", "NOT_APPLICABLE", "NOT_VALIDATED"
}


def _schema_errors(report: dict, assessment_type: str) -> list[str]:
    schema_path = SCHEMAS[assessment_type]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(report), key=lambda e: list(e.absolute_path))
    return [
        f"schema at {'.'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def _validate_metric_results(metrics: list, prefix: str) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, metric in enumerate(metrics):
        metric_id = metric["metric_id"]
        location = f"metric_results[{index}]"
        if metric_id in seen:
            errors.append(f"{location}: duplicate metric_id {metric_id}")
        seen.add(metric_id)

        status = metric["status"]
        value = metric["value"]
        numerator = metric.get("numerator")
        denominator = metric.get("denominator")
        interval = metric.get("interval")

        if status in NON_NUMERIC_STATUSES and value is not None:
            errors.append(f"{location}: {status} must not carry a measured value")
        if denominator == 0:
            if value is not None or status != "NOT_APPLICABLE":
                errors.append(
                    f"{location}: zero denominator requires null value and NOT_APPLICABLE status"
                )
        if numerator is not None and denominator is not None and denominator > 0:
            if numerator < 0 or numerator > denominator:
                errors.append(f"{location}: numerator must be between 0 and denominator")
        if interval is not None:
            if interval.get("lower", 0) > interval.get("upper", 0):
                errors.append(f"{location}: interval lower bound exceeds upper bound")
        if prefix == "ida" and metric_id.startswith(("ERA-", "CAP-", "REG-")):
            errors.append(f"{location}: runtime-only metric {metric_id} is not allowed in IDA")
        if prefix == "era" and metric_id.startswith("IDA-"):
            errors.append(f"{location}: offline-only metric {metric_id} is not allowed in ERA")
    return errors


def _validate_composite(report: dict) -> list[str]:
    errors: list[str] = []
    composite = report["composite"]
    status = composite["status"]
    gates = report.get("gate_results", [])
    critical = [gate for gate in gates if gate.get("severity") == "critical"]
    critical_blockers = [
        gate for gate in critical
        if gate.get("status") in {"FAIL", "UNKNOWN", "NOT_RUN", "NOT_ASSESSED"}
    ]

    if status == "VALIDATED_FOR_SCOPE":
        if report["evidence_sufficiency"]["status"] != "sufficient_for_scope":
            errors.append("VALIDATED_FOR_SCOPE requires sufficient_for_scope evidence")
        if critical_blockers:
            errors.append("VALIDATED_FOR_SCOPE is forbidden while critical gates are unresolved")
    return errors


def validate_report(report: dict, assessment_type: str | None = None) -> list[str]:
    """Return schema and cross-field errors; an empty list means contract-valid."""
    if not isinstance(report, dict):
        return ["report root must be an object"]

    actual_type = report.get("assessment_type")
    if assessment_type is None:
        assessment_type = actual_type
    if assessment_type not in SCHEMAS:
        return [f"unsupported assessment_type: {assessment_type!r}"]
    if actual_type != assessment_type:
        return [f"assessment_type mismatch: expected {assessment_type}, got {actual_type!r}"]

    try:
        errors = _schema_errors(report, assessment_type)
    except (OSError, json.JSONDecodeError, Exception) as exc:
        return [f"could not load or validate schema: {exc}"]
    if errors:
        return errors

    errors.extend(_validate_metric_results(
        report.get("metric_results", []),
        "ida" if assessment_type == "independent_dataset_assessment" else "era",
    ))
    errors.extend(_validate_composite(report))

    if assessment_type == "independent_dataset_assessment":
        gate_ids = [gate["gate_id"] for gate in report["gate_results"]]
        if len(gate_ids) != len(set(gate_ids)):
            errors.append("gate_results contains duplicate gate_id")
        critical_fail = any(
            gate["severity"] == "critical" and gate["status"] == "FAIL"
            for gate in report["gate_results"]
        )
        critical_unknown = any(
            gate["severity"] == "critical"
            and gate["status"] in {"UNKNOWN", "NOT_RUN", "NOT_ASSESSED"}
            for gate in report["gate_results"]
        )
        if critical_fail and report["overall_status"] == "PASS":
            errors.append("overall_status cannot be PASS when a critical gate fails")
        if critical_unknown and report["overall_status"] == "PASS":
            errors.append("overall_status cannot be PASS while a critical gate is unresolved")

    else:
        run_ids = [run["run_id"] for run in report["runs"]]
        if len(run_ids) != len(set(run_ids)):
            errors.append("runs contains duplicate run_id")
        for index, run in enumerate(report["runs"]):
            if run["status"] == "valid" and not run.get("trace_ref"):
                errors.append(f"runs[{index}]: valid run requires trace_ref")
        if report["grader_validation"]["status"] == "PASS":
            if report["grader_validation"]["sample_count"] == 0:
                errors.append("grader_validation PASS requires a non-zero sample_count")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, help="Path to an IDA or ERA JSON report")
    args = parser.parse_args()

    report_path = Path(args.report)
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot read report: {exc}", file=sys.stderr)
        return 2

    errors = validate_report(report)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(f"PASS: {report['assessment_type']} report contract is valid")
    print("NOTE: schema/contract validity does not prove construct validity or runtime effectiveness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
