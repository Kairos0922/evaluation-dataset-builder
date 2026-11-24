#!/usr/bin/env python3
"""Mark RELEASE.md published only after the release workflow has verified every gate."""
import base64
import json
import os
import re
import sys
import urllib.request

from verify_release import (
    API,
    api_request,
    release_pr_binding,
    require,
    repository_tree_signature,
)


def build_published_release_doc(current, report, candidate_sha, release_sha,
                                workflow_run_id=None):
    heading = re.search(r"^# .*0\\.0\\.1.*发布候选说明\\s*$", current, re.MULTILINE)
    require(heading is not None,
            "RELEASE.md is missing a recognized v0.0.1 candidate heading.")
    text = (
        current[:heading.start()]
        + "# Evaluation Dataset Builder 0.0.1"
        + current[heading.end():]
    )

    status = (
        "**状态：** 已正式发布。Git Tag `v0.0.1` 与 GitHub Release 已创建；"
        f"候选 SHA `{candidate_sha}`，发布目标提交 `{release_sha}`。"
        "Builder 证据 PR #38 继续保持 Draft/Open。"
    )
    text, replaced = re.subn(
        r"^\\*\\*状态：\\*\\*.*$",
        lambda _: status,
        text,
        count=1,
        flags=re.MULTILINE,
    )
    require(replaced == 1, "RELEASE.md is missing its status line.")

    gate = re.search(r"^## 发布门禁[^\\n]*\\n", text, re.MULTILINE)
    require(gate is not None, "RELEASE.md is missing the release-gate checklist.")
    next_heading = re.search(r"^## ", text[gate.end():], re.MULTILINE)
    gate_end = gate.end() + next_heading.start() if next_heading else len(text)
    gate_body = text[gate.end():gate_end].replace("- [ ] ", "- [x] ")
    text = text[:gate.end()] + gate_body + text[gate_end:]

    text = text.replace(
        "PR #42 已合并；发布验证器已运行，但执行期间 GitHub API 返回 HTTP 401，未能完成发布。",
        "PR #42 已合并；完整发布验证、v0.0.1 标签创建和 GitHub Release 发布均已完成。",
    )
    text = text.replace(
        "排除发布工作流的 GitHub API HTTP 401 后，重新执行完整验证，再创建绑定最终 merge commit 的 v0.0.1 Tag 并发布 GitHub Release。",
        "v0.0.1 标签已创建并绑定最终 merge commit，GitHub Release 已正式发布。",
    )
    text = text.replace(
        "行为评测通过、Builder 证据通过或文档齐备都不构成发布授权。本次发布已获明确授权，但因发布验证步骤的 HTTP 401 而停止；不得将其描述为已发布。",
        "行为评测与 Builder 证据均通过本次完整发布门禁，用户已明确批准发布。v0.0.1 已正式发布；Builder 证据 PR #38 继续保持 Draft/Open。",
    )

    # Remove the stale failure-only status block from the earlier release attempt.
    text = re.sub(
        r"\\n## Release attempt status[^\\n]*.*\\Z",
        "",
        text,
        flags=re.DOTALL,
    )

    builder = report.get("builder_evidence") or {}
    require(
        builder.get("status") == "PASS"
        and builder.get("pilot_count") == 3
        and builder.get("skill_tree_matches_builder_evidence_and_release_candidate") is True,
        "RELEASE.md cannot be marked published without exact-SHA Builder and three-trial evidence.",
    )
    stability = report["stability"]
    baseline = report["baseline_comparison"]
    evidence = (
        "\\n\\n## Release evidence\\n\\n"
        f"- Candidate PR head SHA: `{candidate_sha}`\\n"
        f"- Merged main commit / tag SHA: `{release_sha}`\\n"
        f"- Release workflow run: `{workflow_run_id or 'not recorded'}`\\n"
        f"- Evaluation workflow run: {report.get('workflow_run_id')}\\n"
        f"- Generator: `{report['models']['generator']}`; Independent Judge: `{report['models']['judge_and_trigger']}`\\n"
        f"- Behavior mean / spread: {stability['behavior_pass_rate']['mean']:.1%} / {stability['behavior_pass_rate']['spread']:.1%}\\n"
        f"- Trigger Precision mean / spread: {stability['trigger_precision']['mean']:.1%} / {stability['trigger_precision']['spread']:.1%}\\n"
        f"- Trigger Recall mean / spread: {stability['trigger_recall']['mean']:.1%} / {stability['trigger_recall']['spread']:.1%}\\n"
        f"- Matched baseline mean uplift: {baseline['mean_uplift']:+.1%}\\n"
        f"- Builder evidence PR: #{builder['pr_number']} at `{builder['candidate_sha']}`\\n"
        f"- Builder production run: {builder['workflow_run_url']}\\n"
        f"- Independently validated datasets / cases: {builder['dataset_count']} / {builder['case_count']}\\n"
        f"- Real Skill trials: {builder['pilot_count']} PASS ({', '.join(builder['pilot_case_ids'])})\\n"
        "\\nThis release does not claim that each documented host's installation, discovery, reference-loading, and tool-integration path has been independently verified.\\n"
    )
    return text.rstrip() + evidence + "\\n"


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
    candidate_head_sha, release_sha = release_pr_binding(
        pr, candidate_sha, candidate_tree, release_tree,
    )
    tag_ref = api_request(f"/repos/{repo}/git/ref/tags/v0.0.1", token)
    tag_object = tag_ref.get("object") or {}
    tag_sha = tag_object.get("sha")
    if tag_object.get("type") == "tag":
        annotated = api_request(f"/repos/{repo}/git/tags/{tag_sha}", token)
        tag_sha = (annotated.get("object") or {}).get("sha")
    require(tag_sha == release_sha, "v0.0.1 tag does not point to the merged main commit.")

    current_file = api_request(f"/repos/{repo}/contents/RELEASE.md?ref=main", token)
    current = base64.b64decode(current_file["content"]).decode("utf-8")
    updated = build_published_release_doc(
        current, report, candidate_head_sha, release_sha,
        workflow_run_id=os.getenv("GITHUB_RUN_ID"),
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
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RELEASE DOCUMENT UPDATE BLOCKED: {exc}", file=sys.stderr)
        sys.exit(1)
