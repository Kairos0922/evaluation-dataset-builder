#!/usr/bin/env python3
"""校验绑定到精确 Skill 提交的目标宿主运行证据。"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - CI and local setup install jsonschema
    jsonschema = None

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "tests" / "target-runtime-report.schema.json"
REQUIRED_HOSTS = {"codex", "claude_code", "claude_ai", "claude_api"}
CHECK_IDS = {
    "discovery", "positive_trigger", "negative_trigger",
    "reference_loading", "task_execution",
}


def derive_status(values):
    values = list(values)
    if "FAIL" in values:
        return "FAIL"
    if "BLOCKED" in values:
        return "BLOCKED"
    if "NOT_RUN" in values:
        return "NOT_RUN"
    return "PASS"


def host_status(host):
    checks = host["checks"]
    values = [checks[name]["status"] for name in CHECK_IDS]
    task = checks["task_execution"]
    values.extend([
        task["side_effect_check"]["status"],
        task["cleanup_check"]["status"],
    ])
    return derive_status(values)


def overall_status(host_reports, required_hosts):
    by_host = {item["host_id"]: item for item in host_reports}
    return derive_status(by_host[name]["status"] for name in required_hosts)


def validate_evidence_references(report):
    artifacts = report.get("evidence_artifacts", [])
    by_id = {}
    for artifact in artifacts:
        evidence_id = artifact["evidence_id"]
        if evidence_id in by_id:
            raise ValueError(f"重复 evidence_id：{evidence_id}")
        by_id[evidence_id] = artifact

    def check_refs(refs, host_id, check_id):
        for evidence_id in refs:
            artifact = by_id.get(evidence_id)
            if artifact is None:
                raise ValueError(f"证据引用不存在：{evidence_id}")
            if artifact["host_id"] != host_id or artifact["check_id"] != check_id:
                raise ValueError(
                    f"证据引用范围不匹配：{evidence_id} 应属于 {host_id}/{check_id}"
                )

    for host in report["host_reports"]:
        host_id = host["host_id"]
        checks = host["checks"]
        for name in CHECK_IDS:
            check_refs(checks[name]["evidence_refs"], host_id, name)
        task = checks["task_execution"]
        check_refs(task["trace_evidence_refs"], host_id, "task_execution")
        check_refs(task["initial_state_evidence_refs"], host_id, "task_execution")
        check_refs(task["final_state_evidence_refs"], host_id, "task_execution")
        check_refs(
            task["side_effect_check"]["evidence_refs"],
            host_id, "task_execution.side_effect_check",
        )
        check_refs(
            task["cleanup_check"]["evidence_refs"],
            host_id, "task_execution.cleanup_check",
        )


def verify_local_evidence_hashes(report, evidence_dir):
    root = Path(evidence_dir).resolve()
    for artifact in report.get("evidence_artifacts", []):
        file_name = artifact["file_name"]
        candidate = (root / file_name).resolve()
        if root not in candidate.parents:
            raise ValueError(f"证据文件路径越界：{file_name}")
        if not candidate.is_file():
            raise ValueError(f"缺少证据文件：{file_name}")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest != artifact["sha256"]:
            raise ValueError(f"证据 SHA-256 不匹配：{file_name}")


def validate_report(report, candidate_sha, skill_tree_sha,
                    require_pass=False, evidence_dir=None):
    if jsonschema is None:
        raise RuntimeError("缺少 jsonschema；请运行 python -m pip install jsonschema")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    errors = sorted(validator.iter_errors(report), key=lambda item: list(item.path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors[:20]
        )
        raise ValueError("目标宿主验证报告不符合 Schema：" + detail)

    if report["candidate_sha"] != candidate_sha:
        raise ValueError("报告 candidate_sha 与本次待发布 PR head SHA 不一致。")
    if report["skill_tree_sha"] != skill_tree_sha:
        raise ValueError("报告 skill_tree_sha 与候选提交中的 Skill 目录树不一致。")

    required_hosts = set(report["required_hosts"])
    if required_hosts != REQUIRED_HOSTS:
        raise ValueError(
            "当前 README 对外记录的四种宿主均属于 0.0.1 验证范围；"
            f"报告必须明确包含：{sorted(REQUIRED_HOSTS)}。"
        )

    hosts = [item["host_id"] for item in report["host_reports"]]
    if len(hosts) != len(set(hosts)) or set(hosts) != REQUIRED_HOSTS:
        raise ValueError("目标宿主报告必须且只能各包含一个 README 已记录的宿主。")

    for host in report["host_reports"]:
        if host["package_sha"] != candidate_sha:
            raise ValueError(f"{host['host_id']} 的 package_sha 与候选提交不一致。")
        if host["package_tree_sha"] != skill_tree_sha:
            raise ValueError(f"{host['host_id']} 的 package_tree_sha 与 Skill 目录树不一致。")
        derived = host_status(host)
        if host["status"] != derived:
            raise ValueError(
                f"{host['host_id']} 声明状态 {host['status']} 与检查项推导状态 {derived} 不一致。"
            )

    derived_overall = overall_status(report["host_reports"], report["required_hosts"])
    if report["overall_status"] != derived_overall:
        raise ValueError(
            f"报告 overall_status={report['overall_status']}，"
            f"但根据宿主结果应为 {derived_overall}。"
        )

    validate_evidence_references(report)
    if evidence_dir:
        verify_local_evidence_hashes(report, evidence_dir)

    if require_pass and report["overall_status"] != "PASS":
        raise ValueError(
            f"目标宿主验证状态为 {report['overall_status']}；正式发布要求四种宿主全部 PASS。"
        )
    return report


def main():
    parser = argparse.ArgumentParser(description="校验目标宿主运行验证证据")
    parser.add_argument("--report", required=True, help="目标宿主验证 JSON 报告路径")
    parser.add_argument("--candidate-sha", required=True, help="PR head 的完整 40 位 SHA")
    parser.add_argument("--skill-tree-sha", required=True, help="skills/evaluation-dataset-builder 的 Git tree SHA")
    parser.add_argument("--evidence-dir", help="可选：证据文件解压目录；提供后会逐一计算 SHA-256")
    parser.add_argument("--require-pass", action="store_true", help="将非 PASS 状态视为发布阻断")
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    validate_report(
        report, args.candidate_sha, args.skill_tree_sha,
        require_pass=args.require_pass, evidence_dir=args.evidence_dir,
    )
    print("runtime-report-schema: PASS")
    print("target-runtime-status: " + report["overall_status"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"TARGET RUNTIME VALIDATION BLOCKED: {exc}", file=sys.stderr)
        sys.exit(1)
