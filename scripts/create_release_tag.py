#!/usr/bin/env python3
"""Create v0.0.1 tag only after the merged PR passes all release evidence checks."""
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
import io
import hashlib
from pathlib import Path

from verify_release import (
    API,
    PR_NUMBER,
    api_request,
    release_pr_binding,
    require,
    repository_tree_signature,
    verify_report,
)


def api_write(path, token, payload):
    request = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "evaluation-dataset-builder-release-tag",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def report_from_run(repo, token, run_id, candidate_sha):
    artifacts = api_request(
        f"/repos/{repo}/actions/runs/{run_id}/artifacts", token
    )
    artifact = next((
        item for item in (artifacts.get("artifacts") or [])
        if item.get("name") == f"candidate-evaluation-report-{run_id}"
        and not item.get("expired")
    ), None)
    require(artifact is not None,
            "The exact-run evaluation report artifact is missing or expired.")
    archive = api_request(
        f"/repos/{repo}/actions/artifacts/{artifact['id']}/zip",
        token,
        binary=True,
    )
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        name = next((item for item in zf.namelist()
                     if item.endswith("eval-report.json")), None)
        require(name is not None, "Artifact ZIP does not contain eval-report.json.")
        report = json.loads(zf.read(name).decode("utf-8"))
    verify_report(report, candidate_sha, run_id)
    return report, artifact


def _zip_entry(zip_file, suffix):
    matches = [
        name for name in zip_file.namelist()
        if not name.endswith("/") and name.endswith(suffix)
    ]
    require(len(matches) == 1,
            "Evidence archive entry is missing or ambiguous: " + suffix)
    return zip_file.read(matches[0])


def _zip_json(zip_file, suffix):
    return json.loads(_zip_entry(zip_file, suffix).decode("utf-8"))


def _artifact_archive(repo, token, run_id, artifact_id, expected_name):
    response = api_request(
        f"/repos/{repo}/actions/runs/{run_id}/artifacts", token
    )
    artifact = next((
        item for item in (response.get("artifacts") or [])
        if int(item.get("id", 0)) == int(artifact_id)
    ), None)
    require(artifact is not None and artifact.get("expired") is False,
            f"Required evidence artifact {artifact_id} is missing or expired.")
    require(artifact.get("name") == expected_name,
            f"Evidence artifact {artifact_id} has unexpected name.")
    archive = api_request(
        f"/repos/{repo}/actions/artifacts/{artifact_id}/zip",
        token,
        binary=True,
    )
    try:
        return zipfile.ZipFile(io.BytesIO(archive))
    except (zipfile.BadZipFile, TypeError) as exc:
        raise ValueError(f"Evidence artifact {artifact_id} is not a valid ZIP.") from exc


def _require_run(repo, token, run_id, *, path, branch, head_sha=None,
                 conclusion="success"):
    run = api_request(f"/repos/{repo}/actions/runs/{run_id}", token)
    require(str(run.get("id")) == str(run_id), "Workflow run ID mismatch.")
    require(run.get("path") == path, f"Workflow run {run_id} has an unexpected workflow path.")
    require(run.get("head_branch") == branch, f"Workflow run {run_id} branch mismatch.")
    if head_sha is not None:
        require(run.get("head_sha") == head_sha, f"Workflow run {run_id} SHA mismatch.")
    require(run.get("status") == "completed" and run.get("conclusion") == conclusion,
            f"Workflow run {run_id} did not complete with the required conclusion.")
    return run


def _job_by_name(jobs, exact_name):
    matches = [job for job in jobs if job.get("name") == exact_name]
    require(len(matches) == 1, "Workflow job is missing or ambiguous: " + exact_name)
    return matches[0]


def _artifact_subtree_hashes(zip_file, case_id):
    marker = f"/artifacts/pilots/{case_id}/"
    prefixes = [
        name.split(marker, 1)[0] + marker
        for name in zip_file.namelist()
        if marker in name and not name.endswith("/")
    ]
    require(bool(prefixes), "Final evidence archive is missing pilot " + case_id)
    prefix = prefixes[0]
    result = {}
    for name in zip_file.namelist():
        if name.startswith(prefix) and not name.endswith("/"):
            relative = name[len(prefix):]
            result[relative] = hashlib.sha256(zip_file.read(name)).hexdigest()
    return result


def validate_builder_evidence_payloads(evidence):
    """Validate immutable, cross-workflow evidence without requiring duplicate execution."""
    index = evidence["index"]
    builder_sha = index["builder"]["candidate_sha"]
    metadata = evidence["builder_metadata"]
    trace = evidence["builder_trace"]
    probe = evidence["connectivity_probe"]
    credential_scan = evidence["credential_scan"]
    diagnostic = evidence["builder_diagnostic_summary"]
    input_verification = evidence["input_verification"]
    independent_validation = evidence["independent_validation"]
    replay_validation = evidence["replay_validation"]
    adjudication = evidence["adjudication"]

    require(metadata.get("candidate_sha") == builder_sha,
            "Builder metadata does not match the recorded Builder execution SHA.")
    require(
        metadata.get("workspace_isolated") is True
        and metadata.get("gold_oracle_mounted") is False
        and metadata.get("independent_validator_mounted") is False
        and metadata.get("webapp_testing_skill_loaded") is False,
        "Builder workspace isolation or independent-oracle boundary was not preserved.",
    )
    require(trace.get("status") == "PASS"
            and int(trace.get("dsh_exit_code", -1)) == 0
            and int(trace.get("builder_skill_tool_calls", 0)) == 1
            and bool(trace.get("generated_files")),
            "DSH trace does not prove one completed Builder Skill invocation and generated files.")
    require(
        probe.get("status") == "PASS"
        and probe.get("scope") == "minimal_model_connectivity_probe"
        and probe.get("tool_calls") == 0
        and probe.get("response_marker_present") is True
        and probe.get("quota_error_detected") is False
        and probe.get("builder_invocation_started") is False,
        "The pre-production DeepSeek connectivity probe did not pass its no-tool/no-quota contract.",
    )
    require(credential_scan.get("secret_value_exposed_in_artifact") is False,
            "Builder evidence artifact contains a credential disclosure.")

    expected_issue_ids = set(index["builder_diagnostic_review"]["expected_issue_ids"])
    diagnostic_issue_text = "\n".join(diagnostic.get("issues") or [])
    observed_issue_ids = {
        issue_id for issue_id in expected_issue_ids if issue_id in diagnostic_issue_text
    }
    require(
        diagnostic.get("status") == "FAIL"
        and int(diagnostic.get("issue_count", 0)) == len(expected_issue_ids)
        and observed_issue_ids == expected_issue_ids
        and index["builder_diagnostic_review"].get("disposition")
            == "REVIEWED_FALSE_POSITIVE_SCOPE_FLAGS",
        "Builder heuristic diagnostic findings differ from the explicitly reviewed Round 4 findings.",
    )
    require(
        input_verification.get("status") == "PASS"
        and int(input_verification.get("file_count", 0)) == 18
        and int(input_verification.get("per_file_sha256_verified", 0)) == 18
        and input_verification.get("formal_evaluation_cases_included") is False
        and input_verification.get("gold_oracle_included") is False,
        "Archived public Builder-input integrity/isolation verification failed.",
    )

    for name, report in (
        ("official independent validator", independent_validation),
        ("replay preparation validation", evidence["replay_preparation_validation"]),
        ("replay output revalidation", replay_validation),
    ):
        require(
            report.get("status") == "PASS"
            and int(report.get("dataset_count", 0)) == 1
            and int(report.get("case_count", 0)) == 15
            and int(report.get("schema_errors", -1)) == 0
            and int(report.get("source_evidence_refs_verified", -1)) == 61
            and report.get("formal_evaluation_cases_created_by_validator") is False,
            f"{name} did not independently validate the original Builder output.",
        )
        dataset = (report.get("datasets") or {}).get("wb-core") or {}
        require(dataset.get("manifest_quality_status") == "needs_info"
                and dataset.get("execution_status") == "NOT_RUN",
                f"{name} did not preserve the Builder dataset's needs_info / NOT_RUN states.")

    expected_hashes = index["dataset_file_sha256"]
    for source_name, files in (
        ("original Builder artifact", evidence["builder_files"]),
        ("final pilot and Oracle archive", evidence["final_builder_files"]),
    ):
        for filename, expected_sha in expected_hashes.items():
            payload = files.get(filename)
            require(isinstance(payload, bytes),
                    f"{source_name} is missing immutable Builder output {filename}.")
            actual_sha = hashlib.sha256(payload).hexdigest()
            require(actual_sha == expected_sha,
                    f"{source_name} SHA-256 mismatch for {filename}.")
    require(evidence.get("reused_pilot_archives_match") is True,
            "WB-02 / WB-10 pilot archives do not match their original successful run artifacts.")

    matrix_cases = {
        item.get("case_id"): item.get("pilot_role")
        for item in (evidence["pilot_matrix"].get("include") or [])
    }
    expected_cases = {
        "WB-02": "search_mutation",
        "WB-10": "state_cycle",
        "WB-12": "delete_confirmation",
    }
    require(matrix_cases == expected_cases,
            "Pilot matrix does not match the three Builder-authored required pilot roles.")

    require(
        adjudication.get("status") == "PASS"
        and adjudication.get("completion_status") == "COMPLETED"
        and adjudication.get("scope") == "independent_three_case_pilot_adjudication"
        and int(adjudication.get("case_count", 0)) == 3
        and int(adjudication.get("passed_cases", 0)) == 3
        and int(adjudication.get("failed_cases", -1)) == 0
        and adjudication.get("verdict_counts") == {"PASS": 3}
        and adjudication.get("formal_cases_created_or_modified") is False
        and adjudication.get("oracle_exposed_to_builder_or_target_skill") is False,
        "Independent Gold Oracle did not pass all three real Skill trials.",
    )
    oracle_cases = adjudication.get("cases") or []
    require(len(oracle_cases) == 3,
            "Gold Oracle report must contain exactly three case-level results.")
    case_ids = set()
    for case in oracle_cases:
        case_id = case.get("case_id")
        case_ids.add(case_id)
        require(case.get("dataset_id") == "wb-core"
                and case.get("execution_valid") is True
                and case.get("contract_verdict") == "PASS"
                and case.get("oracle_verdict") == "PASS",
                f"Gold Oracle case {case_id} did not pass its contract and independent adjudication.")
        require(all(item.get("status") == "PASS" for item in case.get("checks") or []),
                f"Gold Oracle case {case_id} contains a non-PASS check.")
        if case_id == "WB-02":
            require(case.get("pilot_role") == "search_mutation"
                    and case.get("business_behavior_verdict") == "EXPECTED_VIOLATION_DETECTED",
                    "WB-02 did not preserve the intended search-defect detection result.")
        elif case_id == "WB-10":
            require(case.get("pilot_role") == "state_cycle"
                    and case.get("business_behavior_verdict") == "PASS",
                    "WB-10 did not pass the within-session state-cycle trial.")
        elif case_id == "WB-12":
            require(case.get("pilot_role") == "delete_confirmation"
                    and case.get("business_behavior_verdict") == "PASS",
                    "WB-12 did not pass the delete-confirmation trial.")
    require(case_ids == set(expected_cases),
            "Gold Oracle case IDs do not match the immutable Builder pilot matrix.")

    dataset_sha = expected_hashes["wb-core.jsonl"]
    for case_id, role in expected_cases.items():
        runner = evidence["pilot_results"][case_id]
        context = evidence["pilot_contexts"][case_id]
        event_bytes = evidence["pilot_events"][case_id]
        require(
            runner.get("case_id") == case_id
            and runner.get("dataset_id") == "wb-core"
            and runner.get("runner_status") == "INVOCATION_OK"
            and runner.get("dsh_exit_code") == 0
            and runner.get("case_budget_status") == "PASS"
            and runner.get("builder_case_sha256") == dataset_sha
            and runner.get("trace", {}).get("webapp_testing_skill_calls") == 1
            and runner.get("trace", {}).get("completed_skill_calls") == 1
            and runner.get("trace", {}).get("final_reason") == "completed",
            f"Pilot {case_id} is not bound to the original Builder case or a completed DSH Skill invocation.",
        )
        require(
            context.get("run_id") == runner.get("run_id")
            and context.get("trace_sha256") == hashlib.sha256(event_bytes).hexdigest()
            and int(context.get("trace_event_count", -1)) == len(event_bytes.decode("utf-8").splitlines())
            and int(runner.get("trace", {}).get("event_count", -1)) == int(context.get("trace_event_count", -2)),
            f"Pilot {case_id} DSH trace identity or digest is inconsistent.",
        )
    delete_audit = evidence["delete_guard_audit"]
    delete_entries = [
        json.loads(line) for line in delete_audit.decode("utf-8").splitlines()
        if line.strip()
    ]
    require(
        len(delete_entries) == 1
        and delete_entries[0].get("method") == "DELETE"
        and delete_entries[0].get("allowed") is True
        and delete_entries[0].get("status") == 200
        and delete_entries[0].get("path") == "/api/tasks/WB-104",
        "WB-12 delete guard does not prove exactly one permitted successful target deletion.",
    )

    return {
        "status": "PASS",
        "pr_number": int(index["builder_pr_number"]),
        "candidate_sha": builder_sha,
        "workflow_run_id": int(index["builder"]["run_id"]),
        "workflow_run_url": index["builder"]["run_url"],
        "builder_job_conclusion": evidence["builder_job_conclusion"],
        "builder_trace_status": "PASS",
        "builder_diagnostic_status": "FAIL_REVIEWED_FALSE_POSITIVE_SCOPE_FLAGS",
        "builder_diagnostic_issue_ids": sorted(expected_issue_ids),
        "independent_validation_run_id": int(index["independent_validation"]["run_id"]),
        "independent_validation_status": "PASS",
        "final_pilot_run_id": int(index["final_pilots"]["run_id"]),
        "final_adjudication_status": "PASS",
        "dataset_count": 1,
        "case_count": 15,
        "schema_errors": 0,
        "source_evidence_refs_verified": 61,
        "manifest_quality_status": "needs_info",
        "execution_status": "NOT_RUN",
        "pilot_count": 3,
        "pilot_case_ids": ["WB-02", "WB-10", "WB-12"],
        "skill_tree_matches_builder_evidence_and_release_candidate": True,
        "dataset_output_hashes_match_all_archives": True,
        "wb02_wb10_original_pilot_archives_reused_byte_for_byte": True,
        "wb12_delete_count": 1,
    }


def verify_builder_evidence(repo, token, builder_pr_number, release_candidate_sha):
    index_path = Path(__file__).resolve().parents[1] / "docs" / "release-evidence" / "round4-evidence-index.json"
    require(index_path.is_file(), "The immutable Round 4 evidence index is missing.")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    require(int(index.get("builder_pr_number", 0)) == int(builder_pr_number),
            "Evidence index Builder PR number mismatch.")

    pr = api_request(f"/repos/{repo}/pulls/{builder_pr_number}", token)
    require(pr.get("state") == "open" and pr.get("draft") is True,
            "Builder evidence PR must remain Draft/Open.")
    require((pr.get("base") or {}).get("ref") == "main",
            "Builder evidence PR must target main.")
    current_builder_sha = (pr.get("head") or {}).get("sha")
    require(bool(current_builder_sha), "Builder evidence PR has no current head SHA.")

    builder_sha = index["builder"]["candidate_sha"]
    builder_branch = (pr.get("head") or {}).get("ref")
    builder_tree = skill_package_tree_signature(repo, builder_sha, token)
    current_builder_tree = skill_package_tree_signature(repo, current_builder_sha, token)
    release_tree = skill_package_tree_signature(repo, release_candidate_sha, token)
    require(builder_tree == current_builder_tree == release_tree,
            "The Builder-run Skill package tree differs from the current Builder PR or release candidate.")

    builder_run = _require_run(
        repo, token, index["builder"]["run_id"],
        path=".github/workflows/validate.yml",
        branch=builder_branch,
        head_sha=builder_sha,
        conclusion="failure",
    )
    builder_jobs_response = api_request(
        f"/repos/{repo}/actions/runs/{builder_run['id']}/jobs?per_page=100", token
    )
    builder_jobs = builder_jobs_response.get("jobs") or []
    require(_job_by_name(builder_jobs, "validate").get("conclusion") == "success"
            and _job_by_name(builder_jobs, "audit-upstream-assets").get("conclusion") == "success"
            and _job_by_name(builder_jobs, "runtime-preflight").get("conclusion") == "success",
            "Builder source validation, upstream asset audit, or runtime preflight did not pass.")
    builder_job = _job_by_name(builder_jobs, "builder-production")
    require(builder_job.get("conclusion") == "failure",
            "The evidence index expects the recorded Builder-production diagnostic stop; refresh the audit if run disposition changed.")

    validator_run = _require_run(
        repo, token, index["independent_validation"]["run_id"],
        path=".github/workflows/validate-existing-builder-artifact.yml",
        branch=builder_branch,
        head_sha=index["independent_validation"]["head_sha"],
        conclusion="success",
    )
    validator_jobs_response = api_request(
        f"/repos/{repo}/actions/runs/{validator_run['id']}/jobs?per_page=100", token
    )
    validator_jobs = validator_jobs_response.get("jobs") or []
    require(_job_by_name(validator_jobs, "validate-archived-artifact").get("conclusion") == "success",
            "Official independent validation workflow job did not pass.")

    replay_run = _require_run(
        repo, token, index["replay"]["run_id"],
        path=".github/workflows/replay-webapp-testing.yml",
        branch=builder_branch,
        head_sha=index["replay"]["head_sha"],
        conclusion="failure",
    )
    replay_jobs_response = api_request(
        f"/repos/{repo}/actions/runs/{replay_run['id']}/jobs?per_page=100", token
    )
    replay_jobs = replay_jobs_response.get("jobs") or []
    for case_id in ("WB-02", "WB-10"):
        matches = [
            job for job in replay_jobs
            if str(job.get("name", "")).startswith("webapp-testing-pilot")
            and case_id in str(job.get("name", ""))
        ]
        require(len(matches) == 1 and matches[0].get("conclusion") == "success",
                f"Original completed {case_id} pilot run is missing or not successful.")
    final_pilot_run = _require_run(
        repo, token, index["final_pilots"]["run_id"],
        path=".github/workflows/round4-wb12-deepseek-retry.yml",
        branch=builder_branch,
        head_sha=index["final_pilots"]["head_sha"],
        conclusion="success",
    )
    final_jobs_response = api_request(
        f"/repos/{repo}/actions/runs/{final_pilot_run['id']}/jobs?per_page=100", token
    )
    final_jobs = final_jobs_response.get("jobs") or []
    require(_job_by_name(final_jobs, "quota-gate").get("conclusion") == "success"
            and _job_by_name(final_jobs, "execute-and-adjudicate").get("conclusion") == "success",
            "Final targeted WB-12 execution or Gold Oracle adjudication job did not pass.")

    builder_index = index["builder"]
    validator_index = index["independent_validation"]
    replay_index = index["replay"]
    final_index = index["final_pilots"]
    with _artifact_archive(
        repo, token, builder_index["run_id"], builder_index["artifact_id"], builder_index["artifact_name"]
    ) as builder_zip, _artifact_archive(
        repo, token, validator_index["run_id"], validator_index["artifact_id"], validator_index["artifact_name"]
    ) as validator_zip, _artifact_archive(
        repo, token, replay_index["run_id"], replay_index["artifact_id"], replay_index["artifact_name"]
    ) as replay_zip, _artifact_archive(
        repo, token, final_index["run_id"], final_index["artifact_id"], final_index["artifact_name"]
    ) as final_zip:
        builder_files = {
            filename: _zip_entry(builder_zip, "webapp-testing-builder-output/" + filename)
            for filename in index["dataset_file_sha256"]
        }
        final_builder_files = {
            filename: _zip_entry(final_zip, "artifacts/source/webapp-testing-builder-output/" + filename)
            for filename in index["dataset_file_sha256"]
        }

        evidence = {
            "index": index,
            "builder_metadata": _zip_json(builder_zip, "builder-run-metadata.json"),
            "builder_trace": _zip_json(builder_zip, "builder-dsh-trace-verification.json"),
            "connectivity_probe": _zip_json(builder_zip, "builder-connectivity-probe.json"),
            "credential_scan": _zip_json(builder_zip, "credential-scan.json"),
            "builder_diagnostic_summary": _zip_json(builder_zip, "builder-validation-summary.json"),
            "input_verification": _zip_json(validator_zip, "independent-builder-input-verification.json"),
            "independent_validation": _zip_json(validator_zip, "independent-builder-output-validation.json"),
            "replay_preparation_validation": _zip_json(replay_zip, "builder-replay-validation.json"),
            "replay_validation": _zip_json(final_zip, "builder-replay-validation.json"),
            "adjudication": _zip_json(final_zip, "artifacts/oracle-adjudication.json"),
            "pilot_matrix": _zip_json(final_zip, "artifacts/source/pilot-matrix.json"),
            "builder_files": builder_files,
            "replay_builder_files": {
                filename: _zip_entry(replay_zip, "webapp-testing-builder-output/" + filename)
                for filename in index["dataset_file_sha256"]
            },
            "final_builder_files": final_builder_files,
            "pilot_results": {},
            "pilot_contexts": {},
            "pilot_events": {},
        }
        for case_id in ("WB-02", "WB-10", "WB-12"):
            evidence["pilot_results"][case_id] = _zip_json(
                final_zip, f"artifacts/pilots/{case_id}/runner-result.json"
            )
            evidence["pilot_contexts"][case_id] = _zip_json(
                final_zip, f"artifacts/pilots/{case_id}/trace-run-context.json"
            )
            evidence["pilot_events"][case_id] = _zip_entry(
                final_zip, f"artifacts/pilots/{case_id}/dsh-events.jsonl"
            )
        evidence["delete_guard_audit"] = _zip_entry(
            final_zip, "artifacts/pilots/WB-12/delete-guard-audit.jsonl"
        )

        # WB-02 and WB-10 were completed in the earlier replay workflow and reused
        # unchanged by the final WB-12 run. Verify every archived file byte-for-byte.
        pilot_archive_hashes_match = True
        for case_id, pilot in replay_index["reused_pilot_artifacts"].items():
            with _artifact_archive(
                repo, token, replay_index["run_id"], pilot["artifact_id"], pilot["artifact_name"]
            ) as old_pilot_zip:
                old_prefix = case_id + "/"
                old_hashes = {}
                for name in old_pilot_zip.namelist():
                    if name.startswith(old_prefix) and not name.endswith("/"):
                        old_hashes[name[len(old_prefix):]] = hashlib.sha256(
                            old_pilot_zip.read(name)
                        ).hexdigest()
                new_hashes = _artifact_subtree_hashes(final_zip, case_id)
                pilot_archive_hashes_match = pilot_archive_hashes_match and bool(old_hashes) and old_hashes == new_hashes
        evidence["reused_pilot_archives_match"] = pilot_archive_hashes_match
        evidence["builder_job_conclusion"] = builder_job.get("conclusion")

        result = validate_builder_evidence_payloads(evidence)

    result.update({
        "current_pr_head_sha": current_builder_sha,
        "builder_candidate_sha": builder_sha,
        "builder_workflow_run_url": builder_run.get("html_url"),
        "validator_workflow_run_url": validator_run.get("html_url"),
        "replay_workflow_run_url": replay_run.get("html_url"),
        "final_pilot_workflow_run_url": final_pilot_run.get("html_url"),
        "builder_artifact_id": int(builder_index["artifact_id"]),
        "independent_validation_artifact_id": int(validator_index["artifact_id"]),
        "final_pilot_oracle_artifact_id": int(final_index["artifact_id"]),
        "skill_tree_matches_release_candidate": True,
    })
    return result

def create_release_tag():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    candidate_sha = os.getenv("RELEASE_CANDIDATE_SHA")
    pr_number = int(os.getenv("RELEASE_PR_NUMBER", str(PR_NUMBER)))
    builder_pr_number = int(os.getenv("RELEASE_BUILDER_PR_NUMBER", "38"))
    require(token and repo and candidate_sha,
            "GITHUB_TOKEN, GITHUB_REPOSITORY, and RELEASE_CANDIDATE_SHA are required.")

    repository = api_request(f"/repos/{repo}", token)
    require(repository.get("default_branch") == "main",
            "Repository default branch must be main before tagging v0.0.1.")

    pr = api_request(f"/repos/{repo}/pulls/{pr_number}", token)
    release_sha = pr.get("merge_commit_sha") or ""
    candidate_tree_signature = repository_tree_signature(repo, candidate_sha, candidate_sha, token)
    release_tree_signature = repository_tree_signature(repo, release_sha, candidate_sha, token)
    pr_head_sha, release_sha = release_pr_binding(
        pr, candidate_sha, candidate_tree_signature, release_tree_signature,
    )
    author = (pr.get("user") or {}).get("login")
    require(bool(author), "Could not identify the release PR author.")

    runs_response = api_request(
        f"/repos/{repo}/actions/runs?per_page=100",
        token,
    )
    matching_runs = [
        run for run in (runs_response.get("workflow_runs") or [])
        if str(run.get("name") or "").startswith("Behavioral Skill Evaluation")
        and run.get("event") in ("push", "workflow_dispatch")
        and candidate_sha in str(run.get("display_title") or "")
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    ]
    require(bool(matching_runs),
            "No successful manual behavioral-evaluation run exists for this exact candidate SHA.")
    latest_run = max(matching_runs, key=lambda item: int(item.get("run_number", 0)))
    run_id = latest_run["id"]

    report, artifact = report_from_run(repo, token, run_id, candidate_sha)
    builder_evidence = verify_builder_evidence(repo, token, builder_pr_number, candidate_sha)
    report["builder_evidence"] = builder_evidence

    tag_name = "v0.0.1"
    try:
        tag_ref = api_request(
            f"/repos/{repo}/git/ref/tags/{tag_name}", token
        )
        existing_sha = (tag_ref.get("object") or {}).get("sha")
        require(existing_sha == release_sha,
                "Existing v0.0.1 tag does not point to the merged main commit.")
        created = False
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        api_write(
            f"/repos/{repo}/git/refs",
            token,
            {"ref": f"refs/tags/{tag_name}", "sha": release_sha},
        )
        created = True

    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/eval-report.json", "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    stability = report["stability"]
    baseline = report["baseline_comparison"]
    notes = (
        "# Evaluation Dataset Builder v0.0.1\n\n"
        f"- Candidate PR head SHA: `{pr_head_sha}`\n"
        f"- Evaluated merge commit / tag SHA: `{release_sha}`\n"
        f"- Validation run: {run_url}\n"
        f"- Builder evidence PR: #{builder_evidence['pr_number']} at {builder_evidence['candidate_sha']}\n"
        f"- Builder production run: {builder_evidence['workflow_run_url']}\n"
        f"- Builder-production job conclusion: {builder_evidence['builder_job_conclusion']}; DSH invocation trace: PASS.\n"
        f"- Builder diagnostic summary: {builder_evidence['builder_diagnostic_status']} ({', '.join(builder_evidence['builder_diagnostic_issue_ids'])}); see the evidence audit for reviewed clauses.\n"
        f"- Independently validated datasets / cases: {builder_evidence['dataset_count']} / {builder_evidence['case_count']}; schema errors: {builder_evidence['schema_errors']}; source references: {builder_evidence['source_evidence_refs_verified']}.\n"
        f"- Dataset quality / execution state: {builder_evidence['manifest_quality_status']} / {builder_evidence['execution_status']} (BR-09 remains unresolved).\n"
        f"- Real Skill trials: {builder_evidence['pilot_count']} PASS ({', '.join(builder_evidence['pilot_case_ids'])})\n"
        f"- Generator: `{report['models']['generator']}`; Judge: `{report['models']['judge_and_trigger']}`\n"
        f"- Complete repeated runs: {report['policy']['actual_runs']}\n"
        f"- Behavior mean / spread: {stability['behavior_pass_rate']['mean']:.1%} / {stability['behavior_pass_rate']['spread']:.1%}\n"
        f"- Trigger Precision mean / spread: {stability['trigger_precision']['mean']:.1%} / {stability['trigger_precision']['spread']:.1%}\n"
        f"- Trigger Recall mean / spread: {stability['trigger_recall']['mean']:.1%} / {stability['trigger_recall']['spread']:.1%}\n"
        f"- Matched baseline mean: {baseline['mean_baseline_behavior_pass_rate']:.1%}; Skill mean: {baseline['mean_skill_behavior_pass_rate']:.1%}; uplift: {baseline['mean_uplift']:+.1%}\n"
        "- Automated behavior, trigger, baseline, and stability gates: PASSED\n"
        "- Limitation: automated behavior evaluation is a Skill entrypoint-text proxy for the pinned model configuration. This release does not claim that each documented host's installation, discovery, reference-loading, or tool-integration path has been independently verified.\n"
        "\nThe attached JSON contains per-case outputs, locally verified Judge evidence, confusion matrices, baseline details, and token usage.\n"
    )
    with open("artifacts/release-notes.md", "w", encoding="utf-8") as handle:
        handle.write(notes)
    print(json.dumps({
        "tag": tag_name,
        "tag_created": created,
        "candidate_sha": candidate_sha,
        "release_commit_sha": release_sha,
        "workflow_run_id": run_id,
        "report_artifact_id": artifact["id"],
        "behavior_mean": report["stability"]["behavior_pass_rate"]["mean"],
        "trigger_precision_mean": report["stability"]["trigger_precision"]["mean"],
        "trigger_recall_mean": report["stability"]["trigger_recall"]["mean"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        create_release_tag()
    except Exception as exc:
        print(f"RELEASE TAG BLOCKED: {exc}", file=sys.stderr)
        sys.exit(1)
