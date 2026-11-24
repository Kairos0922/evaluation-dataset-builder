#!/usr/bin/env python3
"""Validate empirical evidence required before enabling a composite quality score."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "formula-validation.schema.json"


def validate_formula_validation_report(report: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = []
    for error in validator.iter_errors(report):
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{location}: {error.message}")
    if errors:
        return errors

    status = report["status"]
    model = report["candidate_model"]
    scalar_enabled = model["scalar_score_enabled"]
    conclusion = report["conclusion"]

    if conclusion["decision"] != status:
        errors.append("conclusion.decision must equal top-level status")

    if status != "VALIDATED_FOR_SCOPE":
        if scalar_enabled:
            errors.append("scalar_score_enabled must remain false unless status is VALIDATED_FOR_SCOPE")
        return errors

    splits = report["data_splits"]
    split_names = ("development", "calibration", "validation", "external")
    families_by_split = {}
    for split_name in split_names:
        split = splits[split_name]
        observed_count = sum(item["sample_count"] for item in split["datasets"])
        if observed_count != split["sample_count"]:
            errors.append(f"data_splits.{split_name}.sample_count does not equal the sum of dataset sample_count values")
        families_by_split[split_name] = {item["dataset_family"] for item in split["datasets"]}
        if split["sample_count"] <= 0:
            errors.append(f"data_splits.{split_name} must contain non-empty evidence for VALIDATED_FOR_SCOPE")

    for index, left in enumerate(split_names):
        for right in split_names[index + 1:]:
            overlap = families_by_split[left] & families_by_split[right]
            if overlap:
                errors.append(
                    f"dataset_family leakage between {left} and {right}: {', '.join(sorted(overlap))}"
                )

    if splits["leakage_audit"]["status"] != "PASS":
        errors.append("data_splits.leakage_audit.status must be PASS")

    expert = report["expert_validation"]
    if expert["status"] != "PASS" or not expert["blinded"] or not expert["independent"]:
        errors.append("expert_validation must PASS with blinded and independent reviewers")
    if expert["reviewer_count"] < 2 or not expert["agreement_metrics"]:
        errors.append("expert_validation requires at least two reviewers and an inter-rater agreement result")

    mutation = report["mutation_validation"]
    if mutation["status"] != "PASS":
        errors.append("mutation_validation.status must be PASS")
    if mutation["mutation_count"] <= 0:
        errors.append("mutation_validation.mutation_count must be positive")
    if mutation["detected_count"] > mutation["mutation_count"]:
        errors.append("mutation_validation.detected_count cannot exceed mutation_count")

    external = report["external_criterion_validation"]
    if external["status"] != "PASS" or not external["criteria"]:
        errors.append("external_criterion_validation requires at least one PASS external criterion")
    if not any(item["status"] == "PASS" and item["sample_count"] > 0 for item in external["criteria"]):
        errors.append("external_criterion_validation requires a passing criterion with non-zero independent sample count")

    robustness = report["robustness"]
    if robustness["status"] != "PASS":
        errors.append("robustness.status must be PASS")

    if scalar_enabled:
        if model["weights"] is None or not model["weights"]:
            errors.append("a scalar score requires non-empty empirically justified weights")
        elif sum(model["weights"].values()) <= 0:
            errors.append("the sum of scalar score weights must be positive")
        if model["thresholds"] is None or not model["thresholds"]:
            errors.append("a scalar score requires explicit validated thresholds")
        threshold = report["threshold_validation"]
        if threshold["status"] != "PASS":
            errors.append("threshold_validation.status must be PASS for scalar score enablement")
        if threshold["selected_threshold"] is None or not threshold["candidate_thresholds"]:
            errors.append("threshold validation requires candidate and selected thresholds")
    else:
        if model["weights"] is not None or model["thresholds"] is not None:
            errors.append("a validated vector profile must not publish scalar weights or thresholds")
        if report["threshold_validation"]["status"] != "NOT_APPLICABLE":
            errors.append("threshold_validation must be NOT_APPLICABLE when no scalar score is enabled")

    if not conclusion["evidence_refs"]:
        errors.append("conclusion.evidence_refs must identify the independent validation evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Formula validation report JSON")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        errors = validate_formula_validation_report(report)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: formula validation evidence report satisfies the release contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
