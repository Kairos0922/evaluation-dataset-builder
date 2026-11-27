#!/usr/bin/env python3
"""Validate empirical evidence required before enabling a composite quality score."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "formula-validation.schema.json"


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


def validate_formula_validation_report(report: dict) -> list[str]:
    non_finite_paths = _non_finite_number_paths(report)
    if non_finite_paths:
        return [f"non-finite numeric value is not valid JSON at {path}" for path in non_finite_paths]

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)
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
        if not split["datasets"]:
            errors.append(f"data_splits.{split_name}.datasets must include at least one source dataset for VALIDATED_FOR_SCOPE")
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
    if len(expert["reviewer_profiles"]) < expert["reviewer_count"]:
        errors.append("reviewer_profiles must identify each independent reviewer")
    content_validity = expert["content_validity"]
    if not content_validity.get("method") or all(
        content_validity.get(key) is None for key in ("cvi", "cvr", "aikens_v")
    ):
        errors.append("expert_validation requires a documented content-validity method and result")
    if not expert["raw_data_ref"]:
        errors.append("expert_validation.raw_data_ref must identify the blinded review data")

    mutation = report["mutation_validation"]
    if mutation["status"] != "PASS":
        errors.append("mutation_validation.status must be PASS")
    if mutation["mutation_count"] <= 0:
        errors.append("mutation_validation.mutation_count must be positive")
    if mutation["detected_count"] > mutation["mutation_count"]:
        errors.append("mutation_validation.detected_count cannot exceed mutation_count")
    if not mutation["results_ref"]:
        errors.append("mutation_validation.results_ref must identify the mutation result evidence")

    external = report["external_criterion_validation"]
    if external["status"] != "PASS" or not external["criteria"]:
        errors.append("external_criterion_validation requires at least one PASS external criterion")
    if not any(item["status"] == "PASS" and item["sample_count"] > 0 for item in external["criteria"]):
        errors.append("external_criterion_validation requires a passing criterion with non-zero independent sample count")

    robustness = report["robustness"]
    if robustness["status"] != "PASS":
        errors.append("robustness.status must be PASS")
    for key in (
        "weight_sensitivity", "normalization_sensitivity", "aggregation_sensitivity",
        "leave_one_dimension_out", "rank_or_grade_instability"
    ):
        result = robustness[key]
        if result["sample_count"] <= 0 or result["value"] is None:
            errors.append(f"robustness.{key} requires an observed result and non-zero sample count")

    uncertainty = report["uncertainty"]
    if uncertainty["confidence_level"] is None or not uncertainty["reported_intervals"]:
        errors.append("validated models require uncertainty intervals and a declared confidence level")
    if any("bootstrap" in method.lower() for method in uncertainty["methods"]) and report["reproducibility"]["random_seed"] is None:
        errors.append("bootstrap-based validation requires a recorded random seed")

    if scalar_enabled:
        if model["weights_source"] == "none":
            errors.append("a scalar score requires a documented weight source")
        if not model["hard_gates"]:
            errors.append("a scalar score requires explicit non-compensatory hard gates")
        if model["weights"] is None or not model["weights"]:
            errors.append("a scalar score requires non-empty empirically justified weights")
        elif sum(model["weights"].values()) <= 0:
            errors.append("the sum of scalar score weights must be positive")
        if model["thresholds"] is None or not model["thresholds"]:
            errors.append("a scalar score requires explicit validated thresholds")
        threshold = report["threshold_validation"]
        if threshold["status"] != "PASS":
            errors.append("threshold_validation.status must be PASS for scalar score enablement")
        if threshold["selected_threshold"] is None or not threshold["candidate_thresholds"] or not threshold["validation_results"]:
            errors.append("threshold validation requires candidate thresholds, a selected threshold and validation results")
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
        report = json.loads(args.report.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)
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
