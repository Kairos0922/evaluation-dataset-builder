# v0.0.2 持久化任务清单

> **这是本次 0.0.2 工作的唯一进度事实来源。** 每完成一项任务，必须在同一工作周期内更新状态、证据和提交 SHA，再开始依赖它的下一项任务。聊天中的口头进度不能替代此文件。

- GitHub Issue：[#43](https://github.com/Kairos0922/evaluation-dataset-builder/issues/43)
- 工作分支：feat/quality-assessment-v0.0.2
- Draft PR：[#44](https://github.com/Kairos0922/evaluation-dataset-builder/pull/44)
- 基线：main（v0.0.1 已发布）
- 当前版本：0.0.1
- 目标版本：0.0.2
- 当前状态：IN_PROGRESS
- 最后更新：2026-11-25

## 状态定义

- TODO：未开始。
- IN_PROGRESS：正在执行。
- BLOCKED：存在明确阻塞，必须记录原因和解除条件。
- DONE：已完成，必须有可复核证据和 commit / run / artifact 引用。
- NOT_APPLICABLE：经论证后确认不适用。

禁止只因文档已写或代码已提交就标记 DONE；任务验收标准必须全部满足。

## 阶段与任务

| ID | 阶段 | 任务 | 状态 | 完成条件 / 证据 |
|---|---|---|---|---|
| RQ-01 | 需求 | 将用户需求、对象、用途和双路径评价边界写入仓库 | DONE | requirements.md；Issue #43；commit ec5b629 |
| RQ-02 | 需求 | 明确不沿用未验证权重/阈值，并保留 PR #38 历史证据 | DONE | requirements.md §3、§5；PR #38 不在本分支修改；decision-log.md D-003/D-006 |
| RS-01 | 研究 | 建立 Agent Benchmark、Construct Validity 和测量学证据库 | DONE | research-evidence.md；NeurIPS ABC / Construct Validity、OECD/JRC、SkillsBench、Agentic Skills at Scale、SkillForgeBench 等来源已记录；commit e8c60fa + 后续研究补充 |
| RS-02 | 研究 | 深入复核内容效度、评分者一致性、IRT/G-Theory、复合指标和阈值方法 | IN_PROGRESS | research-evidence.md 已补充 CVI/CVR、IRT 样本量、G-Theory 和 OECD/JRC 复合指标手册；formula-validation-protocol.md 已细化权重来源、阈值和敏感性方法；仍需完成适用条件比较矩阵 |
| RS-03 | 研究 | 复核通用 Agent / Skill 运行效标、历史故障、变异和 Judge 验证实践 | IN_PROGRESS | ABC、SkillsBench、Agentic Skills at Scale、SkillForgeBench、Judge 验证和 fault exposure 已记录；仍需细化运行效标及其验证边界 |
| DS-01 | 设计 | 完成离线独立质量评价方法和维度操作定义 | IN_PROGRESS | methodology-design.md + metric-catalog.md 已建立 IDA 指标候选；仍需定义审查锚点、评分者校准和内容效度流程；metric catalog commit 4b91a78 |
| DS-02 | 设计 | 完成真实运行评价方法，区分 Agent / 环境 / Judge 误差 | IN_PROGRESS | methodology-design.md + metric-catalog.md 定义 ERA 与共享运行指标；formula-validation-protocol.md 规定验证证据；仍需形成可执行运行协议 |
| DS-03 | 设计 | 设计 Capability 专属评价与统计方案 | IN_PROGRESS | 已定义观察题目通过率画像、IRT 难度/区分度、Test Information、DIF、测量不变性和 G-Theory 的用途与限制；当前 analyzer 仅输出描述性通过率，IRT/G-Theory 估计与假设检验未完成 |
| DS-04 | 设计 | 设计 Regression 专属评价与统计方案 | IN_PROGRESS | 已定义同 case/model/environment/seed 配对、McNemar exact、历史故障、Mutation、失败暴露和重复运行不一致；需用真实故障集验证代表性和检出效度 |
| FM-01 | 公式 | 定义构念蓝图、指标类型和候选公式模型族 | DONE | methodology-design.md §3、§5；formula-validation-protocol.md §2、§5；commit f84ef13 + b6cd238 |
| FM-02 | 公式 | 设计公式构建、权重来源、阈值选择与敏感性分析协议 | IN_PROGRESS | formula-validation-protocol.md 已明确规范性/经验性/混合权重、损失驱动阈值、模型比较和敏感性分析；仍需冻结预注册分析计划和实际效标 |
| FM-03 | 公式 | 建立独立效度验证实验与证明报告 | TODO | 执行专家盲评、缺陷注入、外部效标、泛化和不确定性验证；当前仅有协议设计 |
| EX-01 | 实验 | 完成公式验证实验设计与样本量/效标规划 | DONE | experimental-design.md；定义 E0–E7 阶段、分组隔离、专家盲评、缺陷注入和真实运行方案；commit 4b2f0d3 |
| EX-02 | 实验 | 建立独立参考数据集与缺陷注入样本 | IN_PROGRESS | defect-mutation-catalog.yaml 已建立 IDA-M01–M12 / ERA-M01–M08；单元测试已扩展覆盖身份错配、来源注册表解析/缺失、覆盖声明不一致、Judge abstention、历史故障逃逸和失败未暴露；尚缺独立公开/生产数据集家族、盲测变体和独立缺陷标签 |
| EX-03 | 实验 | 完成专家内容效度与评分者一致性实验 | TODO | 盲评原始数据、专家资历/协议、CVI/CVR/一致性统计 |
| EX-04 | 实验 | 完成缺陷注入识别实验 | TODO | 盲测结果、按缺陷类型的检出/误报和置信区间 |
| EX-05 | 实验 | 完成 Capability / Regression 真实运行效标实验 | BLOCKED | 需要 PR #38 先完成 Builder 正式产出且独立 Validator PASS；当前 PR #38 run #1662 的 Builder production / independent-validation jobs 均 skipped。不得重复运行已完成的历史流程，也不得用合成轨迹冒充真实结果。解除条件：PR #38 产生正式 Builder artifact 并通过独立验证，之后使用本项目 runtime-record.schema.json 收集新运行证据 |
| SC-01 | 方案 | 冻结 v0.0.2 需求、架构和验收标准 | TODO | 需求评审决议、设计基线 commit |
| IM-01 | 实现 | 设计并实现 IDA 报告 Schema / 机器可读契约 | DONE | schemas/ida-report.schema.json；JSON 语法检查通过；commit f47905e |
| IM-02 | 实现 | 实现独立离线评价器和确定性检查 | IN_PROGRESS | 实现已通过前一轮单测；本轮扩展来源缺失/解析、覆盖不一致和身份错配测试，run #1784 仅有 1 个测试断言文本不匹配，已修正，等待最新 head 全量复验 |
| IM-03 | 实现 | 实现人工/LLM Judge 校准与证据记录接口 | TODO | 独立校准集协议、Judge 结果契约 |
| IM-04 | 实现 | 实现 ERA 运行结果 Schema / 机器可读契约 | DONE | schemas/era-report.schema.json + schemas/runtime-record.schema.json；Skill references 已同步；精确数据集 SHA、Agent/模型/Harness/环境、Run/Trace、Judge、Capability/Regression 字段已定义；JSON 语法检查通过；commits ef7515c、5030629、f18e010 |
| IM-05 | 实现 | 实现 Capability / Regression 统计分析模块 | IN_PROGRESS | scripts/assess_runtime_quality.py 已实现 Judge 混淆指标、Wilson CI、配对版本差异、McNemar exact、历史/变异故障检出、重复运行不一致和成本画像；IRT/G-Theory 与真实运行验证未完成；tests/test_assess_runtime_quality.py 已添加，待 CI 执行 |
| IM-06 | 实现 | 实现候选综合公式比较与敏感性分析 | TODO | 多模型比较；不合格时禁止输出 validated 综合分 |
| IM-07 | 集成 | 更新 Skill 质量标准、按需加载引用和版本到 0.0.2 | IN_PROGRESS | quality-standard.md/yaml 已替换旧固定权重；IDA/ERA 报告 Schema、Runtime Record Schema 已加入 Skill references，SKILL.md 已引用；validate_skill.py 增加 Draft 2020-12 Schema 检查；版本元数据待发布候选阶段更新，正式包验证待 CI |
| QA-01 | 质量 | 建立元评测数据、已知缺陷注入和专家盲评样本 | IN_PROGRESS | 已有缺陷目录与确定性单测；尚缺独立来源的真实数据集、专家盲评样本、训练/验证隔离和审计记录 |
| QA-02 | 质量 | 完成离线评价器验证与报告 | IN_PROGRESS | 结构检查器、报告契约和 151 项 CI 测试已通过；语义内容效度、专家一致性、独立缺陷识别实验尚未完成 |
| QA-03 | 质量 | 完成真实运行评价的端到端验证 | BLOCKED | 与 EX-05 同一前置条件：PR #38 正式 Builder artifact + independent Validator PASS；当前没有可用的正式数据集和真实 Agent 运行记录 |
| QA-04 | 质量 | 完成综合公式独立验证；若证据不足则明确 NOT_VALIDATED | IN_PROGRESS | 已有公式验证协议和向量画像定义；尚缺专家效标、缺陷注入数据、真实运行效标与冻结验证集。证据不足时保持 NOT_VALIDATED，不得发布标量总分 |
| CI-01 | 工程 | 增加 CI、Schema、单测和端到端离线验收 | IN_PROGRESS | run #1774（45513077814）在旧实现 head 上 151 项测试 PASS；扩展到 155 项后，run #1784（45513477801）有 1 个测试断言失败，已修正，最新 head 需再次完整 CI。Builder production、独立 Gold Oracle 和 Skill pilot jobs 按本 PR 条件跳过，不属于本轮质量评价实现验收。 |
| DOC-01 | 文档 | 更新 README、CHANGELOG、版本和限制说明 | TODO | v0.0.2 内容一致 |
| REL-01 | 发布 | 建立发布候选 PR 并完成审查 | TODO | 所有适用验收门禁通过，PR 记录证据 |
| REL-02 | 发布 | 用户批准后创建 v0.0.2 Tag 和 GitHub Release | TODO | Release 指向精确验证过的提交，证据齐全 |

## 外部依赖与阻塞

- PR #38（Builder 正式生产与独立验证）是本项目真实运行评价的外部依赖。当前可核验的 PR #38 head 为 7f34ddb；其 run #1662 只通过上游资产审计，Builder production、independent-validation、pilot 等 jobs 均 skipped。
- 因此当前没有经过正式门禁的 Builder 输出可供本项目做真实数据集质量评价，也没有可用于 ERA 的真实 Agent 运行记录。
- 本任务不会修改 PR #38，不会重复执行已完成的 Builder/Pilot/Oracle 历史证据，不会把单元测试夹具或合成轨迹伪装成真实运行证据。
- PR #38 的 Builder 正式产出和独立 Validator PASS 后，才解除 EX-05 / QA-03 阻塞；届时应绑定精确 dataset SHA、Agent/Skill revision、模型、Harness、环境和 run records。
- 当前 PR #44 的 CI PASS 只证明本项目代码、Schema、Skill 包和离线测试通过，不代表公式效度或真实运行评价已经通过。

## 当前已完成

- [x] v0.0.2 需求边界写入 GitHub Issue #43。
- [x] 建立工作分支 feat/quality-assessment-v0.0.2。
- [x] 写入需求规格。
- [x] 建立初版研究证据库。
- [x] 写入双路径方法论候选架构。
- [x] 建立本任务追踪文件。
- [x] 完成 IDA 确定性离线评价器及报告验证器，并通过单元测试。
- [x] 完成 ERA 运行记录统计分析器初版及单元测试。
- [x] 在精确 PR head 上通过 actionlint、正式包、Benchmark 样例和 151 项离线单测（run #1774）。
- [ ] 扩展缺陷注入测试后，在最新 head 上再次通过完整 CI。

## 当前不代表已完成的事项

- 候选指标尚未完成系统文献复核。
- 任何综合公式、权重、阈值均未验证。
- 未建立专家盲评或缺陷注入数据。
- 未完成独立评价器和真实运行评价器实现。
- 未进行 v0.0.2 版本发布。

## 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-25 | 建立需求、研究证据库、双路径方法论、公式验证协议、实验设计、设计决策、候选指标字典、IDA/ERA/Runtime Record Schema、离线 IDA 检查器、ERA 分析器、报告验证器与测试；Draft PR #44 已创建。更新 Skill 质量标准并加入报告 Schema 与运行记录 Schema；validate_skill.py 增加 JSON Schema 检查；Release Gate 测试同步纳入新增 Schema 和当前 Workflow 实现。补充 CVI/CVR、IRT 样本量、G-Theory、SkillsBench 和 OECD/JRC 复合指标手册证据；细化规范性/经验性权重、损失驱动阈值和敏感性验证方法；正式定义 IDA/ERA 用途条件化质量画像；建立 defect-mutation-catalog.yaml 和对应测试。PR #44 run #1774 在精确 head cb43aa7 上 actionlint、正式包、Benchmark 样例和 151 项离线测试全部 PASS；IM-02 与 CI-01 的前一版验收完成；缺陷测试扩展后的最新 head 复验中。 PR #44 run #1784（45513477801）actionlint、正式包、Benchmark 样例 PASS，155 项测试中仅 1 个断言失败；修正描述断言后，run #1789（45513651073）仍有 1 个失败：missing-source mutation 使用 synthetic_gap_fill，但当前 Case Schema 要求该来源必须引用 synthetic_scenario；已改为 schema-valid 的 unknown + information_gaps 样本，等待最新 head 重跑。公式效度、专家盲评、缺陷注入、真实 Agent 运行、IRT/G-Theory、版本元数据和 Release 仍未完成。RQ-01、RQ-02、RS-01、FM-01、EX-01、IM-01、IM-02、IM-04、CI-01 完成；RS-02、RS-03、DS-01、DS-02、FM-02、IM-05、IM-07 进行中。 |
