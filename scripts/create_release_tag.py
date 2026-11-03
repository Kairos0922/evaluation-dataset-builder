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


def create_release_tag():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    candidate_sha = os.getenv("RELEASE_CANDIDATE_SHA")
    pr_number = int(os.getenv("RELEASE_PR_NUMBER", str(PR_NUMBER)))
    require(token and repo and candidate_sha,
            "GITHUB_TOKEN, GITHUB_REPOSITORY, and RELEASE_CANDIDATE_SHA are required.")

    repository = api_request(f"/repos/{repo}", token)
    require(repository.get("default_branch") == "main",
            "Repository default branch must be main before tagging v0.0.1.")

    pr = api_request(f"/repos/{repo}/pulls/{pr_number}", token)
    candidate_commit = api_request(f"/repos/{repo}/git/commits/{candidate_sha}", token)
    release_sha = pr.get("merge_commit_sha") or ""
    release_commit = api_request(f"/repos/{repo}/git/commits/{release_sha}", token)
    pr_head_sha, release_sha = release_pr_binding(
        pr, candidate_sha,
        (candidate_commit.get("tree") or {}).get("sha"),
        (release_commit.get("tree") or {}).get("sha"),
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
        f"- Generator: `{report['models']['generator']}`; Judge: `{report['models']['judge_and_trigger']}`\n"
        f"- Complete repeated runs: {report['policy']['actual_runs']}\n"
        f"- Behavior mean / spread: {stability['behavior_pass_rate']['mean']:.1%} / {stability['behavior_pass_rate']['spread']:.1%}\n"
        f"- Trigger Precision mean / spread: {stability['trigger_precision']['mean']:.1%} / {stability['trigger_precision']['spread']:.1%}\n"
        f"- Trigger Recall mean / spread: {stability['trigger_recall']['mean']:.1%} / {stability['trigger_recall']['spread']:.1%}\n"
        f"- Matched baseline mean: {baseline['mean_baseline_behavior_pass_rate']:.1%}; Skill mean: {baseline['mean_skill_behavior_pass_rate']:.1%}; uplift: {baseline['mean_uplift']:+.1%}\n"
        "- Automated behavior, trigger, baseline, and stability gates: PASSED\n"
        "- Limitation: this is a SKILL.md entrypoint-text proxy; packaged references are not loaded through host resource tools, and it is not a full target Skills runtime test. Target-runtime validation remains necessary before production deployment.\n"
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
