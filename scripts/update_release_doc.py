#!/usr/bin/env python3
"""Mark RELEASE.md published only after the release workflow has created the GitHub Release."""
import base64
import json
import os
import sys
import urllib.request

from verify_release import API, api_request, latest_approved_review, require


def build_published_release_doc(current, report, candidate_sha, release_sha, reviewer):
    require("# Release 0.0.1 — Candidate (not yet published)" in current
            or "# Release 0.0.1 — Published" in current,
            "RELEASE.md does not contain the expected v0.0.1 heading.")
    text = current.replace(
        "# Release 0.0.1 — Candidate (not yet published)",
        "# Release 0.0.1 — Published",
    )
    gates = (
        "Behavioral pass rate >= 90% on every run",
        "Trigger Precision >= 95% and Recall >= 95% on every run",
        "Baseline comparison reviewed and accepted",
        "Stability spread <= 5 percentage points for all three metrics",
        "Independent human review of critical cases and generated outputs",
    )
    for gate in gates:
        text = text.replace(f"- [ ] {gate}", f"- [x] {gate}")
    text = text.replace(
        "- [ ] Target-runtime validation",
        "Target-runtime validation remains a deployment follow-up; this release "
        "validates the portable Skill-text proxy, not a full host runtime.",
    )
    text = text.replace(
        "This is a release candidate only. Do not publish tag v0.0.1 until every "
        "automated and human gate in RELEASE-GATE.md has passed on the exact release commit.",
        "v0.0.1 was published after all automated and independent human release "
        "gates passed on the exact candidate commit recorded below.",
    )
    evidence = (
        "## Release evidence\n\n"
        f"- Reviewed PR head SHA: `{candidate_sha}`\n"
        f"- Merged master commit / tag SHA: `{release_sha}`\n"
        f"- Evaluation workflow run: {report.get('workflow_run_id')}\n"
        f"- Generator: `{report['models']['generator']}`\n"
        f"- Independent Judge: `{report['models']['judge_and_trigger']}`\n"
        f"- Behavior mean / spread: {report['stability']['behavior_pass_rate']['mean']:.1%} / {report['stability']['behavior_pass_rate']['spread']:.1%}\n"
        f"- Trigger Precision mean / spread: {report['stability']['trigger_precision']['mean']:.1%} / {report['stability']['trigger_precision']['spread']:.1%}\n"
        f"- Trigger Recall mean / spread: {report['stability']['trigger_recall']['mean']:.1%} / {report['stability']['trigger_recall']['spread']:.1%}\n"
        f"- Matched baseline mean uplift: {report['baseline_comparison']['mean_uplift']:+.1%}\n"
        f"- Independent reviewer: {reviewer}\n"
        "\nThe machine-readable evaluation report is attached to the GitHub Release. "
        "Run target-host validation before production deployment.\n"
    )
    if "\n## Release evidence\n" in text:
        text = text.split("\n## Release evidence\n", 1)[0]
    return text.rstrip() + "\n\n" + evidence


def put_file(path, token, payload):
    request = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "evaluation-dataset-builder-release-doc",
        },
        method="PUT",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    supplied_candidate_sha = os.getenv("RELEASE_CANDIDATE_SHA")
    require(token and repo,
            "GITHUB_TOKEN and GITHUB_REPOSITORY are required.")

    with open("artifacts/eval-report.json", encoding="utf-8") as handle:
        report = json.load(handle)
    candidate_sha = report.get("git_sha")
    require(bool(candidate_sha),
            "Evaluation report does not identify its candidate SHA.")
    if supplied_candidate_sha:
        require(candidate_sha == supplied_candidate_sha,
                "Evaluation report SHA does not match supplied candidate SHA.")
    release = api_request(f"/repos/{repo}/releases/tags/v0.0.1", token)
    require(release.get("tag_name") == "v0.0.1",
            "GitHub Release v0.0.1 must exist before updating RELEASE.md.")
    repository = api_request(f"/repos/{repo}", token)
    require(repository.get("default_branch") == "master",
            "Repository default branch must be master.")
    pr = api_request(f"/repos/{repo}/pulls/13", token)
    require(pr.get("merged") is True and (pr.get("base") or {}).get("ref") == "master",
            "PR #13 must be merged into master before RELEASE.md can be updated.")
    require((pr.get("head") or {}).get("sha") == candidate_sha,
            "Merged PR #13 head differs from the published candidate.")
    release_sha = pr.get("merge_commit_sha")
    require(bool(release_sha),
            "Merged PR #13 has no merge_commit_sha.")
    tag_ref = api_request(f"/repos/{repo}/git/ref/tags/v0.0.1", token)
    tag_object = tag_ref.get("object") or {}
    tag_sha = tag_object.get("sha")
    if tag_object.get("type") == "tag":
        annotated = api_request(f"/repos/{repo}/git/tags/{tag_sha}", token)
        tag_sha = (annotated.get("object") or {}).get("sha")
    require(tag_sha == release_sha,
            "v0.0.1 tag does not point to the merged master commit.")
    reviews = api_request(f"/repos/{repo}/pulls/13/reviews?per_page=100", token)
    reviewer = latest_approved_review(
        reviews, (pr.get("user") or {}).get("login"), candidate_sha,
        report.get("workflow_run_id"),
    )

    current_file = api_request(
        f"/repos/{repo}/contents/RELEASE.md?ref=master", token
    )
    current = base64.b64decode(current_file["content"]).decode("utf-8")
    updated = build_published_release_doc(
        current, report, candidate_sha, release_sha, reviewer["user"]["login"]
    )
    result = put_file(
        f"/repos/{repo}/contents/RELEASE.md",
        token,
        {
            "message": "Mark v0.0.1 as published with verified release evidence",
            "content": base64.b64encode(updated.encode("utf-8")).decode("ascii"),
            "sha": current_file["sha"],
            "branch": "master",
        },
    )
    print(json.dumps({
        "release_doc_updated": True,
        "candidate_sha": candidate_sha,
        "release_commit_sha": release_sha,
        "commit_sha": result.get("commit", {}).get("sha"),
        "reviewer": reviewer["user"]["login"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RELEASE DOCUMENT UPDATE BLOCKED: {exc}", file=sys.stderr)
        sys.exit(1)
