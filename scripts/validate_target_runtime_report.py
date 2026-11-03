#!/usr/bin/env python3
"""Validate structured target-host runtime evidence before independent release approval."""
import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - documented development dependency
    jsonschema = None

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "tests" / "target-runtime-report.schema.json"
REQUIRED_HOSTS = {"codex", "claude_code", "claude_ai", "claude_api"}


def validate_report(report, candidate_sha, skill_tree_sha):
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

    if report.get("candidate_sha") != candidate_sha:
        raise ValueError("报告 candidate_sha 与本次待发布 PR head SHA 不一致。")
    if report.get("skill_tree_sha") != skill_tree_sha:
        raise ValueError("报告 skill_tree_sha 与候选提交中的 Skill 目录树不一致。")

    hosts = [item.get("host_id") for item in report.get("host_reports", [])]
    if len(hosts) != len(set(hosts)):
        raise ValueError("目标宿主报告存在重复 host_id。")
    if set(hosts) != REQUIRED_HOSTS:
        missing = sorted(REQUIRED_HOSTS - set(hosts))
        extra = sorted(set(hosts) - REQUIRED_HOSTS)
        raise ValueError(f"宿主覆盖范围不完整；缺少={missing}，多余={extra}。")

    for host in report["host_reports"]:
        if host.get("package_sha") != candidate_sha:
            raise ValueError(f"{host['host_id']} 的 package_sha 与候选提交不一致。")
        if host.get("package_tree_sha") != skill_tree_sha:
            raise ValueError(f"{host['host_id']} 的 package_tree_sha 与 Skill 目录树不一致。")

    if report.get("overall_status") != "PASS":
        raise ValueError("目标宿主验证整体状态不是 PASS。")
    return report


def main():
    parser = argparse.ArgumentParser(description="校验目标宿主运行验证证据")
    parser.add_argument("--report", required=True, help="目标宿主验证 JSON 报告路径")
    parser.add_argument("--candidate-sha", required=True, help="PR head 的完整 40 位 SHA")
    parser.add_argument("--skill-tree-sha", required=True, help="candidate:skills/evaluation-dataset-builder 的 Git tree SHA")
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    validate_report(report, args.candidate_sha, args.skill_tree_sha)
    print("runtime-schema: PASS")
    print("target-runtime: PASS " + report["evidence_url"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"TARGET RUNTIME VALIDATION BLOCKED: {exc}", file=sys.stderr)
        sys.exit(1)
