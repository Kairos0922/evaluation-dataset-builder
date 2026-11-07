# Benchmark Schema 与验证设计说明 v0.2

## 目标

为 Evaluation Dataset Builder 建立独立的 Benchmark 验证设施，验证构建产物是否结构完整、引用闭合、覆盖声明有依据，以及实验统计是否正确。该设施不属于 Skill 正式运行包。

## 对象边界

| 对象 | 职责 |
|---|---|
| Task | 定义被测构建任务、输入资产和预期数据集数量 |
| Ground Truth | 保存独立确认的事实、规则、能力、风险和覆盖要求 |
| Dataset Manifest | 每个数据集一个清单，复用正式 dataset-manifest-schema.json |
| Dataset Case | 继续使用正式 Skill 的 dataset-schema.json |
| Defect Specification | 定义可重复使用的缺陷类型和注入策略 |
| Defect Instance | 表示一次独立、可追溯的缺陷注入样本 |
| Benchmark Run | 绑定任务、Ground Truth、输入快照和实验记录 |
| Coverage Validation | 独立确认「数据集 × 覆盖项」是否被指定用例和断言测量 |

## 四层验证

- L1 Schema Validation：JSON Schema 验证字段和数据类型。
- L2 Referential Integrity：跨文件引用、ID 唯一性、状态和统计约束。
- L3 Semantic Validity：专家或独立语义审查。静态校验无法证明自然语言断言是否真的测量目标能力。
- L4 Empirical Validity：真实 Agent 缺陷注入与正常对照实验。未执行时必须标记未运行。

## 多数据集约束

- 顶层使用 dataset_manifests[]，不再使用单数 dataset_manifest。
- Manifest 的 dataset_id 全局唯一。
- 每个 Case 必须且只能通过 dataset_id 归属一个 Manifest。
- 每个 Manifest 的 case_count 必须等于实际归属用例数。
- Task 声明 expected_dataset_count 时，必须与 Manifest 数量一致。
- Ground Truth 覆盖要求通过 dataset_refs 声明适用数据集；省略时适用于所有数据集。
- 每个数据集独立计算覆盖分母、有效覆盖数和缺口。

## 覆盖全集闭环

覆盖分母来自 Ground Truth coverage_requirements，而不是已经生成的 Case。对每个适用的数据集和覆盖项，必须有明确处置记录。

VALID 记录必须闭合到同一数据集中的 Case、Case coverage_tag、grading criterion、证据和独立审查者。NOT_APPLICABLE 必须有理由，且不允许引用 Case/断言。INVALID、INCONCLUSIVE、缺失记录均不得计为覆盖。重复或互相矛盾的处置记录属于错误。

Manifest 中已有 coverage 字段继续作为描述性报告字段；验证器不将其自报数字作为权威覆盖率。验证器根据 Ground Truth 和审查记录重算覆盖统计。验证器只能检查证据引用非空、审查者标识与创建者标识不同，不能证明真实身份或底层证据真实性；L3/L4 必须检查原始证据、执行记录和审查权限。

## 统计定义

defect_id 表示缺陷定义；defect_instance_id 表示独立注入实例；run_id 表示一次 Benchmark 运行。重复运行同一实例不得增加独立缺陷样本数。

报告至少区分：
- 观测检出率：有效观测中 DETECTED 的比例。
- 至少一次检出实例率：每个实例至少一次检出，再按独立实例统计。
- 全部有效重复均检出实例率：每个实例所有有效重复均检出，再按独立实例统计。
- K 分布：每个缺陷实例有效重复次数的分布。
- 正常对照误报率：有有效正常对照执行证据的观测中出现误报的比例。

只有注入 VALID、对照 PASS、注入 Trace 完整，且正常对照执行有唯一 execution ID 与 evidence 的观测才进入检出率分母。执行 ID 在注入组和对照组之间必须全局互斥，也不能跨观测复用。K 不固定时，不将至少一次检出率直接称为标准 pass@K。当前离线汇总不是完整统计推断；正式报告仍需考虑任务/Agent 聚类和适当的置信区间方法。

## 状态

- PASS：结构、引用和适用的离线约束均通过。
- FAIL：存在确定性契约错误。
- INCONCLUSIVE：证据不足或语义裁决未完成。
- ERROR：输入不可解析或验证环境故障。

当前验证器的 PASS 只代表离线契约通过，不代表 L3/L4 已通过。
