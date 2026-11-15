#!/usr/bin/env python3
"""Mark RELEASE.md published only after the release workflow has verified every gate."""
import base64
import json
import os
import sys
import urllib.request

from verify_release import (
    API,
    api_request,
    latest_approved_review,
    release_pr_binding,
    require,
    repository_tree_signature,
)


def build_published_release_doc(current, report, candidate_sha, release_sha, reviewer):
    require("# 0.0.1 发布候选说明" in current,
            "RELEASE.md does not contain the expected v0.0.1 heading.")
    text = current.replace("# 0.0.1 发布候选说明", "# Evaluation Dataset Builder 0.0.1")
    text = text.replace("**状态：** 尚未正式发布", "**状态：** 已正式发布")
    require("## 发布门禁" in text, "RELEASE.md is missing the release-gate checklist.")
    before, checklist = text.split("## 发布门禁", 1)
    checklist = checklist.replace("- [ ] ", "- [x] ")
    text = before + "## 发布门禁" + checklist
    builder = report.get("builder_evidence") or {}
    require(builder.get("status") == "PASS"
            and builder.get("pilot_count") == 3
            and builder.get("skill_tree_matches_release_candidate") is True,
            "RELEASE.md cannot be marked published without exact-SHA Builder and three-trial evidence.")
    stability = report["stability"]
    baseline = report["baseline_comparison"]
    evidence = (
        "\n\n## Release evidence\n\n"
        f"- Reviewed PR head SHA: `{candidate_sha}`\n"
        f"- Merged main commit / tag SHA: `{release_sha}`\n"
        f"- Evaluation workflow run: {report.get('workflow_run_id')}\n"
        f"- Generator: `{report['models']['generator']}`\n"
        f"- Independent Judge: `{report['models']['judge_and_trigger']}`\n"
        f"- Behavior mean / spread: {stability['behavior_pass_rate']['mean']:.1%} / {stability['behavior_pass_rate']['spread']:.1%}\n"
        f"- Trigger Precision mean / spread: {stability['trigger_precision']['mean']:.1%} / {stability['trigger_precision']['spread']:.1%}\n"
        f"- Trigger Recall mean / spread: {stability['trigger_recall']['mean']:.1%} / {stability['trigger_recall']['spread']:.1%}\n"
        f"- Matched baseline mean uplift: {baseline['mean_uplift']:+.1%}\n"
        f"- Independent reviewer: {reviewer}\n"
        "\nThis release does not claim that each documented host's installation, discovery, reference-loading, and tool-integration path has been independently verified.\n"
    )
    if "\n## Release evidence\n" in text:
        text = text.split("\n## Release evidence\n", 1)[0]
    return text.rstrip() + evidence + "\n"


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
    pr_number = int(os.getenv("RELEASE_PR_NUMBER", "0"))
    require(token and repo and pr_number > 0,
            "GITHUB_TOKEN, GITHUB_REPOSITORY, and RELEASE_PR_NUMBER are required.")

    with open("artifacts/eval-report.json", encoding="utf-8") as handle:
        report = json.load(handle)
    candidate_sha = report.get("git_sha")
    require(bool(candidate_sha), "Evaluation report does not identify its candidate SHA.")
    if supplied_candidate_sha:
        require(candidate_sha == supplied_candidate_sha,
                "Evaluation report SHA does not match supplied candidate SHA.")

    release = api_request(f"/repos/{repo}/releases/tags/v0.0.1", token)
    require(release.get("tag_name") == "v0.0.1",
            "GitHub Release v0.0.1 must exist before updating RELEASE.md.")
    repository = api_request(f"/repos/{repo}", token)
    require(repository.get("default_branch") == "main",
            "Repository default branch must be main.")
    pr = api_request(f"/repos/{repo}/pulls/{pr_number}", token)
    release_sha = pr.get("merge_commit_sha") or ""
    candidate_tree = repository_tree_signature(repo, candidate_sha, candidate_sha, token)
    release_tree = repository_tree_signature(repo, release_sha, candidate_sha, token)
    reviewed_head_sha, release_sha = release_pr_binding(
        pr, candidate_sha, candidate_tree, release_tree,
    )
    tag_ref = api_request(f"/repos/{repo}/git/ref/tags/v0.0.1", token)
    tag_object = tag_ref.get("object") or {}
    tag_sha = tag_object.get("sha")
    if tag_object.get("type") == "tag":
        annotated = api_request(f"/repos/{repo}/git/tags/{tag_sha}", token)
        tag_sha = (annotated.get("object") or {}).get("sha")
    require(tag_sha == release_sha, "v0.0.1 tag does not point to the merged main commit.")

    reviews = api_request(f"/repos/{repo}/pulls/{pr_number}/reviews?per_page=100", token)
    reviewer = latest_approved_review(
        reviews, (pr.get("user") or {}).get("login"), reviewed_head_sha,
        report.get("workflow_run_id"),
    )
    current_file = api_request(f"/repos/{repo}/contents/RELEASE.md?ref=main", token)
    current = base64.b64decode(current_file["content"]).decode("utf-8")
    updated = build_published_release_doc(
        current, report, reviewed_head_sha, release_sha,
        reviewer["user"]["login"],
    )
    result = put_file(
        f"/repos/{repo}/contents/RELEASE.md",
        token,
        {
            "message": "Mark v0.0.1 as published with verified release evidence",
            "content": base64.b64encode(updated.encode("utf-8")).decode("ascii"),
            "sha": current_file["sha"],
            "branch": "main",
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
