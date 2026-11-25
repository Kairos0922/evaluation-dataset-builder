# v0.0.2 架构与验收基线

**状态：** 已建立的工程基线；发布批准与实证效度结论仍独立受控  
**基线日期：** 2026-11-26  
**需求来源：** Issue #43、requirements.md、decision-log.md D-001 至 D-006

## 1. 目标与非目标

本版本为通用 Agent、Skill、Agent+Skill 及多工具工作流评测集提供可审计的质量评价体系，支持 Capability 与 Regression 两种用途。

本版本不承诺交付一个通用标量总分，不继承 0.0.1 未经独立验证的权重或阈值，不将 Schema/CI 通过解释为语义效度，不将 Builder 自己生成的预期答案当作独立 Gold。

## 2. 架构边界

系统由五个逻辑层组成：

1. **输入与身份层**：数据集 Manifest、JSONL、来源注册表、目标对象/版本、运行协议和 SHA-256 身份。
2. **IDA 离线评价层**：读取数据集及其来源/覆盖声明，不执行被测 Agent；输出结构、来源可解析性、覆盖一致性、重复和证据缺口等可确定性结果。
3. **ERA 运行证据层**：从真实 Runner/Trace/Oracle 结果形成 Runtime Record；必须绑定数据集、目标版本、模型、Harness、环境、工具和运行身份。
4. **分析与验证层**：分别分析共享运行质量、Capability 和 Regression；校验报告 Schema 与跨字段不变量；Judge 校准、专家内容效度和公式验证使用独立证据契约。
5. **治理与发布层**：持久化 TASKS、决策、实验协议、CI、PR、CHANGELOG、版本元数据、Release Gate 和最终发布证据。

## 3. 两条不可互相替代的评价路径

### 3.1 IDA

输入：Manifest、Cases JSONL、可选来源注册表、冻结的评审协议及独立审查记录。

输出：IDA 机器可读报告。机器检查只对可确定性属性给出结论；构念对齐、任务可解性、Gold 正确性、语义 Rubric、泄漏和污染必须依赖来源核验、独立专家或专门审计。

### 3.2 ERA

输入：冻结数据集 SHA、Agent/Skill revision、模型、Harness、工具、环境、执行参数、随机种子、Runner/Trace、Judge 与独立 Gold/Oracle。

输出：逐次 Runtime Record 和 ERA 报告。无真实记录时使用 NOT_RUN；环境失败、Agent 失败、Judge 失败、UNKNOWN 分开记载，不得从缺失数据推断 PASS。

### 3.3 用途专属分支

- Capability：描述任务响应画像；仅在响应矩阵、模型假设和样本条件支持时使用 IRT、DIF、Test Information 或 G-Theory。
- Regression：同任务/环境/协议配对比较；分别报告历史故障、变异缺陷、False Pass/False Fail、失败暴露、重复性和成本。
- 不允许用 Capability 的平均通过率替代 Regression 配对结果，也不允许用 Mutation Score 替代真实故障检出。

## 4. 证据等级与关键不变量

- **结构证据**：Schema、字段完整性、哈希和跨字段约束。
- **确定性质量证据**：来源身份/解析、覆盖声明一致性、精确重复等。
- **独立语义证据**：专家盲评、独立仲裁、外部 Oracle、独立 Judge 校准。
- **实证运行证据**：真实 Agent/Skill 运行、故障回放、重复运行和外部效标。
- **验证结论**：只有冻结协议、独立数据和预注册分析支持时才可升级。

关键不变量：

1. IDA 与 ERA 独立报告。
2. 关键门禁不能被平均值抵消。
3. 未知、未运行、未评估、不适用是不同状态。
4. 任何综合值默认关闭；无效度证据时 value=null、status=NOT_VALIDATED。
5. Builder 生成的 expected behavior、reference outcome 或自评标签不得充当独立 Gold。
6. 双盲评审者互不交流；仲裁者独立；12-case freeze 必须完整且 hash-bound。
7. Freeze Gate 验证成功本身不启动 Runner；执行仍须独立授权。
8. 生产凭据、个人数据和第三方受限 Benchmark 数据不得进入公开仓库或报告。

## 5. 模块与数据流

```text
Manifest + Cases + Source Registry
                |
                v
        IDA Deterministic Checker
                |
                v
           IDA Report -----------+
                                 |
Frozen Run Protocol              |
+ Dataset / Target / Environment |
                |                |
                v                |
       Runner / Trace / Oracle   |
                |                |
                v                |
          Runtime Records        |
                |                |
                v                |
       ERA Capability / Regression
                |                |
                +-------> Report Contract Validator
                                 |
Expert Review / Judge Calibration / Mutation / External Criteria
                |
                v
      Independent Evidence Contracts
                |
                v
       Formula Validation Protocol
                |
                v
  NOT_VALIDATED unless independent evidence supports scope
```

## 6. 版本与兼容策略

- 0.0.1 保持已发布版本和历史证据不变。
- 0.0.2 开发资产、Schema 和分析器在独立分支演进。
- 对机器可读契约的破坏性变更必须提升 schema_version，并同步测试、Skill reference（若属于正式包）、文档和 Release Gate。
- 运行报告必须绑定精确版本和 SHA；无法确认的版本身份不得纳入确认性分析。
- 不将仅供研究的协议、验证器或数据集加入正式 Skill 包，除非其确实属于运行时用户功能。

## 7. 验收基线

| 层级 | 必需证据 | 通过含义 | 不代表 |
|---|---|---|---|
| 结构/包 | Skill validator、Schema、引用检查 | 包结构和契约正确 | 语义有效 |
| 确定性检查 | IDA/ERA validator、单测 | 已编码不变量正确执行 | 缺陷目录完整 |
| 专家效度 | 独立盲评、仲裁、原始评分、CVI/CVR/Aiken's V | 在明确专家样本范围内获得内容证据 | 所有领域专家共识 |
| Judge 效度 | 独立 Gold、校准协议、盲法、重复评分、错误分析 | 在指定任务/模型/版本范围内估计 Judge 表现 | 通用 Judge 有效 |
| 缺陷检出 | 盲测、独立确认变异、控制样本、区间 | 估计指定缺陷族检出/误报 | 真实故障泛化 |
| Capability | 多 Agent × Task 响应、模型诊断、独立效标 | 指定能力范围内测量证据 | 跨域普遍能力 |
| Regression | 配对版本、历史故障、变异、重复运行 | 指定回归集上的变化与检出证据 | 所有未来回归 |
| 公式 | 预注册、独立开发/验证切分、外部效标、敏感性 | 在明确范围内 VALIDATED_FOR_SCOPE 或诚实拒绝 | 通用固定权重/阈值 |
| 发布 | 精确候选 SHA 的全部适用门禁、审查和用户批准 | 可发布候选 | 未经批准自动发布 |

## 8. 当前基线状态

本文件冻结的是**工程边界、数据流和验收解释规则**，不是实验结论或发布批准。Round 4 当前已知证据为 15 条用例、3 条真实 Pilot、12 条 NOT_RUN；IDA/ERA 均 PARTIAL，Judge NOT_RUN，Regression 无配对，IRT/G-Theory 未拟合，综合分 NOT_VALIDATED。具体数值以 `round4-real-evidence-results.md` 和最新 CI artifact 为准。

## 9. 变更控制

修改本基线须同时更新 decision-log、TASKS、受影响 Schema/验证器/测试和验收证据。不得仅通过修改文档降低验收标准；不得把外部阻塞改写为 DONE。
