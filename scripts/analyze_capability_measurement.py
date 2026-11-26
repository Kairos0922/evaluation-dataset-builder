#!/usr/bin/env python3
"""Exploratory Rasch and two-facet G-study for balanced Capability evidence.

Only valid runs with independent Gold provenance are admitted. The estimator
fails closed for sparse, unbalanced, duplicated, or separated designs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "capability-measurement-report.schema.json"
GOLD_SOURCES = {"independent_oracle", "expert_adjudication"}


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-min(value, 700))
        return 1.0 / (1.0 + z)
    z = math.exp(max(value, -700))
    return z / (1.0 + z)


def _not_assessed(reason: str) -> dict:
    return {"status": "NOT_ASSESSED", "reason": reason}


def _prepare_matrix(records: list[dict]) -> tuple[list[str], list[str], list[list[int]], list[str]]:
    eligible = []
    exclusions = []
    for record in records:
        outcomes = record.get("outcomes", {})
        if record.get("status") != "valid":
            exclusions.append(f"{record.get('run_id')}: run status is not valid")
            continue
        if outcomes.get("gold_source") not in GOLD_SOURCES or outcomes.get("gold_outcome") not in {"pass", "fail"}:
            exclusions.append(f"{record.get('run_id')}: independent Gold outcome unavailable")
            continue
        if outcomes.get("agent_outcome") not in {"pass", "fail"}:
            exclusions.append(f"{record.get('run_id')}: binary Agent outcome unavailable")
            continue
        eligible.append(record)

    if not eligible:
        return [], [], [], exclusions

    persons = sorted({item["configuration_id"] for item in eligible})
    items = sorted({item["case_id"] for item in eligible})
    cells: dict[tuple[str, str], int] = {}
    for record in eligible:
        key = (record["configuration_id"], record["case_id"])
        if key in cells:
            raise ValueError(f"duplicate person-item cell: {key[0]} / {key[1]}; repeated runs require an explicit seed facet")
        cells[key] = 1 if record["outcomes"]["agent_outcome"] == "pass" else 0

    expected = len(persons) * len(items)
    if len(cells) != expected:
        missing = [
            f"{person}/{item}"
            for person in persons for item in items
            if (person, item) not in cells
        ]
        raise ValueError(
            f"unbalanced person-item design: observed {len(cells)} of {expected} cells; "
            f"first missing cells: {', '.join(missing[:8])}"
        )
    matrix = [[cells[(person, item)] for item in items] for person in persons]
    return persons, items, matrix, exclusions


def _rasch_fit_mnsq(observed: list[int], expected: list[float]) -> dict:
    residual_squares = [(actual - predicted) ** 2 for actual, predicted in zip(observed, expected)]
    variances = [predicted * (1.0 - predicted) for predicted in expected]
    information = sum(variances)
    outfit_terms = [
        residual / variance
        for residual, variance in zip(residual_squares, variances)
        if variance > 1e-12
    ]
    return {
        "infit_msq": sum(residual_squares) / information if information > 1e-12 else 0.0,
        "outfit_msq": statistics.mean(outfit_terms) if outfit_terms else 0.0,
    }


def fit_rasch_1pl(persons: list[str], items: list[str], matrix: list[list[int]],
                  max_iterations: int = 500, tolerance: float = 1e-7) -> dict:
    """Joint maximum-likelihood Rasch fit; refuses complete separation."""
    p_count, i_count = len(persons), len(items)
    if p_count < 3 or i_count < 3:
        return _not_assessed("Rasch estimation requires at least three persons and three items for this exploratory implementation.")
    if any(sum(row) in {0, i_count} for row in matrix):
        return _not_assessed("complete person separation (all-fail or all-pass response vector) makes joint maximum-likelihood ability estimates diverge.")
    if any(sum(matrix[p][i] for p in range(p_count)) in {0, p_count} for i in range(i_count)):
        return _not_assessed("complete item separation (all-fail or all-pass item) makes joint maximum-likelihood difficulty estimates diverge.")

    theta = [0.0] * p_count
    difficulty = [0.0] * i_count
    converged = False
    iterations = 0
    for iteration in range(1, max_iterations + 1):
        largest_delta = 0.0
        for p in range(p_count):
            probabilities = [_sigmoid(theta[p] - difficulty[i]) for i in range(i_count)]
            score = sum(matrix[p][i] - probabilities[i] for i in range(i_count))
            information = sum(value * (1.0 - value) for value in probabilities)
            if information <= 1e-12:
                return _not_assessed("Rasch person information collapsed during estimation.")
            delta = max(-1.0, min(1.0, score / information))
            theta[p] += 0.5 * delta
            largest_delta = max(largest_delta, abs(delta))
        for i in range(i_count):
            probabilities = [_sigmoid(theta[p] - difficulty[i]) for p in range(p_count)]
            score = sum(probabilities[p] - matrix[p][i] for p in range(p_count))
            information = sum(value * (1.0 - value) for value in probabilities)
            if information <= 1e-12:
                return _not_assessed("Rasch item information collapsed during estimation.")
            delta = max(-1.0, min(1.0, score / information))
            difficulty[i] += 0.5 * delta
            largest_delta = max(largest_delta, abs(delta))

        center = sum(difficulty) / i_count
        difficulty = [value - center for value in difficulty]
        theta = [value - center for value in theta]
        iterations = iteration
        if largest_delta < tolerance:
            converged = True
            break

    if not converged:
        return _not_assessed(f"Rasch estimator did not converge within {max_iterations} iterations.")

    person_results = []
    for index, person in enumerate(persons):
        expected = [_sigmoid(theta[index] - difficulty[item]) for item in range(i_count)]
        info = sum(value * (1.0 - value) for value in expected)
        fit = _rasch_fit_mnsq(matrix[index], expected)
        person_results.append({
            "configuration_id": person,
            "ability_logit": theta[index],
            "standard_error": 1.0 / math.sqrt(info) if info > 0 else None,
            "raw_score": sum(matrix[index]),
            "item_count": i_count,
            **fit,
        })

    grid = [-2.0, -1.0, 0.0, 1.0, 2.0]
    item_results = []
    for index, item in enumerate(items):
        information_values = []
        for ability in grid:
            probability = _sigmoid(ability - difficulty[index])
            information_values.append(probability * (1.0 - probability))
        info_at_zero = information_values[2]
        item_expected = [_sigmoid(theta[p] - difficulty[index]) for p in range(p_count)]
        item_fit = _rasch_fit_mnsq(
            [matrix[p][index] for p in range(p_count)], item_expected
        )
        item_information = sum(value * (1.0 - value) for value in item_expected)
        item_results.append({
            "case_id": item,
            "difficulty_logit": difficulty[index],
            "standard_error": 1.0 / math.sqrt(item_information),
            **item_fit,
            "information_by_theta": [
                {"theta": ability, "information": value}
                for ability, value in zip(grid, information_values)
            ],
            "information_at_theta_zero": info_at_zero,
        })

    return {
        "status": "ESTIMATED_EXPLORATORY",
        "model": "Rasch_1PL_joint_maximum_likelihood",
        "converged": True,
        "iterations": iterations,
        "persons": person_results,
        "items": item_results,
        "fit_diagnostics": {
            "status": "DESCRIPTIVE_ONLY",
            "person_infit_mean_square": statistics.mean(row["infit_msq"] for row in person_results),
            "person_outfit_mean_square": statistics.mean(row["outfit_msq"] for row in person_results),
            "item_infit_mean_square": statistics.mean(row["infit_msq"] for row in item_results),
            "item_outfit_mean_square": statistics.mean(row["outfit_msq"] for row in item_results),
            "interpretation": "Descriptive Rasch infit/outfit mean squares only; no universal cutoff or inferential fit decision is applied.",
        },
        "test_information_by_theta": [
            {
                "theta": ability,
                "information": sum(
                    _sigmoid(ability - difficulty[i]) *
                    (1.0 - _sigmoid(ability - difficulty[i]))
                    for i in range(i_count)
                ),
            }
            for ability in grid
        ],
        "limitations": [
            "Exploratory 1PL Rasch estimates only; no 2PL discrimination, multidimensional IRT, DIF, or measurement-invariance tests are implemented.",
            "Infit/outfit mean squares are descriptive diagnostics only; no universal cutoff, formal p-value, or model acceptance decision is applied.",
            "Joint maximum likelihood estimates can be biased in small samples; standard errors are local Fisher-information approximations.",
            "The person population is the supplied configuration set and must not be generalized beyond its declared scope.",
            "No universal sample-size threshold or validity claim is implied by successful convergence.",
        ],
    }


def estimate_g_theory(persons: list[str], items: list[str], matrix: list[list[int]]) -> dict:
    """Balanced crossed person x item random-facet ANOVA method-of-moments."""
    p_count, i_count = len(persons), len(items)
    if p_count < 2 or i_count < 2:
        return _not_assessed("A crossed person-by-item G-study requires at least two persons and two items.")
    grand = sum(sum(row) for row in matrix) / (p_count * i_count)
    person_means = [sum(row) / i_count for row in matrix]
    item_means = [
        sum(matrix[p][i] for p in range(p_count)) / p_count
        for i in range(i_count)
    ]
    ss_person = i_count * sum((value - grand) ** 2 for value in person_means)
    ss_item = p_count * sum((value - grand) ** 2 for value in item_means)
    ss_residual = sum(
        (matrix[p][i] - person_means[p] - item_means[i] + grand) ** 2
        for p in range(p_count) for i in range(i_count)
    )
    ms_person = ss_person / (p_count - 1)
    ms_item = ss_item / (i_count - 1)
    ms_residual = ss_residual / ((p_count - 1) * (i_count - 1))
    raw_person = (ms_person - ms_residual) / i_count
    raw_item = (ms_item - ms_residual) / p_count
    variance_person = max(0.0, raw_person)
    variance_item = max(0.0, raw_item)
    variance_person_item_residual = max(0.0, ms_residual)

    relative_error = variance_person_item_residual / i_count
    absolute_error = (variance_item + variance_person_item_residual) / i_count
    g_denominator = variance_person + relative_error
    phi_denominator = variance_person + absolute_error
    g_coefficient = variance_person / g_denominator if g_denominator > 0 else None
    phi_coefficient = variance_person / phi_denominator if phi_denominator > 0 else None

    d_study = []
    for planned_items in range(1, i_count + 1):
        rel = variance_person_item_residual / planned_items
        absolute = (variance_item + variance_person_item_residual) / planned_items
        d_study.append({
            "planned_item_count": planned_items,
            "relative_G_coefficient": (
                variance_person / (variance_person + rel)
                if variance_person + rel > 0 else None
            ),
            "absolute_Phi_coefficient": (
                variance_person / (variance_person + absolute)
                if variance_person + absolute > 0 else None
            ),
        })

    warnings = []
    if raw_person < 0 or raw_item < 0:
        warnings.append("One or more method-of-moments variance components were negative and truncated to zero; interpret coefficients cautiously.")
    if p_count < 5 or i_count < 5:
        warnings.append("The crossed design is small; variance components and dependability coefficients are unstable and descriptive only.")

    return {
        "status": "ESTIMATED_EXPLORATORY",
        "design": "balanced_crossed_person_by_item",
        "person_count": p_count,
        "item_count": i_count,
        "observation_count": p_count * i_count,
        "variance_components": {
            "person": variance_person,
            "item": variance_item,
            "person_by_item_plus_residual": variance_person_item_residual,
            "raw_person_component": raw_person,
            "raw_item_component": raw_item,
        },
        "coefficients": {
            "relative_G_coefficient": g_coefficient,
            "absolute_Phi_coefficient": phi_coefficient,
        },
        "d_study": d_study,
        "warnings": warnings,
        "limitations": [
            "Two-facet balanced crossed random-effects method-of-moments approximation; person-by-item interaction and residual are confounded.",
            "No separate seed, environment, or Judge facet is estimated; repeated records per person-item cell are rejected.",
            "Variance components depend on the declared person/item universe and random-facet assumptions.",
            "These estimates do not establish construct validity or authorize a composite score.",
        ],
    }


def analyze_records(records: list[dict], *, max_iterations: int = 500, tolerance: float = 1e-7) -> dict:
    if not records:
        raise ValueError("runtime record collection is empty")
    dataset_ids = {item.get("dataset_id") for item in records}
    dataset_hashes = {item.get("dataset_sha256") for item in records}
    if len(dataset_ids) != 1 or len(dataset_hashes) != 1:
        raise ValueError("all records must bind to one dataset identity and SHA-256")
    persons, items, matrix, exclusions = _prepare_matrix(records)
    if persons and items:
        irt = fit_rasch_1pl(persons, items, matrix, max_iterations, tolerance)
        g_study = estimate_g_theory(persons, items, matrix)
    else:
        irt = _not_assessed("No eligible valid binary Agent outcomes with independent Gold provenance.")
        g_study = _not_assessed("No eligible valid binary Agent outcomes with independent Gold provenance.")
    raw = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": "0.0.2",
        "report_id": "capability-measurement-" + hashlib.sha256(raw).hexdigest()[:16],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dataset": {"dataset_id": next(iter(dataset_ids)), "sha256": next(iter(dataset_hashes))},
        "evidence": {
            "input_record_count": len(records),
            "eligible_person_count": len(persons),
            "eligible_item_count": len(items),
            "eligible_observation_count": len(persons) * len(items),
            "label_source": "independent_gold_only",
            "person_ids": persons,
            "item_ids": items,
            "excluded_records": exclusions,
        },
        "irt": irt,
        "g_theory": g_study,
        "overall_status": (
            "ESTIMATED_EXPLORATORY"
            if irt["status"] == "ESTIMATED_EXPLORATORY" or g_study["status"] == "ESTIMATED_EXPLORATORY"
            else "NOT_ASSESSED"
        ),
        "limitations": [
            "This tool analyzes supplied evidence; it does not create Gold labels or run Agents.",
            "Exploratory estimates are not validated for any population until preregistered fit, precision, invariance, and external validation studies are completed.",
            "No composite score, universal pass threshold, or release gate is derived from these outputs.",
        ],
    }


def validate_report(report: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(report), key=lambda error: list(error.absolute_path))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True, type=Path, help="JSONL runtime records")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-iterations", type=int, default=500)
    parser.add_argument("--tolerance", type=float, default=1e-7)
    args = parser.parse_args()
    try:
        records = [json.loads(line) for line in args.records.read_text(encoding="utf-8").splitlines() if line.strip()]
        report = analyze_records(records, max_iterations=args.max_iterations, tolerance=args.tolerance)
        errors = validate_report(report)
        if errors:
            raise ValueError("report schema validation failed: " + "; ".join(errors))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(f"Report written: {args.output}")
    print(f"Rasch: {report['irt']['status']}; G-Theory: {report['g_theory']['status']}")
    print("NOTE: exploratory measurement estimates are not empirical validity claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
