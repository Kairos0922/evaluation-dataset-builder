#!/usr/bin/env python3
"""Import blinded manual/LLM Judge observations into a v0.0.2 calibration report.

This importer validates structure, frozen suite identity and evidence references.
It never authenticates external reviewers or upgrades an empirical report to
VALIDATED_FOR_SCOPE; independent validation remains a separate decision.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "judge-calibration-observations.schema.json"
sys.path.insert(0, str(ROOT))
from scripts.validate_judge_calibration import validate_report


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value, raw


def build_report(observations: dict, suite_path: Path, observations_bytes: bytes,
                 *, run_id: str | None = None, commit_sha: str | None = None) -> dict:
    schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    input_errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(observations),
        key=lambda error: list(error.absolute_path),
    )
    if input_errors:
        raise ValueError("invalid observations: " + "; ".join(
            f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
            for error in input_errors
        ))

    suite_raw = suite_path.read_bytes()
    suite = json.loads(suite_raw.decode("utf-8"))
    dataset = observations["dataset"]
    if sha256_bytes(suite_raw) != dataset["suite_sha256"]:
        raise ValueError("dataset.suite_sha256 does not match frozen suite bytes")
    if suite.get("suite_id") != dataset["suite_id"]:
        raise ValueError("dataset.suite_id does not match frozen suite")
    suite_ids = [case.get("id") for case in suite.get("cases", []) if isinstance(case, dict)]
    case_ids = dataset["case_ids"]
    observation_rows = observations["observations"]
    result_ids = [item["case_id"] for item in observation_rows]
    if len(suite_ids) != len(set(suite_ids)) or set(case_ids) != set(suite_ids) or len(case_ids) != len(suite_ids):
        raise ValueError("dataset.case_ids must exactly match unique frozen suite case IDs")
    repeat_counts = Counter(result_ids)
    expected_repeats = observations["protocol"]["repeats_per_case"]
    if set(result_ids) != set(case_ids) or any(repeat_counts[case_id] != expected_repeats for case_id in case_ids):
        raise ValueError("observations must contain exactly protocol.repeats_per_case rows per frozen suite case_id")
    repeat_pairs = []
    for item in observation_rows:
        repeat_index = item.get("repeat_index") or 1
        if not isinstance(repeat_index, int) or repeat_index < 1 or repeat_index > expected_repeats:
            raise ValueError("repeat_index must be within protocol.repeats_per_case")
        repeat_pairs.append((item["case_id"], repeat_index))
    if len(repeat_pairs) != len(set(repeat_pairs)):
        raise ValueError("duplicate case_id/repeat_index observation pair")

    kind = observations["calibration_kind"]
    if kind == "synthetic_smoke":
        if dataset["label_source"] != "synthetic_fixture" or dataset["independent_gold"]:
            raise ValueError("synthetic_smoke requires synthetic_fixture labels and independent_gold=false")
        status = "NOT_VALIDATED"
    else:
        if dataset["label_source"] == "synthetic_fixture" or not dataset["independent_gold"]:
            raise ValueError("independent_empirical cannot use Builder/synthetic labels as Gold")
        if not dataset["held_out"] or not dataset["split_id"]:
            raise ValueError("independent_empirical requires a named held-out split")
        protocol = observations["protocol"]
        if not protocol["blinded"] or not protocol["independent_review"]:
            raise ValueError("independent_empirical requires blinded and independent review")
        if not observations["judge"]["separate_from_subject"]:
            raise ValueError("Judge must be independent from the evaluated subject")
        status = "PARTIAL"

    results = []
    for item in observations["observations"]:
        row = {key: item.get(key) for key in (
            "case_id", "gold_status", "judge_status", "evidence_validated",
            "output_sha256", "gold_evidence_ref", "judge_evidence_ref",
            "reviewer_id", "adjudicator_id",
        ) if key in item}
        row["repeat_index"] = item.get("repeat_index") or 1
        results.append(row)
    adjudicable = [item for item in results if item["gold_status"] in {"PASS", "FAIL"}]
    exact = sum(item["gold_status"] == item["judge_status"] for item in adjudicable)
    summary = {
        "case_count": len(results),
        "adjudicable_count": len(adjudicable),
        "exact_matches": exact,
        "false_passes": sum(item["gold_status"] == "FAIL" and item["judge_status"] == "PASS" for item in adjudicable),
        "false_fails": sum(item["gold_status"] == "PASS" and item["judge_status"] == "FAIL" for item in adjudicable),
        "abstentions": sum(item["judge_status"] == "UNKNOWN" for item in results),
        "accuracy": exact / len(adjudicable) if adjudicable else None,
    }
    protocol = dict(observations["protocol"])
    if run_id is not None:
        protocol["run_id"] = run_id
    if commit_sha is not None:
        protocol["commit_sha"] = commit_sha
    report = {
        "schema_version": "0.0.2",
        "report_id": "judge-calibration-" + sha256_bytes(suite_raw + observations_bytes)[:20],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "calibration_kind": kind,
        "status": status,
        "dataset": dataset,
        "judge": observations["judge"],
        "protocol": protocol,
        "results": results,
        "summary": summary,
        "source_observations_sha256": sha256_bytes(observations_bytes),
        "limitations": [
            "This importer validates structure, suite identity and declared evidence references; it cannot authenticate reviewer identity or the truth of external evidence.",
            "Independent empirical imports remain PARTIAL and are never automatically upgraded to VALIDATED_FOR_SCOPE.",
            "A held-out designation and blinding declaration must be independently audited against the actual review process.",
        ],
    }
    errors = validate_report(report, suite_path)
    if errors:
        raise ValueError("generated report failed validation: " + "; ".join(errors))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True, type=Path)
    parser.add_argument("--observations", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--commit-sha")
    args = parser.parse_args()
    try:
        source, raw = load_json(args.observations)
        report = build_report(source, args.suite, raw, run_id=args.run_id, commit_sha=args.commit_sha)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"FAIL: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(report['results'])} Judge observations; status={report['status']}; accuracy={report['summary']['accuracy']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
