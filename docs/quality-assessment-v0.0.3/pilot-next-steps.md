# v0.0.3 下一阶段：真实 Agent Pilot 执行清单

> 本文记录 v0.0.3 仓库工程准备完成后的下一阶段工作。它是执行清单，不代表真实数据已获授权、真实 Agent 已运行或 Pilot 已通过。

## 当前决策与边界

- 当前阶段：从工程契约验证转入真实 Pilot 准备；V03-11 保持 BLOCKED，V03-08 保持 BLOCKED，直到各自解除条件有证据。
- PR #52 继续保持 Draft；未经明确指示不合并。
- 真实轨迹必须由用户确认具有合法授权，并在提交前完成脱敏与最小化处理。
- 不导入凭据、访问令牌、个人敏感信息、无关对话或不必要的原始附件。
- 不把 SYNTHETIC / ILLUSTRATIVE_ONLY 夹具当作真实能力证据。
- 不由仓库工具启动 Agent。真实运行由用户在获授权、可隔离、可审计的 Harness 中执行。
- 不因 Pilot 结果预设成功；失败、无法复现、环境故障和证据不足都必须如实保留。
- 不新增未经论证的指标、权重、阈值或综合分；沿用现有 Case / Manifest / Runtime Record / IDA / ERA 契约。

## A. 用户侧：真实轨迹准备

- [ ] A1. 选定一个真实 Agent 工作场景，并说明评估目标、目标 Agent/Skill 版本及任务边界。
- [ ] A2. 确认轨迹来源的授权范围、允许用途、保留期限和可分享范围；记录授权审查结果。
- [ ] A3. 对原始轨迹做数据最小化和脱敏；移除密钥、令牌、个人敏感信息及与任务无关内容。
- [ ] A4. 按 `trajectory-source.schema.json` 登记来源身份、授权状态和脱敏审查信息。
- [ ] A5. 将允许使用的轨迹整理为符合 `trajectory-event.schema.json` 的规范化 JSONL；保留必要的事件顺序、工具调用/结果、用户纠正或返工信号及产物修订关系。
- [ ] A6. 在分享前确认 JSONL 不包含未授权内容；仅提供脱敏后的最小必要材料及其来源说明。

**交付物：** 已授权且已脱敏的 source metadata 与 normalized events JSONL。若无法确认授权或脱敏完整性，停止在此阶段，不上传数据。

## B. 助手侧：候选发现与人工资格审查

- [ ] B1. 运行来源/事件 Schema 与跨记录约束校验；不通过时先修复数据，不进入候选发现。
- [ ] B2. 运行 `discover_trajectory_candidates.py`，生成候选任务及其来源指针。
- [ ] B3. 对每个候选进行人工资格审查：区分 Agent 能力问题、用户需求变化、信息不足、工具/环境故障、外部服务故障和无法判定情形。
- [ ] B4. 仅对有充分证据的候选填写 failure qualification；不得由长对话、工具调用次数或单一返工信号直接推断能力缺陷。
- [ ] B5. 为合格候选建立 task slice，检查上下文闭合、必要输入、依赖、预期产物、泄漏风险与复现条件。
- [ ] B6. 对不合格或证据不足的候选保留拒绝/待定理由，不为提高入选率而放宽标准。

**交付物：** 候选清单、资格审查记录、经审查的 task slices，以及拒绝/待定理由。

## C. 助手侧：转成正式 Case 并完成 IDA 门禁

- [ ] C1. 将通过审查的 Slice 转成现有 Case 草稿；不从历史轨迹自动生成 Gold 或标准答案。
- [ ] C2. 校验 Case Schema、来源追溯、任务边界、输入完整性和执行要求。
- [ ] C3. 运行现有 IDA 评估与报告验证；逐项解释 PASS、FAIL、NOT_ASSESSED，不把结构通过表述成构念效度通过。
- [ ] C4. 对未达到执行准备条件的 Case 进行修订或排除，并保留原因。
- [ ] C5. 冻结本轮 Dataset Manifest、Case JSONL 和执行配置；记录目标 Agent/Skill revision、model、harness、environment、tool versions 及必要 seed。
- [ ] C6. 确认 Manifest 与所选 Case 均达到 READY_TO_RUN，再生成 ERA Run Plan。

**交付物：** 经 IDA 检查的 Case、冻结 Manifest/Case JSONL/configuration，以及状态为 `DRAFT_NOT_EXECUTED` 的 ERA Run Plan。

## D. 用户侧：Harness 真实执行

- [ ] D1. 按 `harness-execution-guide.md` 完成运行前检查：授权、隔离环境、预算、数据权限、副作用控制、清理/重置方案。
- [ ] D2. 对 Run Plan 中每个 Case 使用真正独立的新 session；禁止跨 Case 共享对话上下文、隐藏状态或前一 Case 产物。
- [ ] D3. 由 Harness 创建 run_id，记录真实配置与运行状态；不伪造成功结果。
- [ ] D4. 保存本轮新生成的 Trace 与 Result；不得用发现阶段历史轨迹冒充 clean-run 证据。
- [ ] D5. 对实际 Trace 文件计算 SHA-256，并确保引用指向可访问、可复核的产物。
- [ ] D6. 如有独立 Oracle，单独记录其来源、判定者、判定依据及与 Agent 输出的隔离关系；没有独立 Oracle 时保持 Gold 为 UNKNOWN。
- [ ] D7. 为每个 Case 生成符合 `era-harness-envelope.schema.json` 的执行 envelope，并完成执行后人工核对。

**交付物：** Harness execution JSONL、独立 Trace/Result 文件或受控引用、可复核的哈希及必要 Oracle 记录。

## E. 助手侧：导入、ERA 分析与证据审计

- [ ] E1. 使用 `import_era_harness_executions.py` 导入执行 envelope；任何身份、session、配置、Trace/Result 或 Schema 校验失败都应阻断导入。
- [ ] E2. 核对导入后的 Runtime Record 与冻结 Run Plan、Manifest、Case、configuration 的绑定关系。
- [ ] E3. 在可访问实际 Trace 文件的环境中重新计算 SHA-256，并与 envelope 中记录值比对；仅有远程引用而无法读取字节时，明确标注“未独立重算”，不得宣称哈希已验证。
- [ ] E4. 运行现有 ERA 分析与报告验证；缺少 Gold/Judge 的项目必须维持 NOT_RUN / NOT_VALIDATED，不得补造正确性结论。
- [ ] E5. 区分 Agent 失败、Harness 故障、工具/环境故障、任务定义缺陷和证据缺失；必要时将运行标记为不可判定。
- [ ] E6. 对候选能力缺口检查是否在 clean-run 中复现；一次成功或失败都不足以单独证明稳定能力水平。
- [ ] E7. 形成 Pilot 结果报告：方法、样本来源、纳入/排除规则、配置、偏差、异常、证据链接、限制与未解决问题。
- [ ] E8. 只有在预先定义的研究问题、重复策略和证据充分性要求得到满足后，才讨论方法有效性；不得事后挑选有利案例。

**交付物：** Runtime Record JSONL、ERA report、证据审计记录、Pilot 结果与限制说明。

## F. 阶段退出条件

### 工程交接完成（V03-08）

- [ ] 至少一组获授权 Case 在用户控制的 Harness 中完成真实执行。
- [ ] 新 Trace / Result / Runtime Record 可追溯到冻结的 Manifest、Case 和配置。
- [ ] Harness envelope 成功导入现有 Runtime Record，且现有 ERA 能消费。
- [ ] 所有未验证项（例如无法独立读取远程 Trace 字节）被显式披露。

满足以上条件只说明执行链路完成真实集成验证，不等于评估方法有效。

### Pilot 实证完成（V03-11）

- [ ] 真实轨迹授权、脱敏、纳入/排除与数据来源可审计。
- [ ] 候选资格审查与 Task Slice 有人工证据支撑。
- [ ] 独立 Oracle 与判定流程在运行前明确；若没有 Oracle，明确限制结论范围。
- [ ] 真实 clean-run、重复策略和环境控制足以回答预先声明的研究问题。
- [ ] 结果包含反例、失败案例、不可判定项和局限，而非只报告成功样本。
- [ ] 结论经过独立复核；只有证据支持的任务才可解除 BLOCKED。

满足以上条件后再评估 V03-11 是否可以 DONE。若数据或资源不足，继续保持 BLOCKED，不得以合成测试替代。

## 责任边界

| 工作 | 用户 | 助手 |
|---|---|---|
| 授权确认、原始数据控制、脱敏 | 负责 | 提供检查要求，不替用户授权 |
| 规范化轨迹分析、候选发现 | 提供材料 | 负责执行和解释 |
| 资格审查、Task Slice、Case/IDA | 参与确认 | 负责分析与工具链处理 |
| 真实 Agent/Harness 执行 | 负责 | 不擅自启动 |
| Trace/Result 产物保存与访问授权 | 负责 | 根据获准提供的证据核查 |
| Runtime Record 导入、ERA 分析 | 提供执行包 | 负责执行与解释 |
| Pilot 结论 | 共同审议 | 提供证据化分析，不夸大结论 |

## 相关文档

- [Harness 执行手册](./harness-execution-guide.md)
- [轨迹发现操作手册](./trajectory-discovery-playbook.md)
- [架构说明](./architecture.md)
- [任务台账](./TASKS.md)
