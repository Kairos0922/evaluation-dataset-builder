# Benchmark Schema 与验证设计说明 v0.1

## 目标

为 Evaluation Dataset Builder 建立独立的 Benchmark 验证设施，验证构建产物是否结构完整、引用闭合、覆盖声明有依据，以及实验统计是否正确。该设施不属于 Skill 正式运行包。

## 对象边界

| 对象 | 职责 |
|---|---|
| Task | 定义被测构建任务、输入资产和预期范围 |
| Ground Truth | 保存独立确认的事实、规则、能力、风险和覆盖要求 |
| Dataset Case | 继续使用正式 Skill 的 dataset-schema.json |
| Defect Specification | 定义可重复使用的缺陷类型和注入策略 |
| Defect Instance | 表示一次独立、可追溯的缺陷注入样本 |
| Benchmark Run | 绑定任务、Ground Truth、输入快照和实验记录 |
| Coverage Validation | 独立确认覆盖项是否被指定用例和断言真实测量 |

## 四层验证

- L1 Schema Validation：JSON Schema 验证字段和数据类型。
- L2 Referential Integrity：跨文件引用、ID 唯一性、状态和统计约束。
- L3 Semantic Validity：专家或独立语义审查。静态校验无法证明自然语言断言是否真的测量目标能力。
- L4 Empirical Validity：真实 Agent 缺陷注入与正常对照实验。未执行时必须标记未运行。

## 统计定义

defect_id 表示缺陷定义；defect_instance_id 表示独立注入实例；run_id 表示一次 Benchmark 运行。重复运行同一实例不得增加独立缺陷样本数。

当前离线验证器对有效注入实例去重统计。真实研究报告还应记录任务/Agent 聚类结构，并根据样本设计选择置信区间方法。不得将当前简单汇总误称为完整统计推断。

## 状态

- PASS：结构、引用和适用的离线约束均通过。
- FAIL：存在确定性契约错误。
- INCONCLUSIVE：证据不足或语义裁决未完成。
- ERROR：输入不可解析或验证环境故障。

当前验证器的 PASS 只代表离线契约通过，不代表 L3/L4 已通过。
