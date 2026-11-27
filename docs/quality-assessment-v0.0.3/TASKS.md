# v0.0.3 持久化任务清单

> 本文件是 v0.0.3 的唯一进度事实来源。每项任务只有在验收标准和可复核证据齐备后才能标记 DONE。

- GitHub Issue: [#51](https://github.com/Kairos0922/evaluation-dataset-builder/issues/51)
- 工作分支: `feat/trajectory-driven-v0.0.3`
- 基线: `main` / v0.0.2
- 开发 PR: [#52](https://github.com/Kairos0922/evaluation-dataset-builder/pull/52)（Draft，CI 验证中）
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
| V03-02 | 契约 | 定义轨迹来源/授权/身份与候选任务 Schema | IN_PROGRESS | schemas/v0.0.3/trajectory-source.schema.json、trajectory-event.schema.json、task-candidate.schema.json；待 CI 验证 |
| V03-03 | 契约 | 定义失败资格审查与任务切片 Schema | IN_PROGRESS | schemas/v0.0.3/failure-qualification.schema.json、task-slice.schema.json；待 CI 验证 |
| V03-04 | 契约 | 定义环境重建 Manifest Schema | IN_PROGRESS | schemas/v0.0.3/environment-reconstruction.schema.json；待 CI 验证 |
| V03-05 | 实现 | 实现安全的轨迹候选导入与确定性校验 | IN_PROGRESS | scripts/discover_trajectory_candidates.py 要求授权/脱敏来源记录后读取规范化事件；tests/test_discover_trajectory_candidates.py；待 CI 验证 |
| V03-06 | 实现 | 实现资格审查/切片契约校验和证据引用校验 | IN_PROGRESS | scripts/validate_trajectory_assets.py 已实现来源、资格、切片、重建跨记录门禁；资格审查/切片自动构建仍待实现；待 CI 验证 |
| V03-07 | 实现 | 实现环境重建清单校验与差异记录 | TODO | CLI、单元测试 |
| V03-08 | 集成 | 将新证据以独立报告/证据引用方式接入 IDA / ERA | TODO | 集成测试、历史兼容测试 |
| V03-09 | 验证 | 建立 SYNTHETIC 端到端样例和对抗性测试 | IN_PROGRESS | tests/fixtures/v0.0.3/ 含规范化事件与五类资产；21 项聚焦测试和两条 CLI 链路已接入 CI，待结果 |
| V03-10 | 验证 | 完成 CI、正式 Skill 包、全量离线测试 | TODO | 精确 HEAD 的 CI run |
| V03-11 | 实证 | 在有明确授权的真实轨迹、独立 Oracle 和运行资源时开展 Pilot | BLOCKED | 授权、脱敏、冻结清单、真实运行证据；未具备时保持 BLOCKED |

## 科学边界

- 自动检测结果仅是候选线索，不得自动判定能力缺陷。
- 单次复现不能证明稳定的能力缺口。
- 结构校验 PASS 不代表语义效度 PASS。
- 合成轨迹只能验证工程链路，不得作为真实轨迹来源或外部效度证据。
- 没有独立 Oracle 时，正确性结论为 UNKNOWN / NOT_ASSESSED。
- 不输出未经独立验证的质量总分、固定权重或通过阈值。
