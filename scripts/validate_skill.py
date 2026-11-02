#!/usr/bin/env python3
"""评测数据集构建 Skill 的结构、打包与模型无关性验证器。"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []
WARNINGS = []

def fail(message):
    ERRORS.append(message)

def check(condition, message):
    if not condition:
        fail(message)

def read_text(relative):
    path = ROOT / relative
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        fail(f"无法读取 {relative}：{exc}")
        return ""

def read_json(relative):
    try:
        return json.loads(read_text(relative))
    except Exception as exc:
        fail(f"{relative} 不是有效 JSON：{exc}")
        return None

def under_any(path, prefixes):
    return any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)

def main():
    manifest = read_json("skill-package.json")
    if not isinstance(manifest, dict):
        return report()

    version = read_text("VERSION").strip()
    check(bool(re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version)),
          "VERSION 必须符合 x.y.z 语义化版本格式")
    check(manifest.get("version") == version, "skill-package.json 与 VERSION 版本不一致")
    check(manifest.get("entrypoint") == "SKILL.md", "入口文件必须为 SKILL.md")

    included = manifest.get("included_files", [])
    excluded = manifest.get("excluded_paths", [])
    check(isinstance(included, list) and bool(included), "included_files 必须是非空数组")
    check(isinstance(excluded, list), "excluded_paths 必须是数组")
    check(len(included) == len(set(included)), "included_files 存在重复路径")

    # 正式运行包采用精确白名单，防止无关文档或开发资产被意外打包。
    required = {
        "SKILL.md", "LICENSE",
        "references/host-agent-capability-adapter.md",
        "references/terminology.md",
        "references/quality-standard.md",
        "references/quality-standard.yaml",
        "references/dataset-schema.json",
        "references/grader-guidelines.md",
        "references/coverage-design-guideline.md",
        "references/source-and-evidence-policy.md",
        "references/business-scenario-model.md",
        "references/scenario-buckets.md",
        "references/change-impact-and-repair.md",
        "references/dataset-manifest-schema.json"
    }
    included_set = set(included)
    check(required.issubset(included_set),
          "正式包清单缺少必需文件：" + ", ".join(sorted(required - included_set)))
    check(included_set == required,
          "正式包清单必须与已审查的运行时白名单完全一致；未批准的额外文件：" +
          ", ".join(sorted(included_set - required)))
    check("README.md" not in included_set,
          "README.md 是仓库说明文档，不得进入正式 Skill 运行包")

    for rel in included:
        path = ROOT / rel
        check(path.is_file(), f"正式包文件不存在：{rel}")
        check(not under_any(rel, ["tests", "scripts", ".github"]),
              f"开发或测试文件不得进入正式包：{rel}")
        check(not rel.lower().endswith((".pyc", ".log", ".env")),
              f"正式包包含不允许的文件类型：{rel}")

    skill = read_text("SKILL.md")
    check(skill.startswith("---\n"), "SKILL.md 必须以 YAML frontmatter 开始")
    parts = skill.split("---", 2)
    if len(parts) >= 3:
        fm = parts[1].strip()
        name = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", fm)
        desc = re.search(r"(?m)^description:\s*(.+)$", fm)
        check(bool(name), "SKILL.md 缺少有效的 name 属性")
        check(bool(desc), "SKILL.md 缺少 description 属性")
        if name:
            check(len(name.group(1)) <= 64, "name 属性超过 64 个字符")
        if desc:
            check(len(desc.group(1)) <= 1024, "description 属性超过 1024 个字符")
    check(len(skill.splitlines()) <= 500, "SKILL.md 超过 500 行建议上限")

    # 验证入口文件引用的正式参考文件存在。
    refs = re.findall(r"references/[A-Za-z0-9._-]+", skill)
    for rel in refs:
        check((ROOT / rel).is_file(), f"SKILL.md 引用了不存在的文件：{rel}")
        check(rel in included, f"SKILL.md 引用的文件未纳入正式包：{rel}")

    # 对正式包做模型/供应商耦合检查。只检查自然语言文件，不扫描固定属性和法律文本。
    forbidden_patterns = [
        r"DeepSeek", r"OpenAI", r"Anthropic", r"Gemini", r"Groq",
        r"Claude", r"GPT-[0-9]", r"\bLLM\b", r"\bllm[_-](?:judge|grader)\b",
        r"模型供应商", r"模型密钥", r"模型 API", r"模型接口",
        r"上下文窗口", r"最大输出 Token"
    ]
    scan_files = [p for p in included if p != "LICENSE"]
    for rel in scan_files:
        path = ROOT / rel
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if re.search(pattern, content, flags=re.IGNORECASE):
                fail(f"正式包疑似包含模型或供应商耦合内容：{rel}（匹配 {pattern}）")

    schema = read_json("references/dataset-schema.json")
    if schema:
        check(schema.get("type") == "object", "用例 Schema 根类型必须为 object")
        check(bool(schema.get("required")), "用例 Schema 缺少 required 字段")
        check(bool(schema.get("properties")), "用例 Schema 缺少 properties")
        case_properties = schema.get("properties", {})
        for field in ("scenario_bucket", "case_origin", "coverage_tags",
                      "observable_assertions", "trace_expectations", "change_links"):
            check(field in case_properties, f"用例 Schema 缺少新规范字段：{field}")
        required_case_fields = set(schema.get("required", []))
        check({"scenario_bucket", "case_origin", "coverage_tags"}.issubset(required_case_fields),
              "用例 Schema 必须要求场景桶、来源类型和覆盖标签")
        check(case_properties.get("coverage_tags", {}).get("minItems", 0) >= 1,
              "用例 Schema 必须要求至少一个覆盖标签")
        bucket = case_properties.get("scenario_bucket", {}).get("enum", [])
        check({"normal", "boundary", "business_rule", "permission_security",
               "state_anomaly", "error_recovery", "multi_turn",
               "tool_interaction", "negative", "adversarial",
               "data_quality", "integration"}.issubset(set(bucket)),
              "用例 Schema 的场景桶枚举不完整")

    manifest_schema = read_json("references/dataset-manifest-schema.json")
    if manifest_schema:
        check(manifest_schema.get("type") == "object", "数据集清单 Schema 根类型必须为 object")
        manifest_required = set(manifest_schema.get("required", []))
        check({"dataset_id", "version", "evaluation_target", "purpose",
               "scope", "coverage", "case_count", "quality_status",
               "execution_status"}.issubset(manifest_required),
              "数据集清单 Schema 缺少必需字段")
        manifest_properties = manifest_schema.get("properties", {})
        check("coverage" in manifest_properties and "dimensions" in
              manifest_properties.get("coverage", {}).get("properties", {}),
              "数据集清单 Schema 缺少覆盖维度定义")

    suite = read_json("tests/self-eval-cases.json")
    if suite:
        cases = suite.get("cases", [])
        ids = [case.get("id") for case in cases]
        check(len(cases) >= 10, "自评测试集至少需要 10 条用例")
        check(len(ids) == len(set(ids)), "自评测试用例 ID 重复")
        check(all(case.get("prompt") and case.get("expected") for case in cases),
              "自评测试用例缺少 prompt 或 expected")

    trigger_suite = read_json("tests/trigger-evals.json")
    if trigger_suite:
        evals = trigger_suite.get("evals", [])
        positives = sum(item.get("should_trigger") is True for item in evals)
        negatives = sum(item.get("should_trigger") is False for item in evals)
        check(positives >= 20, "触发测试至少需要 20 条正向用例")
        check(negatives >= 20, "触发测试至少需要 20 条负向用例")
        check(positives == negatives, "触发测试正负样本数量必须平衡")
        check(len({item.get("query") for item in evals}) == len(evals), "触发测试 query 重复")
        check(all(item.get("query") and isinstance(item.get("should_trigger"), bool) for item in evals),
              "触发测试条目格式无效")

    # 质量标准 YAML 与数据结构的静态检查。
    yaml_path = ROOT / "references/quality-standard.yaml"
    if yaml_path.is_file():
        try:
            import yaml
            cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            weights = cfg["scoring"]["weights"]
            check(sum(weights.values()) == 100, "质量评分权重之和必须为 100")
            check(all(isinstance(v, (int, float)) and 0 < v <= 100 for v in weights.values()),
                  "质量评分权重必须为 0 到 100 之间的正数")
            check(bool(cfg["scoring"]["critical_gates"]), "质量标准缺少关键门禁")
            dataset_checks = set(cfg.get("checks", {}).get("dataset_level", []))
            required_dataset_checks = {
                "business_model_traceability", "gap_priority_coverage",
                "synthetic_case_labeling", "observable_assertion_coverage",
                "trace_evidence_coverage", "change_impact_traceability"
            }
            check(required_dataset_checks.issubset(dataset_checks),
                  "机器可读质量标准缺少新数据集级检查项")
        except ImportError:
            WARNINGS.append("未安装 PyYAML，跳过 YAML 语义检查")
        except Exception as exc:
            fail(f"质量标准 YAML 无效：{exc}")

    return report()

def report():
    if ERRORS:
        print("验证失败：")
        for item in ERRORS:
            print(f"- {item}")
        for item in WARNINGS:
            print(f"警告：{item}")
        return 1
    for item in WARNINGS:
        print(f"警告：{item}")
    print("验证通过：包清单、入口引用、模型无关性、Schema、测试集与质量标准结构。")
    print("注意：静态验证不能替代语义审查和目标环境行为测试。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
