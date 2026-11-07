#!/usr/bin/env python3
"""Validate DSH L3 output against the repository schemas and synthetic ground truth."""
import json
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("artifacts/l3-output")
CASE_SCHEMA = json.loads((ROOT / "skills/evaluation-dataset-builder/references/dataset-schema.json").read_text(encoding="utf-8"))
MANIFEST_SCHEMA = json.loads((ROOT / "skills/evaluation-dataset-builder/references/dataset-manifest-schema.json").read_text(encoding="utf-8"))
EXPECTED_COVERAGE = {"COV-01", "COV-02", "COV-03", "COV-04", "COV-05", "COV-06"}

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    required = [
        "dataset-core.jsonl", "dataset-sla-regression.jsonl",
        "manifest-core.json", "manifest-sla-regression.json",
        "coverage-matrix.json", "source-map.json", "quality-report.md",
    ]
    missing = [name for name in required if not (OUT / name).is_file() or (OUT / name).stat().st_size == 0]
    if missing:
        raise SystemExit("缺少必需交付物：" + ", ".join(missing))

    datasets = {}
    all_ids = set()
    coverage = set()
    for filename in ("dataset-core.jsonl", "dataset-sla-regression.jsonl"):
        cases = []
        for line_no, line in enumerate((OUT / filename).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{filename}:{line_no} JSON 无效：{exc}")
            jsonschema.validate(case, CASE_SCHEMA)
            if case["case_id"] in all_ids:
                raise SystemExit("case_id 重复：" + case["case_id"])
            cases.append(case)
            all_ids.add(case["case_id"])
            if case["quality_status"] not in ("candidate", "needs_info"):
                raise SystemExit("用例质量状态不能越过独立审查：" + case["case_id"])
            for tag in case.get("coverage_tags", []):
                coverage.add(tag["coverage_item_id"])
            datasets.setdefault(case["dataset_id"], []).append(case)
        if not cases:
            raise SystemExit(filename + " 未生成任何用例")

    manifests = [
        load_json(OUT / "manifest-core.json"),
        load_json(OUT / "manifest-sla-regression.json"),
    ]
    manifest_ids = set()
    for manifest in manifests:
        jsonschema.validate(manifest, MANIFEST_SCHEMA)
        if manifest["dataset_id"] in manifest_ids:
            raise SystemExit("Manifest dataset_id 重复")
        manifest_ids.add(manifest["dataset_id"])
        owned = datasets.get(manifest["dataset_id"], [])
        if manifest["case_count"] != len(owned):
            raise SystemExit(f"{manifest['dataset_id']} case_count 与实际归属用例数不符")
        if manifest["execution_status"] not in ("NOT_RUN", "DESIGN_ONLY"):
            raise SystemExit("合成 L3 任务不得声称真实执行完成")

    if set(datasets) != manifest_ids:
        raise SystemExit("用例 dataset_id 与 Manifest 集合不一致")
    case_count = len(all_ids)
    if not 6 <= case_count <= 8:
        raise SystemExit(f"用例数量应为 6–8，实际为 {case_count}")
    multi_turn_count = sum("multi_turn" in case.get("scenario_bucket", []) for group in datasets.values() for case in group)
    if not 1 <= multi_turn_count <= 2:
        raise SystemExit(f"应仅为缺少服务名称的上下文补充设计 1–2 条多轮用例，实际为 {multi_turn_count}")
    missing_coverage = EXPECTED_COVERAGE - coverage
    if missing_coverage:
        raise SystemExit("Ground Truth 覆盖项缺失：" + ", ".join(sorted(missing_coverage)))
    if not {"core-ticket-lifecycle", "sla-policy-regression"}.issubset(manifest_ids):
        raise SystemExit("两个数据集未体现不同用途的稳定标识")
    print(json.dumps({
        "status": "PASS",
        "dataset_count": len(manifests),
        "case_count": case_count,
        "coverage_items": sorted(coverage),
        "multi_turn_cases": multi_turn_count,
        "schema_errors": 0,
        "execution_claims": "NOT_RUN/DESIGN_ONLY only",
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
