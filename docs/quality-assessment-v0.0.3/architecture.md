# v0.0.3 与现有 Evaluation Dataset Builder 的融合架构

## 1. 架构决策

v0.0.3 不建立一套平行的“轨迹评测产品”，也不把轨迹方法论变成新的强制评分维度。它增强现有 Builder 的任务来源、用例设计和证据链，使已有 IDA / ERA 能够利用更贴近真实工作的任务与运行证据。

核心原则：**复用现有资产、扩展现有契约、按需启用新步骤；只有出现现有流程无法表达的证据缺口时，才增加最小的新结构。**

v0.0.2 的 IDA、ERA、Runtime Record、Judge Calibration、Oracle/Verifier 证据协议和报告语义保持稳定。v0.0.3 不回写或重新解释历史结果。

## 2. 现有流程中的位置

现有 Builder 的主流程仍然是：

`业务资料 / 需求 / 历史案例 → 业务模型与覆盖设计 → 用例生成 → 判定契约 → 独立质量审查（IDA）→ 运行计划与执行 → Runtime Record / Trace → 运行评价（ERA）`

真实 Agent 轨迹是**可选的补充证据入口**，不是替代业务资料，也不是所有数据集必须经过的前置步骤：

`经授权的真实轨迹 → 发现候选问题 → 证据审查 → 提炼/补充业务场景与用例 → 回到现有 IDA / ERA 流程`

轨迹中观察到的用户不满、纠偏或返工只帮助定位值得研究的任务。它们本身不能证明 Agent 能力缺陷，也不能直接成为评分项。

## 3. 方法论如何映射到现有模块

| 轨迹方法 | 融入现有位置 | 处理方式 | 不做什么 |
|---|---|---|---|
| 从真实工作轨迹发现能力缺口 | 业务分析、来源管理、场景规划 | 作为新增候选来源，与产品文档、业务规则、历史缺陷和用户反馈并列；保留来源引用与证据等级 | 不替代业务依据；不将反馈信号自动判成失败 |
| 区分 Agent 错误与上下文/歧义/工具/环境问题 | 现有 ERA 失败归因与证据审查 | 复用现有归因概念；补足决策时可见上下文和归因证据 | 不再造第二套互不兼容的归因体系 |
| 将长轨迹切成最小完整任务 | 现有场景与 Case 设计 | 把切片结果转成普通 Builder 场景/用例输入；保留起止事件、初始上下文、交付物和证据引用 | 不以轨迹长度作为复杂度或质量指标；不创建脱离 Case 的平行任务对象 |
| 还原执行环境 | 现有 Manifest、执行就绪检查和 Runtime Record | 仅对需要复现的用例补充依赖、状态、权限、工具版本、资源、重置与清理信息 | 不要求纯文本/非执行类用例也提供容器或环境清单 |
| 新上下文复测 | 现有 ERA 执行协议 | 复用冻结的 Agent/模型/Harness/工具/环境/数据集身份和新会话要求 | 不另建与 ERA 并行的 Runner 或重复记录体系 |
| 独立 Verifier / Oracle | 现有 Judge Calibration、Oracle 和 Gold 证据 | 复用独立性、盲法、校准、UNKNOWN/abstention 和证据绑定规则 | 不让 Builder 自己生成答案并独立证明自身正确 |
| 轨迹诊断与成本观察 | 现有 ERA Runtime Record / 报告 | 将可追溯的决策、工具调用、返工、错误传播和成本作为诊断证据；先报告原始可观察事实 | 不未经构念、单位、效标和可靠性验证就升级为 IDA/ERA 指标或综合分 |

## 4. 新增结构的边界

新增的 trajectory source、normalized event、candidate 和 qualification 结构只服务于“轨迹证据如何安全进入现有 Builder”这一缺口：

- Source / Event：记录授权、脱敏、来源身份和事件引用；原始轨迹优先留在受控来源，不复制敏感内容。
- Candidate：发现流程的工作队列记录，可追溯到来源事件；状态只表示待审查线索。
- Qualification：审查候选是否有足够证据进入场景/用例设计，并记录反证、未知和归因；它不是独立的模型评分报告。
- Task Slice：若需要保留切片工件，应视为生成现有 Case 的中间材料。最终必须映射到现有 dataset/case ID、判定契约和来源引用，不另起一套 Case 生命周期。
- Reconstruction details：按执行需求并入现有执行 Manifest / Runtime Record。只有需要复现的任务才要求这些字段。

这些结构不得要求所有 Builder 用户理解或执行轨迹工作流。没有真实轨迹时，原有业务资料驱动的 Builder 工作流必须保持完整可用。

## 5. 与 IDA / ERA 的责任边界

### IDA（离线数据集质量评价）

IDA 继续评价最终数据集及其现有契约。轨迹来源可以补充 IDA 可审查的来源引用、场景依据、上下文完整性声明、用例可判定性和执行准备信息。

确定性检查可以验证字段、引用、身份、哈希和内部一致性；不能仅凭这些检查证明轨迹真实性、语义归因正确、任务代表性或构念效度。轨迹“来自真实用户”也不自动意味着它是好用例。

### ERA（真实运行证据评价）

ERA 继续消费现有 Runtime Record / Trace、冻结身份、Judge/Gold 和运行结果。轨迹切片产生的任务应进入既有 ERA 执行协议；复测结果应使用现有 Runtime Record 及其数据集/用例身份关联。

历史轨迹是任务发现证据，不等于新 Agent 的复测结果。只有实际 clean-run 发生后，才产生新的运行记录。未运行保持 NOT_RUN；缺少独立 Gold 时不得报告 Judge accuracy、False Pass 或 False Fail。

## 6. 端到端融合流程

1. **正常构建仍然优先。** 按现有 Skill 流程分析业务资料、定义能力和覆盖、生成 Case 与判定契约。
2. **有授权轨迹时才启用发现。** 先验证来源授权与脱敏状态，再读取规范化事件；发现信号只产生 candidate。
3. **人工/独立证据审查。** 核对任务目标、当时可见信息、事后要求、工具和环境健康情况；无法归因时保留 UNKNOWN，不强行归咎 Agent。
4. **回到现有场景与 Case。** 将可复用的最小任务转成普通场景、Case、来源映射和判定契约；检查答案泄漏、上下文闭包和合理变体。
5. **按执行需要补足环境信息。** 对依赖状态或工具的任务，补齐现有执行 Manifest 所需的状态、权限、依赖、重置和清理信息；不适用时不强制填写。
6. **复用现有 IDA。** 对最终数据集运行离线质量检查；轨迹来源只作为证据输入，不自动加分。
7. **复用现有 ERA。** 在冻结配置下用新会话执行，写入 Runtime Record，使用独立 Verifier/Oracle 判定，再由 ERA 分析结果与归因。
8. **反馈回 Builder。** 依据真实运行发现修复具体 Case、判定契约或环境描述，并通过现有变更影响分析局部更新；不因一次失败就直接增加能力指标。

## 7. 质量与科学证据约束

- Discovery signal ≠ confirmed failure ≠ capability gap ≠ validated benchmark item。
- 工程 Schema/Validator/CI 通过，只证明软件契约与测试范围内的行为，不证明方法学有效。
- 合成样例只验证工程链路，必须标记 SYNTHETIC / ILLUSTRATIVE_ONLY。
- 不因新方法论引入新的综合分、权重、阈值或“轨迹质量分”。
- 任何候选新指标必须先明确构念、测量对象、单位、分子/分母、独立效标、可靠性与适用边界；在证据不足时只保留诊断字段。
- 真实轨迹导入、执行和外部系统操作均需明确授权；文件可访问不等于有权使用。

## 8. 版本策略

v0.0.3 首先完成最小融合：证明轨迹证据能够进入现有 Builder 的场景/Case/来源链，并由现有 IDA/ERA 识别和消费，而不是只证明新增 trajectory 专用对象之间可以互相校验。

实现优先级：
1. 审查现有 Schema、Runtime Record、IDA/ERA 输入与 Skill 流程，列出复用点和确实无法表达的缺口。
2. 将 Candidate 到现有 Case 的映射做成可审查、可验证的转换。
3. 将必要的上下文/环境信息接入现有执行契约，避免第二套 Manifest。
4. 复用 ERA 的 clean-run、Runtime Record、Judge/Oracle 和报告路径。
5. 只在端到端证据证明必要时，才扩展 IDA/ERA 的报告字段或实现新的确定性检查。

v0.0.2 正式 Skill 包和发布资产在 v0.0.3 合并前保持不变。

## 9. ERA Run Plan 草稿：计划与执行严格分离

现有仓库具备 Runtime Record Schema、ERA 分析器和特定 DSH Pilot 的证据导入路径，但没有可通用复用的 ERA Run Plan / clean-run 调度器。特定 DSH Runner 绑定 WebApp Testing 场景，不应伪装成通用 Runner。

v0.0.3 因此只增加 scripts/build_era_run_plan.py，作为**从现有数据集契约到具体 Harness 的薄适配层**：

- 输入仍是现有 Dataset Manifest、Case JSONL 和一份冻结的 Runtime Record 执行身份配置；不引入第二套 Dataset Manifest。
- 生成前验证 Manifest / Case Schema、case_count、所有 Case 的 dataset_id、唯一 case_id 和所选 Case 的 execution_requirements.status=READY_TO_RUN。
- 计划绑定 Manifest SHA、Case JSONL SHA，以及与既有 import_dsh_pilot_records.py 完全一致的数据集 SHA 算法，避免 Builder/IDA 与 ERA 侧对数据集身份产生不同解释。
- 每个计划项保留原始 Case、逐 Case 执行要求和历史来源引用。历史来源引用仅用于 provenance；Runner 必须为新执行产生独立 trace_ref / result_ref。
- 运行身份字段沿用 Runtime Record Schema 的 configuration_id、target_revision、target_type、model、harness、environment、tool_versions 和可选 seed。
- 计划状态固定为 DRAFT_NOT_EXECUTED。计划生成不分配 run_id、不触发模型请求、不声称执行成功，也不产生 Runtime Record。

具体 Harness 后续消费计划时，必须在每个 Case 的新 session 中执行，按原样绑定 dataset_sha256 / case_id / 冻结配置，并仅在执行开始后分配真实 run_id。若无独立 Oracle，gold_outcome 必须保持 unknown；基础设施异常不得归因于 Agent。

这一步证明的是“现有 Case 可被安全整理成 ERA 执行计划”，不是“Runner 已经执行”。真实执行适配仍需针对具体 Harness 完成，并在授权和隔离条件具备后验证。


## 10. Harness 产物适配：执行与导入分离

对现有执行路径的核对确认：仓库当前没有可直接消费通用 ERA Run Plan 的通用 clean-run Harness。现有 DSH Pilot 导入路径与 WebApp Testing 专用基准强绑定，包括固定 Skill/工具身份、浏览器及服务端证据、预算与清理条件、三条 Pilot Case 和对应 Oracle adjudication。它不是通用 Agent Harness，不能安全地直接消费任意 Case。

因此 v0.0.3 不把 DSH Pilot Runner 改造成通用 Runner，也不新增第二套 Runtime Record。新增的 `scripts/import_era_harness_executions.py` 仅作为**Harness 产物导入适配器**：

- 输入为 Run Plan 和 Harness 已完成执行后生成的 JSONL envelope；每条 envelope 在 Runtime Record 外携带 `plan_id`、`case_id`、`session_id`，避免修改 v0.0.2 Runtime Record Schema。
- 导入器逐条校验现有 Runtime Record Schema，并核对 dataset_id / dataset_sha256 / case_id 与冻结配置身份。
- 要求每个 Case 恰好一条记录、run_id 唯一、session_id 非空且跨 Case 不复用；新 trace_ref / result_ref 不得复用历史来源引用，并要求 trace_sha256。
- 当前适配器没有独立 Oracle 证据输入，因此强制 `gold_outcome=unknown`、`gold_source=not_available`；不得从 Agent 自报或 Harness 成功状态推导 Gold。
- 输出仅为既有 v0.0.2 Runtime Record JSONL，可继续交给现有 ERA；不新增 Runtime Record 字段或评分规则。

该适配器不启动 Agent、不创建 run_id、不验证远端 trace 文件真实性，也不替代 Harness 的隔离、会话创建、资源清理和实际执行责任。合成测试只证明导入契约。真正的 clean-run 仍需选定获授权的通用 Harness、配置执行资源，并由 Harness 产出可核验的新 Trace / Result。

## 11. 用户控制的 Harness 执行交接

真实 Agent 执行由用户在选定且获授权的 Harness / 隔离环境中发起。为使“仓库准备工作”与“真实实证”边界明确，v0.0.3 提供：

- `schemas/v0.0.3/era-harness-envelope.schema.json`：定义单次执行的外层交接契约；内层仍是未修改的 v0.0.2 Runtime Record。
- `scripts/import_era_harness_executions.py`：先验证 envelope Schema，再验证 Runtime Record Schema 与 Run Plan 身份绑定。
- `docs/quality-assessment-v0.0.3/harness-execution-guide.md`：用户执行前检查、逐 Case fresh-session 协议、工件要求、导入命令、人工复核和自动化边界。

该交接包不是 Harness 实现，不会自动调用模型。它使用户可以选择已有工具执行，并将真实产物按既有 ERA 契约导入。导入器不能仅凭 session_id 字段证明上下文隔离，也不会下载远端工件复算 Trace SHA；这两项必须由 Harness 机制与人工审查提供证据。
