#!/usr/bin/env python3
"""验证 Agent Skills 目录结构及评测数据集专属资产。"""
from pathlib import Path
import json
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - CI and documented local setup install PyYAML
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "evaluation-dataset-builder"
SKILL_NAME = "evaluation-dataset-builder"
ERRORS = []

EXPECTED_SKILL_FILES = {
    "SKILL.md",
    "references/terminology.md",
    "references/quality-standard.md",
    "references/quality-standard.yaml",
    "references/ida-report.schema.json",
    "references/era-report.schema.json",
    "references/runtime-record.schema.json",
    "references/dataset-schema.json",
    "references/grader-guidelines.md",
    "references/coverage-design-guideline.md",
    "references/source-and-evidence-policy.md",
    "references/business-scenario-model.md",
    "references/scenario-buckets.md",
    "references/change-impact-and-repair.md",
    "references/dataset-manifest-schema.json",
}

ALLOWED_FRONTMATTER_FIELDS = {
    "name", "description", "license", "compatibility", "metadata", "allowed-tools"
}


def fail(message):
    ERRORS.append(message)


def check(condition, message):
    if not condition:
        fail(message)


def read_repo_text(relative):
    path = ROOT / relative
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        fail(f"无法读取仓库文件 {relative}：{exc}")
        return ""


def read_skill_text(relative):
    path = SKILL_DIR / relative
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        fail(f"无法读取 Skill 文件 {relative}：{exc}")
        return ""


def read_skill_json(relative):
    try:
        return json.loads(read_skill_text(relative))
    except Exception as exc:
        fail(f"Skill 文件 {relative} 不是有效 JSON：{exc}")
        return None


def validate_frontmatter(skill_text, version):
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", skill_text, flags=re.DOTALL)
    check(bool(match), "SKILL.md 必须以 YAML frontmatter 开始，并包含 Markdown 正文")
    if not match:
        return

    raw_frontmatter, body = match.groups()
    if yaml is None:
        fail("缺少 PyYAML；请先运行 python -m pip install pyyaml")
        return

    try:
        frontmatter = yaml.safe_load(raw_frontmatter)
    except Exception as exc:
        fail(f"SKILL.md frontmatter 不是有效 YAML：{exc}")
        return

    check(isinstance(frontmatter, dict), "SKILL.md frontmatter 必须是 YAML 对象")
    if not isinstance(frontmatter, dict):
        return

    keys = set(frontmatter)
    check({"name", "description"}.issubset(keys),
          "SKILL.md frontmatter 必须包含 name 和 description")
    check(keys.issubset(ALLOWED_FRONTMATTER_FIELDS),
          "SKILL.md frontmatter 包含规范未定义的字段：" +
          ", ".join(sorted(keys - ALLOWED_FRONTMATTER_FIELDS)))

    name = frontmatter.get("name")
    description = frontmatter.get("description")
    check(isinstance(name, str) and 1 <= len(name) <= 64,
          "name 必须是 1–64 个字符的字符串")
    if isinstance(name, str):
        check(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)),
              "name 只能使用小写字母、数字和单个连字符分段")
        check(name == SKILL_DIR.name == SKILL_NAME,
              "name 必须与 Skill 目录名一致")
    check(isinstance(description, str) and 1 <= len(description) <= 1024,
          "description 必须是 1–1024 个字符的字符串")
    if isinstance(description, str):
        check("<" not in description and ">" not in description,
              "description 不得包含尖括号标记")

    license_name = frontmatter.get("license")
    if license_name is not None:
        check(isinstance(license_name, str) and bool(license_name.strip()),
              "license 必须是非空字符串")

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        check(isinstance(compatibility, str) and 1 <= len(compatibility) <= 500,
              "compatibility 必须是 1–500 个字符的字符串")

    metadata = frontmatter.get("metadata")
    if metadata is not None:
        check(isinstance(metadata, dict), "metadata 必须是键值映射")
        if isinstance(metadata, dict):
            check(all(isinstance(k, str) and isinstance(v, str)
                      for k, v in metadata.items()),
                  "metadata 的键和值都必须是字符串")
            if "version" in metadata:
                check(metadata["version"] == version,
                      "SKILL.md metadata.version 与仓库 VERSION 不一致")

    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None:
        check(isinstance(allowed_tools, str),
              "allowed-tools 必须是空格分隔的字符串")

    check(bool(body.strip()), "SKILL.md Markdown 正文不能为空")


def main():
    version = read_repo_text("VERSION").strip()
    check(bool(re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version)),
          "VERSION 必须符合 x.y.z 语义化版本格式")

    check(SKILL_DIR.is_dir(), f"缺少标准 Skill 目录：{SKILL_DIR.relative_to(ROOT)}")
    if not SKILL_DIR.is_dir():
        return report()

    actual_files = {
        item.relative_to(SKILL_DIR).as_posix()
        for item in SKILL_DIR.rglob("*") if item.is_file()
    }
    check(actual_files == EXPECTED_SKILL_FILES,
          "Skill 目录必须只包含已审核的运行时文件；缺少：" +
          ", ".join(sorted(EXPECTED_SKILL_FILES - actual_files)) +
          "；多余：" + ", ".join(sorted(actual_files - EXPECTED_SKILL_FILES)))

    check((ROOT / "README.md").is_file(), "仓库根目录必须保留面向用户的 README.md")
    check(not (SKILL_DIR / "README.md").exists(),
          "README.md 是仓库用户手册，不应放进 Skill 目录")
    check(not (ROOT / "SKILL.md").exists(),
          "SKILL.md 必须位于标准 Skill 子目录，而不是仓库根目录")
    check(not (ROOT / "skill-package.json").exists(),
          "Agent Skills 目录本身就是可安装单元，不需要自定义 skill-package.json")

    skill = read_skill_text("SKILL.md")
    check(len(skill.splitlines()) <= 500, "SKILL.md 超过 500 行建议上限")
    validate_frontmatter(skill, version)

    # SKILL.md 应直接声明每份按需资源，避免 reference-to-reference 的深层依赖。
    refs = set(re.findall(r"references/[A-Za-z0-9._-]+", skill))
    expected_refs = {p for p in EXPECTED_SKILL_FILES if p.startswith("references/")}
    check(refs == expected_refs,
          "SKILL.md 必须直接引用全部且仅引用 Skill 内的参考文件；缺少：" +
          ", ".join(sorted(expected_refs - refs)) +
          "；无效：" + ", ".join(sorted(refs - expected_refs)))

    for relative_path in expected_refs:
        check((SKILL_DIR / relative_path).is_file(),
              f"SKILL.md 引用了不存在的文件：{relative_path}")

    # 参考文件不应继续引入第二层 references 路径。
    for relative_path in expected_refs:
        content = read_skill_text(relative_path)
        # JSON Schema 的 $id URI 可以包含目录名 references；它不是二级资源依赖。
        reference_body = re.sub(r'"\$id"\s*:\s*"[^"]+"', "", content)
        check("references/" not in reference_body,
              f"{relative_path} 不应继续引用第二层 references 路径")

    # 正式 Skill 内容不得绑定到具体服务商或产品名称。
    forbidden_patterns = [
        r"DeepSeek", r"OpenAI", r"Anthropic", r"Gemini", r"Groq",
        r"Claude", r"GPT-[0-9]", r"模型供应商", r"模型密钥",
        r"模型 API", r"模型接口"
    ]
    for relative_path in EXPECTED_SKILL_FILES:
        content = read_skill_text(relative_path)
        for pattern in forbidden_patterns:
            if re.search(pattern, content, flags=re.IGNORECASE):
                fail(f"Skill 文件疑似包含具体模型或服务商绑定：{relative_path}（匹配 {pattern}）")

    case_schema = read_skill_json("references/dataset-schema.json")
    if isinstance(case_schema, dict):
        check(case_schema.get("type") == "object", "用例 Schema 根类型必须为 object")
        case_properties = case_schema.get("properties", {})
        required_case_fields = set(case_schema.get("required", []))
        for field in ("scenario_bucket", "case_origin", "coverage_tags",
                      "observable_assertions", "trace_expectations", "change_links"):
            check(field in case_properties, f"用例 Schema 缺少字段：{field}")
        check({"scenario_bucket", "case_origin", "coverage_tags", "execution_requirements"}.issubset(required_case_fields),
              "用例 Schema 必须要求场景桶、来源类型、覆盖标签和执行状态")
        check(case_properties.get("coverage_tags", {}).get("minItems", 0) >= 1,
              "用例 Schema 必须要求至少一个覆盖标签")
        check({"dimension", "value", "coverage_item_id"}.issubset(
            set(case_properties.get("coverage_tags", {}).get("items", {}).get("required", []))
        ), "每个覆盖标签必须关联稳定的 coverage_item_id")
        source_item_required = set(case_properties.get("source_refs", {}).get("items", {}).get("required", []))
        check({"source_type", "title"}.issubset(source_item_required),
              "来源记录必须包含来源类型和可识别标题")
        check(case_properties.get("grading", {}).get("properties", {}).get("criteria", {}).get("minItems", 0) >= 1,
              "每条用例的判定契约必须至少定义一个判定项")
        criterion_required = set(
            case_properties.get("grading", {}).get("properties", {}).get("criteria", {}).get("items", {}).get("required", [])
        )
        check({"criterion_id", "description", "pass_condition", "fail_condition", "evidence_required"}.issubset(criterion_required),
              "评分项必须包含稳定标识、描述、通过/失败条件和证据要求")
        for grading_field in ("pass_conditions", "fail_conditions", "evidence_required"):
            check(case_properties.get("grading", {}).get("properties", {}).get(grading_field, {}).get("minItems", 0) >= 1,
                  f"判定契约字段 {grading_field} 必须至少包含一项")
        check("information_gaps" in case_properties and
              "quality_review" in case_properties,
              "用例 Schema 必须支持信息缺口与可追溯质量审查")
        bucket_schema = case_properties.get("scenario_bucket", {})
        bucket = bucket_schema.get("items", {}).get("enum", [])
        check("scenario_type" not in case_properties,
              "用例 Schema 不得保留与 scenario_bucket 重叠的旧分类字段")
        check(bucket_schema.get("type") == "array" and bucket_schema.get("minItems", 0) >= 1
              and bucket_schema.get("uniqueItems") is True,
              "scenario_bucket 必须是至少包含一个且不重复的数组")
        check({"normal", "boundary", "business_rule", "permission_security",
               "state_anomaly", "error_recovery", "multi_turn",
               "tool_interaction", "negative", "adversarial",
               "data_quality", "integration"}.issubset(set(bucket)),
              "用例 Schema 的场景桶枚举不完整")
        methods = case_properties.get("grading", {}).get("properties", {}).get("method", {}).get("enum", [])
        check("rubric_based" in methods and "llm_judge" not in methods,
              "判定方法枚举必须保持实现无关")

    manifest_schema = read_skill_json("references/dataset-manifest-schema.json")
    if isinstance(manifest_schema, dict):
        check(manifest_schema.get("type") == "object", "数据集清单 Schema 根类型必须为 object")
        manifest_required = set(manifest_schema.get("required", []))
        check({"dataset_id", "version", "evaluation_target", "purpose",
               "scope", "coverage", "case_count", "quality_status",
               "execution_status"}.issubset(manifest_required),
              "数据集清单 Schema 缺少必需字段")
        properties = manifest_schema.get("properties", {})
        check("dimensions" in properties.get("coverage", {}).get("properties", {}),
              "数据集清单 Schema 缺少覆盖维度定义")
        check("data_splits" in properties and "leakage_check" in properties,
              "数据集清单 Schema 必须支持适用的数据集划分与独立性证据")

    if yaml is None:
        fail("缺少 PyYAML；无法验证机器可读质量标准")
    else:
        try:
            config = yaml.safe_load(read_skill_text("references/quality-standard.yaml"))
            standard = config.get("standard", {})
            check(standard.get("id") == "agent-skill-dataset-quality",
                  "质量标准 id 无效")
            check(standard.get("version") == "2.0.0",
                  "质量标准版本必须为 2.0.0")
            check(standard.get("applies_to_release") == "0.0.2",
                  "质量标准必须声明适用于 0.0.2")
            check(set(standard.get("targets", [])) ==
                  {"agent", "skill", "agent_with_skill"},
                  "质量标准必须覆盖通用 Agent、Skill 和 Agent+Skill")
            check(set(standard.get("purposes", [])) ==
                  {"capability", "regression", "both"},
                  "质量标准必须支持 Capability 与 Regression")

            paths = config.get("assessment_paths", {})
            independent = paths.get("independent", {})
            runtime = paths.get("runtime", {})
            check(independent.get("id") == "IDA" and
                  independent.get("requires_agent_execution") is False and
                  independent.get("runtime_metrics_allowed") is False,
                  "IDA 必须是独立离线评价且不得包含运行专属指标")
            check(runtime.get("id") == "ERA" and
                  runtime.get("requires_agent_execution") is True and
                  runtime.get("requires_exact_version_binding") is True,
                  "ERA 必须要求真实运行和精确版本绑定")
            for assessment in (independent, runtime):
                schema_ref = assessment.get("report_schema")
                schema_path = SKILL_DIR / "references" / schema_ref if isinstance(schema_ref, str) else None
                check(schema_path is not None and schema_path.is_file(),
                      f"缺少 Skill 内的评价报告 Schema：{schema_ref}")

            required_gates = {
                "G01_source_provenance", "G02_construct_alignment",
                "G03_task_solvability", "G04_ground_truth_validity",
                "G05_rubric_validity", "G06_safety_authorization",
                "G07_integrity_leakage", "G08_runtime_auditability"
            }
            configured_gates = set(config.get("critical_gates", []))
            check(required_gates.issubset(configured_gates),
                  "质量标准缺少必要的关键门禁")
            check(len(configured_gates) == len(config.get("critical_gates", [])),
                  "关键门禁不得重复")

            composite = config.get("composite", {})
            check(composite.get("enabled_by_default") is False,
                  "未验证的综合评分不得默认启用")
            check(composite.get("status") == "NOT_VALIDATED",
                  "综合评分初始状态必须为 NOT_VALIDATED")
            check(composite.get("value") is None and
                  composite.get("weights") is None and
                  composite.get("thresholds") is None,
                  "未验证的综合评分不得设置数值、权重或阈值")
            check(bool(composite.get("candidate_models")),
                  "必须保留候选模型族以供实证比较")

            for key in ("validation_protocol", "validation_experiments"):
                ref = composite.get(key)
                if isinstance(ref, str) and ref.startswith("https://github.com/Kairos0922/evaluation-dataset-builder/blob/main/"):
                    relative = ref.split("/blob/main/", 1)[1].split("#", 1)[0]
                    resolved = ROOT / relative
                else:
                    resolved = ROOT / ref if isinstance(ref, str) else None
                check(resolved is not None and resolved.is_file(),
                      f"综合公式缺少验证依据文件：{ref}")

            governance = config.get("governance", {})
            for key in ("metric_catalog", "methodology", "research_evidence"):
                ref = governance.get(key)
                if isinstance(ref, str) and ref.startswith("https://github.com/Kairos0922/evaluation-dataset-builder/blob/main/"):
                    relative = ref.split("/blob/main/", 1)[1].split("#", 1)[0]
                    resolved = ROOT / relative
                else:
                    resolved = ROOT / ref if isinstance(ref, str) else None
                check(resolved is not None and resolved.is_file(),
                      f"质量标准缺少治理引用：{ref}")
            check(governance.get("no_unvalidated_thresholds") is True,
                  "必须禁止未经验证的阈值")
            check(governance.get("no_compensation_for_critical_gate_failure") is True,
                  "关键门禁失败不得被其他维度补偿")
            check(governance.get("report_evidence_sufficiency_separately") is True,
                  "必须单独报告证据充分性")

            markdown = read_skill_text("references/quality-standard.md")
            check("独立离线评价（IDA）" in markdown and
                  "真实环境运行评价（ERA）" in markdown,
                  "质量标准文档必须分别定义 IDA 与 ERA")
            check("当前标准不提供已验证的通用综合分" in markdown,
                  "质量标准必须明确当前没有已验证的通用综合分")
            check("不预设" in markdown or "不得" in markdown,
                  "质量标准必须明确禁止未经验证的权重或阈值")
        except Exception as exc:
            fail(f"质量标准配置无效：{exc}")

    try:
        suite = json.loads(read_repo_text("tests/self-eval-cases.json"))
    except Exception as exc:
        fail(f"自评测试集不是有效 JSON：{exc}")
        suite = None
    if isinstance(suite, dict):
        cases = suite.get("cases", [])
        ids = [case.get("id") for case in cases]
        check(len(cases) >= 10, "自评测试集至少需要 10 条用例")
        check(len(ids) == len(set(ids)), "自评测试用例 ID 重复")
        check(all(case.get("prompt") and case.get("expected") for case in cases),
              "自评测试用例缺少 prompt 或 expected")

    try:
        trigger_suite = json.loads(read_repo_text("tests/trigger-evals.json"))
    except Exception as exc:
        fail(f"触发测试集不是有效 JSON：{exc}")
        trigger_suite = None
    if isinstance(trigger_suite, dict):
        evals = trigger_suite.get("evals", [])
        positives = sum(item.get("should_trigger") is True for item in evals)
        negatives = sum(item.get("should_trigger") is False for item in evals)
        check(positives >= 20, "触发测试至少需要 20 条正向用例")
        check(negatives >= 20, "触发测试至少需要 20 条负向用例")
        check(positives == negatives, "触发测试正负样本数量必须平衡")
        check(len({item.get("query") for item in evals}) == len(evals),
              "触发测试 query 重复")
        check(all(item.get("query") and isinstance(item.get("should_trigger"), bool) for item in evals),
              "触发测试条目格式无效")

    return report()


def report():
    if ERRORS:
        print("验证失败：")
        for item in ERRORS:
            print(f"- {item}")
        return 1
    print("验证通过：Agent Skills 目录与元数据、按需引用、Schema、质量标准和离线测试数据。")
    print("注意：静态验证不能替代真实使用场景评测和目标宿主环境验证。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
