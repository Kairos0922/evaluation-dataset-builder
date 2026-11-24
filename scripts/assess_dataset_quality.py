#!/usr/bin/env python3
"""Create a conservative, offline IDA report from a dataset manifest and JSONL cases."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SKILL_REFERENCES = ROOT / "skills" / "evaluation-dataset-builder" / "references"
MANIFEST_SCHEMA = SKILL_REFERENCES / "dataset-manifest-schema.json"
CASE_SCHEMA = SKILL_REFERENCES / "dataset-schema.json"
SCHEMA_CACHE = {}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(instance, schema_path: Path) -> list[str]:
    validator = SCHEMA_CACHE.get(schema_path)
    if validator is None:
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        SCHEMA_CACHE[schema_path] = validator
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    cases = []
    errors = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            errors.append(f"line {line_number}: blank JSONL line")
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"line {line_number}: case must be a JSON object")
            continue
        cases.append(value)
    return cases, errors


def dataset_digest(manifest_bytes: bytes, cases_bytes: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(b"evaluation-dataset-builder-ida-v0.0.2\0")
    digest.update(manifest_bytes)
    digest.update(b"\0")
    digest.update(cases_bytes)
    return digest.hexdigest()


def canonical_case_fingerprint(case: dict) -> str:
    normalized = {key: value for key, value in case.items() if key != "case_id"}
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_source_registry(path: Path | None):
    if path is None:
        return None
    data = load_json(path)
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict) and isinstance(data.get("sources"), list):
        entries = data["sources"]
    elif isinstance(data, dict):
        entries = [
            dict(value, source_id=key) if isinstance(value, dict) else {"source_id": key}
            for key, value in data.items()
        ]
    else:
        raise ValueError("source registry must be a list, a {sources: []} object, or an ID-keyed object")
    registry = {}
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("source_id"):
            raise ValueError("every source registry entry must contain source_id")
        if entry["source_id"] in registry:
            raise ValueError(f"duplicate source_id in registry: {entry['source_id']}")
        registry[entry["source_id"]] = entry
    return registry


def check_source_references(cases: list[dict], registry: dict | None):
    if registry is None:
        return "UNKNOWN", 0, 0, ["No independent source registry was supplied."]
    references = []
    for case in cases:
        for source in case.get("source_refs", []):
            references.append((case.get("case_id", "<unknown>"), source))
    if not references:
        return "UNKNOWN", 0, 0, ["No case-level source references were supplied."]
    unresolved = []
    for case_id, source in references:
        source_id = source.get("source_id")
        registered = registry.get(source_id)
        if not source_id or registered is None:
            unresolved.append(f"{case_id}: unresolved source_id {source_id!r}")
            continue
        if registered.get("title") and registered["title"] != source.get("title"):
            unresolved.append(f"{case_id}: title mismatch for {source_id}")
        if registered.get("source_type") and registered["source_type"] != source.get("source_type"):
            unresolved.append(f"{case_id}: source_type mismatch for {source_id}")
    if unresolved:
        return "FAIL", len(references) - len(unresolved), len(references), unresolved
    return "PASS", len(references), len(references), []


def coverage_summary(manifest: dict, cases: list[dict]):
    actual = defaultdict(set)
    for case in cases:
        for tag in case.get("coverage_tags", []):
            dimension = tag.get("dimension")
            item_id = tag.get("coverage_item_id")
            if dimension and item_id:
                actual[dimension].add(item_id)

    declared = []
    inconsistencies = []
    for item in manifest.get("coverage", {}).get("dimensions", []):
        dimension = item.get("dimension")
        if not dimension:
            continue
        actual_count = len(actual.get(dimension, set()))
        total = item.get("total")
        covered = item.get("covered")
        rate = item.get("coverage_rate")
        if covered is not None and covered != actual_count:
            inconsistencies.append(
                f"{dimension}: manifest covered={covered}, observed unique coverage_item_id={actual_count}"
            )
        if isinstance(total, int) and total > 0 and isinstance(covered, int) and rate is not None:
            expected_rate = covered / total
            if abs(rate - expected_rate) > 1e-9:
                inconsistencies.append(
                    f"{dimension}: coverage_rate={rate}, expected covered/total={expected_rate}"
                )
        if total == 0 and rate is not None:
            inconsistencies.append(f"{dimension}: total=0 requires coverage_rate=null")
        declared.append({
            "dimension": dimension,
            "declared_total": total,
            "declared_covered": covered,
            "observed_unique_coverage_items": actual_count,
            "observed_case_tag_count": sum(
                1 for case in cases for tag in case.get("coverage_tags", [])
                if tag.get("dimension") == dimension
            )
        })
    for dimension, item_ids in sorted(actual.items()):
        if dimension not in {item.get("dimension") for item in manifest.get("coverage", {}).get("dimensions", [])}:
            declared.append({
                "dimension": dimension,
                "declared_total": None,
                "declared_covered": None,
                "observed_unique_coverage_items": len(item_ids),
                "observed_case_tag_count": sum(
                    1 for case in cases for tag in case.get("coverage_tags", [])
                    if tag.get("dimension") == dimension
                )
            })
            inconsistencies.append(f"{dimension}: case tags contain a dimension not declared in manifest")
    return declared, inconsistencies


def metric(metric_id, status, value, unit, evidence_refs, limitations, numerator=None, denominator=None, notes=None):
    return {
        "metric_id": metric_id,
        "status": status,
        "value": value,
        "unit": unit,
        "numerator": numerator,
        "denominator": denominator,
        "interval": None,
        "evidence_refs": evidence_refs,
        "limitations": limitations,
        "notes": notes or ""
    }


def build_report(manifest_path: Path, cases_path: Path, output_path: Path, evaluation_purpose: str, source_registry_path: Path | None = None):
    manifest_bytes = manifest_path.read_bytes()
    cases_bytes = cases_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    cases, parse_errors = load_jsonl(cases_path)
    manifest_errors = validate_schema(manifest, MANIFEST_SCHEMA)
    case_errors = []
    valid_case_count = 0
    for index, case in enumerate(cases, start=1):
        errors = validate_schema(case, CASE_SCHEMA)
        if not errors:
            valid_case_count += 1
        case_errors.extend(
            f"case[{index}] {case.get('case_id', '<missing-id>')}: {error}"
            for error in errors
        )

    dataset_id = manifest.get("dataset_id", "unknown")
    version = manifest.get("version", "unknown")
    digest = dataset_digest(manifest_bytes, cases_bytes)
    case_ids = [case.get("case_id") for case in cases]
    duplicate_ids = sorted({case_id for case_id in case_ids if case_ids.count(case_id) > 1})
    dataset_mismatches = [
        case.get("case_id", "<missing-id>")
        for case in cases if case.get("dataset_id") != dataset_id
    ]
    fingerprints = Counter(canonical_case_fingerprint(case) for case in cases)
    duplicate_fingerprints = {fingerprint: count for fingerprint, count in fingerprints.items() if count > 1}
    exact_duplicate_case_count = sum(count - 1 for count in duplicate_fingerprints.values())

    scenario_counts = Counter(
        bucket
        for case in cases
        for bucket in case.get("scenario_bucket", [])
    )
    source_case_count = sum(bool(case.get("source_refs")) for case in cases)
    source_reference_count = sum(len(case.get("source_refs", [])) for case in cases)
    criteria_count = sum(
        len(case.get("grading", {}).get("criteria", []))
        for case in cases
    )
    coverage, coverage_errors = coverage_summary(manifest, cases)
    registry = load_source_registry(source_registry_path)
    source_status, resolved_sources, total_sources, source_errors = check_source_references(cases, registry)

    structural_errors = manifest_errors + case_errors + parse_errors
    count_mismatch = manifest.get("case_count") != len(cases)
    if count_mismatch:
        structural_errors.append(
            f"manifest case_count={manifest.get('case_count')} but JSONL contains {len(cases)} cases"
        )

    dataset_id_integrity_ok = not duplicate_ids and not dataset_mismatches and not count_mismatch
    schema_ok = not structural_errors
    source_presence_rate = source_case_count / len(cases) if cases else None
    exact_duplicate_rate = exact_duplicate_case_count / len(cases) if cases else None

    evidence_refs = [
        f"file://{manifest_path.name}",
        f"file://{cases_path.name}",
        f"sha256:{digest}"
    ]
    if source_registry_path:
        evidence_refs.append(f"file://{source_registry_path.name}")

    findings = []
    for error in structural_errors:
        findings.append({
            "finding_id": f"STRUCT-{len(findings) + 1:03d}",
            "severity": "high",
            "description": error,
            "evidence_refs": evidence_refs,
            "affected_case_ids": [],
            "recommendation": "修复结构、Schema 或清单与用例之间的不一致后重新评价。"
        })
    for case_id in duplicate_ids:
        findings.append({
            "finding_id": f"INTEGRITY-{len(findings) + 1:03d}",
            "severity": "critical",
            "description": f"Duplicate case_id: {case_id}",
            "evidence_refs": evidence_refs,
            "affected_case_ids": [case_id],
            "recommendation": "为每条用例分配唯一稳定标识，并检查是否存在重复记录。"
        })
    for case_id in dataset_mismatches:
        findings.append({
            "finding_id": f"DATASET-ID-{len(findings) + 1:03d}",
            "severity": "high",
            "description": f"Case {case_id} has a dataset_id that does not match the manifest.",
            "evidence_refs": evidence_refs,
            "affected_case_ids": [case_id],
            "recommendation": "统一用例和清单中的 dataset_id。"
        })
    for error in coverage_errors:
        findings.append({
            "finding_id": f"COVERAGE-{len(findings) + 1:03d}",
            "severity": "medium",
            "description": error,
            "evidence_refs": evidence_refs,
            "affected_case_ids": [],
            "recommendation": "核对覆盖全集、用例标签和清单统计；不要用不一致的统计声称覆盖完成。"
        })
    for error in source_errors:
        findings.append({
            "finding_id": f"SOURCE-{len(findings) + 1:03d}",
            "severity": "high",
            "description": error,
            "evidence_refs": evidence_refs,
            "affected_case_ids": [],
            "recommendation": "修复 source_id、标题或来源类型映射，并由独立审查确认来源支持相关主张。"
        })
    if exact_duplicate_case_count:
        findings.append({
            "finding_id": f"REDUNDANCY-{len(findings) + 1:03d}",
            "severity": "medium",
            "description": f"Found {exact_duplicate_case_count} exact duplicate case payload(s) after excluding case_id.",
            "evidence_refs": evidence_refs,
            "affected_case_ids": [],
            "recommendation": "人工确认重复簇，判断是否有意重复采样；本检查不识别语义重复。"
        })
    if cases and source_case_count < len(cases):
        findings.append({
            "finding_id": f"SOURCE-PRESENCE-{len(findings) + 1:03d}",
            "severity": "high",
            "description": f"{len(cases) - source_case_count} case(s) have no source_refs.",
            "evidence_refs": evidence_refs,
            "affected_case_ids": [
                case.get("case_id", "<missing-id>")
                for case in cases if not case.get("source_refs")
            ],
            "recommendation": "补充可追溯来源或明确的合成/推断来源，并说明其适用边界。"
        })

    case_schema_ok = not case_errors and not parse_errors
    critical_gate_fail = bool(not schema_ok or duplicate_ids or dataset_mismatches or count_mismatch)
    gates = [
        {
            "gate_id": "G01_source_provenance",
            "status": source_status,
            "severity": "critical",
            "rationale": (
                "Source IDs and identity fields resolve against the supplied registry; this does not prove claim support."
                if registry is not None and source_status == "PASS"
                else "Source identity/claim support cannot be independently established without a source registry and source review."
            ),
            "evidence_refs": evidence_refs
        },
        {
            "gate_id": "G02_construct_alignment",
            "status": "NOT_ASSESSED",
            "severity": "critical",
            "rationale": "Requires an independent review of whether tasks measure their declared target construct.",
            "evidence_refs": []
        },
        {
            "gate_id": "G03_task_solvability",
            "status": "NOT_ASSESSED",
            "severity": "critical",
            "rationale": "No Oracle or independent human execution was performed by this offline checker.",
            "evidence_refs": []
        },
        {
            "gate_id": "G04_ground_truth_validity",
            "status": "NOT_ASSESSED",
            "severity": "critical",
            "rationale": "Ground Truth correctness requires independent source/Oracle verification.",
            "evidence_refs": []
        },
        {
            "gate_id": "G05_rubric_validity",
            "status": "FAIL" if any("grading" in error.lower() for error in case_errors) else "UNKNOWN",
            "severity": "critical",
            "rationale": "Schema and presence checks do not prove semantic alignment or grading validity.",
            "evidence_refs": evidence_refs
        },
        {
            "gate_id": "G06_safety_authorization",
            "status": "NOT_ASSESSED",
            "severity": "critical",
            "rationale": "Safety, authorization and side-effect constraints require contextual expert review.",
            "evidence_refs": []
        },
        {
            "gate_id": "G07_integrity_leakage",
            "status": "FAIL" if critical_gate_fail else "UNKNOWN",
            "severity": "critical",
            "rationale": (
                "Case ID, dataset ID or manifest case-count integrity failed."
                if critical_gate_fail
                else "Basic identifiers were checked, but leakage/contamination and source independence were not tested."
            ),
            "evidence_refs": evidence_refs
        },
        {
            "gate_id": "G08_runtime_auditability",
            "status": "NOT_APPLICABLE",
            "severity": "high",
            "rationale": "IDA does not execute the target Agent; runtime auditability belongs to ERA.",
            "evidence_refs": []
        }
    ]

    metrics = [
        metric(
            "IDA-STR-00",
            "PASS" if not manifest_errors else "FAIL",
            1.0 if not manifest_errors else 0.0,
            "manifest_schema_conformance",
            evidence_refs,
            ["Manifest schema conformance does not prove that declared facts are true."],
            1 if not manifest_errors else 0,
            1
        ),
        metric(
            "IDA-STR-01",
            ("NOT_APPLICABLE" if not cases else "PASS" if schema_ok else "FAIL"),
            valid_case_count / len(cases) if cases else None,
            "proportion_of_cases_passing_schema",
            evidence_refs,
            ["Schema conformance does not prove semantic validity."],
            valid_case_count,
            len(cases)
        ),
        metric(
            "IDA-STR-02",
            ("NOT_APPLICABLE" if not cases else "PASS" if dataset_id_integrity_ok else "FAIL"),
            (len(set(case_ids)) / len(case_ids)) if case_ids else None,
            "unique_case_id_proportion",
            evidence_refs,
            ["This checks identifiers and manifest consistency, not semantic duplicate cases."],
            len(set(case_ids)),
            len(case_ids)
        ),
        metric(
            "IDA-EVD-00",
            "MEASURED" if cases else "NOT_APPLICABLE",
            source_presence_rate,
            "case_source_reference_presence",
            evidence_refs,
            ["Presence of source_refs does not establish source authenticity or claim support."],
            source_case_count,
            len(cases)
        ),
        metric(
            "IDA-COV-00",
            "MEASURED",
            coverage,
            "coverage_consistency_profile",
            evidence_refs,
            ["Counts and internal consistency do not prove that the declared coverage universe is complete or representative."]
        ),
        metric(
            "IDA-DIV-01",
            "MEASURED",
            dict(sorted(scenario_counts.items())),
            "case_count_by_scenario_bucket",
            evidence_refs,
            ["Distribution is descriptive; uniform distribution is not assumed to be desirable."]
        ),
        metric(
            "IDA-RED-00",
            "MEASURED" if cases else "NOT_APPLICABLE",
            exact_duplicate_rate,
            "exact_duplicate_payload_rate_excluding_case_id",
            evidence_refs,
            ["This is exact canonical-payload duplication only; semantic redundancy requires separate review."],
            exact_duplicate_case_count,
            len(cases)
        ),
        metric(
            "IDA-RUB-00",
            "MEASURED",
            {"criterion_count": criteria_count, "case_count": len(cases)},
            "grading_criteria_inventory",
            evidence_refs,
            ["Criterion count is descriptive and does not establish rubric completeness or validity."]
        )
    ]

    overall_status = (
        "NOT_ASSESSED" if not cases
        else "FAIL" if not schema_ok or not dataset_id_integrity_ok or critical_gate_fail
        else "PARTIAL"
    )
    evidence_status = "insufficient" if not cases or not schema_ok else "partial"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = {
        "schema_version": "0.0.2",
        "assessment_id": f"ida-{dataset_id}-{digest[:12]}",
        "assessment_type": "independent_dataset_assessment",
        "created_at": now,
        "dataset": {
            "dataset_id": dataset_id,
            "version": version,
            "sha256": digest,
            "case_count": len(cases),
            "manifest_ref": manifest_path.name
        },
        "evaluation_purpose": evaluation_purpose,
        "assessor": {
            "name": "offline-dataset-quality-assessor",
            "version": "0.0.2",
            "independence": "same_author",
            "review_protocol_ref": "docs/quality-assessment-v0.0.2/methodology-design.md"
        },
        "overall_status": overall_status,
        "gate_results": gates,
        "metric_results": metrics,
        "evidence_sufficiency": {
            "status": evidence_status,
            "rationale": "Automated structural checks completed; semantic expert review and runtime evidence are not included in this assessment.",
            "missing_evidence": [
                "independent construct-alignment review",
                "Oracle or independent solvability evidence",
                "Ground Truth claim-support review",
                "rubric semantic validity review",
                "safety and authorization review",
                "leakage and contamination audit",
                "real Agent runtime evidence"
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
            "This tool performs deterministic offline checks only.",
            "It does not establish source claim support, construct validity, task solvability, Ground Truth correctness or semantic rubric validity.",
            "It does not execute the target Agent or Skill.",
            "It does not assess semantic duplicates or contamination.",
            "The dataset digest is SHA-256 over a versioned prefix, raw manifest bytes, a NUL separator and raw JSONL bytes."
        ],
        "not_assessed": [
            "construct_alignment",
            "task_solvability",
            "ground_truth_validity",
            "rubric_semantic_validity",
            "safety_authorization",
            "leakage_contamination",
            "capability_measurement",
            "regression_fault_detection",
            "runtime_reliability"
        ],
        "not_applicable": ["runtime_auditability_in_IDA"]
    }

    if source_registry_path:
        report["limitations"].append("Source registry identity resolution was performed; claim support still requires independent review.")

    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report, structural_errors, duplicate_ids, coverage_errors, source_errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path, help="JSONL file with one case object per line")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--evaluation-purpose", required=True, choices=["capability", "regression", "both"])
    parser.add_argument("--source-registry", type=Path, help="Optional independent JSON source registry")
    args = parser.parse_args()

    try:
        report, structural_errors, duplicate_ids, coverage_errors, source_errors = build_report(
            args.manifest, args.cases, args.output, args.evaluation_purpose, args.source_registry
        )
    except Exception as exc:
        print(f"FAIL: could not assess dataset: {exc}", file=sys.stderr)
        return 2

    print(f"Report written: {args.output}")
    print(f"Assessment: {report['overall_status']}; evidence: {report['evidence_sufficiency']['status']}")
    print(f"Cases: {report['dataset']['case_count']}; SHA-256: {report['dataset']['sha256']}")
    print("Composite score: NOT_VALIDATED (no value emitted)")
    if structural_errors or duplicate_ids or coverage_errors or source_errors:
        print("Findings detected; inspect the report for details.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
