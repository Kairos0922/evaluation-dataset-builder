#!/usr/bin/env python3
"""离线验证 Benchmark 契约、覆盖全集、跨数据集引用和实验统计。"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
CASE_SCHEMA_PATH = ROOT / "skills/evaluation-dataset-builder/references/dataset-schema.json"


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _object(value):
    return value if isinstance(value, dict) else {}


def _array(value):
    return value if isinstance(value, list) else []


def _validate_schema(value, schema_path, label, errors):
    try:
        validator = Draft202012Validator(load_json(schema_path))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"ERROR:SCHEMA_LOAD:{label}:{exc}")
        return
    for error in sorted(validator.iter_errors(value), key=lambda item: list(map(str, item.path))):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"SCHEMA:{label}:{location}:{error.message}")


def _index(items, key, label, errors):
    result = {}
    for position, item in enumerate(_array(items)):
        if not isinstance(item, dict):
            errors.append(f"TYPE:{label}[{position}]:expected object")
            continue
        identifier = item.get(key)
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"MISSING_ID:{label}:{key}[{position}]")
            continue
        if identifier in result:
            errors.append(f"DUPLICATE_ID:{label}:{identifier}")
        else:
            result[identifier] = item
    return result


def _status(errors):
    if any(item.startswith("ERROR:") for item in errors):
        return "ERROR"
    if any(not item.startswith("INCONCLUSIVE:") for item in errors):
        return "FAIL"
    return "INCONCLUSIVE" if errors else "PASS"


def validate_package(package):
    errors = []
    if not isinstance(package, dict):
        return {"status": "ERROR", "errors": ["Benchmark package root must be an object"], "statistics": {}}

    required = ["task", "ground_truth", "dataset_manifests", "cases", "defect_specs",
                "defect_instances", "runs", "coverage_validations"]
    for field in required:
        if field not in package:
            errors.append(f"MISSING_COLLECTION:{field}")
    if errors:
        return {"status": "FAIL", "errors": errors, "statistics": {}}

    task, gt = package["task"], package["ground_truth"]
    if not isinstance(task, dict) or not isinstance(gt, dict):
        return {"status": "FAIL", "errors": ["TYPE:task and ground_truth must be objects"], "statistics": {}}

    collections = {}
    for field in ["dataset_manifests", "cases", "defect_specs", "defect_instances", "runs", "coverage_validations"]:
        value = package[field]
        if not isinstance(value, list):
            errors.append(f"TYPE:{field}:expected array")
            collections[field] = []
        else:
            collections[field] = value

    _validate_schema(task, SCHEMA_DIR / "task.schema.json", "task", errors)
    _validate_schema(gt, SCHEMA_DIR / "ground-truth.schema.json", "ground_truth", errors)
    for index, manifest in enumerate(collections["dataset_manifests"]):
        _validate_schema(manifest, ROOT / "skills/evaluation-dataset-builder/references/dataset-manifest-schema.json",
                         f"dataset_manifests[{index}]", errors)
    for field, schema_name in [("defect_specs", "defect.schema.json"),
                               ("defect_instances", "defect-instance.schema.json"),
                               ("runs", "run.schema.json"),
                               ("coverage_validations", "coverage-validation.schema.json")]:
        for index, value in enumerate(collections[field]):
            _validate_schema(value, SCHEMA_DIR / schema_name, f"{field}[{index}]", errors)

    manifests = [item for item in collections["dataset_manifests"] if isinstance(item, dict)]
    cases = [item for item in collections["cases"] if isinstance(item, dict)]
    defects = [item for item in collections["defect_specs"] if isinstance(item, dict)]
    instances = [item for item in collections["defect_instances"] if isinstance(item, dict)]
    runs = [item for item in collections["runs"] if isinstance(item, dict)]
    coverage_records = [item for item in collections["coverage_validations"] if isinstance(item, dict)]

    for index, case in enumerate(collections["cases"]):
        if isinstance(case, dict):
            for error in Draft202012Validator(load_json(CASE_SCHEMA_PATH)).iter_errors(case):
                location = ".".join(str(part) for part in error.absolute_path) or "$"
                errors.append(f"CASE_SCHEMA:cases[{index}]:{location}:{error.message}")
        else:
            errors.append(f"TYPE:cases[{index}]:expected object")

    task_id, gt_id = task.get("task_id"), gt.get("ground_truth_id")
    if task.get("ground_truth_ref") != gt_id:
        errors.append("UNRESOLVED_REFERENCE:task.ground_truth_ref")

    source_index = _index(gt.get("sources", []), "source_id", "source", errors)
    capability_index = _index(gt.get("capabilities", []), "capability_id", "capability", errors)
    rule_index = _index(gt.get("rules", []), "rule_id", "rule", errors)
    risk_index = _index(gt.get("risks", []), "risk_id", "risk", errors)
    scenario_index = _index(gt.get("scenarios", []), "scenario_id", "scenario", errors)
    workflow_index = _index(gt.get("workflows", []), "workflow_id", "workflow", errors)
    coverage_index = _index(gt.get("coverage_requirements", []), "coverage_item_id", "coverage", errors)
    manifest_index = _index(manifests, "dataset_id", "dataset_manifest", errors)
    case_index = _index(cases, "case_id", "case", errors)
    defect_index = _index(defects, "defect_id", "defect", errors)
    instance_index = _index(instances, "defect_instance_id", "defect_instance", errors)

    source_ids = set(source_index)
    capability_ids, rule_ids = set(capability_index), set(rule_index)
    risk_ids, scenario_ids, workflow_ids = set(risk_index), set(scenario_index), set(workflow_index)
    manifest_ids = set(manifest_index)
    expected_dataset_count = _object(task.get("expected_scope")).get("expected_dataset_count")
    if expected_dataset_count is not None and expected_dataset_count != len(manifest_index):
        errors.append(f"EXPECTED_DATASET_COUNT_MISMATCH:expected={expected_dataset_count}:actual={len(manifest_index)}")
    scope = _object(task.get("expected_scope"))
    for field, known in [("capability_refs", capability_ids), ("rule_refs", rule_ids),
                         ("risk_refs", risk_ids), ("scenario_refs", scenario_ids)]:
        for ref in _array(scope.get(field)):
            if ref not in known:
                errors.append(f"UNRESOLVED_REFERENCE:task.expected_scope.{field}:{ref}")

    adjudication = _object(gt.get("adjudication")).get("status")
    rules = [item for item in _array(gt.get("rules")) if isinstance(item, dict)]
    if adjudication == "CONFLICTED" or any(rule.get("status") == "CONFLICTED" for rule in rules):
        errors.append("UNRESOLVED_RULE_CONFLICT:ground_truth.adjudication")
    elif adjudication != "APPROVED":
        errors.append("INCONCLUSIVE:ground_truth_not_approved")
    if adjudication == "APPROVED":
        for rule in rules:
            if rule.get("status") != "CONFIRMED":
                errors.append(f"UNCONFIRMED_RULE_IN_APPROVED_GROUND_TRUTH:{rule.get('rule_id')}:{rule.get('status')}")

    source_collections = [
        ("rule", rules, "rule_id"),
        ("fact", _array(gt.get("facts")), "fact_id"),
        ("capability", _array(gt.get("capabilities")), "capability_id"),
        ("scenario", _array(gt.get("scenarios")), "scenario_id"),
        ("workflow", _array(gt.get("workflows")), "workflow_id"),
        ("risk", _array(gt.get("risks")), "risk_id"),
    ]
    for label, values, id_key in source_collections:
        for item in values:
            if not isinstance(item, dict):
                continue
            for source_ref in _array(item.get("source_refs")):
                if source_ref not in source_ids:
                    errors.append(f"UNRESOLVED_REFERENCE:ground_truth_{label}:{item.get(id_key)}:source:{source_ref}")

    known_targets = capability_ids | rule_ids | risk_ids | scenario_ids | workflow_ids
    for coverage_id, item in coverage_index.items():
        for target_ref in _array(item.get("target_refs")):
            if target_ref not in known_targets:
                errors.append(f"UNRESOLVED_REFERENCE:coverage:{coverage_id}:target:{target_ref}")
        for source_ref in _array(item.get("source_refs")):
            if source_ref not in source_ids:
                errors.append(f"UNRESOLVED_REFERENCE:coverage:{coverage_id}:source:{source_ref}")
        dataset_refs = item.get("dataset_refs", list(manifest_ids))
        if not isinstance(dataset_refs, list) or not dataset_refs:
            errors.append(f"INVALID_COVERAGE_DATASET_SCOPE:{coverage_id}")
        else:
            for dataset_ref in dataset_refs:
                if dataset_ref not in manifest_ids:
                    errors.append(f"UNRESOLVED_REFERENCE:coverage:{coverage_id}:dataset:{dataset_ref}")

    criteria = {}
    criteria_by_case = defaultdict(set)
    for case_id, case in case_index.items():
        dataset_id = case.get("dataset_id")
        if dataset_id not in manifest_ids:
            errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:dataset:{dataset_id}")
        for ref in _array(case.get("capability_keys")):
            if ref not in capability_ids:
                errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:capability:{ref}")
        for ref in _array(case.get("business_rule_refs")):
            if ref not in rule_ids:
                errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:business_rule:{ref}")
        for ref in _array(case.get("workflow_refs")):
            if ref not in workflow_ids:
                errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:workflow:{ref}")
        if case.get("scenario_id") and case.get("scenario_id") not in scenario_ids:
            errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:scenario:{case.get('scenario_id')}")
        for source in _array(case.get("source_refs")):
            source = _object(source)
            ref = source.get("source_id")
            if ref and ref not in source_ids:
                errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:source:{ref}")
        for tag in _array(case.get("coverage_tags")):
            ref = _object(tag).get("coverage_item_id")
            if ref not in coverage_index:
                errors.append(f"UNRESOLVED_REFERENCE:case:{case_id}:coverage:{ref}")
        grading = _object(case.get("grading"))
        for criterion in _array(grading.get("criteria")):
            if not isinstance(criterion, dict):
                errors.append(f"TYPE:criterion:{case_id}:expected object")
                continue
            criterion_id = criterion.get("criterion_id")
            if not isinstance(criterion_id, str) or not criterion_id:
                errors.append(f"MISSING_ID:criterion:{case_id}")
                continue
            if criterion_id in criteria:
                errors.append(f"DUPLICATE_ID:criterion:{criterion_id}")
                continue
            criteria[criterion_id] = (case_id, criterion)
            criteria_by_case[case_id].add(criterion_id)
            for ref in _array(criterion.get("coverage_item_refs")):
                if ref not in coverage_index:
                    errors.append(f"UNRESOLVED_REFERENCE:criterion:{criterion_id}:coverage:{ref}")
            for ref in _array(criterion.get("source_refs")):
                if ref not in source_ids:
                    errors.append(f"UNRESOLVED_REFERENCE:criterion:{criterion_id}:source:{ref}")

    # 每个数据集单独核验用例归属与数量；不接受跨数据集误归属。
    cases_by_dataset = defaultdict(list)
    for case_id, case in case_index.items():
        cases_by_dataset[case.get("dataset_id")].append(case_id)
    for dataset_id, manifest in manifest_index.items():
        actual_count = len(cases_by_dataset.get(dataset_id, []))
        if manifest.get("case_count") != actual_count:
            errors.append(f"DATASET_CASE_COUNT_MISMATCH:{dataset_id}:expected={manifest.get('case_count')}:actual={actual_count}")
        for split in _array(manifest.get("data_splits")):
            if not isinstance(split, dict):
                errors.append(f"TYPE:dataset_split:{dataset_id}:expected object")
                continue
            for case_ref in _array(split.get("case_ids")):
                if case_ref not in case_index or case_index[case_ref].get("dataset_id") != dataset_id:
                    errors.append(f"UNRESOLVED_REFERENCE:dataset_manifest:{dataset_id}:split:{case_ref}")

    # 覆盖验证必须闭合：每个 Ground Truth 覆盖项，在其适用的每个数据集中都必须有明确处置。
    dispositions = defaultdict(list)
    seen_records = {}
    for record in coverage_records:
        coverage_ref = record.get("coverage_item_ref")
        dataset_ref = record.get("dataset_ref")
        case_ref = record.get("case_ref")
        status = record.get("status")
        if coverage_ref not in coverage_index:
            errors.append(f"UNRESOLVED_REFERENCE:coverage_validation:{coverage_ref}")
            continue
        if dataset_ref not in manifest_index:
            errors.append(f"UNRESOLVED_REFERENCE:coverage_validation_dataset:{dataset_ref}")
            continue
        if dataset_ref not in _array(coverage_index[coverage_ref].get("dataset_refs", list(manifest_ids))):
            errors.append(f"COVERAGE_DATASET_SCOPE_MISMATCH:{coverage_ref}:{dataset_ref}")
        pair_key = (dataset_ref, coverage_ref, case_ref)
        if pair_key in seen_records and seen_records[pair_key] != status:
            errors.append(f"CONFLICTING_COVERAGE_DISPOSITION:{dataset_ref}:{coverage_ref}:{case_ref}")
        elif pair_key in seen_records:
            errors.append(f"DUPLICATE_COVERAGE_DISPOSITION:{dataset_ref}:{coverage_ref}:{case_ref}")
        seen_records[pair_key] = status
        dispositions[(dataset_ref, coverage_ref)].append(record)

        assertion_refs = _array(record.get("assertion_refs"))
        if status == "VALID":
            if not case_ref or case_ref not in case_index:
                errors.append(f"VALID_COVERAGE_MISSING_CASE:{dataset_ref}:{coverage_ref}")
                continue
            case = case_index[case_ref]
            if case.get("dataset_id") != dataset_ref:
                errors.append(f"COVERAGE_CASE_DATASET_MISMATCH:{coverage_ref}:{case_ref}:{dataset_ref}")
            tags = [_object(tag).get("coverage_item_id") for tag in _array(case.get("coverage_tags"))]
            if coverage_ref not in tags:
                errors.append(f"COVERAGE_VALIDATION_WITHOUT_CASE_TAG:{coverage_ref}:{case_ref}")
            if not assertion_refs:
                errors.append(f"VALID_COVERAGE_MISSING_ASSERTION:{coverage_ref}:{case_ref}")
            for assertion_ref in assertion_refs:
                if assertion_ref not in criteria or criteria[assertion_ref][0] != case_ref:
                    errors.append(f"UNRESOLVED_REFERENCE:coverage_validation_assertion:{assertion_ref}")
                elif coverage_ref not in _array(criteria[assertion_ref][1].get("coverage_item_refs")):
                    errors.append(f"COVERAGE_ASSERTION_MISMATCH:{coverage_ref}:{assertion_ref}")
            if not _array(record.get("evidence_refs")):
                errors.append(f"MISSING_COVERAGE_EVIDENCE:{coverage_ref}:{case_ref}")
            creator = _object(gt.get("provenance")).get("created_by")
            reviewer = record.get("reviewer")
            if not reviewer or reviewer == creator:
                errors.append(f"NON_INDEPENDENT_COVERAGE_REVIEW:{coverage_ref}:{case_ref}")
        elif status == "NOT_APPLICABLE":
            if not record.get("rationale"):
                errors.append(f"MISSING_NOT_APPLICABLE_RATIONALE:{coverage_ref}:{dataset_ref}")
            if case_ref or assertion_refs:
                errors.append(f"NOT_APPLICABLE_HAS_CASE_OR_ASSERTION:{coverage_ref}:{dataset_ref}")
        elif status == "INVALID":
            errors.append(f"INVALID_COVERAGE_CLAIM:{coverage_ref}:{dataset_ref}:{case_ref}")
        elif status == "INCONCLUSIVE":
            errors.append(f"INCONCLUSIVE:COVERAGE:{coverage_ref}:{dataset_ref}")

    for coverage_id, requirement in coverage_index.items():
        dataset_refs = _array(requirement.get("dataset_refs", list(manifest_ids)))
        for dataset_ref in dataset_refs:
            records = dispositions.get((dataset_ref, coverage_id), [])
            if not records:
                errors.append(f"INCONCLUSIVE:COVERAGE_DISPOSITION_MISSING:{dataset_ref}:{coverage_id}")
            statuses = {item.get("status") for item in records}
            if len(statuses) > 1:
                errors.append(f"CONFLICTING_COVERAGE_DISPOSITION:{dataset_ref}:{coverage_id}")
            if "VALID" not in statuses and "NOT_APPLICABLE" not in statuses:
                errors.append(f"INCONCLUSIVE:COVERAGE_GAP:{dataset_ref}:{coverage_id}")

    for case_id, case in case_index.items():
        for tag in _array(case.get("coverage_tags")):
            coverage_ref = _object(tag).get("coverage_item_id")
            if coverage_ref in coverage_index:
                matching = [item for item in coverage_records
                            if item.get("case_ref") == case_id and item.get("coverage_item_ref") == coverage_ref
                            and item.get("dataset_ref") == case.get("dataset_id")]
                if not matching:
                    errors.append(f"INCONCLUSIVE:COVERAGE_VALIDATION_MISSING:{case_id}:{coverage_ref}")

    for manifest_id, manifest in manifest_index.items():
        for source_ref in _array(manifest.get("source_refs")):
            if source_ref not in source_ids:
                errors.append(f"UNRESOLVED_REFERENCE:dataset_manifest:{manifest_id}:source:{source_ref}")

    for defect_id, defect in defect_index.items():
        for field, known in [("target_capability_refs", capability_ids), ("related_rule_refs", rule_ids),
                             ("related_risk_refs", risk_ids)]:
            for ref in _array(defect.get(field)):
                if ref not in known:
                    errors.append(f"UNRESOLVED_REFERENCE:defect:{defect_id}:{field}:{ref}")
        expected_cases = set(_array(_object(defect.get("detection_expectation")).get("case_refs")))
        for ref in expected_cases:
            if ref not in case_index:
                errors.append(f"UNRESOLVED_REFERENCE:defect:{defect_id}:case:{ref}")
        for ref in _array(_object(defect.get("detection_expectation")).get("criterion_refs")):
            if ref not in criteria:
                errors.append(f"UNRESOLVED_REFERENCE:defect:{defect_id}:criterion:{ref}")
            elif criteria[ref][0] not in expected_cases:
                errors.append(f"DEFECT_CRITERION_CASE_MISMATCH:{defect_id}:{ref}")

    for instance_id, instance in instance_index.items():
        if instance.get("defect_ref") not in defect_index:
            errors.append(f"UNRESOLVED_REFERENCE:defect_instance:{instance_id}:defect")
        if instance.get("target_task_id") != task_id:
            errors.append(f"UNRESOLVED_REFERENCE:defect_instance:{instance_id}:task")

    observations = defaultdict(list)
    run_ids = set()
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
        for experiment in _array(run.get("experiments")):
            if not isinstance(experiment, dict):
                errors.append(f"TYPE:experiment:{run_id}:expected object")
                continue
            ref = experiment.get("defect_instance_ref")
            if ref not in instance_index:
                errors.append(f"UNRESOLVED_REFERENCE:run:{run_id}:defect_instance:{ref}")
                continue
            if ref in seen:
                errors.append(f"DUPLICATE_EXPERIMENT_INSTANCE:{run_id}:{ref}")
            seen.add(ref)
            if experiment.get("injection_status") == "FAILED" and experiment.get("detection_status") == "DETECTED":
                errors.append(f"INVALID_DETECTION_DENOMINATOR:{run_id}:{ref}")
            if experiment.get("control_status") == "PASS":
                if not _array(experiment.get("control_execution_run_ids")) or not _array(experiment.get("control_evidence_refs")):
                    errors.append(f"MISSING_CONTROL_EXECUTION_EVIDENCE:{run_id}:{ref}")
            observations[ref].append(experiment)

    valid_instances, detected_any, detected_all = set(), set(), set()
    eligible_observations = 0
    detected_observations = 0
    false_positive_controls = 0
    control_observations = 0
    excluded_observations = 0
    k_distribution = Counter()
    instance_details = {}
    for ref, records in observations.items():
        eligible = [item for item in records
                    if item.get("injection_status") == "VALID"
                    and item.get("control_status") == "PASS"
                    and item.get("detection_status") in {"DETECTED", "MISSED"}
                    and _array(item.get("control_execution_run_ids"))
                    and _array(item.get("control_evidence_refs"))]
        excluded_observations += len(records) - len(eligible)
        k = len(eligible)
        if k:
            valid_instances.add(ref)
            k_distribution[str(k)] += 1
            eligible_observations += k
            detected = sum(item.get("detection_status") == "DETECTED" for item in eligible)
            detected_observations += detected
            if detected:
                detected_any.add(ref)
            if detected == k:
                detected_all.add(ref)
            instance_details[ref] = {"valid_repeats": k, "detected_repeats": detected}
        for item in records:
            if item.get("control_status") == "PASS" and item.get("control_detection_status") in {"FALSE_POSITIVE", "NO_FALSE_POSITIVE"}:
                control_observations += 1
                if item.get("control_detection_status") == "FALSE_POSITIVE":
                    false_positive_controls += 1

    stats = {
        "defect_instance_count": len(valid_instances),
        "eligible_experiment_observation_count": eligible_observations,
        "excluded_experiment_observation_count": excluded_observations,
        "detected_experiment_observation_count": detected_observations,
        "observation_detection_rate": detected_observations / eligible_observations if eligible_observations else None,
        "detected_any_run_instance_count": len(detected_any),
        "instance_detection_any_rate": len(detected_any) / len(valid_instances) if valid_instances else None,
        "detected_all_valid_runs_instance_count": len(detected_all),
        "instance_detection_all_valid_runs_rate": len(detected_all) / len(valid_instances) if valid_instances else None,
        "valid_repeat_count_distribution": dict(sorted(k_distribution.items(), key=lambda pair: int(pair[0]))),
        "instance_repeat_details": instance_details,
        "control_observation_count": control_observations,
        "control_false_positive_count": false_positive_controls,
        "control_false_positive_rate": false_positive_controls / control_observations if control_observations else None,
        "run_count": len(runs),
        "experiment_observation_count": sum(len(_array(run.get("experiments"))) for run in runs),
        "dataset_coverage": {
            dataset_id: {
                "coverage_requirement_count": sum(dataset_id in _array(item.get("dataset_refs", list(manifest_ids)))
                                                  for item in coverage_index.values()),
                "valid_coverage_count": sum(
                    any(record.get("status") == "VALID" for record in dispositions.get((dataset_id, coverage_id), []))
                    for coverage_id, item in coverage_index.items()
                    if dataset_id in _array(item.get("dataset_refs", list(manifest_ids)))
                ),
                "coverage_gaps": [
                    coverage_id for coverage_id, item in coverage_index.items()
                    if dataset_id in _array(item.get("dataset_refs", list(manifest_ids)))
                    and not any(record.get("status") == "VALID" for record in dispositions.get((dataset_id, coverage_id), []))
                ]
            } for dataset_id in manifest_index
        }
    }
    return {"status": _status(errors), "errors": errors, "statistics": stats}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_package(load_json(args.package))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"status": "ERROR", "errors": [str(exc)], "statistics": {}}
    except Exception as exc:
        result = {"status": "ERROR", "errors": [f"VALIDATOR_EXCEPTION:{type(exc).__name__}:{exc}"], "statistics": {}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.strict and result["status"] != "PASS" else (2 if result["status"] == "ERROR" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
