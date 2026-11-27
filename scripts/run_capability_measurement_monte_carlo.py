#!/usr/bin/env python3
"""Reproducible Rasch 1PL parameter-recovery simulation (simulation evidence only)."""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from pathlib import Path

from scripts.analyze_capability_measurement import fit_rasch_1pl, _sigmoid


def _correlation(left: list[float], right: list[float]) -> float:
    lm, rm = statistics.mean(left), statistics.mean(right)
    numerator = sum((a-lm)*(b-rm) for a,b in zip(left,right))
    denominator = math.sqrt(sum((a-lm)**2 for a in left) * sum((b-rm)**2 for b in right))
    return numerator / denominator if denominator else 0.0


def _quantiles(values: list[float]) -> dict:
    ordered = sorted(values)
    def q(probability: float) -> float:
        position = (len(ordered)-1)*probability
        low, high = math.floor(position), math.ceil(position)
        if low == high:
            return ordered[low]
        return ordered[low] + (ordered[high]-ordered[low])*(position-low)
    return {"p2_5": q(0.025), "median": q(0.5), "p97_5": q(0.975)}


def run_experiment(*, replications: int = 30, persons: int = 80, items: int = 25, seed: int = 8000) -> dict:
    if replications < 1 or persons < 3 or items < 3:
        raise ValueError("replications must be positive; persons and items must be at least three")
    metrics = {"ability_correlation": [], "item_correlation": [], "ability_rmse": [], "item_rmse": []}
    failures: list[dict] = []
    for replication in range(replications):
        rng = random.Random(seed + replication)
        true_theta = [rng.gauss(0.0, 0.8) for _ in range(persons)]
        true_difficulty = [rng.gauss(0.0, 0.9) for _ in range(items)]
        matrix = [
            [int(rng.random() < _sigmoid(true_theta[p] - true_difficulty[i])) for i in range(items)]
            for p in range(persons)
        ]
        fit = fit_rasch_1pl(
            [f"person-{p:03d}" for p in range(persons)],
            [f"item-{i:03d}" for i in range(items)],
            matrix,
        )
        if fit.get("status") != "ESTIMATED_EXPLORATORY":
            failures.append({"replication": replication, "reason": fit.get("reason", "unknown fit failure")})
            continue
        estimated_theta = [row["ability_logit"] for row in fit["persons"]]
        estimated_difficulty = [row["difficulty_logit"] for row in fit["items"]]
        # The estimator identifies the scale by centering estimated and true item difficulties.
        center = statistics.mean(true_difficulty)
        aligned_theta = [value-center for value in true_theta]
        aligned_difficulty = [value-center for value in true_difficulty]
        metrics["ability_correlation"].append(_correlation(aligned_theta, estimated_theta))
        metrics["item_correlation"].append(_correlation(aligned_difficulty, estimated_difficulty))
        metrics["ability_rmse"].append(math.sqrt(statistics.mean((a-b)**2 for a,b in zip(aligned_theta, estimated_theta))))
        metrics["item_rmse"].append(math.sqrt(statistics.mean((a-b)**2 for a,b in zip(aligned_difficulty, estimated_difficulty))))
    valid = len(metrics["ability_correlation"])
    if not valid:
        raise RuntimeError("all Monte Carlo replications failed; no recovery summary is estimable")
    return {
        "experiment": "rasch_1pl_parameter_recovery",
        "evidence_level": "SIMULATION_ONLY",
        "seed": seed,
        "requested_replications": replications,
        "valid_replications": valid,
        "failed_replications": len(failures),
        "design": {"persons": persons, "items": items, "theta_distribution": "Normal(0, 0.8)", "difficulty_distribution": "Normal(0, 0.9)", "response_model": "Bernoulli(logit(theta - difficulty))"},
        "metrics_across_valid_replications": {
            name: {"mean": statistics.mean(values), **_quantiles(values)}
            for name, values in metrics.items()
        },
        "failed_replication_reasons": failures,
        "interpretation": "Quantiles describe variation across simulated replications, not confidence intervals for real-world performance. Results assess parameter recovery only under the correctly specified unidimensional Rasch data-generating model; they do not test model fit, DIF, local independence, real Agent validity, or G-Theory assumptions.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replications", type=int, default=30)
    parser.add_argument("--persons", type=int, default=80)
    parser.add_argument("--items", type=int, default=25)
    parser.add_argument("--seed", type=int, default=8000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_experiment(replications=args.replications, persons=args.persons, items=args.items, seed=args.seed)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
