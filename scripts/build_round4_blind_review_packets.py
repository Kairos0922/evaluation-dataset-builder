#!/usr/bin/env python3
"""Build two independently blinded Oracle-review packets from frozen Builder cases."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import tempfile
import zipfile
from pathlib import Path

def _reject_json_constant(token: str):
    raise ValueError(f"invalid JSON numeric constant: {token}")


EXPECTED_DATASET_SHA256 = "000d38b110b60eae902f86737ea6bd1368f98c6632c42a47bb9470a4a08bfc45"
TARGET_CASE_IDS = {
    "WB-01", "WB-03", "WB-04", "WB-05", "WB-06", "WB-07",
    "WB-08", "WB-09", "WB-11", "WB-13", "WB-14", "WB-15",
}
PUBLIC_ASSETS = (
    "business-rules.md",
    "application-overview.md",
    "capability-description.md",
    "runtime-and-tool-contracts.md",
)
FORBIDDEN_CASE_FIELDS = {
    "title", "objective", "expected_behavior", "forbidden_behavior",
    "reference_outcome", "grading", "observable_assertions",
    "trace_expectations", "quality_status", "assumptions",
    "coverage_tags", "execution_requirements", "business_rule_refs",
    "workflow_refs", "scenario_bucket", "case_origin",
}
PACKET_SCHEMA_VERSION = "1.0.0"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_cases(dataset_path: Path, expected_dataset_sha256: str | None = EXPECTED_DATASET_SHA256):
    raw = dataset_path.read_bytes()
    dataset_sha256 = sha256_bytes(raw)
    if expected_dataset_sha256 and dataset_sha256 != expected_dataset_sha256:
        raise ValueError(
            f"frozen dataset SHA-256 mismatch: expected {expected_dataset_sha256}, got {dataset_sha256}"
        )

    selected = {}
    for line_no, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line, parse_constant=_reject_json_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"invalid dataset JSONL at line {line_no}: {exc}") from exc
        case_id = item.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"dataset line {line_no} has no case_id")
        if case_id in selected:
            raise ValueError(f"duplicate case ID: {case_id}")
        if case_id in TARGET_CASE_IDS:
            selected[case_id] = {
                "case_id": case_id,
                "case_sha256": sha256_bytes(line),
                "user_input": item.get("user_input"),
            }
    missing = TARGET_CASE_IDS - set(selected)
    if missing:
        raise ValueError("frozen dataset missing target cases: " + ", ".join(sorted(missing)))
    for case_id, item in selected.items():
        if not isinstance(item["user_input"], str) or not item["user_input"].strip():
            raise ValueError(f"{case_id} has no usable user_input")
    return dataset_sha256, selected


def _write_zip(source_dir: Path, archive_path: Path):
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir.parent))


def _worksheet(label: str) -> str:
    return f"""# 独立 Oracle 审查工作表：{label}

> 请独立完成，不与另一位审查者讨论本条内容。只依据本包中的任务原文和公开规范资产形成判断。不要猜测被测应用实际表现；本表记录的是执行前 Oracle 设计审查。

## A. 构念与任务有效性

- 主要测量构念：
- 次要构念（如有）：
- 任务是否与构念相关：ESSENTIAL / USEFUL_NOT_ESSENTIAL / NOT_NECESSARY
- 任务可理解性：1 / 2 / 3 / 4
- 任务可执行性：1 / 2 / 3 / 4
- 可能的构念污染或无关难度：
- 任务是否存在歧义？请引用原文：

## B. 独立规范与 Oracle 断言

请自行从公开业务规则和能力/运行契约中识别规范，不要把任务提示中的结论当作规范真值。

| Assertion ID | 规范来源/条款 | 应观察的行为或状态 | 独立证据方法 | PASS 条件 | FAIL 条件 | UNKNOWN 条件 |
|---|---|---|---|---|---|---|
| | | | | | | |

## C. 双结果判定规则

- Application outcome 如何独立判定：
- Skill outcome 如何独立判定：
- 当应用违反规则但 Skill 准确发现并报告时，应如何判定：
- 当证据不足、环境污染或运行中断时，应如何处理：

## D. 动作预算与安全边界

- 允许的写操作/状态变更次数：
- 允许的脚本/流程执行次数：
- 必须禁止的副作用：
- 运行前必须核验的初始状态：
- 必须立即停止并标记 UNKNOWN 的条件：

## E. 评审结论

- Oracle 设计是否足以在执行前冻结：YES / NO / NEEDS_REVISION
- 需要补充的规范或证据：
- 与其他审查者可能存在的关键分歧：
- 评审理由（至少 2 个可核验证据引用）：

Reviewer pseudonym:
Review timestamp (UTC):
Protocol version: Round4 Oracle independent review v1.0
"""


def _reviewer_readme(slot: str, dataset_sha: str, source_hashes: dict[str, str]) -> str:
    source_rows = "\n".join(f"- {name} SHA-256: {digest}" for name, digest in source_hashes.items())
    return f"""# Round 4 独立 Oracle 盲审资料包

**Reviewer slot:** {slot}  
**Packet schema:** {PACKET_SCHEMA_VERSION}  
**Frozen dataset SHA-256:** {dataset_sha}

## 审查目的

请独立审查 12 条任务是否具有可辩护、可执行、可观察的 Oracle 判定规则。你需要从任务原文和公开规范资产出发，独立定义断言、证据方法、PASS/FAIL/UNKNOWN 条件、双结果判定及动作预算。

## 盲审要求

1. 不与另一位审查者共享任务排序、标签或判断，先独立提交全部工作表。
2. 本包刻意不包含 Builder 生成的 case title、objective、expected_behavior、grading、reference_outcome、observable_assertions、trace_expectations 或质量标签。
3. 任务提示是原始输入，不是规范真值。规范以公开业务规则为准；应用实现不是规范来源。
4. 分开评价 Application 与 Skill。应用失败不自动意味着 Skill 失败；Skill 准确识别并报告应用偏差，仍可能是 Skill PASS。
5. 对证据缺失、状态不干净、哈希不符、预算超限或执行中断，使用 UNKNOWN，不得推测补齐。
6. 任何分歧必须保留两份原始意见，再单独仲裁。不得覆盖原始记录。
7. 不要运行用例，不要访问线上系统，不要修改应用；当前任务仅为执行前 Oracle 设计审查。

## 文件结构

- cases/：匿名标签的原始任务提示和空白独立审查表。
- sources/：用于审查的公开输入资产及其哈希。
- manifest.json：本审查包内容哈希，不含原始 case ID。

## 评分锚点

四点评分：1=严重不足；2=有明显缺陷；3=基本充分但需小修；4=充分、明确且可审计。必要性单独使用 ESSENTIAL / USEFUL_NOT_ESSENTIAL / NOT_NECESSARY。

## 公开来源文件

{source_rows}

## 提交要求

请为每条用例填写对应的 review-sheet.md，并单独提供一份总体意见，指出需要冻结、修改或标记 UNKNOWN 的用例。请勿在提交材料中添加真实姓名、邮箱或其他个人身份信息。
"""


def build_packets(
    dataset_path: Path,
    assets_dir: Path,
    output_dir: Path,
    *,
    expected_dataset_sha256: str | None = EXPECTED_DATASET_SHA256,
    seed: int = 20261125,
) -> dict:
    dataset_sha, cases = load_cases(dataset_path, expected_dataset_sha256)
    missing_assets = [name for name in PUBLIC_ASSETS if not (assets_dir / name).is_file()]
    if missing_assets:
        raise ValueError("missing public assets: " + ", ".join(missing_assets))

    output_dir.mkdir(parents=True, exist_ok=True)
    source_bytes = {name: (assets_dir / name).read_bytes() for name in PUBLIC_ASSETS}
    source_hashes = {name: sha256_bytes(data) for name, data in source_bytes.items()}
    result = {"dataset_sha256": dataset_sha, "reviewer_archives": [], "crosswalk_archive": None}

    with tempfile.TemporaryDirectory(prefix="round4-blind-review-") as temp:
        temp_root = Path(temp)
        crosswalk_dir = temp_root / "coordinator"
        crosswalk_dir.mkdir()
        crosswalk_rows = []

        for slot_index, slot in enumerate(("A", "B")):
            reviewer_root = temp_root / f"reviewer-{slot.lower()}"
            (reviewer_root / "cases").mkdir(parents=True)
            (reviewer_root / "sources").mkdir()
            ordered_ids = sorted(cases)
            random.Random(seed + slot_index * 1009).shuffle(ordered_ids)

            for index, case_id in enumerate(ordered_ids, start=1):
                label = f"R{slot}-ITEM-{index:02d}"
                case = cases[case_id]
                case_dir = reviewer_root / "cases" / label
                case_dir.mkdir()
                prompt = case["user_input"].strip()
                (case_dir / "task.md").write_text(
                    f"# 任务原文：{label}\n\n"
                    "> 以下为原始用户任务输入。任务原文不是 Gold Oracle；请独立从规范资产推导判定规则。\n\n"
                    f"{prompt}\n",
                    encoding="utf-8",
                )
                (case_dir / "review-sheet.md").write_text(_worksheet(label), encoding="utf-8")
                crosswalk_rows.append({
                    "reviewer_slot": slot,
                    "blind_label": label,
                    "case_id": case_id,
                    "case_sha256": case["case_sha256"],
                })

            for name, data in source_bytes.items():
                (reviewer_root / "sources" / name).write_bytes(data)

            packet_files = sorted(p for p in reviewer_root.rglob("*") if p.is_file())
            packet_manifest = {
                "packet_schema_version": PACKET_SCHEMA_VERSION,
                "reviewer_slot": slot,
                "dataset_sha256": dataset_sha,
                "source_assets": source_hashes,
                "items": [
                    {
                        "blind_label": p.parent.name,
                        "path": p.relative_to(reviewer_root).as_posix(),
                        "sha256": sha256_bytes(p.read_bytes()),
                    }
                    for p in packet_files
                    if p.name == "task.md"
                ],
                "case_count": len(ordered_ids),
            }
            (reviewer_root / "manifest.json").write_text(
                json.dumps(packet_manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (reviewer_root / "README.md").write_text(
                _reviewer_readme(slot, dataset_sha, source_hashes),
                encoding="utf-8",
            )

            archive_path = output_dir / f"round4-oracle-reviewer-{slot.lower()}.zip"
            _write_zip(reviewer_root, archive_path)
            result["reviewer_archives"].append({
                "reviewer_slot": slot,
                "path": str(archive_path),
                "sha256": sha256_bytes(archive_path.read_bytes()),
                "case_count": len(ordered_ids),
            })

        with (crosswalk_dir / "crosswalk.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["reviewer_slot", "blind_label", "case_id", "case_sha256"],
            )
            writer.writeheader()
            writer.writerows(crosswalk_rows)
        (crosswalk_dir / "README.md").write_text(
            "# Coordinator-only crosswalk\n\n"
            "仅协调者保管。不得放入任何审查者资料包或发送给审查者。"
            "该文件将匿名标签映射回冻结 Builder 用例 ID，并用于收集审查结果。\n",
            encoding="utf-8",
        )
        crosswalk_archive = output_dir / "round4-oracle-review-coordinator-only.zip"
        _write_zip(crosswalk_dir, crosswalk_archive)
        result["crosswalk_archive"] = {
            "path": str(crosswalk_archive),
            "sha256": sha256_bytes(crosswalk_archive.read_bytes()),
        }

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-jsonl", type=Path, required=True)
    parser.add_argument("--assets-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261125)
    parser.add_argument(
        "--expected-dataset-sha256",
        default=EXPECTED_DATASET_SHA256,
        help="Expected frozen dataset SHA-256; use empty string only for isolated tests.",
    )
    args = parser.parse_args()
    result = build_packets(
        args.dataset_jsonl,
        args.assets_dir,
        args.output_dir,
        expected_dataset_sha256=args.expected_dataset_sha256 or None,
        seed=args.seed,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
