"""Regression guard for the Builder's bounded production protocol."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks" / "webapp-testing" / "BUILDER-TASK.md"
RUNTIME_CONTRACT = ROOT / "benchmarks" / "webapp-testing" / "assets" / "public" / "runtime-and-tool-contracts.md"


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


def test_builder_task_requires_mutation_and_script_execution_budgets():
    task = TASK.read_text(encoding="utf-8")
    runtime = RUNTIME_CONTRACT.read_text(encoding="utf-8")
    required_task = (
        "明确每条用例的动作预算和执行次数",
        "max_mutating_actions",
        "max_test_script_executions",
        "3 次状态变更、1 次脚本执行",
        "1 次确认删除",
        "重复执行、重新点击和重试都计入总预算",
        "不得为了补齐证据重复执行或重置",
    )
    required_runtime = (
        "## 6. 动作预算与重复执行",
        "3 次状态变更、1 次测试脚本执行",
        "1 次确认删除",
        "最终状态正确不抵消超出动作预算的副作用",
    )
    missing = [phrase for phrase in required_task if phrase not in task]
    missing.extend(f"runtime:{phrase}" for phrase in required_runtime if phrase not in runtime)
    assert not missing, f"Explicit action-budget contract is incomplete: {missing}"


def test_builder_task_separates_skill_defect_detection_from_application_compliance():
    task = TASK.read_text(encoding="utf-8")
    required = (
        "评分主体与缺陷发现语义（强制）",
        "本任务的评测对象是执行 Web 应用测试的 webapp-testing Skill，不是 Workboard 应用本身。",
        "准确观察、正确解释并如实报告 FAIL",
        "不得把“应用返回错误结果”直接写成 Skill 的 criterion fail_condition",
        "case-level pass_conditions / fail_conditions 与每个 criterion 的语义一致性",
    )
    missing = [phrase for phrase in required if phrase not in task]
    assert not missing, f"Builder task does not disambiguate the evaluation subject: {missing}"


class BuilderReadmeCaseGroupingTests(unittest.TestCase):
    def test_case_groups_must_match_case_semantics(self):
        text = TASK.read_text(encoding="utf-8")
        required = (
            "README 用例分组必须与实际用例语义一致",
            "不得按 case_id 连续编号或文件顺序机械切分",
            "不得把只读侦察用例归入写操作组",
            "所有 case_id 恰好出现一次",
            "分组数量之和必须等于 JSONL 实际用例数",
        )
        missing = [phrase for phrase in required if phrase not in text]
        self.assertFalse(missing, f"README case grouping contract is incomplete: {missing}")
