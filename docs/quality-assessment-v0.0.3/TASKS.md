# v0.0.3 持久化任务清单

> 本文件是 v0.0.3 的唯一进度事实来源。每项任务只有在验收标准和可复核证据齐备后才能标记 DONE。

- GitHub Issue: [#51](https://github.com/Kairos0922/evaluation-dataset-builder/issues/51)
- 工作分支: `feat/trajectory-driven-v0.0.3`
- 基线: `main` / v0.0.2
- 开发 PR: [#52](https://github.com/Kairos0922/evaluation-dataset-builder/pull/52)（Draft）
- 最近一次完整 CI 验证：Run #2147 / 46085403868，PR HEAD `ff5fdaff1ced2dd48f084b0b0a0fdcfe8621b3ac`（包含 no-trace fixture 修复 commit `de21c723dc0c50a2116a1f31b58951558d8b1a96`），validate 与 v0.0.2 release-candidate package 均 PASS
- 轨迹→Case→IDA 与无轨迹回归：Run #2147 steps 9–14 全部 PASS；已归档轨迹 Case、无轨迹 Case 和两份 IDA report 到 `trajectory-to-ida-integration` artifact（90 天）
- 真实 Builder production / independent validation / Pilot 等受保护任务按条件 SKIPPED；没有真实轨迹或真实 Pilot 结论
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
| V03-08 | 集成 | 将审查后的轨迹候选映射到现有 Case / Manifest，并复用 IDA / ERA | IN_PROGRESS | Case 草稿转换和 IDA 已打通；仍需完成无轨迹回归与 ERA clean-run / Runtime Record 接入，不能将 IDA 贯通等同于 ERA 完成 |
| V03-09 | 验证 | 建立 SYNTHETIC 端到端样例和对抗性测试 | DONE | Run #2124：候选发现 CLI、v0.0.3 资产链贯通样例、离线测试全部 PASS；仅证明工程契约，不代表真实轨迹有效性 |
| V03-10 | 验证 | 完成 CI、正式 Skill 包、全量离线测试 | DONE | Run #2137（commit `e98df48`）：actionlint、正式 Skill 包、Benchmark、轨迹发现、v0.0.3 证据链、Case adapter、IDA CLI 与报告验证、全量离线测试、G-Theory 模拟、IDA mutation 均 PASS。受保护的 Builder production / independent validation / Pilot jobs 按条件 SKIPPED，不属于本项通过证据 |
| V03-11 | 实证 | 在明确授权的真实轨迹、独立 Oracle 和运行资源下开展 Pilot | BLOCKED | 当前无获准真实轨迹输入与新的独立 Pilot 授权；保持 BLOCKED，不以合成样例替代 |
| V03-12 | 架构集成 | 对照 v0.0.2 Case / Manifest / Runtime Record / IDA / ERA，确定复用边界 | DONE | `integration-contract-map.md`，commit `68f421f9555e841b0b0540e4fca415cb4d785e59`；基于 main 分支正式 Schema 和 Skill 流程逐项对照 |
| V03-13 | 集成实现 | 实现经过审查的 Candidate / Slice → 现有 Case 草稿转换器并接入 IDA | DONE | `scripts/build_case_draft_from_slice.py`；4 项专项测试；Run #2137 steps 11–12 PASS：输出符合 main 的 Case Schema，现有 `assess_dataset_quality.py` 成功消费，`validate_quality_assessment.py` 验证报告通过；G01 source provenance=PASS，构念/可解性保持 NOT_ASSESSED，综合分 NOT_VALIDATED |

| V03-14 | 回归 | 验证无轨迹输入时原有 Builder / IDA 工作流保持可用 | DONE | Run #2147 step 13 PASS：不含 trajectory-specific 字段的 `synthetic_gap_fill` Case 直接通过现有 IDA CLI；source provenance PASS，构念效度仍 NOT_ASSESSED。v0.0.2 Skill package 与全量离线测试同次 CI PASS。该合成 smoke test 证明接口兼容，不代表真实业务有效性 |
| V03-15 | 验证 | 归档轨迹→Case→IDA 及无轨迹回归证据 | DONE | Run #2147 step 14 PASS；GitHub Actions artifact `trajectory-to-ida-integration`，包含轨迹 Case draft、轨迹 JSONL、轨迹 IDA report、无轨迹 IDA report，保留 90 天 |\n| V03-16 | ERA 集成 | 验证新 clean-run Runtime Record 能绑定轨迹来源 Case，并由现有 ERA 消费 | IN_PROGRESS | 新增 `tests/test_trajectory_era_integration.py`：合成契约测试检查 dataset SHA / case_id / 新 trace_ref 绑定、历史 source trace 不被复用、缺少 Gold/Judge 时保持 NOT_RUN / NOT_VALIDATED；等待 PR CI 执行。该测试不执行 Agent，不构成真实运行证据 |

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
