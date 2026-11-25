#!/usr/bin/env python3
"""Analyze normalized Agent / Skill runtime records and create an ERA report."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from statistics import NormalDist, median

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCHEMA = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "runtime-record.schema.json"
CONFIDENCE_Z = NormalDist().inv_cdf(0.975)


def load_records(path: Path):
    schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records = []
    errors = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            errors.append(f"line {line_number}: blank line")
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc}")
            continue
        for error in validator.iter_errors(record):
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            errors.append(f"line {line_number} {location}: {error.message}")
        records.append(record)
    return records, errors


def wilson_interval(successes: int, total: int, confidence: float = 0.95):
    if total <= 0:
        return None
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) / total) + (z * z / (4 * total * total))) / denominator
    return {
        "lower": max(0.0, center - margin),
        "upper": min(1.0, center + margin),
        "level": confidence,
        "method": "Wilson score interval"
    }


def rate_metric(metric_id, successes, total, unit, evidence_refs, limitations, confidence=0.95):
    if total <= 0:
        return {
            "metric_id": metric_id,
            "status": "NOT_ASSESSED",
            "value": None,
            "unit": unit,
            "numerator": None,
            "denominator": None,
            "interval": None,
            "evidence_refs": evidence_refs,
            "limitations": limitations
        }
    return {
        "metric_id": metric_id,
        "status": "MEASURED",
        "value": successes / total,
        "unit": unit,
        "numerator": successes,
        "denominator": total,
        "interval": wilson_interval(successes, total, confidence),
        "evidence_refs": evidence_refs,
        "limitations": limitations
    }


def exact_mcnemar_pvalue(regressions: int, improvements: int):
    discordant = regressions + improvements
    if discordant == 0:
        return 1.0
    tail = min(regressions, improvements)
    log_terms = [
        math.lgamma(discordant + 1)
        - math.lgamma(index + 1)
        - math.lgamma(discordant - index + 1)
        - discordant * math.log(2)
        for index in range(tail + 1)
    ]
    maximum = max(log_terms)
    one_tail = math.exp(maximum) * sum(math.exp(value - maximum) for value in log_terms)
    return min(1.0, 2 * one_tail)


def bootstrap_interval(values: list[float], iterations: int = 2000, seed: int = 2026):
    if not values:
        return None
    import random
    rng = random.Random(seed)
    n = len(values)
    samples = []
    for _ in range(iterations):
        samples.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    samples.sort()
    return {
        "lower": samples[int(0.025 * (iterations - 1))],
        "upper": samples[int(0.975 * (iterations - 1))],
        "level": 0.95,
        "method": f"paired percentile bootstrap ({iterations} resamples; seed={seed})"
    }


def _unique_objects(records, key):
    unique = {}
    for record in records:
        value = record[key]
        signature = json.dumps(value, sort_keys=True, separators=(",", ":"))
        unique[signature] = value
    return list(unique.values())


def _configuration_map(records):
    configurations = {}
    for record in records:
        config_id = record["configuration_id"]
        value = {
            "configuration_id": config_id,
            "target_revision": record["target_revision"],
            "model": record["model"],
            "harness": record["harness"],
            "environment": record["environment"],
            "tool_versions": record["tool_versions"],
            "execution_parameters": {}
        }
        if config_id in configurations and configurations[config_id] != value:
            raise ValueError(f"configuration_id {config_id!r} maps to inconsistent runtime metadata")
        configurations[config_id] = value
    return [configurations[key] for key in sorted(configurations)]


def _single_or_multiple(values, keys):
    distinct = {
        json.dumps({key: value.get(key) for key in keys}, sort_keys=True)
        for value in values
    }
    if len(distinct) == 1:
        return json.loads(next(iter(distinct)))
    return None


def _pair_analysis(records, baseline_revision: str, candidate_revision: str):
    grouped = defaultdict(list)
    for record in records:
        pair_id = record.get("pair_id")
        if pair_id:
            grouped[pair_id].append(record)
    valid_pairs = []
    incomplete = []
    for pair_id, pair in grouped.items():
        baseline = [item for item in pair if item["target_revision"] == baseline_revision]
        candidate = [item for item in pair if item["target_revision"] == candidate_revision]
        if len(baseline) != 1 or len(candidate) != 1:
            incomplete.append(pair_id)
            continue
        old, new = baseline[0], candidate[0]
        if old["case_id"] != new["case_id"]:
            incomplete.append(pair_id)
            continue
        if any(old[key] != new[key] for key in ("model", "harness", "environment", "tool_versions", "seed")):
            incomplete.append(pair_id)
            continue
        if old["status"] != "valid" or new["status"] != "valid":
            incomplete.append(pair_id)
            continue
        if old["agent_outcome"] not in {"pass", "fail"} or new["agent_outcome"] not in {"pass", "fail"}:
            incomplete.append(pair_id)
            continue
        valid_pairs.append((pair_id, old, new))
    return valid_pairs, incomplete


def _flakiness(records):
    groups = defaultdict(list)
    for record in records:
        repeat_id = record.get("repeat_group_id")
        outcome = record.get("agent_outcome")
        if repeat_id and record["status"] == "valid" and outcome in {"pass", "fail"}:
            key = (
                repeat_id,
                record["case_id"],
                record["configuration_id"],
                record["target_revision"]
            )
            groups[key].append(outcome)
    repeated = [outcomes for outcomes in groups.values() if len(outcomes) > 1]
    discordant = sum(1 for outcomes in repeated if len(set(outcomes)) > 1)
    return discordant, len(repeated)


def _percentile(values, probability):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def build_era_report(
    records_path: Path,
    output_path: Path,
    dataset_version: str,
    target_name: str,
    evaluation_purpose: str,
    baseline_revision: str | None = None,
    candidate_revision: str | None = None,
    confidence: float = 0.95,
    bootstrap_resamples: int = 2000,
    bootstrap_seed: int = 2026,
):
    if not 0 < confidence < 1:
        raise ValueError("confidence must be strictly between 0 and 1")
    if bootstrap_resamples < 1:
        raise ValueError("bootstrap_resamples must be positive")
    records, validation_errors = load_records(records_path)
    if validation_errors:
        raise ValueError("runtime record schema validation failed: " + "; ".join(validation_errors[:20]))
    if not records:
        raise ValueError("runtime record file contains no records")
    for record in records:
        record["agent_outcome"] = record["outcomes"]["agent_outcome"]
        record["process_outcome"] = record["outcomes"]["process_outcome"]
        record["grader_outcome"] = record["outcomes"]["grader_outcome"]
        record["gold_outcome"] = record["outcomes"]["gold_outcome"]
        record["gold_source"] = record["outcomes"]["gold_source"]

    dataset_ids = {record["dataset_id"] for record in records}
    dataset_hashes = {record["dataset_sha256"] for record in records}
    target_types = {record["target_type"] for record in records}
    if len(dataset_ids) != 1 or len(dataset_hashes) != 1 or len(target_types) != 1:
        raise ValueError("all runtime records must bind to one dataset_id, dataset_sha256 and target_type")

    run_ids = [record["run_id"] for record in records]
    if len(run_ids) != len(set(run_ids)):
        raise ValueError("run_id values must be unique")

    if evaluation_purpose in {"regression", "both"}:
        if not baseline_revision or not candidate_revision:
            raise ValueError("baseline and candidate revisions are required for Regression Evaluation")
        if baseline_revision == candidate_revision:
            raise ValueError("baseline_revision and candidate_revision must differ")

    configs = _configuration_map(records)
    model_summary = _single_or_multiple([config["model"] for config in configs], ["provider", "model_id", "revision"])
    harness_summary = _single_or_multiple([config["harness"] for config in configs], ["name", "version"])
    environment_summary = _single_or_multiple([config["environment"] for config in configs], ["name", "version", "digest", "region"])
    tool_versions = {}
    for config in configs:
        for tool_name, version in config["tool_versions"].items():
            previous = tool_versions.get(tool_name)
            tool_versions[tool_name] = version if previous in (None, version) else "multiple"

    model_summary = model_summary or {"provider": "multiple", "model_id": "multiple", "model_revision": None}
    if "revision" in model_summary:
        model_summary["model_revision"] = model_summary.pop("revision")
    harness_summary = harness_summary or {"name": "multiple", "version": "multiple"}
    environment_summary = environment_summary or {"name": "multiple", "version": "multiple", "digest": None, "region": None}

    revisions = {record["target_revision"] for record in records}
    target_revision = next(iter(revisions)) if len(revisions) == 1 else None
    protocol_id = f"runtime-{hashlib.sha256(records_path.read_bytes()).hexdigest()[:12]}"
    digest = next(iter(dataset_hashes))
    dataset_id = next(iter(dataset_ids))
    target_type = next(iter(target_types))
    evidence_ref = f"file://{records_path.name}"

    total_runs = len(records)
    valid_runs = [record for record in records if record["status"] == "valid"]
    environment_failed = sum(record["status"] == "environment_failed" for record in records)
    agent_failed_runs = sum(record["status"] == "agent_failed" for record in records)
    outcome_rows = [
        record for record in valid_runs
        if record["agent_outcome"] in {"pass", "fail"}
    ]
    agent_passes = sum(record["agent_outcome"] == "pass" for record in outcome_rows)
    process_rows = [
        record for record in valid_runs
        if record["process_outcome"] in {"pass", "fail"}
    ]
    process_passes = sum(record["process_outcome"] == "pass" for record in process_rows)

    # A Gold Oracle label without a linked grader_id is not a Judge abstention or a Judge decision.
    # Keep Oracle evidence available while excluding it from Judge error-rate denominators.
    gold_rows = [
        record for record in records
        if record["outcomes"]["gold_source"] in {"independent_oracle", "expert_adjudication"}
        and record["gold_outcome"] in {"pass", "fail"}
    ]
    graded_gold_rows = [record for record in gold_rows if record["outcomes"].get("grader_id")]
    judged_rows = [record for record in graded_gold_rows if record["grader_outcome"] in {"pass", "fail"}]
    grader_correct = sum(record["gold_outcome"] == record["grader_outcome"] for record in judged_rows)
    graded_gold_fail_rows = [record for record in graded_gold_rows if record["gold_outcome"] == "fail"]
    graded_gold_pass_rows = [record for record in graded_gold_rows if record["gold_outcome"] == "pass"]
    false_passes = sum(record["grader_outcome"] == "pass" for record in graded_gold_fail_rows)
    false_fails = sum(record["grader_outcome"] == "fail" for record in graded_gold_pass_rows)
    abstentions = sum(record["grader_outcome"] in {"abstain", "unknown"} for record in graded_gold_rows)

    fault_rows = [
        record for record in records
        if record["fault"]["injected"] and record["fault"]["kind"] in {"historical", "mutation"}
    ]
    historical_rows = [record for record in fault_rows if record["fault"]["kind"] == "historical" and record["fault"]["detected"] is not None]
    mutation_rows = [record for record in fault_rows if record["fault"]["kind"] == "mutation" and record["fault"]["detected"] is not None]
    exposed_rows = [record for record in fault_rows if record["fault"]["failure_exposed"] is not None]
    historical_detected = sum(record["fault"]["detected"] is True for record in historical_rows)
    mutation_detected = sum(record["fault"]["detected"] is True for record in mutation_rows)
    failure_exposed = sum(record["fault"]["failure_exposed"] is True for record in exposed_rows)

    paired = []
    incomplete_pairs = []
    regressions = improvements = 0
    paired_delta = None
    mcnemar_p = None
    if evaluation_purpose in {"regression", "both"}:
        paired, incomplete_pairs = _pair_analysis(records, baseline_revision, candidate_revision)
        regressions = sum(old["agent_outcome"] == "pass" and new["agent_outcome"] == "fail" for _, old, new in paired)
        improvements = sum(old["agent_outcome"] == "fail" and new["agent_outcome"] == "pass" for _, old, new in paired)
        if paired:
            old_rate = sum(old["agent_outcome"] == "pass" for _, old, _ in paired) / len(paired)
            new_rate = sum(new["agent_outcome"] == "pass" for _, _, new in paired) / len(paired)
            paired_delta = new_rate - old_rate
            mcnemar_p = exact_mcnemar_pvalue(regressions, improvements)

    flaky_groups, repeated_groups = _flakiness(records)
    durations = [record["cost"]["duration_seconds"] for record in records if record["cost"]["duration_seconds"] is not None]
    costs = [record["cost"]["cost_usd"] for record in records if record["cost"]["cost_usd"] is not None]
    tokens = [
        record["cost"].get("total_tokens")
        if record["cost"].get("total_tokens") is not None
        else record["cost"]["input_tokens"] + record["cost"]["output_tokens"]
        for record in records
        if record["cost"].get("total_tokens") is not None
        or (record["cost"]["input_tokens"] is not None and record["cost"]["output_tokens"] is not None)
    ]
    cache_read_tokens = [record["cost"].get("cache_read_tokens") for record in records if record["cost"].get("cache_read_tokens") is not None]
    cache_write_tokens = [record["cost"].get("cache_write_tokens") for record in records if record["cost"].get("cache_write_tokens") is not None]
    model_steps = [record["cost"].get("model_steps") for record in records if record["cost"].get("model_steps") is not None]

    metrics = [
        rate_metric("ERA-RUN-01", len(valid_runs), total_runs, "valid_run_rate", [evidence_ref], ["Valid-run rate does not by itself measure Agent quality."], confidence),
        rate_metric("ERA-RUN-02", environment_failed, total_runs, "environment_failure_rate", [evidence_ref], ["Environment failures must not be attributed to the Agent or dataset."], confidence),
        rate_metric("ERA-RUN-03", agent_passes, len(outcome_rows), "agent_outcome_pass_rate", [evidence_ref], ["This is the tested Agent outcome, not a standalone dataset quality score."], confidence),
        rate_metric("ERA-RUN-04", process_passes, len(process_rows), "process_compliance_rate", [evidence_ref], ["Process requirements must be defined by the task and rubric."], confidence),
        rate_metric("ERA-GRD-01", false_passes, len(graded_gold_fail_rows), "grader_false_pass_rate", [evidence_ref], ["Gold labels must come from an independent Oracle or expert adjudication."], confidence),
        rate_metric("ERA-GRD-02", false_fails, len(graded_gold_pass_rows), "grader_false_fail_rate", [evidence_ref], ["Gold labels must come from an independent Oracle or expert adjudication."], confidence),
        rate_metric("ERA-GRD-03", abstentions, len(graded_gold_rows), "grader_abstention_rate", [evidence_ref], ["Abstentions must remain distinct from pass and fail."], confidence),
        rate_metric("ERA-GRD-04", grader_correct, len(judged_rows), "grader_accuracy_on_judged_gold_rows", [evidence_ref], ["Accuracy excludes abstentions; report coverage and abstention separately."], confidence),
        rate_metric("ERA-RUN-05", failure_exposed, len(exposed_rows), "failure_exposure_rate_on_injected_fault_runs", [evidence_ref], ["Failure exposure is distinct from fault detection."], confidence),
        {
            "metric_id": "ERA-RUN-06",
            "status": "MEASURED" if durations or costs or tokens else "NOT_ASSESSED",
            "value": {
                "duration_seconds_median": median(durations) if durations else None,
                "duration_seconds_p95": _percentile(durations, 0.95),
                "cost_usd_median": median(costs) if costs else None,
                "total_tokens_median": median(tokens) if tokens else None,
                "cache_read_tokens_median": median(cache_read_tokens) if cache_read_tokens else None,
                "cache_write_tokens_median": median(cache_write_tokens) if cache_write_tokens else None,
                "model_steps_median": median(model_steps) if model_steps else None,
                "tool_calls_median": median([
                    record["cost"]["tool_calls"] for record in records
                    if record["cost"]["tool_calls"] is not None
                ]) if any(record["cost"]["tool_calls"] is not None for record in records) else None
            },
            "unit": "runtime_cost_profile",
            "numerator": None,
            "denominator": None,
            "interval": None,
            "evidence_refs": [evidence_ref],
            "limitations": ["Cost profiles are descriptive and depend on the runtime environment and accounting source."]
        }
    ]

    item_profiles = defaultdict(list)
    for record in outcome_rows:
        item_profiles[record["case_id"]].append(record["agent_outcome"] == "pass")
    if evaluation_purpose in {"capability", "both"}:
        metrics.append({
            "metric_id": "CAP-00",
            "status": "MEASURED" if item_profiles else "NOT_ASSESSED",
            "value": {
                case_id: {
                    "pass_rate": sum(values) / len(values),
                    "observed_runs": len(values)
                }
                for case_id, values in sorted(item_profiles.items())
            } if item_profiles else None,
            "unit": "empirical_item_pass_rate_by_case",
            "numerator": None,
            "denominator": None,
            "interval": None,
            "evidence_refs": [evidence_ref],
            "limitations": ["Descriptive item pass rates are not IRT difficulty or discrimination parameters."]
        })
        for metric_id, description in [
            ("CAP-01", "IRT item difficulty parameter not estimated; observed pass rates are only descriptive."),
            ("CAP-02", "IRT item discrimination not estimated."),
            ("CAP-03", "Test information function not estimated."),
            ("CAP-04", "Conditional measurement error not estimated."),
            ("CAP-05", "Ability estimate stability not estimated."),
            ("CAP-06", "Differential item functioning not assessed."),
            ("CAP-07", "External capability validity not assessed.")
        ]:
            metrics.append({
                "metric_id": metric_id,
                "status": "NOT_ASSESSED",
                "value": None,
                "unit": None,
                "numerator": None,
                "denominator": None,
                "interval": None,
                "evidence_refs": [],
                "limitations": [description, "Do not infer this metric from empirical pass rates alone."]
            })

    if evaluation_purpose in {"regression", "both"}:
        historical_exposure_rows = [record for record in historical_rows if record["fault"]["failure_exposed"] is not None]
        historical_exposed = sum(record["fault"]["failure_exposed"] is True for record in historical_exposure_rows)
        metrics.extend([
            rate_metric("REG-01", historical_detected, len(historical_rows), "historical_fault_detection_rate", [evidence_ref], ["Historical fault runs are counted at run-instance level; unique fault IDs are reported separately in the analysis metadata."], confidence),
            rate_metric("REG-02", mutation_detected, len(mutation_rows), "mutation_detection_rate", [evidence_ref], ["Mutation detection is not a substitute for real historical fault detection."], confidence),
            {
                "metric_id": "REG-03",
                "status": "MEASURED" if paired else "NOT_ASSESSED",
                "value": {
                    "candidate_minus_baseline_pass_rate": paired_delta,
                    "baseline_pass_to_candidate_fail": regressions,
                    "baseline_fail_to_candidate_pass": improvements,
                    "mcnemar_exact_two_sided_p": mcnemar_p
                } if paired else None,
                "unit": "paired_pass_rate_difference_and_mcnemar",
                "numerator": None,
                "denominator": len(paired) if paired else None,
                "interval": bootstrap_interval(
                    [
                        (1.0 if new["agent_outcome"] == "pass" else 0.0)
                        - (1.0 if old["agent_outcome"] == "pass" else 0.0)
                        for _, old, new in paired
                    ],
                    bootstrap_resamples,
                    bootstrap_seed
                ) if paired else None,
                "evidence_refs": [evidence_ref],
                "limitations": ["Pairs require one valid baseline and one valid candidate run for the same case and pair_id."]
            },
            {
                "metric_id": "REG-04",
                "status": "NOT_ASSESSED",
                "value": None,
                "unit": None,
                "numerator": None,
                "denominator": None,
                "interval": None,
                "evidence_refs": [],
                "limitations": ["Criticality classification and complete critical-risk universe are not encoded in runtime records."]
            },
            rate_metric("REG-06", flaky_groups, repeated_groups, "discordant_repeated_group_rate", [evidence_ref], ["This measures observed Agent outcome discordance within declared repeat groups; it does not identify the source of variance."], confidence),
            rate_metric("REG-07", historical_exposed, len(historical_exposure_rows), "historical_fault_failure_exposure_rate", [evidence_ref], ["This is limited to historical fault replays; shared all-fault exposure is reported as ERA-RUN-05."], confidence),
            {
                "metric_id": "REG-08",
                "status": "MEASURED" if fault_rows and any(record["cost"]["cost_usd"] is not None for record in fault_rows) and sum(record["fault"]["detected"] is True for record in fault_rows) > 0 else "NOT_ASSESSED",
                "value": (
                    sum(record["cost"]["cost_usd"] for record in fault_rows if record["cost"]["cost_usd"] is not None)
                    / sum(record["fault"]["detected"] is True for record in fault_rows)
                ) if fault_rows and any(record["cost"]["cost_usd"] is not None for record in fault_rows) and sum(record["fault"]["detected"] is True for record in fault_rows) > 0 else None,
                "unit": "usd_per_detected_fault_run",
                "numerator": None,
                "denominator": None,
                "interval": None,
                "evidence_refs": [evidence_ref],
                "limitations": ["Cost per detected fault depends on the selected fault set and accounting method."]
            }
        ])

    if evaluation_purpose in {"regression", "both"}:
        regression_status = "PARTIAL" if paired or historical_rows or mutation_rows else "NOT_RUN"
        regression_result = {
            "status": regression_status,
            "baseline_revision": baseline_revision,
            "candidate_revision": candidate_revision,
            "paired_case_count": len(paired),
            "historical_faults_replayed": len({record["fault"]["fault_id"] or record["run_id"] for record in historical_rows}),
            "mutants_replayed": len({record["fault"]["fault_id"] or record["run_id"] for record in mutation_rows}),
            "results_ref": evidence_ref,
            "limitations": [
                "No pass/fail acceptance threshold is applied.",
                "Historical fault replay and mutation detection are reported separately.",
                f"Incomplete or invalid pair IDs: {len(incomplete_pairs)}."
            ]
        }
    else:
        regression_result = None

    if evaluation_purpose in {"capability", "both"}:
        capability_result = {
            "status": "PARTIAL" if item_profiles else "NOT_RUN",
            "method": "descriptive per-item pass rates only; IRT and G-Theory are not fitted by this analyzer",
            "agent_configurations": len({record["configuration_id"] for record in records}),
            "task_count": len({record["case_id"] for record in records}),
            "results_ref": evidence_ref,
            "limitations": [
                "Item pass rates are descriptive and do not establish item discrimination or construct validity.",
                "IRT assumptions, local independence, DIF and measurement invariance have not been tested."
            ]
        }
    else:
        capability_result = None

    configurations = _configuration_map(records)
    runs = []
    for record in records:
        runs.append({
            "run_id": record["run_id"],
            "status": record["status"],
            "seed": record.get("seed"),
            "started_at": record["started_at"],
            "trace_ref": record.get("trace_ref"),
            "result_ref": record.get("result_ref"),
            "failure_class": record["status"] if record["status"] != "valid" else None,
            "case_id": record["case_id"],
            "configuration_id": record["configuration_id"],
            "target_revision": record["target_revision"],
            "agent_outcome": record["outcomes"]["agent_outcome"],
            "process_outcome": record["outcomes"]["process_outcome"],
            "grader_outcome": record["outcomes"]["grader_outcome"],
            "gold_outcome": record["outcomes"]["gold_outcome"],
            "pair_id": record.get("pair_id"),
            "repeat_group_id": record.get("repeat_group_id"),
            "fault_kind": record["fault"]["kind"],
            "fault_id": record["fault"].get("fault_id"),
            "fault_injected": record["fault"]["injected"],
            "fault_detected": record["fault"]["detected"],
            "failure_exposed": record["fault"]["failure_exposed"],
            "duration_seconds": record["cost"]["duration_seconds"],
            "input_tokens": record["cost"]["input_tokens"],
            "output_tokens": record["cost"]["output_tokens"],
            "tool_calls": record["cost"]["tool_calls"],
            "cost_usd": record["cost"]["cost_usd"]
        })

    grader_metrics = []
    if graded_gold_rows:
        grader_metrics = [
            {"metric_id": "ERA-GRD-01", "status": "MEASURED" if graded_gold_fail_rows else "NOT_ASSESSED", "value": false_passes / len(graded_gold_fail_rows) if graded_gold_fail_rows else None, "unit": "false_pass_rate", "interval": wilson_interval(false_passes, len(graded_gold_fail_rows), confidence) if graded_gold_fail_rows else None, "evidence_refs": [evidence_ref]},
            {"metric_id": "ERA-GRD-02", "status": "MEASURED" if graded_gold_pass_rows else "NOT_ASSESSED", "value": false_fails / len(graded_gold_pass_rows) if graded_gold_pass_rows else None, "unit": "false_fail_rate", "interval": wilson_interval(false_fails, len(graded_gold_pass_rows), confidence) if graded_gold_pass_rows else None, "evidence_refs": [evidence_ref]},
            {"metric_id": "ERA-GRD-03", "status": "MEASURED", "value": abstentions / len(graded_gold_rows), "unit": "abstention_rate", "interval": wilson_interval(abstentions, len(graded_gold_rows), confidence), "evidence_refs": [evidence_ref]},
            {"metric_id": "ERA-GRD-04", "status": "MEASURED" if judged_rows else "NOT_ASSESSED", "value": grader_correct / len(judged_rows) if judged_rows else None, "unit": "accuracy_on_non_abstained_gold_rows", "interval": wilson_interval(grader_correct, len(judged_rows), confidence) if judged_rows else None, "evidence_refs": [evidence_ref]}
        ]
    grader_status = "PARTIAL" if graded_gold_rows else "NOT_RUN"

    findings = []
    if not gold_rows:
        findings.append({
            "finding_id": "ERA-NO-GOLD",
            "severity": "high",
            "description": "No independent Oracle or expert-adjudicated gold outcomes were available for grader validation.",
            "evidence_refs": [evidence_ref]
        })
    if gold_rows and not graded_gold_rows:
        findings.append({
            "finding_id": "ERA-NO-GRADER",
            "severity": "medium",
            "description": "Independent Gold labels are available, but no Judge output is linked to these records; Judge error and abstention metrics are not assessed.",
            "evidence_refs": [evidence_ref]
        })
    if incomplete_pairs:
        findings.append({
            "finding_id": "ERA-INCOMPLETE-PAIRS",
            "severity": "medium",
            "description": f"{len(incomplete_pairs)} pair_id group(s) could not form one valid baseline/candidate pair.",
            "evidence_refs": [evidence_ref]
        })

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = {
        "schema_version": "0.0.2",
        "assessment_id": f"era-{dataset_id}-{hashlib.sha256(records_path.read_bytes()).hexdigest()[:12]}",
        "assessment_type": "empirical_runtime_assessment",
        "created_at": now,
        "dataset": {
            "dataset_id": dataset_id,
            "version": dataset_version,
            "sha256": digest
        },
        "evaluation_purpose": evaluation_purpose,
        "target": {
            "target_type": target_type,
            "name": target_name,
            "version": None,
            "revision": target_revision
        },
        "runtime_protocol": {
            "protocol_id": protocol_id,
            "model": model_summary,
            "harness": harness_summary,
            "environment": environment_summary,
            "tool_versions": tool_versions,
            "execution_parameters": {
                "confidence_level": confidence,
                "bootstrap_resamples": bootstrap_resamples,
                "bootstrap_seed": bootstrap_seed,
                "baseline_revision": baseline_revision,
                "candidate_revision": candidate_revision
            },
            "protocol_ref": str(records_path.name),
            "configurations": configurations
        },
        "runs": runs,
        "grader_validation": {
            "status": grader_status,
            "reference_standard": "Only independent_oracle and expert_adjudication gold_source records are used.",
            "sample_count": len(graded_gold_rows),
            "metric_results": grader_metrics,
            "limitations": [
                "A partial measurement is not a pass decision; no acceptance thresholds are applied.",
                "Human-Judge agreement requires human/expert labels and should be reported separately from automated Oracle labels."
            ]
        },
        "capability_analysis": capability_result,
        "regression_analysis": regression_result,
        "metric_results": metrics,
        "evidence_sufficiency": {
            "status": "partial" if valid_runs else "insufficient",
            "rationale": "Runtime records were analyzed; validity depends on protocol fidelity, independent gold labels, coverage and appropriate statistical assumptions.",
            "missing_evidence": [
                "independent Judge adjudication beyond supplied gold labels",
                "IRT model fit and measurement invariance",
                "G-Theory variance decomposition",
                "external real-task validation",
                "expert review of failure classifications"
            ]
        },
        "composite": {
            "status": "NOT_VALIDATED",
            "value": None,
            "model_id": None,
            "scope": None,
            "validation_report_ref": None,
            "limitations": ["No empirically validated composite formula, weights or thresholds are available."]
        },
        "findings": findings,
        "limitations": [
            "This analyzer summarizes supplied runtime records; it does not execute the Agent or Skill.",
            "Runtime record correctness and completeness must be independently audited.",
            "Agent, environment and Judge variability are not fully separated by this descriptive analyzer.",
            "Capability output is descriptive; IRT and G-Theory are not fitted.",
            "Regression pairing uses pair_id and requires one valid baseline and one valid candidate record per pair."
        ]
    }

    try:
        from .validate_quality_assessment import validate_report
    except ImportError:
        from validate_quality_assessment import validate_report
    contract_errors = validate_report(report)
    if contract_errors:
        raise ValueError("generated ERA report failed its schema/semantic contract: " + "; ".join(contract_errors))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True, type=Path, help="JSONL runtime records")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--target-name", required=True)
    parser.add_argument("--evaluation-purpose", required=True, choices=["capability", "regression", "both"])
    parser.add_argument("--baseline-revision")
    parser.add_argument("--candidate-revision")
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--bootstrap-resamples", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=2026)
    args = parser.parse_args()

    try:
        report = build_era_report(
            args.records,
            args.output,
            args.dataset_version,
            args.target_name,
            args.evaluation_purpose,
            args.baseline_revision,
            args.candidate_revision,
            args.confidence,
            args.bootstrap_resamples,
            args.bootstrap_seed
        )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print(f"Report written: {args.output}")
    print(f"Assessment: {report['assessment_id']}")
    print(f"Valid runs: {sum(run['status'] == 'valid' for run in report['runs'])}/{len(report['runs'])}")
    print("Composite score: NOT_VALIDATED (no value emitted)")
    print("NOTE: Runtime analysis is evidence for the declared scope, not a universal dataset quality score.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
