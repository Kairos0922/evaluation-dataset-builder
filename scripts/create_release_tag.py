#!/usr/bin/env python3
"""Create v0.0.1 tag only after the merged PR passes all release evidence checks."""
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
import io

from verify_release import (
    API,
    PR_NUMBER,
    api_request,
    latest_approved_review,
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


def artifact_json(repo, token, artifact, filename):
    archive = api_request(
        f"/repos/{repo}/actions/artifacts/{artifact['id']}/zip",
        token,
        binary=True,
    )
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        matches = [name for name in zf.namelist() if name.endswith(filename)]
        require(len(matches) == 1, "Evidence artifact is missing or ambiguous: " + filename)
        return json.loads(zf.read(matches[0]).decode("utf-8"))


def validate_builder_evidence_payloads(summary, trace, adjudication, pilot_artifact_names):
    require(summary.get("status") == "PASS", "Independent Builder output validation did not pass.")
    require(int(summary.get("dataset_count", 0)) > 0 and int(summary.get("case_count", 0)) > 0,
            "Builder validation summary has no generated datasets or cases.")
    require(trace.get("status") == "PASS" and int(trace.get("dsh_exit_code", -1)) == 0,
            "DSH trace does not prove a successful Builder invocation.")
    require(int(trace.get("builder_skill_tool_calls", 0)) > 0 and bool(trace.get("generated_files")),
            "DSH trace lacks a completed Builder Skill call or generated files.")
    require(adjudication.get("status") == "PASS"
            and adjudication.get("scope") == "independent_three_case_pilot_adjudication"
            and adjudication.get("case_count") == 3
            and adjudication.get("passed_cases") == 3
            and adjudication.get("failed_cases") == 0,
            "Independent Gold Oracle did not pass all three real Skill trials.")
    require(adjudication.get("formal_cases_created_or_modified") is False
            and adjudication.get("oracle_exposed_to_builder_or_target_skill") is False,
            "Pilot adjudication violates the independent-oracle boundary.")
    cases = adjudication.get("cases") or []
    require(len(cases) == 3 and all(item.get("adjudication_status") == "PASS" for item in cases),
            "Pilot adjudication must contain exactly three passing case results.")
    case_ids = {item.get("case_id") for item in cases}
    roles = {item.get("pilot_role") for item in cases}
    require(None not in case_ids and roles == {"search_mutation", "multi_turn", "delete_confirmation"},
            "Pilot adjudication does not cover the three required real-task roles.")
    expected = {"webapp-testing-pilot-" + case_id for case_id in case_ids}
    require(set(pilot_artifact_names) == expected,
            "Pilot evidence artifacts do not match the adjudicated case IDs.")
    return {
        "status": "PASS",
        "dataset_count": int(summary["dataset_count"]),
        "case_count": int(summary["case_count"]),
        "pilot_count": 3,
        "pilot_case_ids": sorted(case_ids),
        "adjudication_status": adjudication["status"],
    }


def skill_package_tree_signature(repo, commit_sha, token):
    tree = repository_tree_signature(repo, commit_sha, commit_sha, token)
    prefix = "skills/evaluation-dataset-builder/"
    result = {path[len(prefix):]: value for path, value in tree.items() if path.startswith(prefix)}
    require(bool(result), "Skill package tree is empty at " + commit_sha)
    return result


def verify_builder_evidence(repo, token, builder_pr_number, release_candidate_sha):
    pr = api_request(f"/repos/{repo}/pulls/{builder_pr_number}", token)
    require(pr.get("state") == "open" and pr.get("draft") is True,
            "Builder evidence PR must remain Draft/Open.")
    require((pr.get("base") or {}).get("ref") == "main", "Builder evidence PR must target main.")
    builder_sha = (pr.get("head") or {}).get("sha")
    builder_branch = (pr.get("head") or {}).get("ref")
    require(bool(builder_sha) and bool(builder_branch), "Builder evidence PR lacks its exact head SHA.")
    require(
        skill_package_tree_signature(repo, builder_sha, token)
        == skill_package_tree_signature(repo, release_candidate_sha, token),
        "Builder evidence used a different Skill package tree than the release candidate.",
    )
    runs_response = api_request(f"/repos/{repo}/actions/runs?per_page=100", token)
    matching = [
        run for run in (runs_response.get("workflow_runs") or [])
        if run.get("name") == "验证 Skill"
        and run.get("head_sha") == builder_sha
        and run.get("head_branch") == builder_branch
        and run.get("event") in ("pull_request", "workflow_dispatch")
    ]
    require(bool(matching), "No Builder workflow run exists for the current Builder PR head SHA.")
    run = max(matching, key=lambda item: int(item.get("run_number", 0)))
    require(run.get("status") == "completed" and run.get("conclusion") == "success",
            "Latest Builder workflow run for the exact SHA did not succeed.")
    run_id = run["id"]
    jobs_response = api_request(f"/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100", token)
    jobs = jobs_response.get("jobs") or []
    by_name = {item.get("name"): item for item in jobs}
    required = ("validate", "audit-upstream-assets", "runtime-preflight",
                "builder-production", "resolve-pilot-matrix", "adjudicate-pilot")
    for name in required:
        require(name in by_name and by_name[name].get("conclusion") == "success",
                "Required Builder evidence job did not succeed: " + name)
    pilot_jobs = [item for item in jobs if str(item.get("name", "")).startswith("webapp-testing-pilot")]
    require(len(pilot_jobs) == 3 and all(item.get("conclusion") == "success" for item in pilot_jobs),
            "Exactly three real Skill pilot jobs must succeed.")
    artifacts_response = api_request(f"/repos/{repo}/actions/runs/{run_id}/artifacts", token)
    artifacts = [item for item in (artifacts_response.get("artifacts") or []) if not item.get("expired")]
    by_name = {item.get("name"): item for item in artifacts}
    for name in ("webapp-testing-builder-result", "webapp-testing-independent-adjudication"):
        require(name in by_name, "Required Builder evidence artifact is missing: " + name)
    pilot_names = sorted(name for name in by_name if name.startswith("webapp-testing-pilot-"))
    require(len(pilot_names) == 3, "Exactly three real Skill pilot evidence artifacts are required.")
    summary = artifact_json(repo, token, by_name["webapp-testing-builder-result"],
                            "builder-validation-summary.json")
    trace = artifact_json(repo, token, by_name["webapp-testing-builder-result"],
                          "builder-dsh-trace-verification.json")
    adjudication = artifact_json(repo, token, by_name["webapp-testing-independent-adjudication"],
                                 "independent-adjudication.json")
    result = validate_builder_evidence_payloads(summary, trace, adjudication, pilot_names)
    result.update({
        "pr_number": builder_pr_number,
        "candidate_sha": builder_sha,
        "workflow_run_id": run_id,
        "workflow_run_url": run.get("html_url"),
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

    reviews = api_request(
        f"/repos/{repo}/pulls/{pr_number}/reviews?per_page=100", token
    )
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

    review = latest_approved_review(reviews, author, pr_head_sha, run_id)
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
    reviewer = (review.get("user") or {}).get("login")
    stability = report["stability"]
    baseline = report["baseline_comparison"]
    notes = (
        "# Evaluation Dataset Builder v0.0.1\n\n"
        f"- Reviewed PR head SHA: `{pr_head_sha}`\n"
        f"- Evaluated merge commit / tag SHA: `{release_sha}`\n"
        f"- Validation run: {run_url}\n"
        f"- Independent reviewer: {reviewer}\n"
        f"- Builder evidence PR: #{builder_evidence['pr_number']} at {builder_evidence['candidate_sha']}\n"
        f"- Builder production run: {builder_evidence['workflow_run_url']}\n"
        f"- Independently validated datasets / cases: {builder_evidence['dataset_count']} / {builder_evidence['case_count']}\n"
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
        "approved_reviewer": reviewer,
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
