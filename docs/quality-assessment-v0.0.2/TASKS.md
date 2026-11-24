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
| RS-02 | 研究 | 深入复核内容效度、评分者一致性、IRT/G-Theory、复合指标和阈值方法 | IN_PROGRESS | research-evidence.md §8–10 已补充 CVI/CVR、IRT 样本量与 G-Theory；仍需完成比较矩阵和适用条件审查 |
| RS-03 | 研究 | 复核通用 Agent / Skill 运行效标、历史故障、变异和 Judge 验证实践 | IN_PROGRESS | ABC、SkillsBench、Agentic Skills at Scale、SkillForgeBench、Judge 验证和 fault exposure 已记录；仍需细化运行效标及其验证边界 |
| DS-01 | 设计 | 完成离线独立质量评价方法和维度操作定义 | IN_PROGRESS | methodology-design.md + metric-catalog.md 已建立 IDA 指标候选；仍需定义审查锚点、评分者校准和内容效度流程；metric catalog commit 4b91a78 |
| DS-02 | 设计 | 完成真实运行评价方法，区分 Agent / 环境 / Judge 误差 | IN_PROGRESS | methodology-design.md + metric-catalog.md 定义 ERA 与共享运行指标；formula-validation-protocol.md 规定验证证据；仍需形成可执行运行协议 |
| DS-03 | 设计 | 设计 Capability 专属评价与统计方案 | TODO | IRT/区分度/测量精度/泛化方案及假设 |
| DS-04 | 设计 | 设计 Regression 专属评价与统计方案 | TODO | 配对变化/历史故障/Mutation/Flakiness 方案 |
| FM-01 | 公式 | 定义构念蓝图、指标类型和候选公式模型族 | DONE | methodology-design.md §3、§5；formula-validation-protocol.md §2、§5；commit f84ef13 + b6cd238 |
| FM-02 | 公式 | 设计公式构建、权重来源、阈值选择与敏感性分析协议 | IN_PROGRESS | formula-validation-protocol.md 已形成开发/验证隔离、效标、模型比较、敏感性和阈值论证草案；仍需冻结预注册分析计划 |
| FM-03 | 公式 | 建立独立效度验证实验与证明报告 | TODO | 执行专家盲评、缺陷注入、外部效标、泛化和不确定性验证；当前仅有协议设计 |
| EX-01 | 实验 | 完成公式验证实验设计与样本量/效标规划 | DONE | experimental-design.md；定义 E0–E7 阶段、分组隔离、专家盲评、缺陷注入和真实运行方案；commit 4b2f0d3 |
| EX-02 | 实验 | 建立独立参考数据集与缺陷注入样本 | TODO | 数据来源、版本、SHA、缺陷标签、对照组和独立确认 |
| EX-03 | 实验 | 完成专家内容效度与评分者一致性实验 | TODO | 盲评原始数据、专家资历/协议、CVI/CVR/一致性统计 |
| EX-04 | 实验 | 完成缺陷注入识别实验 | TODO | 盲测结果、按缺陷类型的检出/误报和置信区间 |
| EX-05 | 实验 | 完成 Capability / Regression 真实运行效标实验 | TODO | 精确版本绑定的运行轨迹、Oracle、统计分析和限制 |
| SC-01 | 方案 | 冻结 v0.0.2 需求、架构和验收标准 | TODO | 需求评审决议、设计基线 commit |
| IM-01 | 实现 | 设计并实现 IDA 报告 Schema / 机器可读契约 | DONE | schemas/ida-report.schema.json；JSON 语法检查通过；commit f47905e |
| IM-02 | 实现 | 实现独立离线评价器和确定性检查 | IN_PROGRESS | scripts/validate_quality_assessment.py 已实现 Schema + 交叉字段检查；tests/test_quality_assessment_validator.py 已覆盖 IDA/ERA 正反例；CI 尚未跑到该测试步骤 |
| IM-03 | 实现 | 实现人工/LLM Judge 校准与证据记录接口 | TODO | 独立校准集协议、Judge 结果契约 |
| IM-04 | 实现 | 实现 ERA 运行结果报告 Schema / 机器可读契约 | DONE | schemas/era-report.schema.json；精确数据集 SHA、Agent/模型/Harness/环境、Run/Trace、Judge、Capability/Regression 分析字段已定义；JSON 语法检查通过；commit fa28651 |
| IM-05 | 实现 | 实现 Capability / Regression 统计分析模块 | TODO | 统计方法测试和边界测试 |
| IM-06 | 实现 | 实现候选综合公式比较与敏感性分析 | TODO | 多模型比较；不合格时禁止输出 validated 综合分 |
| IM-07 | 集成 | 更新 Skill 质量标准、按需加载引用和版本到 0.0.2 | IN_PROGRESS | quality-standard.md/yaml 已替换旧固定权重，IDA/ERA Schema 已加入 Skill references，SKILL.md 已引用；版本元数据待发布候选阶段更新，正式包验证待 CI |
| QA-01 | 质量 | 建立元评测数据、已知缺陷注入和专家盲评样本 | TODO | 数据来源、隔离、标注和审计记录 |
| QA-02 | 质量 | 完成离线评价器验证与报告 | TODO | 结构、内容、评分者一致性、缺陷检出证据 |
| QA-03 | 质量 | 完成真实运行评价的端到端验证 | TODO | Agent/Skill 真实运行，Capability 与 Regression 分别有结果 |
| QA-04 | 质量 | 完成综合公式独立验证；若证据不足则明确 NOT_VALIDATED | TODO | 独立验证集、效度/稳健性/误差报告 |
| CI-01 | 工程 | 增加 CI、Schema、单测和端到端离线验收 | IN_PROGRESS | PR #44 workflow run 45510288348（run #1691）失败于 validate_skill.py：旧的二级 references 检查把 JSON Schema 的 $id URI 误判为依赖；已在 commit 0c537fa 修复，等待最新 head 重验；离线单测尚未执行 |
| DOC-01 | 文档 | 更新 README、CHANGELOG、版本和限制说明 | TODO | v0.0.2 内容一致 |
| REL-01 | 发布 | 建立发布候选 PR 并完成审查 | TODO | 所有适用验收门禁通过，PR 记录证据 |
| REL-02 | 发布 | 用户批准后创建 v0.0.2 Tag 和 GitHub Release | TODO | Release 指向精确验证过的提交，证据齐全 |

## 当前已完成

- [x] v0.0.2 需求边界写入 GitHub Issue #43。
- [x] 建立工作分支 feat/quality-assessment-v0.0.2。
- [x] 写入需求规格。
- [x] 建立初版研究证据库。
- [x] 写入双路径方法论候选架构。
- [x] 建立本任务追踪文件。

## 当前不代表已完成的事项

- 候选指标尚未完成系统文献复核。
- 任何综合公式、权重、阈值均未验证。
- 未建立专家盲评或缺陷注入数据。
- 未完成独立评价器和真实运行评价器实现。
- 未进行 v0.0.2 版本发布。

## 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-25 | 建立需求、研究证据库、双路径方法论、公式验证协议、实验设计、设计决策、候选指标字典、IDA/ERA Schema、初版报告验证器与测试；Draft PR #44 已创建。更新 Skill 质量标准并加入报告 Schema。补充 CVI/CVR、IRT 样本量、G-Theory、SkillsBench 版本和 failure exposure 证据。PR #44 run #1691 发现 Skill validator 误判 Schema $id，已修复，等待重验。RQ-01、RQ-02、RS-01、FM-01、EX-01、IM-01、IM-04 完成；RS-02、RS-03、DS-01、DS-02、FM-02、IM-02、IM-07、CI-01 进行中。 |
