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
        "先生成权威数据，再确定性派生产物",
        "一次集中质量审查",
        "仅做有证据的局部修正",
        "明确停止条件",
        "保持质量优先",
        "不得在本次模型运行期间临时编写 Python/JavaScript/Shell 脚本",
        "经过审查的确定性工具",
        "派生逻辑不得创造或改写业务事实",
    )
    missing = [phrase for phrase in required if phrase not in text]
    assert not missing, f"Builder execution protocol is incomplete: {missing}"
