#!/usr/bin/env python3
"""Fail-closed verifier for publishing the v0.0.1 GitHub Release."""
import base64
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from validate_target_runtime_report import REQUIRED_HOSTS, validate_report as validate_target_runtime_report

API = "https://api.github.com"
PR_NUMBER = int(os.getenv("RELEASE_PR_NUMBER", "0"))
BEHAVIOR_MIN = 0.90
PRECISION_MIN = 0.95
RECALL_MIN = 0.95
MAX_SPREAD = 0.05
CRITICAL_CASES = ("SE03", "SE04", "SE05", "SE08", "SE09", "SE11", "SE12")


def api_request(path, token, binary=False):
    url = path if path.startswith("https://") else API + path
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "evaluation-dataset-builder-release-verifier",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
    return body if binary else json.loads(body.decode("utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def repository_tree_signature(repo, commit_sha, candidate_sha, token):
    """Return a recursive tree signature excluding only the matching runtime report file and directory entries."""
    commit = api_request(f"/repos/{repo}/git/commits/{commit_sha}", token)
    root_tree_sha = (commit.get("tree") or {}).get("sha")
    require(bool(root_tree_sha), f"Commit {commit_sha} does not expose a Git tree.")
    tree = api_request(f"/repos/{repo}/git/trees/{root_tree_sha}?recursive=1", token)
    require(tree.get("truncated") is False,
            "Repository tree response was truncated; exact merge comparison is unavailable.")
    report_path = f"tests/runtime-evidence/{candidate_sha}.json"
    ignored_paths = {"tests", "tests/runtime-evidence", report_path}
    return {
        item["path"]: (item.get("mode"), item.get("type"), item.get("sha"))
        for item in tree.get("tree") or []
        if item.get("path") not in ignored_paths
    }


def release_pr_binding(pr, candidate_sha, candidate_tree_signature, release_tree_signature):
    """Bind evaluation to the PR head; allow only its separately merged runtime report file to be added."""
    require(pr.get("merged") is True and pr.get("state") == "closed",
            "The release PR must be merged and closed.")
    require((pr.get("base") or {}).get("ref") == "main",
            "The release PR must merge into main.")
    reviewed_head_sha = (pr.get("head") or {}).get("sha")
    release_sha = pr.get("merge_commit_sha")
    require(bool(reviewed_head_sha) and bool(release_sha),
            "The merged PR must expose both its reviewed head SHA and merge_commit_sha.")
    require(candidate_sha == reviewed_head_sha,
            "Evaluation candidate SHA must equal the reviewed PR head SHA.")
    require(
        isinstance(candidate_tree_signature, dict)
        and candidate_tree_signature == release_tree_signature,
        "The merged release tree contains changes outside the separately committed target-runtime report; reevaluate the final candidate.",
    )
    return reviewed_head_sha, release_sha


def verify_report(report, candidate_sha, run_id):
    require(report.get("git_sha") == candidate_sha,
            "Evaluation report SHA does not match the release tag.")
    require(str(report.get("workflow_run_id")) == str(run_id),
            "Evaluation report workflow_run_id does not match the Actions run.")
    require(report.get("automated_gate_pass") is True,
            "The report's automated_gate_pass is not true.")
    gates = report.get("automated_gates") or {}
    require(bool(gates), "The report has no automated_gates.")
    failed = [name for name, value in gates.items()
              if not isinstance(value, dict) or value.get("pass") is not True]
    require(not failed, "Automated release gates failed: " + ", ".join(failed))
    policy = report.get("policy") or {}
    require(int(policy.get("actual_runs", 0)) >= 2,
            "At least two full runs are required.")
    models = report.get("models") or {}
    generator = models.get("generator")
    judge = models.get("judge_and_trigger")
    require(bool(generator) and bool(judge) and generator != judge,
            "Generator and independent Judge model IDs must be present and distinct.")
    generator_endpoint = str(report.get("api_base_url") or "").rstrip("/")
    judge_endpoint = str(report.get("judge_api_base_url") or "").rstrip("/")
    require(bool(generator_endpoint) and bool(judge_endpoint) and generator_endpoint != judge_endpoint,
            "The independent Judge must use a separately configured provider endpoint.")
    trigger_count = int(policy.get("trigger_eval_count", 0))
    require(trigger_count >= 40,
            "At least 40 trigger evaluation examples are required.")
    runs = report.get("runs") or []
    require(len(runs) >= 2, "The report does not contain two complete runs.")
    for run in runs:
        require(run.get("automated_run_pass") is True,
                "At least one repeated run failed its hard gates.")
        skill_cases = run.get("skill_cases") or []
        baseline_cases = run.get("baseline_cases") or []
        trigger_cases = run.get("trigger_cases") or []
        require(bool(skill_cases) and len(skill_cases) == len(baseline_cases),
                "Skill and matched-baseline case counts are empty or differ.")
        require(len(trigger_cases) == trigger_count,
                "A repeated run has missing trigger evaluation cases.")
        metrics = run.get("metrics") or {}
        require(float(metrics.get("behavior_evaluability_rate", 0)) == 1.0,
                "A repeated run contains UNKNOWN or unscorable behavior checks.")
        require(float(metrics.get("baseline_evaluability_rate", 0)) == 1.0,
                "A repeated run contains UNKNOWN or unscorable baseline checks.")
        for case in skill_cases + baseline_cases:
            for check in case.get("checks") or []:
                status = check.get("status")
                require(status in ("PASS", "FAIL"),
                        "A behavior or baseline check is UNKNOWN or has no explicit status.")
                if status == "PASS":
                    require(check.get("score") == 1
                            and check.get("evidence_validated") is True
                            and bool(check.get("evidence")),
                            "A passing Judge result lacks verified evidence.")
                else:
                    require(check.get("score") == 0,
                            "A failing Judge result must have score 0.")
        require(float(metrics.get("behavior_pass_rate", 0)) >= BEHAVIOR_MIN,
                "A run is below the behavior pass-rate threshold.")
        require(float(metrics.get("trigger_precision", 0)) >= PRECISION_MIN,
                "A run is below the Trigger Precision threshold.")
        require(float(metrics.get("trigger_recall", 0)) >= RECALL_MIN,
                "A run is below the Trigger Recall threshold.")
        require(int(run.get("trigger_parse_errors", 0)) == 0,
                "A run contains Trigger classifier parse/API errors.")
    baseline = report.get("baseline_comparison") or {}
    require(baseline.get("required") is True and baseline.get("complete") is True,
            "The matched baseline is missing or incomplete.")
    stability = report.get("stability_gates") or {}
    for key in ("behavior_pass_rate", "trigger_precision", "trigger_recall"):
        item = stability.get(key) or {}
        require(item.get("pass") is True and float(item.get("spread", 1)) <= MAX_SPREAD,
                f"Stability gate failed for {key}.")
    return report


TARGET_RUNTIME_URL_PATTERN = re.compile(
    r"target-runtime:\s*PASS\s+"
    r"(https://github\.com/([^/\s]+)/([^/\s]+)/blob/([0-9a-f]{40})/"
    r"tests/runtime-evidence/([0-9a-f]{40})\.json)(?=\s|$)",
    flags=re.IGNORECASE,
)


def target_runtime_evidence_url(review, repo=None, candidate_sha=None):
    """Accept only an immutable report permalink in this repository."""
    body = review.get("body") or ""
    match = TARGET_RUNTIME_URL_PATTERN.search(body)
    require(match is not None,
            "Independent approval must include target-runtime: PASS followed by an immutable GitHub report permalink.")
    owner_repo = f"{match.group(2)}/{match.group(3)}"
    if repo:
        require(owner_repo.lower() == repo.lower(),
                "Target-runtime report must be stored in the release repository.")
    if candidate_sha:
        require(match.group(5) == candidate_sha,
                "Target-runtime report filename must equal the evaluated candidate SHA.")
    return match.group(1)


def load_target_runtime_report(review, repo, token, candidate_sha, skill_tree_sha):
    """Fetch a commit-pinned report from this repository and enforce release PASS."""
    url = target_runtime_evidence_url(review, repo=repo, candidate_sha=candidate_sha)
    match = TARGET_RUNTIME_URL_PATTERN.search(url)
    evidence_commit_sha = match.group(4)
    report_path = f"tests/runtime-evidence/{candidate_sha}.json"
    comparison = api_request(f"/repos/{repo}/compare/{evidence_commit_sha}...main", token)
    require(comparison.get("status") in ("ahead", "identical"),
            "Target-runtime evidence report commit must already be merged into main.")
    payload = api_request(
        f"/repos/{repo}/contents/{urllib.parse.quote(report_path, safe='/')}?ref={evidence_commit_sha}",
        token,
    )
    require(payload.get("type") == "file" and payload.get("encoding") == "base64",
            "Target-runtime report permalink does not resolve to a repository file.")
    require(payload.get("path") == report_path,
            "Target-runtime report file path does not match the candidate SHA.")
    try:
        raw = base64.b64decode("".join((payload.get("content") or "").split()), validate=True)
        report = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Target-runtime report could not be decoded: {exc}") from exc
    validate_target_runtime_report(
        report, candidate_sha, skill_tree_sha, require_pass=True
    )
    return report, url, evidence_commit_sha


def skill_package_tree_sha(repo, commit_sha, token):
    """Resolve the exact Git tree SHA of the installable Skill directory."""
    commit = api_request(f"/repos/{repo}/git/commits/{commit_sha}", token)
    root_tree_sha = (commit.get("tree") or {}).get("sha")
    require(bool(root_tree_sha), "Candidate commit does not expose a Git tree.")
    tree = api_request(f"/repos/{repo}/git/trees/{root_tree_sha}?recursive=1", token)
    require(tree.get("truncated") is False,
            "Repository tree response was truncated; cannot verify Skill package SHA.")
    matches = [
        item for item in tree.get("tree") or []
        if item.get("path") == "skills/evaluation-dataset-builder"
        and item.get("type") == "tree"
    ]
    require(len(matches) == 1 and bool(matches[0].get("sha")),
            "Could not resolve a unique Skill package tree SHA.")
    return matches[0]["sha"]


def latest_approved_review(reviews, author, reviewed_head_sha, run_id):
    latest_by_user = {}
    for review in reviews:
        user = (review.get("user") or {}).get("login")
        if not user:
            continue
        prior = latest_by_user.get(user)
        if prior is None or str(review.get("submitted_at", "")) > str(prior.get("submitted_at", "")):
            latest_by_user[user] = review
    blocking = [
        review for user, review in latest_by_user.items()
        if user != author and review.get("state") == "CHANGES_REQUESTED"
    ]
    require(not blocking, "A reviewer has an outstanding CHANGES_REQUESTED review.")
    run_url_fragment = f"/actions/runs/{run_id}"
    for user, review in latest_by_user.items():
        if user == author or review.get("state") != "APPROVED":
            continue
        if review.get("commit_id") != reviewed_head_sha:
            continue
        body = review.get("body") or ""
        missing = [case_id for case_id in CRITICAL_CASES if case_id not in body]
        if missing:
            continue
        if run_url_fragment not in body or "baseline" not in body.lower() or "spread" not in body.lower():
            continue
        try:
            target_runtime_evidence_url(review)
        except ValueError:
            continue
        return review
    raise ValueError(
        "No independent APPROVED review exists on the exact PR head SHA with "
        "critical-case findings, baseline/stability assessment, the Actions run link, "
        "and target-runtime: PASS with an HTTPS evidence link."
    )


def main():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    tag_name = os.getenv("GITHUB_REF_NAME")
    tag_sha = os.getenv("GITHUB_SHA")
    require(token and repo and tag_name and tag_sha,
            "GITHUB_TOKEN, GITHUB_REPOSITORY, GITHUB_REF_NAME, and GITHUB_SHA are required.")
    require(tag_name == "v0.0.1", "This workflow only publishes v0.0.1.")

    repository = api_request(f"/repos/{repo}", token)
    require(repository.get("default_branch") == "main",
            "Repository default branch must be main before v0.0.1 can be published.")

    pr = api_request(f"/repos/{repo}/pulls/{PR_NUMBER}", token)
    require(pr.get("merged") is True and pr.get("state") == "closed",
            "The release PR must be merged and closed.")
    require((pr.get("base") or {}).get("ref") == "main",
            "The release PR must have merged into main.")
    candidate_sha = (pr.get("head") or {}).get("sha")
    release_sha = (pr.get("merge_commit_sha") or "")
    candidate_tree_signature = repository_tree_signature(repo, candidate_sha, candidate_sha, token)
    release_tree_signature = repository_tree_signature(repo, release_sha, candidate_sha, token)
    reviewed_head_sha, release_sha = release_pr_binding(
        pr, candidate_sha, candidate_tree_signature, release_tree_signature,
    )

    tag_ref = api_request(
        f"/repos/{repo}/git/ref/tags/{urllib.parse.quote(tag_name, safe='')}", token
    )
    tag_object = tag_ref.get("object") or {}
    if tag_object.get("type") == "tag":
        tag_object = api_request(
            f"/repos/{repo}/git/tags/{tag_object['sha']}", token
        ).get("object") or {}
    require(tag_object.get("sha") == release_sha == tag_sha,
            "The v0.0.1 tag must point to the actual merged main commit (PR merge_commit_sha).")
    author = (pr.get("user") or {}).get("login")
    require(author, "Could not identify the release PR author.")

    reviews = api_request(
        f"/repos/{repo}/pulls/{PR_NUMBER}/reviews?per_page=100", token
    )
    runs_response = api_request(
        f"/repos/{repo}/actions/runs?per_page=100",
        token,
    )
    matching_runs = [
        item for item in (runs_response.get("workflow_runs") or [])
        if str(item.get("name") or "").startswith("Behavioral Skill Evaluation")
        and item.get("event") in ("push", "workflow_dispatch")
        and candidate_sha in str(item.get("display_title") or "")
        and item.get("status") == "completed"
        and item.get("conclusion") == "success"
    ]
    require(bool(matching_runs),
            "No successful manual behavioral-evaluation run exists for this exact candidate SHA.")
    latest_run = max(matching_runs, key=lambda item: int(item.get("run_number", 0)))
    run_id = latest_run["id"]

    review = latest_approved_review(reviews, author, reviewed_head_sha, run_id)
    package_tree_sha = skill_package_tree_sha(repo, candidate_sha, token)
    runtime_report, runtime_report_url, runtime_report_commit = load_target_runtime_report(
        review, repo, token, candidate_sha, package_tree_sha
    )
    artifacts = api_request(f"/repos/{repo}/actions/runs/{run_id}/artifacts", token)
    artifact = next((
        item for item in (artifacts.get("artifacts") or [])
        if item.get("name") == f"candidate-evaluation-report-{run_id}" and not item.get("expired")
    ), None)
    require(artifact is not None, "The exact-run evaluation report artifact is missing or expired.")

    archive = api_request(
        f"/repos/{repo}/actions/artifacts/{artifact['id']}/zip", token, binary=True
    )
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        report_name = next((name for name in zf.namelist()
                            if name.endswith("eval-report.json")), None)
        require(report_name is not None, "The artifact ZIP does not contain eval-report.json.")
        report = json.loads(zf.read(report_name).decode("utf-8"))
    verify_report(report, candidate_sha, run_id)

    artifact_path = Path("artifacts/eval-report.json")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    stability = report["stability"]
    baseline = report["baseline_comparison"]
    runtime_evidence_url = runtime_report_url
    notes = (
        "# Evaluation Dataset Builder v0.0.1\n\n"
        f"- Reviewed PR head SHA: `{reviewed_head_sha}`\n"
        f"- Evaluated merge commit / tag SHA: `{release_sha}`\n"
        f"- Validation run: {run_url}\n"
        f"- Independent reviewer: {(review.get('user') or {}).get('login')}\n"
        f"- Target runtime validation evidence: {runtime_evidence_url}\n"
        f"- Target runtime evidence commit: `{runtime_report_commit}`\n"
        f"- Verified hosts: {', '.join(sorted(runtime_report['required_hosts']))}\n"
        f"- Generator: `{report['models']['generator']}`; Judge: `{report['models']['judge_and_trigger']}`\n"
        f"- Complete repeated runs: {report['policy']['actual_runs']}\n"
        f"- Behavior mean / spread: {stability['behavior_pass_rate']['mean']:.1%} / {stability['behavior_pass_rate']['spread']:.1%}\n"
        f"- Trigger Precision mean / spread: {stability['trigger_precision']['mean']:.1%} / {stability['trigger_precision']['spread']:.1%}\n"
        f"- Trigger Recall mean / spread: {stability['trigger_recall']['mean']:.1%} / {stability['trigger_recall']['spread']:.1%}\n"
        f"- Matched baseline mean: {baseline['mean_baseline_behavior_pass_rate']:.1%}; Skill mean: {baseline['mean_skill_behavior_pass_rate']:.1%}; uplift: {baseline['mean_uplift']:+.1%}\n"
        "- Automated behavior, trigger, baseline, and stability gates: PASSED\n"
        "- Limitation: automated behavior evaluation is a Skill entrypoint-text proxy; target-runtime validation is a separate mandatory release gate and its evidence is linked above.\n"
        "\nThe attached JSON contains per-case outputs, locally verified Judge evidence, confusion matrices, baseline details, and token usage.\n"
    )
    Path("artifacts/release-notes.md").write_text(notes, encoding="utf-8")
    print(json.dumps({
        "release_gate": "PASS",
        "tag": tag_name,
        "candidate_sha": candidate_sha,
        "release_commit_sha": release_sha,
        "workflow_run_id": run_id,
        "artifact_id": artifact["id"],
        "approved_reviewer": (review.get("user") or {}).get("login"),
        "behavior_mean": report["stability"]["behavior_pass_rate"]["mean"],
        "precision_mean": report["stability"]["trigger_precision"]["mean"],
        "recall_mean": report["stability"]["trigger_recall"]["mean"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RELEASE BLOCKED: {exc}", file=sys.stderr)
        sys.exit(1)
