#!/usr/bin/env python3
"""离线验证 Benchmark 契约、跨文件引用和实验统计。"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
CASE_SCHEMA_PATH = ROOT / "skills/evaluation-dataset-builder/references/dataset-schema.json"


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _validate_schema(value, schema_path, label, errors):
    validator = Draft202012Validator(load_json(schema_path))
    for error in sorted(validator.iter_errors(value), key=lambda item: list(map(str, item.path))):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"SCHEMA:{label}:{location}:{error.message}")


def _index(items, key, label, errors):
    result = {}
    for item in items:
        identifier = item.get(key)
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"MISSING_ID:{label}:{key}")
            continue
        if identifier in result:
            errors.append(f"DUPLICATE_ID:{label}:{identifier}")
        result[identifier] = item
    return result


def validate_package(package):
    errors = []
    if not isinstance(package, dict):
        return {"status": "ERROR", "errors": ["Benchmark package root must be an object"], "statistics": {}}
    required = ["task", "ground_truth", "dataset_manifest", "cases", "defect_specs", "defect_instances", "runs", "coverage_validations"]
    for field in required:
        if field not in package:
            errors.append(f"MISSING_COLLECTION:{field}")
    if errors:
        return {"status": "FAIL", "errors": errors, "statistics": {}}

    task, gt, manifest = package["task"], package["ground_truth"], package["dataset_manifest"]
    cases, defects = package["cases"], package["defect_specs"]
    instances, runs, coverage_records = package["defect_instances"], package["runs"], package["coverage_validations"]
    for value, name, label in [(task, "task.schema.json", "task"), (gt, "ground-truth.schema.json", "ground_truth")]:
        _validate_schema(value, SCHEMA_DIR / name, label, errors)
    for label, values, schema_name in [
        ("defect", defects, "defect.schema.json"),
        ("defect_instance", instances, "defect-instance.schema.json"),
        ("run", runs, "run.schema.json"),
        ("coverage_validation", coverage_records, "coverage-validation.schema.json")
    ]:
        if not isinstance(values, list):
            errors.append(f"TYPE:{label}:expected array")
            continue
        for index, value in enumerate(values):
            _validate_schema(value, SCHEMA_DIR / schema_name, f"{label}[{index}]", errors)

    if not isinstance(cases, list) or not isinstance(manifest, dict):
        errors.append("TYPE:cases must be array and dataset_manifest must be object")
        return {"status": "FAIL", "errors": errors, "statistics": {}}

    case_validator = Draft202012Validator(load_json(CASE_SCHEMA_PATH))
    for index, case in enumerate(cases):
        for error in case_validator.iter_errors(case):
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            errors.append(f"CASE_SCHEMA:cases[{index}]:{location}:{error.message}")

    task_id, gt_id = task.get("task_id"), gt.get("ground_truth_id")
    if task.get("ground_truth_ref") != gt_id:
        errors.append("UNRESOLVED_REFERENCE:task.ground_truth_ref")

    source_ids = {x.get("source_id") for x in gt.get("sources", [])}
    capability_ids = {x.get("capability_id") for x in gt.get("capabilities", [])}
    rule_ids = {x.get("rule_id") for x in gt.get("rules", [])}
    risk_ids = {x.get("risk_id") for x in gt.get("risks", [])}
    scenario_ids = {x.get("scenario_id") for x in gt.get("scenarios", [])}
    coverage = _index(gt.get("coverage_requirements", []), "coverage_item_id", "coverage", errors)
    case_index = _index(cases, "case_id", "case", errors)
    defect_index = _index(defects, "defect_id", "defect", errors)
    instance_index = _index(instances, "defect_instance_id", "defect_instance", errors)

    scope = task.get("expected_scope", {})
    for field, known in [("capability_refs", capability_ids), ("rule_refs", rule_ids), ("risk_refs", risk_ids), ("scenario_refs", scenario_ids)]:
        for ref in scope.get(field, []):
            if ref not in known:
                errors.append(f"UNRESOLVED_REFERENCE:task.expected_scope.{field}:{ref}")

    adjudication = gt.get("adjudication", {}).get("status")
    if adjudication == "CONFLICTED" or (adjudication == "APPROVED" and any(x.get("status") == "CONFLICTED" for x in gt.get("rules", []))):
        errors.append("UNRESOLVED_RULE_CONFLICT:ground_truth.adjudication")
    elif adjudication != "APPROVED":
        errors.append("INCONCLUSIVE:ground_truth_not_approved")
    for rule in gt.get("rules", []):
        for source_ref in rule.get("source_refs", []):
            if source_ref not in source_ids:
                errors.append(f"UNRESOLVED_REFERENCE:ground_truth_rule:{rule.get('rule_id')}:source:{source_ref}")
    for item in coverage.values():
        known_targets = capability_ids | rule_ids | risk_ids | scenario_ids
        for target_ref in item.get("target_refs", []):
            if target_ref not in known_targets:
                errors.append(f"UNRESOLVED_REFERENCE:coverage:{item.get('coverage_item_id')}:target:{target_ref}")

    if not manifest.get("dataset_id"):
        errors.append("MISSING_ID:dataset_manifest.dataset_id")
    if manifest.get("case_count") != len(cases):
        errors.append("DATASET_CASE_COUNT_MISMATCH")

    for case_id, case in case_index.items():
        if case.get("dataset_id") != manifest.get("dataset_id"):
            errors.append(f"DATASET_MISMATCH:{case_id}")
        for ref in case.get("capability_keys", []):
            if ref not in capability_ids:
                errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:capability:{ref}")
        for source in case.get("source_refs", []):
            ref = source.get("source_id")
            if ref and ref not in source_ids:
                errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:source:{ref}")
        for tag in case.get("coverage_tags", []):
            ref = tag.get("coverage_item_id")
            if ref not in coverage:
                errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:coverage:{ref}")

    criteria = {}
    linked = defaultdict(set)
    for case_id, case in case_index.items():
        for criterion in case.get("grading", {}).get("criteria", []):
            criterion_id = criterion.get("criterion_id")
            if criterion_id in criteria:
                errors.append(f"DUPLICATE_ID:criterion:{criterion_id}")
            criteria[criterion_id] = (case_id, criterion)
            for ref in criterion.get("coverage_item_refs", []):
                if ref not in coverage:
                    errors.append(f"UNRESOLVED_REFERENCE:criterion:{criterion_id}:coverage:{ref}")
                linked[(case_id, ref)].add(criterion_id)
            for ref in criterion.get("source_refs", []):
                if ref not in source_ids:
                    errors.append(f"UNRESOLVED_REFERENCE:criterion:{criterion_id}:source:{ref}")

    for case_id, case in case_index.items():
        for tag in case.get("coverage_tags", []):
            ref = tag.get("coverage_item_id")
            if ref in coverage and not linked[(case_id, ref)]:
                errors.append(f"COVERAGE_WITHOUT_ASSERTION:{case_id}:{ref}")

    validated_pairs = set()
    for record in coverage_records:
        cov_ref, case_ref = record.get("coverage_item_ref"), record.get("case_ref")
        validated_pairs.add((case_ref, cov_ref))
        if cov_ref not in coverage:
            errors.append(f"UNRESOLVED_REFERENCE:coverage_validation:{cov_ref}")
        if case_ref not in case_index:
            errors.append(f"UNRESOLVED_REFERENCE:coverage_validation_case:{case_ref}")
        for assertion_ref in record.get("assertion_refs", []):
            if assertion_ref not in criteria or criteria[assertion_ref][0] != case_ref:
                errors.append(f"UNRESOLVED_REFERENCE:coverage_validation_assertion:{assertion_ref}")
        if record.get("status") == "VALID" and not record.get("evidence_refs"):
            errors.append(f"MISSING_COVERAGE_EVIDENCE:{cov_ref}:{case_ref}")
        if record.get("status") == "INVALID":
            errors.append(f"INVALID_COVERAGE_CLAIM:{cov_ref}:{case_ref}")
        if record.get("status") == "INCONCLUSIVE":
            errors.append(f"INCONCLUSIVE:COVERAGE:{cov_ref}:{case_ref}")
        if record.get("status") == "NOT_APPLICABLE" and not record.get("rationale"):
            errors.append(f"MISSING_NOT_APPLICABLE_RATIONALE:{cov_ref}:{case_ref}")

    for case_id, case in case_index.items():
        for tag in case.get("coverage_tags", []):
            pair = (case_id, tag.get("coverage_item_id"))
            if pair not in validated_pairs:
                errors.append(f"INCONCLUSIVE:COVERAGE_VALIDATION_MISSING:{pair[0]}:{pair[1]}")

    for defect_id, defect in defect_index.items():
        for field, known in [("target_capability_refs", capability_ids), ("related_rule_refs", rule_ids), ("related_risk_refs", risk_ids)]:
            for ref in defect.get(field, []):
                if ref not in known:
                    errors.append(f"UNRESOLVED_REFERENCE:defect:{defect_id}:{field}:{ref}")
        for ref in defect.get("detection_expectation", {}).get("case_refs", []):
            if ref not in case_index:
                errors.append(f"UNRESOLVED_REFERENCE:defect:{defect_id}:case:{ref}")
        expected_cases = set(defect.get("detection_expectation", {}).get("case_refs", []))
        for ref in defect.get("detection_expectation", {}).get("criterion_refs", []):
            if ref not in criteria:
                errors.append(f"UNRESOLVED_REFERENCE:defect:{defect_id}:criterion:{ref}")
            elif criteria[ref][0] not in expected_cases:
                errors.append(f"DEFECT_CRITERION_CASE_MISMATCH:{defect_id}:{ref}")

    for instance_id, instance in instance_index.items():
        if instance.get("defect_ref") not in defect_index:
            errors.append(f"UNRESOLVED_REFERENCE:defect_instance:{instance_id}:defect")
        if instance.get("target_task_id") != task_id:
            errors.append(f"UNRESOLVED_REFERENCE:defect_instance:{instance_id}:task")

    run_ids, observations = set(), defaultdict(list)
    for run in runs:
        run_id = run.get("run_id")
        if run_id in run_ids:
            errors.append(f"DUPLICATE_ID:run:{run_id}")
        run_ids.add(run_id)
        if run.get("task_ref") != task_id:
            errors.append(f"UNRESOLVED_REFERENCE:run:{run_id}:task")
        if run.get("ground_truth_ref") != gt_id:
            errors.append(f"UNRESOLVED_REFERENCE:run:{run_id}:ground_truth")
        seen = set()
        for experiment in run.get("experiments", []):
            ref = experiment.get("defect_instance_ref")
            if ref not in instance_index:
                errors.append(f"UNRESOLVED_REFERENCE:run:{run_id}:defect_instance:{ref}")
                continue
            if ref in seen:
                errors.append(f"DUPLICATE_EXPERIMENT_INSTANCE:{run_id}:{ref}")
            seen.add(ref)
            if experiment.get("injection_status") == "FAILED" and experiment.get("detection_status") == "DETECTED":
                errors.append(f"INVALID_DETECTION_DENOMINATOR:{run_id}:{ref}")
            if experiment.get("control_status") == "FAIL":
                errors.append(f"CONTROL_EXPERIMENT_FAILED:{run_id}:{ref}")
            observations[ref].append(experiment)

    valid, detected = set(), set()
    for ref, records in observations.items():
        if any(x.get("injection_status") == "VALID" for x in records):
            valid.add(ref)
            if any(x.get("injection_status") == "VALID" and x.get("detection_status") == "DETECTED" and x.get("control_status") == "PASS" for x in records):
                detected.add(ref)
    stats = {
        "defect_instance_count": len(valid),
        "detected_defect_instance_count": len(detected),
        "detection_rate": len(detected) / len(valid) if valid else None,
        "run_count": len(runs),
        "experiment_observation_count": sum(len(x) for x in observations.values())
    }
    has_failure = any(not item.startswith("INCONCLUSIVE:") for item in errors)
    status = "FAIL" if has_failure else ("INCONCLUSIVE" if errors else "PASS")
    return {"status": status, "errors": errors, "statistics": stats}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_package(load_json(args.package))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.strict and result["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
