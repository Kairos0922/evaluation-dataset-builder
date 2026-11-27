# v0.0.3 现有契约接口对照与融合决策

## 1. 目的

本文件将 v0.0.3 轨迹方法与 main 分支已发布的 v0.0.2 契约逐项对照。它是后续实现的边界依据：优先把经过审查的轨迹证据转换为现有 Dataset Case / Manifest / Runtime Record 能消费的内容；不建立第二套数据集、运行记录或评价报告体系。

基线文件均读取自 main：
- `skills/evaluation-dataset-builder/references/dataset-schema.json`
- `skills/evaluation-dataset-builder/references/dataset-manifest-schema.json`
- `skills/evaluation-dataset-builder/references/runtime-record.schema.json`
- `docs/quality-assessment-v0.0.2/schemas/ida-report.schema.json`
- `docs/quality-assessment-v0.0.2/schemas/era-report.schema.json`
- `skills/evaluation-dataset-builder/SKILL.md`

## 2. 已有能力与可复用契约

| v0.0.3 需要表达的内容 | 已有字段/模块 | 融合决策 |
|---|---|---|
| 轨迹是用例来源之一 | Case `case_origin=execution_trace`；`source_refs[]` 支持 `source_type=trace_log` | 直接复用；轨迹 source ID、标题、版本、authority、locator 与证据引用映射到既有来源对象 |
| 场景/能力归属 | Case `scenario_id`、`capability_keys`、`scenario_bucket`、`coverage_tags` | 复用既有业务模型和覆盖体系，不新增 trajectory-specific coverage taxonomy |
| 任务目标与输入输出 | Case `objective`、`user_input`、`expected_behavior` | 切片审查后转为标准 Case 字段；无法从证据确认的内容不得自动补写 |
| 可判定标准 | Case `grading`、`reference_outcome`、`quality_status`、`quality_review`、`information_gaps` | 复用既有判定契约；Gold 不明时保留 UNKNOWN / needs_info，不以轨迹中最终产物直接充当正确答案 |
| 执行前置条件 | Case `execution_requirements`；Manifest `scope`、`assumptions`、`limitations` | 将切片上下文闭包、依赖和执行约束归入现有字段；只对确实需要执行的 Case 要求 |
| 数据集来源追溯 | Manifest `source_refs` | 复用来源引用；Case 级 source_refs 保留精细来源身份和 locator |
| 真实复测身份 | Runtime Record 的 `dataset_sha256`、`case_id`、`run_id`、`configuration_id`、`target_revision`、`model`、`harness`、`environment`、`tool_versions`、`seed` | 复用现有 Runtime Record；历史发现轨迹不能冒充新运行记录 |
| Trace 证据 | Runtime Record `trace_ref` / `result_ref` | 将 clean-run 新 Trace 外部存储并通过引用关联；历史源轨迹保留在 source evidence，不覆盖新运行 trace |
| 失败归因 | Runtime Record `status`、`fault`、`outcomes`；ERA runs / findings | 复用现有归因及 UNKNOWN 语义；不建立平行归因枚举或报告 |
| 数据集质量检查 | IDA 的 dataset identity、gate_results、metric_results、evidence_sufficiency、findings | 先让最终 Case/Manifest 通过现有 IDA；仅当现有报告无法指出真实缺口时再提案扩展 |
| 运行质量检查 | ERA 的 runtime_protocol、runs、grader_validation、metric_results、findings | 先使用现有 ERA；不因轨迹来源而自动增加指标 |

## 3. 新轨迹对象的生命周期与出口

新对象只作为**摄取与审查阶段的暂存证据**：

`Authorized Source → Normalized Events → Candidate → Human/Independent Qualification → Reviewed Slice → Existing Case + Source Mapping`

- Source / Event：只负责授权、脱敏、来源身份和事件定位。原始轨迹不默认复制进 Builder。
- Candidate：候选线索队列，不是正式评测用例，也不进入 IDA / ERA。
- Qualification：证据审查记录，不是 Agent 质量分数，不取代 Case 的 quality_review。
- Slice：中间编辑材料。它必须能追溯回来源事件，并在转入数据集时生成/关联稳定的 `case_id` 和 `dataset_id`。
- 最终出口：标准 Case JSONL、现有 Manifest、现有 IDA 报告；若需要复测，再走现有 ERA Runtime Record。

## 4. 字段映射规则与不可自动推断项

| 切片/审查材料 | 目标 Case 字段 | 规则 |
|---|---|---|
| 已审查的任务名称 | `title` | 人工确认，不能直接使用候选描述代替 |
| 任务能力/行为缺口 | `objective` / `capability_keys` | 必须映射到现有能力词汇；没有依据则保留待审 |
| 决策点之前可见的完整上下文 | `user_input` / `execution_requirements` | 仅保留完成任务所必需且当时可见的内容；排除事后补充、最终答案和未来状态 |
| 可观察的正确结果 | `expected_behavior` | 需由权威资料、独立专家或 Gold 确认；用户不满/返工不等于正确答案 |
| 来源事件及片段定位 | `source_refs[]` | source_type 使用 `trace_log`；保留授权来源身份、版本与 locator |
| 审查后判定标准 | `grading` | 必须定义评分主体、pass/fail/UNKNOWN、证据要求和可接受变体 |
| 未解决的上下文/规则缺口 | `quality_status=needs_info` + `information_gaps` | 不得为了生成可执行 Case 而填造事实 |
| 执行环境需求 | `execution_requirements` | 按任务需要写入初始状态、依赖、权限、副作用、重置/清理等 |
| 来源类型 | `case_origin=execution_trace` | 只有 Case 的核心场景确实由执行轨迹提炼时使用；混合来源按既有枚举和实际依据填写 |

禁止自动推断：
- 从用户纠偏直接推断 Agent 错误或能力缺陷；
- 从轨迹最终产物直接推断 Gold / reference_outcome；
- 从多轮交互、长轨迹或返工次数直接推断任务难度或评分指标；
- 从历史环境快照推断当前复测环境已经成功重建；
- 从 source 文件可访问推断用户已授权；
- 从一次 clean-run 失败推断稳定、普遍的能力缺陷。

## 5. 哪些信息不应该塞入 v0.0.2 Runtime Record

Runtime Record 已绑定一次实际运行及其 dataset/case/configuration/target/model/harness/environment/tool/trace/outcome/cost。历史轨迹发现过程中的事件级标注、候选评分、切片理由和来源资格审查，不属于一次 clean-run 的运行结果。

因此：
- 历史轨迹继续作为来源证据，使用 Source/Event 的外部引用；
- 新 clean-run 产生独立 run_id、trace_ref、result_ref 和实际 outcomes；
- 不把历史发现轨迹填入新 run 的 trace_ref；
- 不因新增轨迹事件而修改 Runtime Record v0.0.2 schema；
- 只有端到端实证证明现有字段确实无法表达某个运行事实时，才另行提出向后兼容的 schema 变更。

## 6. 对 IDA / ERA 的最小集成策略

### IDA

第一阶段不改 IDA 报告 Schema 或指标目录。将转换后的标准 Case JSONL 和 Manifest 交给现有 `assess_dataset_quality.py`。现有检查能够验证结构、来源引用存在性、覆盖一致性、分布、精确重复和报告契约；其无法证明轨迹真实性、语义归因、代表性、Gold 正确性或构念效度，这些仍由独立审查承担。

### ERA

第一阶段不改 ERA 报告 Schema、Runtime Record Schema 或分析器。将标准 Case 纳入数据集后，按现有 ERA protocol 执行全新 session，写入 Runtime Record，绑定精确 dataset SHA 和 case_id，再用独立 Oracle / Judge evidence 形成结果。未执行仍为 NOT_RUN；没有 Gold 时不报告 Judge accuracy。

## 7. 真实最小端到端验收

合成测试只验证转换逻辑，不声称实证有效。工程验收至少应证明：

1. 一个已审查的合成轨迹候选可以生成符合现有 Case Schema 的草稿/待审用例。
2. 未提供 `expected_behavior`、`grading` 或必要上下文时，转换明确拒绝或产出 `needs_info`，不伪造答案。
3. 输出 Case 的 `source_refs` 与轨迹 Source 身份一致，`case_origin` 与来源实际类型一致。
4. 输出的 Manifest / Case 文件可被现有 IDA CLI 读取，IDA 报告可被现有报告 validator 接受。
5. 只有真实 clean-run 才产生 Runtime Record；历史 source trace 不会被错误当作新运行 trace。
6. 新增转换功能不改变没有轨迹输入时的既有 Builder 流程。
7. v0.0.2 正式包、Schema、IDA/ERA 历史报告和既有回归测试保持兼容。

## 8. 结论

当前已足够表达最终用例与运行评价的大部分核心信息。v0.0.3 真正需要的新能力是**安全地从轨迹证据形成候选，并把经过审查的候选转化为现有 Case 的可追溯草稿**。在完成该转换和现有 IDA 的端到端验证之前，不应继续扩大轨迹专用 Schema / CLI 的范围，也不应修改 IDA / ERA 指标。
