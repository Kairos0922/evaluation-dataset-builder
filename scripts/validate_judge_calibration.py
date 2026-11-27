#!/usr/bin/env python3
"""Validate v0.0.2 Judge calibration evidence contracts without claiming validity."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "judge-calibration-report.schema.json"


def _reject_json_constant(token: str):
    raise ValueError(f"invalid JSON numeric constant: {token}")


def _non_finite_number_paths(value, path: str = "<root>") -> list[str]:
    if isinstance(value, float) and not math.isfinite(value):
        return [path]
    if isinstance(value, dict):
        return [found for key, child in value.items()
                for found in _non_finite_number_paths(child, f"{path}.{key}")]
    if isinstance(value, list):
        return [found for index, child in enumerate(value)
                for found in _non_finite_number_paths(child, f"{path}[{index}]")]
    return []


def recompute_summary(results: list[dict], case_ids: list[str], repeats_per_case: int) -> dict:
    """Summarize at case level; repeated judgments are not independent cases."""
    grouped = {case_id: [] for case_id in case_ids}
    for item in results:
        case_id = item["case_id"]
        if case_id not in grouped:
            raise ValueError(f"result contains case_id outside frozen suite: {case_id}")
        grouped[case_id].append(item)
    if any(not rows for rows in grouped.values()):
        raise ValueError("every frozen case must have at least one Judge observation")

    adjudicable_count = 0
    exact_matches = 0
    false_passes = 0
    false_fails = 0
    abstentions = 0
    disagreement_cases = 0
    unanimous_cases = 0
    for case_id, rows in grouped.items():
        gold_labels = {row["gold_status"] for row in rows}
        if len(gold_labels) != 1:
            raise ValueError(f"Gold status changes across repeats for case_id {case_id}")
        gold = next(iter(gold_labels))
        judge_labels = [row["judge_status"] for row in rows]
        counts = Counter(judge_labels)
        highest = max(counts.values())
        winners = [label for label, count in counts.items() if count == highest]
        majority = winners[0] if len(winners) == 1 else "UNKNOWN"

        abstentions += sum(label == "UNKNOWN" for label in judge_labels)
        if len(set(judge_labels)) > 1:
            disagreement_cases += 1
        else:
            unanimous_cases += 1
        if gold in {"PASS", "FAIL"}:
            adjudicable_count += 1
            exact_matches += majority == gold
            false_passes += gold == "FAIL" and "PASS" in judge_labels
            false_fails += gold == "PASS" and "FAIL" in judge_labels

    return {
        "case_count": len(case_ids),
        "observation_count": len(results),
        "accuracy_unit": "case",
        "adjudicable_count": adjudicable_count,
        "exact_matches": exact_matches,
        "false_passes": false_passes,
        "false_fails": false_fails,
        "abstentions": abstentions,
        "abstention_unit": "judgement",
        "accuracy": exact_matches / adjudicable_count if adjudicable_count else None,
        "repeat_disagreement_cases": disagreement_cases,
        "repeat_agreement_rate": (
            unanimous_cases / len(case_ids) if repeats_per_case > 1 and case_ids else None
        ),
    }


def validate_report(report: object, suite_path: Path | None = None) -> list[str]:
    non_finite_paths = _non_finite_number_paths(report)
    if non_finite_paths:
        return [f"non-finite numeric value is not valid JSON at {path}" for path in non_finite_paths]
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
    repeat_pairs = [(item["case_id"], item.get("repeat_index") or 1) for item in results]
    if len(repeat_pairs) != len(set(repeat_pairs)):
        errors.append("results contain duplicate case_id/repeat_index pairs")
    if set(ids) != set(dataset["case_ids"]):
        errors.append("dataset.case_ids must exactly match results.case_id values")
    repeat_counts = Counter(ids)
    expected_repeats = protocol["repeats_per_case"]
    if any(repeat_counts[case_id] != expected_repeats for case_id in dataset["case_ids"]):
        errors.append("each dataset case must have exactly protocol.repeats_per_case observations")
    if any((item.get("repeat_index") or 1) > expected_repeats for item in results):
        errors.append("repeat_index exceeds protocol.repeats_per_case")
    try:
        expected = recompute_summary(results, dataset["case_ids"], expected_repeats)
    except ValueError as exc:
        errors.append(str(exc))
        expected = None
    if expected is not None:
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
            suite = json.loads(raw, parse_constant=_reject_json_constant)
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
        report = json.loads(args.report.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)
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
