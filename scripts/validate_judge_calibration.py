#!/usr/bin/env python3
"""Validate v0.0.2 Judge calibration evidence contracts without claiming validity."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "judge-calibration-report.schema.json"


def validate_report(report: object, suite_path: Path | None = None) -> list[str]:
    if not isinstance(report, dict):
        return ["report root must be an object"]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = [
        f"schema at {'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report),
            key=lambda e: list(e.absolute_path),
        )
    ]
    if errors:
        return errors

    dataset = report["dataset"]
    judge = report["judge"]
    protocol = report["protocol"]
    results = report["results"]
    summary = report["summary"]
    kind = report["calibration_kind"]
    status = report["status"]

    ids = [item["case_id"] for item in results]
    if len(ids) != len(set(ids)):
        errors.append("results contain duplicate case_id values")
    if set(ids) != set(dataset["case_ids"]):
        errors.append("dataset.case_ids must exactly match results.case_id values")
    if summary["case_count"] != len(results):
        errors.append("summary.case_count must equal results length")

    adjudicable = [item for item in results if item["gold_status"] in {"PASS", "FAIL"}]
    exact = sum(item["gold_status"] == item["judge_status"] for item in adjudicable)
    false_passes = sum(item["gold_status"] == "FAIL" and item["judge_status"] == "PASS" for item in adjudicable)
    false_fails = sum(item["gold_status"] == "PASS" and item["judge_status"] == "FAIL" for item in adjudicable)
    abstentions = sum(item["judge_status"] == "UNKNOWN" for item in results)
    accuracy = exact / len(adjudicable) if adjudicable else None
    expected = {
        "adjudicable_count": len(adjudicable),
        "exact_matches": exact,
        "false_passes": false_passes,
        "false_fails": false_fails,
        "abstentions": abstentions,
        "accuracy": accuracy,
    }
    for key, value in expected.items():
        actual = summary[key]
        if isinstance(value, float):
            if actual is None or abs(actual - value) > 1e-9:
                errors.append(f"summary.{key} does not match recomputed value")
        elif actual != value:
            errors.append(f"summary.{key} expected {value}, got {actual}")

    if not judge["separate_from_subject"]:
        errors.append("Judge must be independent from the evaluated subject")
    if kind == "synthetic_smoke":
        if dataset["label_source"] != "synthetic_fixture" or dataset["independent_gold"]:
            errors.append("synthetic_smoke requires synthetic_fixture labels and independent_gold=false")
        if status == "VALIDATED_FOR_SCOPE":
            errors.append("synthetic smoke evidence cannot validate Judge validity")
    if kind == "independent_empirical":
        if dataset["label_source"] not in {"independent_expert", "adjudicated_oracle", "historical_incident"}:
            errors.append("independent_empirical requires an independent label source")
        if not dataset["independent_gold"] or not dataset["held_out"] or not dataset["split_id"]:
            errors.append("independent_empirical requires independent Gold and a named held-out split")
        if not protocol["blinded"] or not protocol["independent_review"]:
            errors.append("independent_empirical requires blinded and independent review")
        if judge.get("judge_type") not in {"human", "llm"}:
            errors.append("independent_empirical requires judge_type human or llm")
        for item in results:
            if not item.get("evidence_validated"):
                errors.append(f"independent_empirical case {item['case_id']} has unvalidated evidence")
            if not item.get("gold_evidence_ref"):
                errors.append(f"independent_empirical case {item['case_id']} lacks Gold evidence reference")
            if not item.get("judge_evidence_ref"):
                errors.append(f"independent_empirical case {item['case_id']} lacks Judge evidence reference")
            if dataset["label_source"] == "independent_expert" and not item.get("reviewer_id"):
                errors.append(f"independent expert case {item['case_id']} lacks anonymous reviewer_id")
            if dataset["label_source"] == "adjudicated_oracle" and not item.get("adjudicator_id"):
                errors.append(f"adjudicated case {item['case_id']} lacks anonymous adjudicator_id")
    if status == "VALIDATED_FOR_SCOPE" and kind != "independent_empirical":
        errors.append("VALIDATED_FOR_SCOPE is allowed only for independent_empirical evidence")

    if suite_path is not None:
        raw = suite_path.read_bytes()
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != dataset["suite_sha256"]:
            errors.append("dataset.suite_sha256 does not match supplied suite bytes")
        try:
            suite = json.loads(raw)
            suite_ids = [case.get("id") for case in suite.get("cases", []) if isinstance(case, dict)]
            if set(suite_ids) != set(dataset["case_ids"]) or len(suite_ids) != len(dataset["case_ids"]):
                errors.append("dataset.case_ids do not match supplied suite case IDs")
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            errors.append("supplied suite must be a JSON object with a cases array")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--suite", type=Path, help="Optional exact calibration-suite JSON used to verify its SHA and case IDs.")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Unable to read report: {exc}", file=sys.stderr)
        return 2
    errors = validate_report(report, args.suite)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: Judge calibration report contract is valid; this does not establish empirical Judge validity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
