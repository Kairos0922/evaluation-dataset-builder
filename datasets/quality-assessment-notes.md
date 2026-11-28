# 质量评价与证据状态说明

## 当前状态（2026-11-28）

- Safety：100/100 条已构建；候选（candidate）；真实 Agent 执行 NOT_RUN。
- Robustness：100/100 条已构建；候选（candidate）；真实 Agent 执行 NOT_RUN。
- 两个数据集的输入已细化为可直接提交的字符串或结构化 Harness fixture；Robustness 覆盖多轮对话、长上下文、结构化文件和模拟工具失败。
- 来源注册表身份解析 PASS；该结果不等于来源主张获得独立核验。
- IDA：已在 GitHub Actions Run #2236（Run ID 46158592359，head `fa49829b3d1518f3b3c84859c36d3cab28eb9525`）对两个数据集分别执行，均为 **PARTIAL / evidence partial**。
- 离线测试：282/282 PASS；两个数据集的 Schema、Manifest、数量、唯一 ID、来源映射、覆盖一致性及 IDA 报告契约均通过。
- IDA 报告 Artifact：[#15268881769](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/46158592359)（`general-agent-benchmark-ida`）。
- Safety IDA digest：`db13fb1fad769ed68ad819faefbbe709435f94f9fa432331952bd210ca79005d`。
- Robustness IDA digest：`d517a68e6a9996e8ec0c7d12ba6a7fdd03f14b0f97f1a6143379ba6de082cc0d`。
- 两份 IDA 报告均保持 composite `NOT_VALIDATED`、value `null`。

## IDA 结论边界

IDA 已检查 Schema、Manifest、case_id / dataset_id / case_count 一致性、来源注册表身份解析、覆盖统计内部一致性和精确 JSON 重复。此次没有发现结构错误、来源注册表解析错误或覆盖统计不一致。

但以下事项仍未被 IDA 自动验证：
- G02 构念与目标对齐：NOT_ASSESSED
- G03 任务可解性：NOT_ASSESSED
- G04 Ground Truth 正确性：NOT_ASSESSED
- G05 Rubric 语义有效性：UNKNOWN
- G06 安全、权限和副作用适当性：NOT_ASSESSED
- G07 泄漏与污染：UNKNOWN
- 语义重复、内容效度和独立专家审查：尚未完成

IDA 的 PARTIAL 是预期的诚实状态，不应被改写为 PASS。结构化校验通过不等于科学效度通过。

## ERA 与综合分

- ERA：无真实 Agent/Skill 运行记录；不得报告真实能力通过率、Judge 有效性、故障检出率、重测可靠性或运行成本。
- Regression：没有同环境、同任务、配对版本的运行记录，不能计算回归检出结论。
- 综合分：`NOT_VALIDATED`；不输出数值、等级、权重或阈值。

## 后续需要的独立证据

1. 独立专家审查安全与鲁棒性构念定义、用例代表性和风险覆盖。
2. 盲法审查逐案预期行为与判定契约，处理评分者分歧。
3. 建立独立 Oracle / Gold 样本并审计来源支持和答案泄漏。
4. 在冻结的 Agent、模型、Harness、工具和环境版本上运行，保留逐案轨迹。
5. 使用重复运行、已知缺陷/受控变异和配对版本数据分别验证 Capability 与 Regression 用途。

本说明不把结构检查、CI 通过或合成用例数量解释为科学效度证明。
