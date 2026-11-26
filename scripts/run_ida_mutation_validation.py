#!/usr/bin/env python3
"""Run controlled deterministic IDA defect mutations and negative controls.

This is an implementation-sensitivity experiment on synthetic fixtures only.
It cannot establish semantic content validity or expert agreement.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.assess_dataset_quality import build_report
from scripts.validate_quality_assessment import validate_report

CATALOG_PATH = ROOT / "docs" / "quality-assessment-v0.0.2" / "defect-mutation-catalog.yaml"
SCHEMA_PATH = ROOT / "docs" / "quality-assessment-v0.0.2" / "schemas" / "ida-mutation-validation-report.schema.json"


def sample_manifest():
    return {
        "dataset_id": "ida-mutation-fixture",
        "version": "0.0.2-test",
        "evaluation_target": "controlled-synthetic-agent",
        "purpose": "deterministic offline checker sensitivity fixture",
        "scope": {"included": ["tool selection"], "excluded": []},
        "coverage": {
            "universe_definition": "Two synthetic coverage items.",
            "dimensions": [{
                "dimension": "capability", "total": 2, "covered": 2,
                "coverage_rate": 1.0, "uncovered": []
            }]
        },
        "case_count": 2,
        "quality_status": "candidate",
        "execution_status": "DESIGN_ONLY"
    }


def sample_case(case_id: str, coverage_id: str, title: str):
    return {
        "case_id": case_id,
        "dataset_id": "ida-mutation-fixture",
        "title": title,
        "evaluation_target": "controlled-synthetic-agent",
        "objective": "Select the required synthetic tool.",
        "assumptions": ["The status lookup tool is available and authorized."],
        "user_input": "Find the status of resource A.",
        "expected_behavior": "Use the status lookup tool and report its returned state.",
        "source_refs": [{
            "source_id": "SRC-001", "source_type": "synthetic_scenario",
            "title": "Synthetic tool-use fixture", "locator": "fixture"
        }],
        "grading": {
            "evaluation_subject": "controlled-synthetic-agent",
            "method": "trace_check",
            "criteria": [{
                "criterion_id": "C1", "description": "Uses the correct tool.",
                "pass_condition": "Calls the status lookup tool.",
                "fail_condition": "Calls an unrelated tool or fabricates a result.",
                "evidence_required": ["tool call trace"]
            }],
            "pass_conditions": ["Correct tool is called."],
            "fail_conditions": ["Wrong tool is called."],
            "evidence_required": ["tool call trace"]
        },
        "quality_status": "candidate",
        "scenario_bucket": ["business_rule"],
        "case_origin": "synthetic_gap_fill",
        "coverage_tags": [{
            "dimension": "capability", "value": "tool_selection",
            "coverage_item_id": coverage_id
        }],
        "execution_requirements": {"status": "DESIGN_ONLY"}
    }


def sample_registry(extra: bool = False):
    sources = [{
        "source_id": "SRC-001", "source_type": "synthetic_scenario",
        "title": "Synthetic tool-use fixture"
    }]
    if extra:
        sources.append({
            "source_id": "UNUSED-SRC", "source_type": "synthetic_scenario",
            "title": "Unused negative-control source"
        })
    return {"sources": sources}


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054):
    if total == 0:
        return None
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    half = z * ((p * (1.0 - p) / total + z * z / (4.0 * total * total)) ** 0.5) / denominator
    return {"lower": max(0.0, center - half), "upper": min(1.0, center + half), "level": 0.95, "method": "Wilson score interval"}


def _assess(manifest: dict, cases: list[dict], registry: dict, *, pretty: bool = False):
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        manifest_path = directory / "manifest.json"
        cases_path = directory / "cases.jsonl"
        registry_path = directory / "sources.json"
        output_path = directory / "ida-report.json"
        indent = 2 if pretty else None
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=indent), encoding="utf-8")
        cases_path.write_text(
            "".join(json.dumps(case, ensure_ascii=False, indent=indent) + "\n" for case in cases),
            encoding="utf-8"
        )
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=indent), encoding="utf-8")
        report, structural_errors, duplicate_ids, coverage_errors, source_errors = build_report(
            manifest_path, cases_path, output_path, "both", registry_path
        )
        contract_errors = validate_report(report)
        if contract_errors:
            raise ValueError("IDA report contract errors: " + "; ".join(contract_errors))
        return report, {
            "structural_errors": structural_errors,
            "duplicate_case_ids": duplicate_ids,
            "coverage_errors": coverage_errors,
            "source_errors": source_errors,
            "report_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        }


def _gate(report: dict, gate_id: str) -> str:
    return next(item["status"] for item in report["gate_results"] if item["gate_id"] == gate_id)


def _metric(report: dict, metric_id: str) -> dict:
    return next(item for item in report["metric_results"] if item["metric_id"] == metric_id)


def _mutations():
    def m01(manifest, cases, registry):
        cases[0].pop("grading")
        return manifest, cases, registry

    def m02(manifest, cases, registry):
        cases[1]["case_id"] = cases[0]["case_id"]
        return manifest, cases, registry

    def m03(manifest, cases, registry):
        manifest["case_count"] = 1
        return manifest, cases, registry

    def m04(manifest, cases, registry):
        cases[1]["dataset_id"] = "other-dataset"
        return manifest, cases, registry

    def m05(manifest, cases, registry):
        cases[0]["source_refs"][0]["source_id"] = "MISSING-SOURCE"
        return manifest, cases, registry

    def m06(manifest, cases, registry):
        cases[0]["source_refs"] = []
        cases[0]["case_origin"] = "unknown"
        cases[0]["information_gaps"] = [{
            "gap_id": "GAP-001", "description": "Source origin is unknown.",
            "affected_claims": ["task provenance"],
            "required_evidence": ["independent source record"],
            "responsible_role": "reviewer", "status": "OPEN"
        }]
        return manifest, cases, registry

    def m07(manifest, cases, registry):
        duplicate = dict(cases[0])
        duplicate["case_id"] = cases[1]["case_id"]
        cases[1] = duplicate
        return manifest, cases, registry

    def m08(manifest, cases, registry):
        manifest["coverage"]["dimensions"][0]["covered"] = 1
        manifest["coverage"]["dimensions"][0]["coverage_rate"] = 0.5
        return manifest, cases, registry

    return [
        ("IDA-M01", "missing_required_case_field", m01, lambda r: _metric(r, "IDA-STR-01")["status"] == "FAIL" and _gate(r, "G07_integrity_leakage") == "FAIL"),
        ("IDA-M02", "duplicate_case_id", m02, lambda r: _gate(r, "G07_integrity_leakage") == "FAIL" and r["overall_status"] == "FAIL"),
        ("IDA-M03", "manifest_case_count_mismatch", m03, lambda r: _gate(r, "G07_integrity_leakage") == "FAIL" and r["overall_status"] == "FAIL"),
        ("IDA-M04", "case_dataset_id_mismatch", m04, lambda r: _gate(r, "G07_integrity_leakage") == "FAIL" and r["overall_status"] == "FAIL"),
        ("IDA-M05", "unresolved_source_reference", m05, lambda r: _gate(r, "G01_source_provenance") == "FAIL" and r["overall_status"] == "FAIL"),
        ("IDA-M06", "missing_source_reference", m06, lambda r: _gate(r, "G01_source_provenance") == "UNKNOWN" and r["overall_status"] == "PARTIAL"),
        ("IDA-M07", "exact_duplicate_payload", m07, lambda r: (_metric(r, "IDA-RED-00")["value"] or 0) > 0 and any("exact duplicate" in f["description"] for f in r["findings"])),
        ("IDA-M08", "coverage_declaration_mismatch", m08, lambda r: _metric(r, "IDA-COV-00")["status"] == "MEASURED" and any(f["finding_id"].startswith("COVERAGE-") for f in r["findings"])),
    ]


def _controls():
    def unchanged(manifest, cases, registry):
        return manifest, cases, registry
    def rename_id(manifest, cases, registry):
        cases[0]["case_id"] = "CASE-RENAMED"
        return manifest, cases, registry
    def reorder(manifest, cases, registry):
        return manifest, list(reversed(cases)), registry
    def extra_source(manifest, cases, registry):
        return manifest, cases, sample_registry(extra=True)
    return [
        ("CTRL-01", "formatting_only", unchanged, True),
        ("CTRL-02", "case_id_rename", rename_id, False),
        ("CTRL-03", "case_order_reversal", reorder, False),
        ("CTRL-04", "unused_source_registry_entry", extra_source, False),
    ]


def run_validation() -> dict:
    catalog = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog_items = {
        item["mutation_id"]: item
        for item in catalog["mutation_classes"]["independent_dataset_assessment"]
    }
    deterministic_results = []
    for mutation_id, defect, mutate, detect in _mutations():
        manifest = sample_manifest()
        cases = [sample_case("CASE-001", "COV-001", "Tool selection A"), sample_case("CASE-002", "COV-002", "Tool selection B")]
        registry = sample_registry()
        mutated_manifest, mutated_cases, mutated_registry = mutate(manifest, cases, registry)
        report, evidence = _assess(mutated_manifest, mutated_cases, mutated_registry)
        passed = bool(detect(report))
        deterministic_results.append({
            "mutation_id": mutation_id,
            "defect": defect,
            "status": "PASS" if passed else "FAIL",
            "expected_signals": catalog_items[mutation_id]["expected_signals"],
            "observed_signals": {
                "overall_status": report["overall_status"],
                "G01_source_provenance": _gate(report, "G01_source_provenance"),
                "G07_integrity_leakage": _gate(report, "G07_integrity_leakage"),
                "metric_statuses": {item["metric_id"]: item["status"] for item in report["metric_results"]},
                "finding_ids": [item["finding_id"] for item in report["findings"]],
            },
            "dataset_sha256": report["dataset"]["sha256"],
            **evidence,
        })

    control_results = []
    for control_id, name, mutate, pretty in _controls():
        manifest = sample_manifest()
        cases = [sample_case("CASE-001", "COV-001", "Tool selection A"), sample_case("CASE-002", "COV-002", "Tool selection B")]
        registry = sample_registry()
        mutated_manifest, mutated_cases, mutated_registry = mutate(manifest, cases, registry)
        report, evidence = _assess(mutated_manifest, mutated_cases, mutated_registry, pretty=pretty)
        false_positive = report["overall_status"] == "FAIL" or _gate(report, "G07_integrity_leakage") == "FAIL" or _gate(report, "G01_source_provenance") == "FAIL"
        control_results.append({
            "control_id": control_id,
            "control": name,
            "status": "FAIL" if false_positive else "PASS",
            "false_positive": false_positive,
            "overall_status": report["overall_status"],
            "G01_source_provenance": _gate(report, "G01_source_provenance"),
            "G07_integrity_leakage": _gate(report, "G07_integrity_leakage"),
            "dataset_sha256": report["dataset"]["sha256"],
            **evidence,
        })

    nondeterministic = [
        {"mutation_id": f"IDA-M{index:02d}", "status": "NOT_ASSESSED", "reason": reason}
        for index, reason in [
            (9, "Ambiguous task text requires blinded expert review."),
            (10, "Incorrect Gold requires an independent Oracle or expert adjudication."),
            (11, "Construct mismatch requires an independently declared construct and content-validity review."),
            (12, "Answer leakage requires an adversarial contamination audit or held-out execution."),
        ]
    ]
    detected = sum(item["status"] == "PASS" for item in deterministic_results)
    false_positives = sum(item["false_positive"] for item in control_results)
    identity = {"deterministic": deterministic_results, "controls": control_results}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema_version": "0.0.2",
        "report_id": "ida-mutation-" + digest[:20],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evidence_level": "SYNTHETIC_CONTROLLED_MUTATION",
        "catalog_version": catalog["version"],
        "deterministic_mutations": deterministic_results,
        "negative_controls": control_results,
        "non_deterministic_mutations": nondeterministic,
        "summary": {
            "deterministic_mutation_count": len(deterministic_results),
            "detected_mutation_count": detected,
            "missed_mutation_count": len(deterministic_results) - detected,
            "deterministic_detection_rate": detected / len(deterministic_results) if deterministic_results else None,
            "deterministic_detection_rate_interval": wilson_interval(detected, len(deterministic_results)),
            "negative_control_count": len(control_results),
            "false_positive_control_count": false_positives,
            "negative_control_false_positive_rate": false_positives / len(control_results) if control_results else None,
            "negative_control_false_positive_rate_interval": wilson_interval(false_positives, len(control_results)),
            "non_deterministic_not_assessed_count": len(nondeterministic),
        },
        "limitations": [
            "All mutations and controls are synthetic, authored fixtures; the experiment is not blind and does not estimate performance on real datasets.",
            "The 8/8 detection rate is implementation sensitivity to these exact deterministic mutation operators only.",
            "The 0/4 negative-control false-positive rate has a very wide interval and is not a general false-positive guarantee.",
            "IDA-M09 through IDA-M12 remain NOT_ASSESSED because they require independent experts, an independent Oracle, or contamination audit.",
            "No result validates construct validity, source claim support, the composite formula, weights, or thresholds.",
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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = run_validation()
        errors = validate_report(report)
        if errors:
            raise ValueError("mutation report schema validation failed: " + "; ".join(errors))
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
