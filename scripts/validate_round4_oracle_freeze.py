#!/usr/bin/env python3
"""Validate a pre-execution Round 4 Oracle freeze manifest against all source hashes."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.compare_round4_blind_reviews import (
    compare_reviews,
    load_crosswalk,
    load_json,
    validate_pair,
)
from scripts.validate_round4_oracle import EXPECTED_CASE_IDS, load_dataset_case_hashes

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "docs/quality-assessment-v0.0.2/schemas/round4-oracle-freeze-manifest.schema.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_freeze_manifest(
    manifest: dict,
    *,
    schema: dict,
    dataset_sha256: str,
    case_hashes: dict[str, str],
    plan_sha256: str,
    reviewer_a: dict,
    reviewer_b: dict,
    reviewer_a_sha256: str,
    reviewer_b_sha256: str,
    comparison_report: dict,
    comparison_report_sha256: str,
    crosswalk_sha256: str,
) -> list[str]:
    errors: list[str] = []
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in validator.iter_errors(manifest):
        location = ".".join(str(part) for part in error.absolute_path)
        errors.append(f"manifest.{location}: {error.message}")
    if not isinstance(manifest, dict):
        return errors

    reviewer_a = reviewer_a if isinstance(reviewer_a, dict) else {}
    reviewer_b = reviewer_b if isinstance(reviewer_b, dict) else {}
    comparison_report = comparison_report if isinstance(comparison_report, dict) else {}

    if manifest.get("dataset_sha256") != dataset_sha256:
        errors.append("manifest dataset_sha256 does not match the frozen dataset")
    if manifest.get("oracle_plan_sha256") != plan_sha256:
        errors.append("manifest oracle_plan_sha256 does not match the supplied plan")

    review_inputs = manifest.get("review_inputs")
    if not isinstance(review_inputs, dict):
        review_inputs = {}
    reviewer_a_id = reviewer_a.get("reviewer_id")
    reviewer_b_id = reviewer_b.get("reviewer_id")
    if review_inputs.get("reviewer_a_id") != reviewer_a_id:
        errors.append("manifest reviewer_a_id does not match Reviewer A submission")
    if review_inputs.get("reviewer_b_id") != reviewer_b_id:
        errors.append("manifest reviewer_b_id does not match Reviewer B submission")
    if reviewer_a_id == reviewer_b_id:
        errors.append("independent reviewer IDs must be distinct")
    if review_inputs.get("reviewer_a_submission_sha256") != reviewer_a_sha256:
        errors.append("Reviewer A submission SHA-256 mismatch")
    if review_inputs.get("reviewer_b_submission_sha256") != reviewer_b_sha256:
        errors.append("Reviewer B submission SHA-256 mismatch")
    if review_inputs.get("comparison_report_sha256") != comparison_report_sha256:
        errors.append("comparison report SHA-256 mismatch")
    if review_inputs.get("crosswalk_sha256") != crosswalk_sha256:
        errors.append("coordinator crosswalk SHA-256 mismatch")

    adjudication = manifest.get("adjudication")
    if not isinstance(adjudication, dict):
        adjudication = {}
    adjudicator_id = adjudication.get("adjudicator_id")
    if adjudicator_id is not None and adjudicator_id in {reviewer_a_id, reviewer_b_id}:
        errors.append("adjudicator must be independent from both reviewers")

    # The caller recomputes the comparison report from both submissions and crosswalk.
    if comparison_report.get("status") != "REQUIRES_HUMAN_ADJUDICATION":
        errors.append("comparison report must retain REQUIRES_HUMAN_ADJUDICATION status")
    if comparison_report.get("dataset_sha256") != dataset_sha256:
        errors.append("comparison report dataset SHA-256 mismatch")
    report_reviewers = comparison_report.get("reviewers")
    if not isinstance(report_reviewers, dict):
        report_reviewers = {}
    report_a = report_reviewers.get("A")
    report_b = report_reviewers.get("B")
    report_a = report_a if isinstance(report_a, dict) else {}
    report_b = report_b if isinstance(report_b, dict) else {}
    if report_a.get("reviewer_id") != reviewer_a_id:
        errors.append("comparison report Reviewer A identity mismatch")
    if report_b.get("reviewer_id") != reviewer_b_id:
        errors.append("comparison report Reviewer B identity mismatch")

    report_cases = comparison_report.get("cases", [])
    if not isinstance(report_cases, list):
        report_cases = []
    report_case_ids = [
        case.get("case_id") for case in report_cases
        if isinstance(case, dict) and isinstance(case.get("case_id"), str)
    ]
    if len(report_case_ids) != 12 or set(report_case_ids) != EXPECTED_CASE_IDS or len(set(report_case_ids)) != 12:
        errors.append("comparison report must cover the exact 12 target cases")

    cases = manifest.get("cases")
    if not isinstance(cases, list):
        cases = []
    case_ids = [
        case.get("case_id") for case in cases
        if isinstance(case, dict) and isinstance(case.get("case_id"), str)
    ]
    if len(case_ids) != 12 or set(case_ids) != EXPECTED_CASE_IDS or len(set(case_ids)) != 12:
        errors.append("freeze manifest must contain each of the 12 target cases exactly once")
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            continue
        case_id = case.get("case_id")
        if not isinstance(case_id, str):
            errors.append(f"case[{index}] case_id must be a string")
            continue
        expected_hash = case_hashes.get(case_id)
        if expected_hash is None:
            errors.append(f"case[{index}] {case_id}: case is absent from frozen dataset")
        elif case.get("case_sha256") != expected_hash:
            errors.append(f"case[{index}] {case_id}: case_sha256 mismatch")
    all_cases_frozen = len(cases) == 12 and all(
        isinstance(case, dict) and case.get("freeze_decision") == "FROZEN"
        for case in cases
    )
    expected_status = "FROZEN" if all_cases_frozen else "NOT_FROZEN"
    if manifest.get("freeze_status") != expected_status:
        errors.append(f"freeze_status must be {expected_status} based on all 12 case decisions")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-jsonl", type=Path, required=True)
    parser.add_argument("--oracle-plan", type=Path, required=True)
    parser.add_argument("--reviewer-a", type=Path, required=True)
    parser.add_argument("--reviewer-b", type=Path, required=True)
    parser.add_argument("--comparison-report", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--require-frozen", action="store_true")
    args = parser.parse_args()

    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        manifest = load_json(args.manifest)
        reviewer_a = load_json(args.reviewer_a)
        reviewer_b = load_json(args.reviewer_b)
        comparison_report = load_json(args.comparison_report)
        crosswalk = load_crosswalk(args.crosswalk)

        pair_errors = validate_pair(reviewer_a, reviewer_b, json.loads(
            (ROOT / "docs/quality-assessment-v0.0.2/schemas/round4-blind-review-submission.schema.json")
            .read_text(encoding="utf-8")
        ))
        if pair_errors:
            print("Oracle freeze validation FAILED:")
            for error in pair_errors:
                print(f"- {error}")
            return 1

        recomputed_report = compare_reviews(reviewer_a, reviewer_b, crosswalk)
        if comparison_report != recomputed_report:
            print("Oracle freeze validation FAILED:")
            print("- comparison report does not exactly match the supplied reviews and coordinator crosswalk")
            return 1

        dataset_sha256, case_hashes = load_dataset_case_hashes(args.dataset_jsonl)
        errors = validate_freeze_manifest(
            manifest,
            schema=schema,
            dataset_sha256=dataset_sha256,
            case_hashes=case_hashes,
            plan_sha256=sha256_file(args.oracle_plan),
            reviewer_a=reviewer_a,
            reviewer_b=reviewer_b,
            reviewer_a_sha256=sha256_file(args.reviewer_a),
            reviewer_b_sha256=sha256_file(args.reviewer_b),
            comparison_report=comparison_report,
            comparison_report_sha256=sha256_file(args.comparison_report),
            crosswalk_sha256=sha256_file(args.crosswalk),
        )
        if args.require_frozen and manifest.get("freeze_status") != "FROZEN":
            errors.append("--require-frozen was set but manifest is NOT_FROZEN")
        if errors:
            print("Oracle freeze validation FAILED:")
            for error in errors:
                print(f"- {error}")
            return 1
        print(json.dumps({
            "status": "FROZEN" if manifest.get("freeze_status") == "FROZEN" else "VALID_NOT_FROZEN",
            "case_count": len(manifest["cases"]),
            "dataset_sha256": dataset_sha256,
            "oracle_plan_sha256": sha256_file(args.oracle_plan),
            "reviewer_ids_distinct": reviewer_a["reviewer_id"] != reviewer_b["reviewer_id"],
            "adjudicator_independent": manifest["adjudication"]["adjudicator_id"] not in {
                reviewer_a["reviewer_id"], reviewer_b["reviewer_id"]
            },
            "execution_authorized": False,
        }, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
