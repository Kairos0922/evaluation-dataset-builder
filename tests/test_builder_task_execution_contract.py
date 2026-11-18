"""Regression guard for the Builder's bounded production protocol."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks" / "webapp-testing" / "BUILDER-TASK.md"


def test_builder_task_requires_bounded_single_pass_execution():
    text = TASK.read_text(encoding="utf-8")
    required = (
        "## 执行协议（强制，优先于默认工作习惯）",
        "一次性读取与建模",
        "先定结构再写产物",
        "直接生成最终文件",
        "一次集中质量审查",
        "仅做有证据的局部修正",
        "明确停止条件",
        "保持质量优先",
        "不得创建临时 Python/JavaScript/Shell 程序",
        "禁止因局部问题重新生成全部数据集",
    )
    missing = [phrase for phrase in required if phrase not in text]
    assert not missing, f"Builder execution protocol is incomplete: {missing}"
