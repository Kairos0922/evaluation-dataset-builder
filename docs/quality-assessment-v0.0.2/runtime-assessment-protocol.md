# v0.0.2 ERA 真实运行执行协议

**状态：** 可执行协议基线；尚未授权或启动新的生产运行  
**版本：** runtime-assessment-protocol/1.0.0  
**适用对象：** Agent、Skill、Agent+Skill、多工具工作流  
**适用用途：** Capability、Regression

## 1. 目的

本协议规定如何将真实 Agent/Skill 执行转换为可审计 Runtime Record，如何区分 Agent、环境、Judge 和数据集误差，以及如何分别执行 Capability 与 Regression 分析。它不提供模型供应商、Runner 或宿主的隐含权限。

## 2. 执行前冻结清单

每个实验批次必须先冻结并记录：

- 数据集 ID、版本、原始文件 SHA-256、用例集合和划分策略；
- 目标类型、Agent/Skill revision、依赖与配置 SHA；
- 模型 provider、model ID/revision、温度、token 参数和系统提示 SHA；
- Harness 名称/版本/commit；
- 环境名称/版本/镜像 digest、区域、初始状态和健康检查；
- 工具名称/版本/API contract；
- 每条用例的前置状态、执行权限、动作预算、超时、重试和禁止副作用；
- 随机种子、重复策略、停止规则和缺失值规则；
- Judge 身份/版本/提示 SHA、独立 Gold 来源、仲裁状态；
- 成本保护、隐私边界、清理策略和失败恢复步骤。

上述身份缺失时，该批次只能作为探索性试运行，不能进入确认性效度分析。运行中改变冻结参数必须创建新批次身份，不得覆盖原始记录。

## 3. 单次运行流程

1. 校验冻结 manifest、目标 revision、数据集 SHA、Oracle 状态和环境健康。
2. 确认当前 case 在 Oracle 冻结范围内，动作预算和副作用许可明确。
3. 创建唯一 run_id、case_id、configuration_id、pair_id（如适用）、repeat_group_id（如适用）。
4. 记录 started_at、seed、模型/Harness/环境/工具版本。
5. 执行一次目标任务，原始轨迹、事件、请求/响应和最终产物使用不可变引用归档。
6. 单独判定 Agent Outcome、Process Outcome、Judge Outcome、Gold Outcome；保留证据引用和 Judge 理由。
7. 记录成本：duration、input/output/cache tokens、model steps、tool calls、cost；未知值写 null，不估算成 0。
8. 记录环境清理、状态重置和任何未完成副作用。
9. 生成符合 Runtime Record Schema 的记录，并执行 Schema 与跨字段验证。
10. 失败、取消、预算耗尽、环境故障或证据缺失均保留原始记录，不删除失败样本。

## 4. 失败归因

| 类别 | 判定条件 | 统计处理 |
|---|---|---|
| valid | 运行完整，环境健康，结果和轨迹可审计 | 可进入相应结果分母 |
| agent_failed | Agent 行为违反冻结任务契约或未完成任务 | 作为 Agent 失败，不等同环境失败 |
| environment_failed | 环境、依赖、服务或 fixture 故障导致结果不可归因 | 单独报告，不计为 Agent PASS/FAIL |
| grader_failed | Judge 崩溃、格式错误、证据解析失败或违反判定契约 | 单独报告，不用 Agent outcome 替代 |
| unknown | 证据不足、Oracle 不确定或多种归因无法区分 | UNKNOWN，不强行归类 |
| cancelled | 人工停止、超时策略终止或安全停止 | 保留原因，按预注册规则处理 |

同一运行可以有不同主体的不同结果。应用/API 的业务失败不自动意味着测试型 Skill 失败；Skill 正确发现并报告应用缺陷时，Skill 结果应按其独立契约判定。

## 5. Judge 与 Gold

- Judge 必须与被测生成端/被测对象保持身份独立，至少记录 provider、model、revision、endpoint origin、prompt SHA 和 implementation SHA。
- Gold/Oracle 必须来自独立专家、独立仲裁、可信历史故障或独立外部 verifier；Builder 生成的预期答案不能作为唯一 Gold。
- 每个 Gold label 必须有来源引用、判定依据和 PASS/FAIL/UNKNOWN 边界。
- Judge abstention 与 Judge failure 不得合并；Judge 的 UNKNOWN 不自动视为正确或错误。
- Judge calibration 使用独立校准集，held-out 集不得用于提示词/参数调优；同一批标签不得同时用于开发和确认性验证。
- 无 Gold 时 Judge accuracy、False Pass/False Fail 等必须 NOT_RUN 或 NOT_ASSESSED。

## 6. Capability 协议

- 以明确的目标能力蓝图分层抽样任务，保留任务域、难度假设、能力标签和适用范围。
- 尽可能使用多个 Agent/模型/配置执行同一冻结任务集，形成 Agent × Task × Seed × Environment 响应矩阵。
- 先报告逐任务和逐能力描述性画像及区间。
- 只有样本量、响应矩阵、局部独立、单调性、模型拟合和参数可识别性得到支持时才拟合 IRT；否则使用预注册的分层/非参数描述，不强行给出能力 θ。
- DIF/测量不变性需要预先定义比较组、锚题和多重比较策略。
- G-Theory 需要可识别的 Agent、Task、Rater、Environment、Seed 等 facet 设计；报告方差分量和决策研究假设。
- 外部能力效标必须独立于本数据集与待验证公式。

## 7. Regression 协议

- Baseline 与 Candidate 必须使用相同 case、尽可能相同环境、工具和执行协议，形成唯一 pair_id。
- 同一 case 的版本对必须完整；不可配对记录单独报告，不得进入配对检验。
- 记录历史真实故障和受控变异缺陷的不同 fault kind；Mutation 与历史故障结果分开报告。
- 对二元配对结果报告转移表、配对差异、McNemar exact 或预注册 Bootstrap 区间。
- 关键安全/权限/副作用约束采用非补偿性门禁。
- 重复运行估计 Flakiness；按预注册设计分解 Agent、环境、Judge 方差。
- 统计回归逃逸、故障发现和失败暴露三个不同事件，不得混为单一 Mutation Score。

## 8. 重复、随机性与停止规则

- 重复次数依据 Pilot 方差、目标区间宽度、成本和功效分析预先确定；本协议不设通用固定次数。
- 不得在观察结果后临时增加重复次数直至达到期望结论。
- 运行中止、重试、缓存命中、模型切换和环境重置必须写入记录。
- 同一批次若更改模型、提示、工具或环境，需建立新 configuration_id。
- 发生安全风险、越权、副作用超预算或凭据泄漏时立即停止，并保留事件证据。

## 9. 分析与报告

分别报告：

- 运行有效性与各类失败数；
- Agent/Process/Judge/Gold 的混淆关系；
- Judge False Pass、False Fail、Abstention、重复评分一致性；
- Capability 任务画像、能力区间和模型假设诊断；
- Regression 配对转移、历史故障和 Mutation 检出；
- Flakiness、Agent/环境/Judge 波动；
- 时延、token、工具调用和成本；
- 置信区间、缺失值、排除规则和证据缺口；
- 目标版本、数据集、模型、环境、协议和分析代码的精确 SHA。

无有效 Gold、无配对记录或分母为零时，使用 NOT_RUN / NOT_ASSESSED / NOT_APPLICABLE，不填零。综合分默认 NOT_VALIDATED、value=null。

## 10. 当前 Round 4 执行边界

现有 Pilot 仅 WB-02、WB-10、WB-12 三条；其余 12 条须先完成双盲 Oracle、独立仲裁和 hash-bound freeze。WB-15 的 Application outcome 保持 UNKNOWN。执行前 Freeze Gate 通过不代表用户授权运行；没有冻结 manifest 和明确授权，不得启动 Runner。
