# v0.0.3 轨迹驱动任务生产架构

## 1. 设计目标

将真实 Agent 工作中的可观察失败转化为可审计的候选评测任务，并通过任务契约、环境重建和独立执行验证其可复现性与测量价值。

本版本扩展 Builder 的任务来源和生产链路，不改变 v0.0.2 IDA / ERA 的基本定义。

## 2. 端到端数据流

```text
Authorized Trace Source
        |
        v
Trace Intake + Provenance
        |
        v
Candidate Discovery (heuristics, not verdicts)
        |
        v
Failure Qualification
        |
        v
Task Slicing + Context Closure
        |
        v
Environment Reconstruction Manifest
        |
        v
Frozen Clean-run Experiment
        |
        +------> Independent Verifier / Oracle
        |
        v
Trace-based Diagnosis + IDA / ERA evidence
```

每一阶段产物均有独立 ID、版本、来源引用和内容哈希。不得覆盖原始轨迹或原始运行记录。

## 3. 核心对象

### 3.1 Trace Source

描述轨迹来源及其使用依据：来源类型、采集/导出时间、宿主与运行身份、授权状态、脱敏状态、原始工件引用及 SHA-256。默认只保存引用和最小必要元数据，不把完整对话、凭据或本地工作区内容复制进候选记录。

### 3.2 Candidate

候选是启发式发现的待审查对象。候选发现信号可以包括用户明确纠偏、同一目标的返工、多轮执行、产物显著变化、明确的输入/交付物线索。信号仅用于排序和定位，不是能力缺陷的证明。

### 3.3 Qualification

必须明确记录：
- 错误决策/失败事件及其轨迹定位；
- 决策发生前 Agent 可见的信息；
- 该信息是否足以发现或避免错误；
- 用户是否在事后补充了关键要求；
- 工具/环境是否健康；
- 任务是否有明确输入、交付物和判定契约；
- 归因及证据充分性。

归因枚举：`agent_decision`、`missing_context`、`task_ambiguity`、`tool_failure`、`environment_failure`、`stochastic`、`mixed`、`unknown`。只有具备支持证据时才可选择具体归因；否则使用 `unknown`。

### 3.4 Task Slice

切片以一个可独立执行和判定的任务为单位，至少包含：
- 原始轨迹的起止事件引用；
- 起点时可见的上下文及其闭包清单；
- 初始状态/输入；
- 预期交付物；
- 约束、权限和禁止副作用；
- 能力假设（作为待验证假设）；
- 判定契约及未知项。

不得把事后反馈、最终答案或隐含答案泄漏到解题者上下文中。合理多解任务必须声明可接受结果范围，而非绑定唯一 Oracle 实现。

### 3.5 Reconstruction Manifest

描述重建任务所需的文件/数据快照、依赖、软件与工具版本、服务、网络、权限、资源预算、随机种子、超时、动作预算、重置和清理策略。重建差异必须记录，不允许默认为与原环境等价。

## 4. 独立验证

- Clean-run 必须使用新的会话/上下文，并绑定冻结的任务、目标、模型、Harness、工具、环境和执行协议身份。
- 运行次数由 Pilot 方差、成本和预注册设计确定；不设未经论证的统一次数。
- Verifier 与 Oracle 独立性沿用 v0.0.2 ERA 要求。Builder 自己生成的答案不得作为唯一 Gold。
- Verifier 需要正例、负例、边界例和合理变体校准；Judge UNKNOWN/abstention 与失败分开。
- 轨迹诊断可记录失败阶段、关键决策、纠偏/返工、错误传播、工具使用和成本，但新增指标先作为诊断证据，不未经验证地聚合成质量分。
- 结果按 Agent、环境、Judge、任务和随机性来源拆分，不将所有失败归咎于数据集。

## 5. 安全与隐私

- 不默认读取用户本地文件、Agent 历史或工作区。
- 仅处理用户明确提供或明确授权的轨迹。
- 凭据、令牌、个人信息、专有数据和无关内容必须在进入数据集前移除或脱敏。
- 原始轨迹优先使用受控外部引用；报告中保存最小必要事件定位和 SHA-256。
- 记录授权范围、保留期限和可撤回/删除流程；授权缺失或范围不清晰时拒绝导入。
- 环境重建禁止隐式执行原轨迹中的危险命令或真实业务副作用。

## 6. IDA / ERA 边界

IDA 可检查轨迹来源字段、授权状态、哈希/引用完整性、切片边界、上下文闭包声明、重建清单完整性和契约结构。确定性校验不能证明轨迹真实、语义归因正确或任务具有构念效度。

ERA 可接收冻结后的 clean-run Runtime Record、Trace、Verifier 和独立 Gold 证据，分析运行有效性、任务表现、重复性和诊断信息。没有实际运行时保持 NOT_RUN；没有独立 Gold 时不报告 Judge accuracy / False Pass / False Fail。

## 7. 版本交付策略

先完成契约与验证器，再完成发现/导入流程，再完成切片与环境清单工具，最后做端到端集成和 Pilot。任何合成演示必须显式标记 `SYNTHETIC` / `ILLUSTRATIVE_ONLY`。工程测试通过不构成实证有效性结论。
