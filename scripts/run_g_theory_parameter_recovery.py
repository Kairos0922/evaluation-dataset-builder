#!/usr/bin/env python3
"""Monte Carlo parameter recovery for the observed-scale binary G-study estimator.

The DGP is a logistic crossed random-effects model. Reference components are
computed independently on the observed binary-score scale by Monte Carlo
integration; finite samples are then analyzed by the production G-study
method-of-moments estimator. Evidence remains SIMULATION_ONLY.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import random
import statistics
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.analyze_capability_measurement import _sigmoid, estimate_g_theory

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "g-theory-monte-carlo-report.schema.json"

SCENARIOS = [
    {"name": "balanced_moderate", "intercept": 0.0, "person_sd": 0.7, "item_sd": 0.5},
    {"name": "low_prevalence", "intercept": -1.4, "person_sd": 0.7, "item_sd": 0.5},
    {"name": "low_person_variance", "intercept": 0.0, "person_sd": 0.2, "item_sd": 0.5},
    {"name": "high_item_variance", "intercept": 0.0, "person_sd": 0.7, "item_sd": 0.9},
]


def _quantiles(values: list[float]) -> dict:
    ordered = sorted(values)
    def q(probability: float) -> float:
        position = (len(ordered) - 1) * probability
        low, high = math.floor(position), math.ceil(position)
        if low == high:
            return ordered[low]
        return ordered[low] + (ordered[high] - ordered[low]) * (position - low)
    return {"p2_5": q(0.025), "median": q(0.5), "p97_5": q(0.975)}


def _metric(values: list[float], truth: float) -> dict:
    mean = statistics.mean(values)
    return {
        "mean": mean,
        "bias": mean - truth,
        "rmse": math.sqrt(statistics.mean((value - truth) ** 2 for value in values)),
        **_quantiles(values),
    }


def _reference_components(*, intercept: float, person_sd: float, item_sd: float,
                          draws: int, seed: int) -> dict:
    """Independent Monte Carlo integration of observed-scale covariance components."""
    rng = random.Random(seed)
    person_effects = [rng.gauss(0.0, person_sd) for _ in range(draws)]
    item_effects = [rng.gauss(0.0, item_sd) for _ in range(draws)]
    item_probability_sums = [0.0] * draws
    person_probability_means = []
    grand_sum = 0.0

    for person_effect in person_effects:
        row_sum = 0.0
        for index, item_effect in enumerate(item_effects):
            probability = _sigmoid(intercept + person_effect + item_effect)
            row_sum += probability
            item_probability_sums[index] += probability
        person_probability_means.append(row_sum / draws)
        grand_sum += row_sum

    grand_mean = grand_sum / (draws * draws)
    item_probability_means = [value / draws for value in item_probability_sums]
    person_variance = statistics.pvariance(person_probability_means)
    item_variance = statistics.pvariance(item_probability_means)
    total_binary_variance = grand_mean * (1.0 - grand_mean)
    residual_raw = total_binary_variance - person_variance - item_variance
    residual_variance = max(0.0, residual_raw)
    return {
        "grand_mean": grand_mean,
        "person_variance": person_variance,
        "item_variance": item_variance,
        "person_by_item_plus_residual_variance": residual_variance,
        "residual_variance_raw": residual_raw,
    }


def _coefficients(reference: dict, item_count: int) -> dict:
    person = reference["person_variance"]
    item = reference["item_variance"]
    residual = reference["person_by_item_plus_residual_variance"]
    relative_denominator = person + residual / item_count
    absolute_denominator = person + (item + residual) / item_count
    return {
        "relative_G_coefficient": person / relative_denominator if relative_denominator > 0 else 0.0,
        "absolute_Phi_coefficient": person / absolute_denominator if absolute_denominator > 0 else 0.0,
    }


def _run_scenario(scenario: dict, *, replications: int, persons: int, items: int,
                  reference_draws: int, seed: int, scenario_index: int) -> dict:
    reference = _reference_components(
        intercept=scenario["intercept"], person_sd=scenario["person_sd"],
        item_sd=scenario["item_sd"], draws=reference_draws,
        seed=seed + 700_000 + scenario_index,
    )
    truth = {
        "person_variance": reference["person_variance"],
        "item_variance": reference["item_variance"],
        "person_by_item_plus_residual": reference["person_by_item_plus_residual_variance"],
        **_coefficients(reference, items),
    }
    metric_values = {
        "person_variance_raw": [],
        "item_variance_raw": [],
        "person_by_item_plus_residual": [],
        "relative_G_coefficient": [],
        "absolute_Phi_coefficient": [],
    }
    failures = []
    negative_person = 0
    negative_item = 0

    for replication in range(replications):
        rng = random.Random(seed + scenario_index * 100_000 + replication)
        person_effects = [rng.gauss(0.0, scenario["person_sd"]) for _ in range(persons)]
        item_effects = [rng.gauss(0.0, scenario["item_sd"]) for _ in range(items)]
        matrix = [
            [
                int(rng.random() < _sigmoid(scenario["intercept"] + person_effect + item_effect))
                for item_effect in item_effects
            ]
            for person_effect in person_effects
        ]
        estimate = estimate_g_theory(
            [f"person-{index:03d}" for index in range(persons)],
            [f"item-{index:03d}" for index in range(items)],
            matrix,
        )
        if estimate.get("status") != "ESTIMATED_EXPLORATORY":
            failures.append({"replication": replication, "reason": estimate.get("reason", "unknown failure")})
            continue
        components = estimate["variance_components"]
        coefficients = estimate["coefficients"]
        raw_person = components["raw_person_component"]
        raw_item = components["raw_item_component"]
        negative_person += raw_person < 0
        negative_item += raw_item < 0
        metric_values["person_variance_raw"].append(raw_person)
        metric_values["item_variance_raw"].append(raw_item)
        metric_values["person_by_item_plus_residual"].append(components["person_by_item_plus_residual"])
        if coefficients["relative_G_coefficient"] is not None:
            metric_values["relative_G_coefficient"].append(coefficients["relative_G_coefficient"])
        if coefficients["absolute_Phi_coefficient"] is not None:
            metric_values["absolute_Phi_coefficient"].append(coefficients["absolute_Phi_coefficient"])

    valid = len(metric_values["person_variance_raw"])
    if valid == 0:
        raise RuntimeError(f"all replications failed for scenario {scenario['name']}")
    recovery = {
        "person_variance_raw": _metric(metric_values["person_variance_raw"], truth["person_variance"]),
        "item_variance_raw": _metric(metric_values["item_variance_raw"], truth["item_variance"]),
        "person_by_item_plus_residual": _metric(
            metric_values["person_by_item_plus_residual"], truth["person_by_item_plus_residual"]
        ),
        "relative_G_coefficient": _metric(
            metric_values["relative_G_coefficient"], truth["relative_G_coefficient"]
        ),
        "absolute_Phi_coefficient": _metric(
            metric_values["absolute_Phi_coefficient"], truth["absolute_Phi_coefficient"]
        ),
    }
    return {
        "name": scenario["name"],
        "parameters": scenario,
        "reference": {**reference, **_coefficients(reference, items)},
        "valid_replications": valid,
        "failed_replications": len(failures),
        "negative_component_rates": {
            "person": negative_person / valid,
            "item": negative_item / valid,
        },
        "parameter_recovery": recovery,
        "failed_replication_reasons": failures,
    }


def run_experiment(*, replications: int = 100, persons: int = 40, items: int = 25,
                   reference_draws: int = 1000, seed: int = 9100,
                   scenarios: list[dict] | None = None) -> dict:
    if replications < 2 or persons < 5 or items < 5 or reference_draws < 100:
        raise ValueError("require replications>=2, persons>=5, items>=5 and reference_draws>=100")
    selected = scenarios or SCENARIOS
    results = [
        _run_scenario(
            scenario, replications=replications, persons=persons, items=items,
            reference_draws=reference_draws, seed=seed, scenario_index=index,
        )
        for index, scenario in enumerate(selected)
    ]
    identity = {
        "seed": seed, "replications": replications, "persons": persons,
        "items": items, "reference_draws": reference_draws, "scenarios": results,
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema_version": "0.0.2",
        "report_id": "g-theory-recovery-" + digest[:20],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evidence_level": "SIMULATION_ONLY",
        "simulation": {
            "seed": seed,
            "replications_per_scenario": replications,
            "persons_per_replication": persons,
            "items_per_replication": items,
            "reference_draws_per_scenario": reference_draws,
            "response_model": "Bernoulli(logit(intercept + person_random_effect + item_random_effect))",
            "random_effects": "independent Normal(0, person_sd) and Normal(0, item_sd)",
            "estimand": "observed_binary_score_scale_person_item_residual_variance_components",
            "coefficient_item_count": items,
        },
        "scenarios": results,
        "limitations": [
            "Reference variance components are Monte Carlo integrals on the observed binary-score scale, not latent logistic-scale variances.",
            "The simulation evaluates the current balanced two-facet method-of-moments estimator under a correctly specified additive logistic random-effects DGP only.",
            "Person-by-item interaction and Bernoulli residual remain confounded; no separate Seed, Environment, or Judge facet is estimated.",
            "Monte Carlo quantiles describe sampling variation across simulated replications, not confidence intervals for real Agent/Skill populations.",
            "This experiment does not validate construct validity, model fit, DIF, measurement invariance, or external criterion validity.",
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
    parser.add_argument("--replications", type=int, default=100)
    parser.add_argument("--persons", type=int, default=40)
    parser.add_argument("--items", type=int, default=25)
    parser.add_argument("--reference-draws", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=9100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = run_experiment(
            replications=args.replications, persons=args.persons, items=args.items,
            reference_draws=args.reference_draws, seed=args.seed,
        )
        errors = validate_report(report)
        if errors:
            raise ValueError("report schema validation failed: " + "; ".join(errors))
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
