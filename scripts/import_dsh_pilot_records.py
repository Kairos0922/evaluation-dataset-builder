#!/usr/bin/env python3
"""Import immutable DSH pilot artifacts into normalized ERA runtime records."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def _reject_json_constant(token: str):
    raise ValueError(f"invalid JSON numeric constant: {token}")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_digest(manifest_bytes: bytes, cases_bytes: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(b"evaluation-dataset-builder-ida-v0.0.2\0")
    digest.update(manifest_bytes)
    digest.update(b"\0")
    digest.update(cases_bytes)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    cases = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"blank JSONL line {line_number}")
        value = json.loads(line, parse_constant=_reject_json_constant)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {line_number} is not an object")
        cases.append(value)
    return cases


def verify_trace_jsonl(trace_path: Path, runner: dict) -> None:
    event_count = 0
    for line_number, line in enumerate(trace_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"blank DSH trace line {line_number} for {runner['case_id']}")
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"invalid DSH trace JSON at line {line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"DSH trace line {line_number} is not an object")
        if event.get("case_id") not in (None, runner.get("case_id")):
            raise ValueError(f"DSH trace case_id mismatch at line {line_number}")
        if event.get("run_id") not in (None, runner.get("run_id")):
            raise ValueError(f"DSH trace run_id mismatch at line {line_number}")
        event_count += 1
    if event_count == 0:
        raise ValueError(f"DSH trace is empty for {runner['case_id']}")


def verify_pilot_evidence(pilot_dir: Path, runner: dict) -> dict[str, str]:
    evidence_files = runner.get("evidence_files")
    if not isinstance(evidence_files, list) or not evidence_files:
        raise ValueError(f"missing evidence_files manifest for {runner['case_id']}")

    root = pilot_dir.resolve()
    verified: dict[str, str] = {}
    for item in evidence_files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError(f"invalid evidence manifest entry for {runner['case_id']}")
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe evidence path for {runner['case_id']}: {relative}")
        if relative.as_posix() in verified:
            raise ValueError(f"duplicate evidence path for {runner['case_id']}: {relative}")
        expected = item.get("sha256")
        if not isinstance(expected, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", expected):
            raise ValueError(f"invalid evidence SHA-256 for {runner['case_id']}: {relative}")
        path = pilot_dir / relative
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ValueError(f"missing evidence file for {runner['case_id']}: {relative}") from exc
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError(f"evidence path escapes pilot directory for {runner['case_id']}: {relative}")
        observed = sha256_file(resolved)
        if observed != expected.lower():
            raise ValueError(f"evidence hash mismatch for {runner['case_id']}: {relative}")
        verified[relative.as_posix()] = observed

    trace_name = "dsh-events.jsonl"
    if trace_name not in verified:
        raise ValueError(f"DSH trace is not SHA-256-bound in evidence_files for {runner['case_id']}")
    verify_trace_jsonl(pilot_dir / trace_name, runner)
    return verified


def runner_is_valid(runner: dict, oracle_case: dict) -> bool:
    trace = runner.get("trace", {})
    required = runner.get("required_skill_evidence", {})
    return all([
        runner.get("runner_status") == "INVOCATION_OK",
        runner.get("dsh_exit_code") == 0,
        runner.get("case_budget_status") == "PASS",
        runner.get("runner_error") is None,
        trace.get("final_reason") == "completed",
        trace.get("webapp_testing_skill_calls") == 1,
        trace.get("completed_skill_calls") == 1,
        runner.get("server_port_closed") is True,
        all(required.get(key) is True for key in ("markdown_report", "json_evidence_index", "screenshot")),
        oracle_case.get("execution_valid") is True,
        oracle_case.get("adjudication_status") == "PASS",
        all(check.get("status") == "PASS" for check in oracle_case.get("checks", [])),
    ])


def build_runtime_record(
    case_id: str,
    runner: dict,
    oracle_case: dict,
    dataset_id: str,
    dataset_sha256: str,
    evidence_ref_prefix: str = "file://",
    trace_sha256: str | None = None,
) -> dict:
    usage = runner.get("trace", {}).get("usage", {})
    totals = usage.get("usage_totals", {})
    fixture_mutations = runner.get("fixture_mutations") or []
    is_mutation = bool(fixture_mutations)
    business_verdict = oracle_case.get("business_behavior_verdict")
    report_support = any(
        check.get("status") == "PASS"
        and ("report correctly identifies" in check.get("check", "").lower()
             or "report verdict matches" in check.get("check", "").lower())
        for check in oracle_case.get("checks", [])
    )
    valid = runner_is_valid(runner, oracle_case)
    if valid:
        run_status = "valid"
        process_outcome = "pass"
    elif runner.get("server_health", {}).get("status") != "ok" or runner.get("server_port_closed") is not True:
        run_status = "environment_failed"
        process_outcome = "unknown"
    elif runner.get("dsh_exit_code") not in (None, 0):
        run_status = "agent_failed"
        process_outcome = "fail"
    else:
        run_status = "unknown"
        process_outcome = "unknown"

    contract_verdict = oracle_case.get("contract_verdict", "unknown").lower()
    oracle_verdict = oracle_case.get("oracle_verdict", "unknown").lower()
    if contract_verdict not in {"pass", "fail", "unknown"}:
        contract_verdict = "unknown"
    if oracle_verdict not in {"pass", "fail", "unknown"}:
        oracle_verdict = "unknown"

    record = {
        "record_version": "0.0.2",
        "run_id": runner["run_id"],
        "dataset_id": dataset_id,
        "dataset_sha256": dataset_sha256,
        "case_id": case_id,
        "configuration_id": "deepseek-flash-dsh-headless-round4",
        "target_revision": runner["webapp_testing_skill_commit"],
        "target_type": "skill",
        "model": {
            "provider": "DeepSeek",
            "model_id": "deepseek-flash",
            "revision": None
        },
        "harness": {
            "name": "DeepSeek DSH Headless",
            "version": "0.2.2-rc.1"
        },
        "environment": {
            "name": "GitHub-hosted runner",
            "version": "ubuntu26/20261116.202",
            "digest": None,
            "region": None
        },
        "tool_versions": {
            "dsh_cli": "0.2.2-rc.1",
            "playwright": "1.64.1",
            "chromium_headless_shell": "156.0.8078.4"
        },
        "status": run_status,
        "seed": None,
        "pair_id": None,
        "repeat_group_id": None,
        "started_at": runner["started_at_utc"],
        "trace_ref": f"{evidence_ref_prefix}pilots/{case_id}/dsh-events.jsonl",
        "result_ref": f"{evidence_ref_prefix}pilots/{case_id}/runner-result.json;oracle-adjudication.json#{case_id}",
        "outcomes": {
            "agent_outcome": contract_verdict,
            "process_outcome": process_outcome,
            "grader_outcome": "unknown",
            "gold_outcome": oracle_verdict,
            "grader_id": None,
            "grader_revision": None,
            "gold_source": "independent_oracle" if oracle_verdict in {"pass", "fail"} else "not_available"
        },
        "fault": {
            "kind": "mutation" if is_mutation else "none",
            "fault_id": ",".join(fixture_mutations) if is_mutation else None,
            "injected": is_mutation,
            "detected": (business_verdict == "EXPECTED_VIOLATION_DETECTED") if is_mutation else None,
            "failure_exposed": report_support if is_mutation else None
        },
        "cost": {
            "duration_seconds": runner.get("dsh_elapsed_seconds"),
            "input_tokens": totals.get("inputTokens"),
            "output_tokens": totals.get("outputTokens"),
            "cache_read_tokens": totals.get("cacheReadTokens"),
            "cache_write_tokens": totals.get("cacheWriteTokens"),
            "total_tokens": totals.get("totalTokens"),
            "model_steps": usage.get("model_step_count"),
            "tool_calls": usage.get("tool_call_count"),
            "cost_usd": None
        }
    }
    if trace_sha256 is not None:
        if not re.fullmatch(r"[a-fA-F0-9]{64}", trace_sha256):
            raise ValueError("trace_sha256 must be a 64-character hexadecimal digest")
        record["trace_sha256"] = trace_sha256
    return record


def import_evidence(
    evidence_root: Path,
    output_path: Path,
    source_registry_output: Path,
    metadata_output: Path,
    builder_run_id: str,
    builder_artifact_id: str,
    independent_validation_run_id: str,
    post_pilot_revalidation_run_id: str,
    pilot_run_id: str,
    pilot_artifact_id: str,
) -> tuple[list[dict], dict]:
    dataset_dir = evidence_root / "source" / "webapp-testing-builder-output"
    manifest_path = dataset_dir / "wb-core.manifest.json"
    cases_path = dataset_dir / "wb-core.jsonl"
    source_map_path = dataset_dir / "source-map.json"
    replay_validation_path = evidence_root / "source" / "builder-replay-validation.json"
    oracle_path = evidence_root / "oracle-adjudication.json"
    for path in (manifest_path, cases_path, source_map_path, replay_validation_path, oracle_path):
        if not path.is_file():
            raise ValueError(f"required immutable evidence file is missing: {path}")

    manifest_bytes = manifest_path.read_bytes()
    cases_bytes = cases_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"), parse_constant=_reject_json_constant)
    cases = load_jsonl(cases_path)
    if manifest.get("case_count") != len(cases):
        raise ValueError("Builder manifest case_count does not match the actual JSONL line count")
    raw_case_sha256 = hashlib.sha256(cases_bytes).hexdigest()
    dataset_sha = dataset_digest(manifest_bytes, cases_bytes)

    source_map = load_json(source_map_path)
    registry = source_map.get("source_registry")
    if not isinstance(registry, list) or not registry:
        raise ValueError("source-map.json does not contain a non-empty source_registry array")
    source_registry_output.parent.mkdir(parents=True, exist_ok=True)
    source_registry_output.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    replay = load_json(replay_validation_path)
    if (
        replay.get("status") != "PASS"
        or replay.get("case_count") != len(cases)
        or replay.get("schema_errors") != 0
        or replay.get("formal_evaluation_cases_created_by_validator") is not False
        or replay.get("execution_status_gate") != "NOT_RUN"
    ):
        raise ValueError("archived independent Builder-output validation evidence is incomplete or not PASS")

    oracle = load_json(oracle_path)
    if (
        oracle.get("status") != "PASS"
        or oracle.get("completion_status") != "COMPLETED"
        or oracle.get("formal_cases_created_or_modified") is not False
        or oracle.get("case_count") != 3
        or oracle.get("failed_cases") != 0
    ):
        raise ValueError("independent Gold Oracle evidence is not a completed three-case PASS")

    oracle_cases = {item["case_id"]: item for item in oracle.get("cases", [])}
    selected_ids = oracle.get("required_case_ids", [])
    if set(selected_ids) != set(oracle_cases) or len(selected_ids) != 3:
        raise ValueError("Oracle case set does not match its declared three-case pilot set")
    case_by_id = {case.get("case_id"): case for case in cases}
    if not set(selected_ids).issubset(case_by_id):
        raise ValueError("Oracle pilot selection includes a case absent from Builder-authored JSONL")

    records = []
    for case_id in selected_ids:
        pilot_dir = evidence_root / "pilots" / case_id
        runner_path = pilot_dir / "runner-result.json"
        trace_path = pilot_dir / "dsh-events.jsonl"
        if not runner_path.is_file() or not trace_path.is_file():
            raise ValueError(f"pilot runtime evidence is missing for {case_id}")
        runner = load_json(runner_path)
        oracle_case = oracle_cases[case_id]
        if runner.get("case_id") != case_id or runner.get("dataset_id") != manifest.get("dataset_id"):
            raise ValueError(f"runner metadata does not match Builder dataset/case for {case_id}")
        if runner.get("builder_case_sha256") != raw_case_sha256:
            raise ValueError(f"pilot {case_id} is not bound to the exact archived Builder JSONL SHA-256")
        target_text = case_by_id[case_id].get("evaluation_target", "")
        target_match = re.search(r"commit ([a-fA-F0-9]{40})", target_text)
        if not target_match or runner.get("webapp_testing_skill_commit") != target_match.group(1):
            raise ValueError(f"pilot {case_id} target revision does not match the Builder-authored case")
        evidence_hashes = verify_pilot_evidence(pilot_dir, runner)
        records.append(build_runtime_record(
            case_id, runner, oracle_case, manifest["dataset_id"], dataset_sha,
            trace_sha256=evidence_hashes["dsh-events.jsonl"],
        ))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")
    metadata = {
        "builder_run_id": builder_run_id,
        "builder_artifact_id": builder_artifact_id,
        "independent_validation_run_id": independent_validation_run_id,
        "post_pilot_revalidation_run_id": post_pilot_revalidation_run_id,
        "builder_production_job_conclusion": "failure_with_artifact_emitted",
        "pilot_run_id": pilot_run_id,
        "pilot_artifact_id": pilot_artifact_id,
        "dataset_id": manifest["dataset_id"],
        "dataset_version": manifest["version"],
        "dataset_sha256": dataset_sha,
        "case_jsonl_sha256": raw_case_sha256,
        "case_count": len(cases),
        "dataset_quality_status": manifest.get("quality_status"),
        "dataset_execution_status": manifest.get("execution_status"),
        "independent_validation_status": replay.get("status"),
        "independent_validation_schema_errors": replay.get("schema_errors"),
        "independent_validation_source_refs_verified": replay.get("source_evidence_refs_verified"),
        "pilot_case_ids": selected_ids,
        "pilot_case_count": len(records),
        "pilot_trace_sha256": {
            record["case_id"]: record["trace_sha256"] for record in records
        },
        "unexecuted_case_count": len(cases) - len(records),
        "oracle_status": oracle.get("status"),
        "oracle_passed_cases": oracle.get("passed_cases"),
        "oracle_failed_cases": oracle.get("failed_cases"),
        "limitations": [
            "Only the three preselected Builder-authored pilot cases were executed; the other twelve cases remain NOT_RUN.",
            "The dataset manifest remains needs_info because BR-09 request-failure and error-recovery evidence is unavailable.",
            "No separate Judge output is present; Judge validation must remain NOT_RUN.",
            "This is one Skill revision and one runtime configuration, not an IRT or G-Theory sample."
        ]
    }
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return records, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-registry-output", required=True, type=Path)
    parser.add_argument("--metadata-output", required=True, type=Path)
    parser.add_argument("--builder-run-id", default="44959366258")
    parser.add_argument("--builder-artifact-id", default="14729741906")
    parser.add_argument("--independent-validation-run-id", default="44968128127")
    parser.add_argument("--post-pilot-revalidation-run-id", default="45291624154")
    parser.add_argument("--pilot-run-id", default="45189512695")
    parser.add_argument("--pilot-artifact-id", default="14824967038")
    args = parser.parse_args()
    try:
        records, metadata = import_evidence(
            args.evidence_root,
            args.output,
            args.source_registry_output,
            args.metadata_output,
            args.builder_run_id,
            args.builder_artifact_id,
            args.independent_validation_run_id,
            args.post_pilot_revalidation_run_id,
            args.pilot_run_id,
            args.pilot_artifact_id,
        )
    except Exception as exc:
        parser.exit(2, f"FAIL: {exc}\n")
    print(f"Imported {len(records)} validated pilot runtime records for {metadata['dataset_id']}.")
    print(f"Dataset SHA-256: {metadata['dataset_sha256']}")
    print(f"Builder cases: {metadata['case_count']}; executed pilots: {metadata['pilot_case_count']}; NOT_RUN: {metadata['unexecuted_case_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
