# v0.0.3 持久化任务清单

> 本文件是 v0.0.3 的唯一进度事实来源。每项任务只有在验收标准和可复核证据齐备后才能标记 DONE。

- GitHub Issue: [#51](https://github.com/Kairos0922/evaluation-dataset-builder/issues/51)
- 工作分支: `feat/trajectory-driven-v0.0.3`
- 基线: `main` / v0.0.2
- 开发 PR: [#52](https://github.com/Kairos0922/evaluation-dataset-builder/pull/52)（Draft）
- 最近一次完整 CI 验证：Run #2124 / 46083024909，commit `2b86993473f261ffffa5b48a1535a989c599b23b`
- 状态: IN_PROGRESS
- 版本原则: 不修改 v0.0.2 历史结果；不把合成样例当作实证。

## 状态定义

- TODO：未开始
- IN_PROGRESS：执行中
- BLOCKED：存在明确阻塞及解除条件
- DONE：验收条件全部满足，并附 commit / CI / artifact 证据
- NOT_APPLICABLE：有论证的不适用项
- DEFERRED：经决策暂缓，不代表完成

## 阶段任务

| ID | 阶段 | 任务 | 状态 | 验收证据 |
|---|---|---|---|---|
| V03-01 | 基线 | 建立 v0.0.3 版本边界、架构和任务台账 | DONE | README.md、architecture.md、TASKS.md、trajectory-discovery-playbook.md；PR #52 |
| V03-02 | 契约 | 定义轨迹来源/授权/身份与候选任务 Schema | DONE | trajectory-source / trajectory-event / task-candidate schemas；Run #2124 精确 HEAD PASS |
| V03-03 | 契约 | 定义失败资格审查与任务切片 Schema | DONE | failure-qualification / task-slice schemas；Run #2124 精确 HEAD PASS；仍是审查中间材料，不取代 Case |
| V03-04 | 契约 | 定义可选环境重建证据 Schema | DONE | environment-reconstruction schema；Run #2124 精确 HEAD PASS；仅适用于需要复现的任务，不建立第二套强制 Manifest |
| V03-05 | 实现 | 实现安全的轨迹候选导入与确定性校验 | DONE | `scripts/discover_trajectory_candidates.py` 先验证授权/脱敏来源再读取规范化事件；合成 CLI 端到端步骤 Run #2124 PASS |
| V03-06 | 实现 | 实现来源、资格审查、切片和重建证据的契约校验 | DONE | `scripts/validate_trajectory_assets.py` 跨记录门禁；Run #2124 完整 validate job PASS。该项是契约校验，不代表语义资格审查自动化 |
| V03-07 | 实现 | 实现环境重建的独立 Runner / Manifest 工作流 | DEFERRED | 接口对照发现现有 Case `execution_requirements`、Manifest 和 Runtime Record 已承载主要执行约束；暂不另建 Runner/Manifest。若端到端案例证明字段不足，再提出最小扩展 |
| V03-08 | 集成 | 将审查后的轨迹候选映射到现有 Case / Manifest，并复用 IDA / ERA | IN_PROGRESS | `integration-contract-map.md` 已完成；下一步实现可审查的 Case draft adapter，并由现有 IDA CLI 验证输出 |
| V03-09 | 验证 | 建立 SYNTHETIC 端到端样例和对抗性测试 | DONE | Run #2124：候选发现 CLI、v0.0.3 资产链贯通样例、离线测试全部 PASS；仅证明工程契约，不代表真实轨迹有效性 |
| V03-10 | 验证 | 完成 CI、正式 Skill 包、全量离线测试 | IN_PROGRESS | Run #2124（精确 commit `2b86993`）：actionlint、正式包、Benchmark 样例、轨迹发现、v0.0.3 贯通、离线测试、G-Theory 模拟、IDA mutation 均 PASS；该次 PR CI 中 Builder production / independent validation / Pilot / Round 4 evidence jobs 按保护条件 SKIPPED。架构文档新提交后需重新验证 |
| V03-11 | 实证 | 在明确授权的真实轨迹、独立 Oracle 和运行资源下开展 Pilot | BLOCKED | 当前无获准真实轨迹输入与新的独立 Pilot 授权；保持 BLOCKED，不以合成样例替代 |
| V03-12 | 架构集成 | 对照 v0.0.2 Case / Manifest / Runtime Record / IDA / ERA，确定复用边界 | DONE | `integration-contract-map.md`，commit `68f421f9555e841b0b0540e4fca415cb4d785e59`；基于 main 分支正式 Schema 和 Skill 流程逐项对照 |
| V03-13 | 集成实现 | 实现经过审查的 Candidate / Slice → 现有 Case 草稿转换器 | TODO | 输出符合现有 Case Schema；保留 trace source 身份和 locator；缺少 expected_behavior / grading / 上下文时拒绝或标记 needs_info；增加 IDA CLI 端到端与无轨迹回归测试 |

## 融合原则

- 轨迹是现有来源体系的可选补充，不替代业务规则、产品文档和已核实历史缺陷。
- Candidate / Qualification / Slice 只在摄取和审查阶段存在；正式用例必须回到既有 Case / Manifest。
- clean-run 必须复用现有 ERA protocol 和 Runtime Record；历史发现轨迹不冒充新运行 trace。
- 先复用 IDA / ERA，不因轨迹方法论增加新指标、综合分、权重或阈值。
- 不要求没有轨迹输入的用户改变既有 Builder 工作流。

## 科学边界

- 自动检测结果仅是候选线索，不得自动判定能力缺陷。
- 单次复现不能证明稳定的能力缺口。
- 结构校验 PASS 不代表语义效度 PASS。
- 合成轨迹只能验证工程链路，不得作为真实轨迹来源或外部效度证据。
- 没有独立 Oracle 时，正确性结论为 UNKNOWN / NOT_ASSESSED。
- 不输出未经独立验证的质量总分、固定权重或通过阈值。
