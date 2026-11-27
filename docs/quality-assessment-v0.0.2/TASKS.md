# v0.0.2 持久化任务清单

> **这是本次 0.0.2 工作的唯一进度事实来源。** 每完成一项任务，必须在同一工作周期内更新状态、证据和提交 SHA，再开始依赖它的下一项任务。聊天中的口头进度不能替代此文件。

- GitHub Issue：[#43](https://github.com/Kairos0922/evaluation-dataset-builder/issues/43)
- 工作分支：feat/quality-assessment-v0.0.2
- Draft PR：[#44](https://github.com/Kairos0922/evaluation-dataset-builder/pull/44)
- 基线：main（v0.0.1 已发布）
- main 当前正式版本：0.0.1
- 本分支候选版本：0.0.2
- 当前状态：22/22 项自主工程任务 DONE；进入 0.0.2 发布准备阶段，尚未形成 Release Candidate 或取得发布批准
- 发布准备审计：RELEASE-PREP-0.0.2.md
- 0.0.2 发布门禁：RELEASE-GATE-0.0.2.md
- 最后更新：2026-11-27

## 状态定义

- TODO：未开始。
- IN_PROGRESS：正在执行。
- BLOCKED：存在明确阻塞，必须记录原因和解除条件。
- DONE：已完成，必须有可复核证据和 commit / run / artifact 引用。
- NOT_APPLICABLE：经论证后确认不适用。
- DEFERRED：经用户/项目决策暂缓，保留记录但不纳入当前执行队列；不代表完成或不适用。

禁止只因文档已写或代码已提交就标记 DONE；任务验收标准必须全部满足。

## 当前执行任务

**当前统计：22 项；DONE 22；IN_PROGRESS 0；BLOCKED 0；DEFERRED 0；TODO 0。** 17 项外部依赖事项由 D-009 移出本次迭代范围，不计入当前任务数，也不计为完成。

> 本表只保留本次迭代决定实际执行并已完成的自主工程任务。经用户决定移出当前范围的外部依赖任务已从任务表删除；其历史证据、未验证边界和原始阻塞原因保留在下方归档记录及 `decision-log.md`，不代表相关科学验证已经通过。


| ID | 阶段 | 任务 | 状态 | 完成条件 / 证据 |
|---|---|---|---|---|
| RQ-01 | 需求 | 将用户需求、对象、用途和双路径评价边界写入仓库 | DONE | requirements.md；Issue #43；commit ec5b629 |
| RQ-02 | 需求 | 明确不沿用未验证权重/阈值，并保留 PR #38 历史证据 | DONE | requirements.md §3、§5；PR #38 不在本分支修改；decision-log.md D-003/D-006 |
| RS-01 | 研究 | 建立 Agent Benchmark、Construct Validity 和测量学证据库 | DONE | research-evidence.md；NeurIPS ABC / Construct Validity、OECD/JRC、SkillsBench、Agentic Skills at Scale、SkillForgeBench 等来源已记录；commit e8c60fa + 后续研究补充 |
| RS-02 | 研究 | 深入复核内容效度、评分者一致性、IRT/G-Theory、复合指标和阈值方法 | DONE | 已完成方法复核与可执行设计：research-evidence.md、methodology-matrix.md、formula-validation-protocol.md、expert-review-protocol.md 覆盖 CVI/CVR/Aiken's V、ICC/Kappa/Alpha、IRT/G-Theory、复合指标、损失驱动阈值、敏感性和功效规划。专家实证另由 EX-03/QA-01 跟踪，不作为文献复核完成的前提。 |
| RS-03 | 研究 | 复核通用 Agent / Skill 运行效标、历史故障、变异和 Judge 验证实践 | DONE | 已完成通用 Agent/Skill Benchmark、Judge、历史故障、Mutation、失败暴露和重复性方法复核；外部候选官方代码许可/访问限制初筛见 external-benchmark-candidates.md。锁定可用版本、数据资产许可、Oracle 和运行环境属于 EX-02/EX-05，仍未完成。 |
| DS-01 | 设计 | 完成离线独立质量评价方法和维度操作定义 | DONE | methodology-design.md、metric-catalog.md 定义 IDA 构念/指标/单位/分子分母/证据/局限；expert-review-protocol.md 定义盲评评分锚点与仲裁。实际专家校准由 EX-03 单独验证。 |
| DS-02 | 设计 | 完成真实运行评价方法，区分 Agent / 环境 / Judge 误差 | DONE | 新增 runtime-assessment-protocol.md，冻结执行前身份、单次运行步骤、失败归因、Judge/Gold 独立性、Capability/Regression 分支、重复/停止规则与报告要求。实际运行效标由 EX-05/EX-06 验证。 |
| DS-03 | 设计 | 设计 Capability 专属评价与统计方案 | DONE | methodology-design.md、metric-catalog.md、formula-validation-protocol.md 与 runtime-assessment-protocol.md 已定义 Capability 任务画像、IRT/DIF/Test Information、G-Theory 适用假设及无假设支持时的替代报告；统计拟合实现/实证另由 IM-05/EX-05 跟踪。 |
| DS-04 | 设计 | 设计 Regression 专属评价与统计方案 | DONE | 已定义同 case/config/environment/seed 配对、转移表、McNemar exact/Bootstrap、历史故障与 Mutation 分开、关键门禁及 Flakiness；真实故障集效度由 EX-05 跟踪。 |
| FM-01 | 公式 | 定义构念蓝图、指标类型和候选公式模型族 | DONE | methodology-design.md §3、§5；formula-validation-protocol.md §2、§5；commit f84ef13 + b6cd238 |
| FM-02 | 公式 | 设计公式构建、权重来源、阈值选择与敏感性分析协议 | DONE | formula-validation-protocol.md 已定义候选模型族、规范性/经验性/混合权重来源、训练/验证隔离、损失驱动阈值、敏感性/稳健性分析和验证结论状态。具体预注册参数必须绑定独立数据集与外部效标，属于 FM-03。 |
| EX-01 | 实验 | 完成公式验证实验设计与样本量/效标规划 | DONE | experimental-design.md；定义 E0–E7 阶段、分组隔离、专家盲评、缺陷注入和真实运行方案；commit 4b2f0d3 |
| EX-06 | 工程/实验 | 将真实 Builder、DSH Trace、Runner 和独立 Oracle 证据转换为规范 Runtime Record，并运行 IDA/ERA | DONE | 在现有冻结证据范围内完成：Builder/Pilot 原始证据导入、Runtime Record、IDA/ERA 分析、Schema/cross-field validator。新增 DSH JSONL 逐行解析、case/run 身份一致性检查、证据清单强制绑定、SHA-256 校验、路径穿越/符号链接逃逸防护，并将 trace_sha256 写入 Runtime Record Schema。代码提交 `e7245d2`，测试修正 `d899ea3`；Run #1983（45800505196，精确 head `d899ea3fab0b0f27a9d8fc1c57e78ade28492683`）230/230 离线测试 PASS，Round 4 real-evidence Job SUCCESS，Artifact 15105794918（ZIP SHA-256 `0d703863f965f99e34f721c00895ada15acd25ef0495015d4492826407962e03`）。该任务仅完成现有可用证据的规范化和分析：IDA/ERA 仍 PARTIAL，3/15 Pilot，12 NOT_RUN，Judge NOT_RUN，composite NOT_VALIDATED；剩余覆盖与效度任务由 EX-05/EX-07 等追踪。 |
| SC-01 | 方案 | 冻结 v0.0.2 需求、架构和验收标准 | DONE | 新增 architecture-and-acceptance-baseline.md，定义模块边界、IDA/ERA 数据流、证据等级、关键不变量、用途分支、版本策略和分层验收矩阵；decision-log.md D-007 采纳，requirements.md 状态同步。 |
| IM-01 | 实现 | 设计并实现 IDA 报告 Schema / 机器可读契约 | DONE | schemas/ida-report.schema.json；JSON 语法检查通过；commit f47905e |
| IM-02 | 实现 | 实现独立离线评价器和确定性检查 | DONE | scripts/assess_dataset_quality.py 实现 Manifest/Case Schema、ID、来源注册表、覆盖一致性、分布、精确重复和报告契约检查；扩展身份错配、来源缺失/解析、覆盖不一致测试；run #1793 在精确 head 885444a 上 155 项测试 PASS |
| IM-04 | 实现 | 实现 ERA 运行结果 Schema / 机器可读契约 | DONE | schemas/era-report.schema.json + schemas/runtime-record.schema.json；Skill references 已同步；精确数据集 SHA、Agent/模型/Harness/环境、Run/Trace、Judge、Capability/Regression 字段已定义；JSON 语法检查通过；commits ef7515c、5030629、f18e010 |
| IM-06 | 实现 | 实现公式验证证据 Schema 和独立验证器 | DONE | Schema、Skill reference、验证器及契约测试已实现；修复 split-level sample_count 契约错误；commit b6740f9 + a2dc04e；run #1808（45550108441）在 head a2dc04e 上 162 项测试 PASS。此状态仅表示报告结构/逻辑契约验证器完成，不代表公式实验有效 |
| P0-ROBUST-01 | 工程 | 加固 IDA 对畸形嵌套字段的失败安全处理并增加回归测试 | DONE | 修复 coverage_tags/source_refs/scenario_bucket/grading/manifest coverage 结构异常导致的统计阶段未处理异常；非法 source registry ID 明确拒绝；新增 3 项回归测试。Run #2034（45916033576，精确 head ee0e03bbc0731acf4ca814a4d4a8b113f0ecad88）SUCCESS，246/246 离线测试 PASS；IDA controlled-mutation 与 Round 4 IDA/ERA/Capability report contracts PASS。该任务仅为工程鲁棒性，不代表语义效度验证。 |
| P0-ROBUST-02 | 工程 | 全仓库 JSON 输入严格解析与非有限数值拒绝 | DONE | 对 IDA/ERA/Capability/Formula/Judge/Target Runtime/Round 4 Oracle/盲审/DSH 导入、Skill 校验及 release evidence 解析路径统一拒绝 JSON 标准外的 NaN/Infinity；报告验证器递归拒绝非有限数值。新增 JSONL 回归测试。Run #2065（45947894476，精确 head `2b238f9a18482f10429d9b04180952b89735675f`）SUCCESS，validate 与 Round 4 real-evidence assessment jobs PASS；生产运行、独立评审、Pilot、adjudication 仍按授权边界 SKIPPED。 |
| P0-CI-01 | 工程 | 修复 CI #1807 中 Formula Validation Validator 对 datasets[].sample_count 的错误读取，并增加回归测试 | DONE | Schema 将 sample_count 定义在 split 层；验证器改为校验来源数据集非空并使用 split 总样本量；commit b6740f9（验证器）、a2dc04e（回归测试）；run #1808（45550108441）精确 head a2dc04e：actionlint、Skill 正式包、Benchmark 贯通样例 PASS，162/162 离线测试 PASS。Builder production / independent-validation jobs 按 PR 条件 SKIPPED |
| CI-01 | 工程 | 增加 CI、Schema、单测和端到端离线验收 | DONE | Run #1890（45606669627，精确 head d38d797cfd3476e0e28cb8155f599e70920bff13）完整验证 PASS：actionlint、正式 Skill 包、Benchmark、185/185 离线测试、Round 4 冻结证据导入/IDA/ERA/报告 JSON Schema 与 cross-field validation 全部 PASS；真实证据 artifact 15017663406。此前 Run #1885 在 validator 加入前 177/177 PASS；Run #1890 包含新增 Oracle validator 与 8 项测试。PR #38 Builder production / independent-validation / pilot Jobs 按范围保护 SKIPPED，不计作本次验证通过 |

## 历史证据与未验证边界（归档，不属于当前任务队列）

- PR #38 已关闭。历史 run #1662 的 skipped 状态已被后续 Round 4 证据取代，不再作为当前阻塞依据。
- Builder 原始输出来自 run #44959366258 / artifact #14729741906；该 production Job 结论为 failure（启发式误报），但 Builder 输出 artifact 已产生。独立验证 run #44968128127 PASS，冻结产出复验 run #45291624154 PASS。只有在此限定下，认定“正式 Builder 输出 + 独立 Validator PASS”前置条件满足；不把 Builder Job 说成 PASS。
- 三条真实 Pilot 与独立 Oracle 证据来自 run #45189512695 / artifact #14824967038：WB-02、WB-10、WB-12，Oracle 3/3 PASS。数据集共 15 条，另外 12 条仍未执行；Manifest 仍为 quality_status=needs_info、execution_status=NOT_RUN。
- PR #44 通过 importer 和 CI 下载冻结证据，不重复运行历史 Builder/Pilot/Oracle，不修改 PR #38，不使用合成轨迹冒充真实结果。
- 当前 PR #44 的 CI PASS 只证明本项目代码、Schema、Skill 包和离线测试通过，不代表公式效度或真实运行评价已经通过。

## 当前已完成

- [x] 完成架构与验收解释基线（SC-01）：architecture-and-acceptance-baseline.md + decision-log D-007。
- [x] 完成 ERA 可执行运行协议（DS-02）：runtime-assessment-protocol.md。
- [x] 完成 Judge Calibration Report Schema、验证器和 8 项契约测试；Run #1933 215/215 PASS（IM-03 仍待执行脚本集成和独立 Gold 实证）。
- [x] 更新根 README、CHANGELOG、研发 README，记录 v0.0.2 未发布状态和限制；质量报告见 [quality-report.md](quality-report.md)。

- [x] v0.0.2 需求边界写入 GitHub Issue #43。
- [x] 建立工作分支 feat/quality-assessment-v0.0.2。
- [x] 写入需求规格。
- [x] 建立初版研究证据库。
- [x] 写入双路径方法论候选架构。
- [x] 建立本任务追踪文件。
- [x] 完成 IDA 确定性离线评价器及报告验证器，并通过单元测试。
- [x] 完成 ERA 运行记录统计分析器初版及单元测试。
- [x] 在精确 PR head 上通过 actionlint、正式包、Benchmark 样例和 151 项离线单测（run #1774）。
- [x] 扩展缺陷注入测试后，在精确 head 885444a 上通过 actionlint、正式包、Benchmark 样例和 155 项离线单测（run #1793）。
- [x] 修复 Formula Validation Validator 与 Schema 的 sample_count 层级错配；在精确 head a2dc04e 上通过 actionlint、正式 Skill 包、Benchmark 贯通样例和 162 项离线测试（run #1808，45550108441）。
- [x] 核实 PR #38 后续 Round 4 Builder/独立验证/Pilot/Oracle 原始证据，确认三条真实 Pilot 已完成；12/15 数据集用例仍 NOT_RUN。
- [x] 增加真实 DSH Pilot Runtime Record importer、缓存 Token/Model Step 字段、缺失 Judge 与 abstention 区分修复及回归测试；增加 PR #44 冻结证据 IDA/ERA CI Job，等待首次执行结果。

## 历史未验证事项（已移出当前任务范围，不构成待办）

- 独立专家内容效度、评分者一致性和 Round 4 双盲 Oracle 仲裁尚未执行。
- 外部参考 Benchmark 的具体数据资产许可、版本哈希、Oracle 和合法快照尚未全部锁定。
- 盲测缺陷注入及其误报/漏报区间尚未执行。
- Round 4 12/15 用例仍 NOT_RUN；完整 Capability 与 Regression 真实效标尚未完成。
- Judge 独立 Gold 校准尚未执行；IRT/G-Theory/DIF 尚未拟合。
- 综合公式、权重和阈值均未验证，标量总分保持关闭。
- v0.0.2 尚未形成 Release Candidate、审查批准或正式发布。

## 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-25 | CI-01 完成 Oracle validator 增量后的完整复验：Run #1890（45606669627，head d38d797cfd3476e0e28cb8155f599e70920bff13）actionlint、正式 Skill 包、Benchmark、185/185 离线测试、Round 4 IDA/ERA 和报告契约验证全部 PASS；artifact 15017663406。新增 Oracle validator 与 8 项测试已纳入本次 185 项测试；CI-01 标记 DONE。PR #38 生产/Pilot Jobs 仍按范围保护 SKIPPED。 |
| 2026-11-25 | Round 4 Oracle 设计、Schema 与验证器：独立判定计划 commit c129b21；记录 Schema commit 0118318；hash-bound validator commit 51ae748，校验数据集/用例/计划哈希、重复记录、评审者集合、仲裁结果与动作预算；新增 8 项 unittest（commits 0cacd6b、fa2a6e1、1330ce9）。WB-15 application outcome 强制 UNKNOWN；超预算不能记 Skill PASS。计划待独立审查者确认，未执行剩余 12 条。 |
| 2026-11-25 | 更新 Round 4 Oracle 计划状态：记录 Schema/hash-bound validator 与执行前 freeze manifest Gate 已实现；人工逐案仲裁仍 NOT_RUN，Runner/执行后 adjudication 尚未实现。下一步明确为双盲评审回收、差异比较、独立仲裁、冻结 Gate 和用户明确授权。 |
| 2026-11-25 | Round 4 执行前 Oracle 冻结 Gate 验证通过：Run #1918（45629438803，head dd3e8d9c769b04cfd742224f4ace2d261afdc5b3）actionlint、正式 Skill 包、Benchmark、205/205 离线测试及 Round 4 IDA/ERA 报告契约验证全部 PASS。冻结 Schema/验证器绑定数据集、计划、两份盲评提交、重算比较报告、crosswalk 和 12 个 case SHA；验证两位评审者与仲裁者身份独立，禁止部分案例冻结。无真实评审提交，因此本轮只验证 Gate 工具，不代表 Oracle 已冻结或授权执行。 |
| 2026-11-25 | Round 4 执行前 Oracle 冻结 Gate：新增 freeze manifest Schema、hash-bound 验证器与 7 项测试；验证器要求双盲评审、独立仲裁、12 条 case SHA 完整、输入提交/比较报告/crosswalk/数据集/计划哈希一致，且任一 case 未冻结则整体不得 FROZEN。比较报告由原始提交和 coordinator crosswalk 重新计算后逐字段核验。代码/测试尚待 CI。修正盲审比较命令文档的 shell 换行符。 |
| 2026-11-25 | Round 4 盲评差异比较器加强：加入两位评审对每个 case SHA 的一致性校验，并比较理由、证据引用和总体意见；新增回归测试。Run #1905（45617038589，精确代码 head bc738ecd37f5aa4ae97ede580cc793c2034e0fe3）通过 actionlint、正式包、Benchmark、196/196 离线测试及 Round 4 IDA/ERA 报告契约验证。无 ResourceWarning。审查者仍未招募或提交，Oracle 未冻结，12 条 NOT_RUN。 |
| 2026-11-25 | Round 4 盲审提交接收与差异比较：新增 round4-blind-review-submission.schema.json，绑定两份审查包 SHA 与冻结数据集 SHA；新增 compare_round4_blind_reviews.py，验证双评审身份、12 个匿名标签和 coordinator crosswalk，并仅输出待人工裁决差异，不自动生成 Gold。新增测试；Run #1899（45615825593，head 3eeebcc）195/195 PASS。该 run 日志中的 ResourceWarning 已由 c235a6d 修复，等待修复后精确 head 复验。评审尚未分发/回收，Oracle 未冻结，12 条 NOT_RUN。 |
| 2026-11-25 | Round 4 独立盲审资料包：新增生成器 scripts/build_round4_blind_review_packets.py（commit 95431be）和 3 项隔离/哈希测试（commit fcb17a8）；Run #1893（45610478776）actionlint、Skill 包、Benchmark、188/188 离线测试 PASS。基于冻结 artifact 14824967038 生成 Reviewer A/B 两份 12-case 包，协调者 crosswalk 单独归档；包 SHA 和分发规程见 round4-blind-review-packet-guide.md。未分发、未收到专家意见、未形成 Oracle 共识；12 条继续 NOT_RUN。 |
| 2026-11-25 | 专家盲评协议落地：新增 expert-review-protocol.md（盲评/仲裁分离、评分锚点、CVI/CVR/Aiken's V、一致性统计、区间/功效规划、无统一阈值）；新增 expert-review-record.schema.json 并镜像至 Skill references，新增 unittest 覆盖 schema 合法性、尺度约束、盲评状态和匿名化。相关 commits 3fd46df、b5d644c、78d2b44、cc4b5c2。未招募专家，所有专家统计仍 NOT_RUN。 |
| 2026-11-25 | PR #44 最新 TASKS.md head 428b3ac 的 Run #1861（45595437684）最终 PASS：actionlint、Skill 正式包、Benchmark、167/167 离线测试、真实证据导入、IDA/ERA、JSON Schema 和 cross-field validation 全部 PASS；报告 artifact 15013081639。Builder production、independent-validation 和 pilot Jobs 依 PR #38 前置条件 SKIPPED。 |
| 2026-11-25 | 最新 TASKS.md 变更前的完整验证 Run #1858（45595208813，精确 head 3f5ad1bce112f8d08b26b618ab51a6d99c32a0ce）成功：actionlint、Skill 包、Benchmark、167/167 测试、真实 IDA/ERA 导入和报告 JSON Schema / cross-field validation PASS；真实证据 Artifact 已归档。该 run 未执行 PR #38 前置条件保护的 Builder production / independent-validation / pilot jobs（SKIPPED）。外部 Benchmark 候选初筛文件 commits e34a5dc + a693120。 |
| 2026-11-25 | P1 外部效标来源初筛：新增 external-benchmark-candidates.md，按构念、Oracle/Verifier、环境复现、数据/代码许可和泄漏风险登记 AppWorld、AgentDojo、WebArena-Verified、OSWorld-Verified、GAIA、WorkArena。AppWorld 任务/环境材料受加密 bundle 与加密再分发要求约束；GAIA 测试数据 gated；WorkArena 实例需 gated access。仅为候选，不导入数据、不声称许可已获批准。CI-01 最新完整验证 Run #1852（head 5cf094f）PASS，167/167 tests，真实 IDA/ERA Schema 验证 PASS。 |
| 2026-11-25 | CI-01 真实报告契约验收完成：commit 6c317dc 将 validate_report() 的 JSON Schema + cross-field 校验接入 Round 4 Job；Run #1847（45594508903，head 0366be3）actionlint、Skill 包、Benchmark、167/167 离线测试、IDA/ERA 报告契约校验及真实证据分析全部 PASS，Artifact 15012860922。其他受 PR #38 前置条件保护的 Jobs 仍为 SKIPPED。Round 4 结果与限制见 round4-real-evidence-results.md。 |
| 2026-11-25 | Round 4 真实证据分析完成：PR #44 run #1842（45551929918）167/167 离线测试、真实证据导入、IDA、ERA PASS，artifact 14994092367。IDA 15/15 Schema、61/61 source ref 解析，但总体 PARTIAL；ERA 3/15 Pilot，3/3 Agent/Oracle PASS，95% Wilson 区间下界 0.4385，Judge NOT_RUN、Regression 无配对、IRT/G-Theory 未拟合、综合分 NOT_VALIDATED。结果详见 round4-real-evidence-results.md。commit 56d0383。发现此前真实证据 Job 未调用正式报告验证器，已在 commit 6c317dc 加入 IDA/ERA JSON Schema 与 cross-field contract validation，待 CI 复验。 |
| 2026-11-25 | 真实证据 CI 首轮：actionlint、Skill 包、Benchmark、167 项离线测试 PASS；真实证据 Job 发现 Artifact name 配置错误，已从 workflow 日志和 run #451895 artifact 列表核实正确名称并修复。Runtime Record 现在记录 DSH 0.2.2-rc.1、Playwright 1.64.1、Chromium Headless Shell 156.0.8078.4 和 Ubuntu runner image ubuntu26/20261116.202。等待最新 head 重跑。 |
| 2026-11-25 | 更新 PR #38 外部依赖状态：正式 Builder artifact 与独立 Validator PASS 已核验，三条真实 Skill Pilot / Gold Oracle 3/3 PASS；新增真实证据导入器和 IDA/ERA CI Job。Builder production Job failure、12/15 NOT_RUN、dataset needs_info 均保留为限制。 |
| 2026-11-25 | P0 修复：Validator 不再读取 Schema 未定义的 datasets[].sample_count，改为依据 split-level sample_count 并检查来源数据集非空；新增两项回归测试。run #1808 在精确 head a2dc04e 上 actionlint、Skill 包、Benchmark 和 162 项离线测试全部 PASS。新增 methodology-matrix.md，覆盖内容效度、IRT、G-Theory、ICC/Kappa、Judge 校准、缺陷注入、外部效标、样本量/功效和区间策略。公式科学效度、专家盲评、真实缺陷和 ERA 实验仍未完成。 |
| 2026-11-25 | 建立需求、研究证据库、双路径方法论、公式验证协议、实验设计、设计决策、候选指标字典、IDA/ERA/Runtime Record Schema、离线 IDA 检查器、ERA 分析器、报告验证器与测试；Draft PR #44 已创建。更新 Skill 质量标准并加入报告 Schema 与运行记录 Schema；validate_skill.py 增加 JSON Schema 检查；Release Gate 测试同步纳入新增 Schema 和当前 Workflow 实现。补充 CVI/CVR、IRT 样本量、G-Theory、SkillsBench 和 OECD/JRC 复合指标手册证据；细化规范性/经验性权重、损失驱动阈值和敏感性验证方法；正式定义 IDA/ERA 用途条件化质量画像；建立 defect-mutation-catalog.yaml 和对应测试。PR #44 run #1774 在精确 head cb43aa7 上 actionlint、正式包、Benchmark 样例和 151 项离线测试全部 PASS；IM-02 与 CI-01 的前一版验收完成；缺陷测试扩展后的最新 head 复验中。 PR #44 run #1784（45513477801）actionlint、正式包、Benchmark 样例 PASS，155 项测试中仅 1 个断言失败；修正描述断言后，run #1789（45513651073）仍有 1 个失败：missing-source mutation 使用 synthetic_gap_fill，但当前 Case Schema 要求该来源必须引用 synthetic_scenario；已改为 schema-valid 的 unknown + information_gaps 样本，等待最新 head 重跑。公式效度、专家盲评、盲测缺陷注入、真实 Agent 运行、IRT/G-Theory、版本元数据和 Release 仍未完成。RQ-01、RQ-02、RS-01、FM-01、EX-01、IM-01、IM-02、IM-04、CI-01 完成；RS-02、RS-03、DS-01、DS-02、FM-02、IM-05、IM-07 进行中。 |

### Round 4 Oracle Freeze Gate 异常输入加固（2026-11-25）
- 复核执行前冻结验证器时，发现畸形嵌套数据可能绕过 JSON Schema 错误收集，并在后续字段读取或集合构造阶段触发未处理异常，涉及比较报告 Reviewer A/B 节点、case_id 类型和顶层 manifest 类型。
- 已加固 scripts/validate_round4_oracle_freeze.py：Schema 校验后对非对象顶层输入提前返回；对 Reviewer A/B 与比较报告节点做类型保护；仅将字符串 case_id 纳入集合比较；非字符串 case_id 返回明确验证错误；仲裁者独立性判断不再假设输入可哈希。
- 新增 2 项回归测试，覆盖畸形嵌套审查报告 / case_id 和非对象顶层 manifest。Freeze Gate 测试由 9 项扩展为 11 项。
- Run #1925（45633631233，精确 head 01e81f4894a4b58361f65fe36fb5b7ca1254707b）通过 actionlint、正式 Skill 包、Benchmark、207/207 离线测试，以及 Round 4 IDA/ERA 报告契约检查；真实证据 artifact 15031253612。IDA/ERA 仍保持 PARTIAL，12 条仍 NOT_RUN，Judge NOT_RUN，综合分 NOT_VALIDATED。
- Run #1923（45633356833）因同一分支后续提交触发并发取消，未完成验证；不作为验收证据。Run #1924（45633425338）在前一代码 head 通过 207/207 测试，但随后代码又有小幅防御性修正，因此以 Run #1925 为当前有效证据。
- 本次仅增强验证器对无效输入的失败安全性，不改变 Oracle 决策规则，不创建 Gold，不授权 Runner。两份盲审包仍未分发/回收；人工评审与仲裁继续 NOT_RUN。

### 端到端推进与外部评审招募（2026-11-25）
- 用户要求一次性完成所有任务。重新核对 Issue #43、PR #44、TASKS.md、Round 4 Oracle plan、盲审包指南和最新 CI。PR #44 当前 head 为 c84d94b8655e8df0deb8fef3b25b3d990353cb1d，Draft/Open/未合并；PR #38 未触碰。
- 独立专家评审任务已按用户决定暂缓（EX-03=DEFERRED）。停止继续招募、催促报名或将评审者报名作为当前迭代的推进条件；原招募说明仅作为历史记录，不代表仍在招募。评审协议与 Schema 保留，未来如重新启动需另行决策。EX-03 不计为 DONE；所有依赖专家效标的科学效度主张继续保持 NOT_ASSESSED / NOT_VALIDATED。
- 盲审包已经生成并通过哈希/结构检查，但本次没有公开上传盲审包，也没有把 coordinator-only crosswalk 暴露给评审者。待志愿者确认后再通过受控渠道分别分发 A/B 包。
- 不会用同一模型伪装两名独立专家，不会自行生成 Gold 或假造真实用户/应用行为；这会破坏本项目 Issue #43 明确要求的独立效度证据。
- 最新 CI Run #1926（45634060282）仍是本分支 TASKS 上次更新后精确代码 head 的有效证据：207/207 离线测试、正式包、Benchmark、actionlint、Round 4 IDA/ERA 报告契约 PASS；生产 Builder / 独立验证 / Pilot jobs SKIPPED。
- 当前可由仓库维护者单独完成的工程工作已推进到执行前冻结门禁。尚需外部输入的工作包括：专家内容效度/评分者一致性、独立 Oracle 盲审和仲裁、外部基准数据许可/快照与独立 Oracle、真实缺陷注入与跨 Agent/Skill 运行效标、公式冻结验证，以及用户批准发布。上述任务不能仅靠本仓库代码或 CI 伪造完成。


### 最新提交 Run #1927 与外部来源许可复核（2026-11-26）
- PR #44 最新提交 `ceb7eadb01fbf3ee8fcabbeccf3f7c311c55ffdc` 对应 Run #1927（45636955491）Workflow SUCCESS。Validate Job：actionlint、正式 Skill 包、Benchmark 贯通样例及离线测试全部通过，207/207 tests PASS。Round 4 real-evidence Job SUCCESS，重新导入冻结证据并执行 IDA/ERA 报告与 cross-field contract validation；报告保持 IDA=PARTIAL、ERA=PARTIAL、Judge=NOT_RUN、composite=NOT_VALIDATED、15 条中 3 条 Pilot / 12 条 NOT_RUN。Artifact #15033410956，SHA-256 `1f0a613ceb675b3156ae591c7550235b5571938026e9446291855b5e01fd3723`。
- 本次 Run #1927 的 Builder production、independent-validation、webapp-testing-pilot、adjudicate-pilot 等受上游门禁保护的 Job 均 SKIPPED；openrouter-preflight 的实际凭据/推理检查步骤也因不是显式 preflight marker commit 而 SKIPPED。不能把本次 CI 描述为新的 Builder 生产执行或 Pilot 扩容。
- 外部候选登记表已基于官方仓库 LICENSE / README 和官方 Hugging Face GAIA 数据集卡复核：AgentDojo 代码仓库 MIT；AppWorld 公开代码及加密保护 bundle 标示 Apache-2.0，bundle 的公开再分发及衍生内容须保持加密；WebArena、BrowserGym、OSWorld、WorkArena 代码仓库标示 Apache-2.0；GAIA validation/test 数据受 gated / 不得以 crawlable 形式再分享的条款约束。以上均不等于数据集、环境镜像、第三方软件、账号或实例的整体许可批准。
- WebArena-Verified 的具体数据版本和独立数据许可、OSWorld-Verified 具体任务/镜像、AgentDojo 各数据资产、WorkArena ServiceNow 实例授权仍未逐项取得并核验；候选仍是桌面初筛，不导入、不运行、不用于公式验证。
- Issue #43 招募公告截至本次核查仍无评审者报名或提交。Reviewer A/B 资料包未分发；没有真实双盲审查、独立仲裁或 12-case Oracle freeze。PR #44 继续 Draft/Open，PR #38 与 main 未修改。


### 外部来源复核文档更新后的精确 head 验证（2026-11-26）
- 最新文档 head `7e874e6dc7dee325afa72f272a774c9ffdf60fb6` 对应 Run #1928（45714022690）Workflow SUCCESS。Validate Job：actionlint、正式 Skill 包、Benchmark 贯通样例及 207/207 离线测试 PASS；Round 4 real-evidence Job SUCCESS，IDA/ERA 报告 JSON Schema 与 cross-field contract validation PASS。
- Run #1928 的 Round 4 结果：IDA=PARTIAL，15 条用例；ERA=PARTIAL，3/3 现有 Pilot 运行有效且 Gold PASS；12 条仍 NOT_RUN；Judge=NOT_RUN；composite=NOT_VALIDATED。Builder production、independent-validation、Pilot 和 adjudication jobs 均 SKIPPED，本次没有新增生产执行。
- Round 4 artifact #15068532330，SHA-256 `169584f44207cacf2e2021f8c4c1054ffacd50899780b66493b4b60c276f2dac`。Run #1928 的精确 head 与 artifact 已核验。
- 这次 Run 只验证代码、文档、离线测试及既有冻结证据的 IDA/ERA 分析，不改变人工评审、Oracle freeze、外部 Benchmark 授权或发布审批状态。


### TASKS.md 最新记录 head 的精确验证（2026-11-26）
- 精确 head `ff89125da4879e3af3d8e243bddc3f00c0da619e` 对应 Run #1929（45714154402）Workflow SUCCESS。actionlint、正式 Skill 包、Benchmark 贯通样例、207/207 离线测试 PASS；Round 4 IDA/ERA 分析与 JSON Schema / cross-field contract validation PASS。
- Round 4 artifact #15068059286，SHA-256 `d4fe7e74d9990d1062ccd6072416b78a23041c3b83863798a9dd581c14ccf09d`。IDA=PARTIAL（15 条），ERA=PARTIAL（现有 3/3 Pilot 有效且 Gold PASS），12 条 NOT_RUN，Judge=NOT_RUN，composite=NOT_VALIDATED。
- Builder production、independent-validation、Pilot 与 adjudication jobs 均 SKIPPED；此 run 不构成新的 Builder 生产执行、外部评审或 Oracle freeze。


### 按 TASKS.md 执行的架构/协议/校准接口补齐（2026-11-26）
- 新增 `architecture-and-acceptance-baseline.md`，并通过 decision-log D-007 冻结工程架构和验收解释基线；requirements.md 已同步为“需求/架构基线已冻结，发布验收待完成”。SC-01 DONE。
- 新增 `runtime-assessment-protocol.md`，将运行前冻结、单次运行、失败归因、Judge/Gold 独立性、Capability/Regression、重复/停止规则写成可执行协议。DS-02 DONE；DS-03/DS-04 设计任务完成，实证仍由 EX-05 跟踪。
- 新增 Judge Calibration Report Schema、`scripts/validate_judge_calibration.py` 和 8 项测试。验证器重新计算 adjudicable denominator、exact match、False Pass/False Fail、abstention 和 accuracy，校验 suite SHA/case IDs，并阻止 synthetic smoke 被标记为 VALIDATED_FOR_SCOPE。IM-03 保持 IN_PROGRESS，因现有 LLM 校准执行脚本尚未集成该报告契约，且没有独立 Gold 实证。
- 更新根 README、CHANGELOG 和研发 README，明确 0.0.2 仍在开发、正式版本仍为 0.0.1、当前实证边界和未完成门禁；DOC-01 IN_PROGRESS，版本元数据等所有发布门禁满足后再升级。
- Run #1933（45719605220，代码 head `878303fba7d4db75df979073d97c9d529b70d74e`）Workflow SUCCESS：actionlint、Skill 正式包、Benchmark、215/215 离线测试 PASS；新增 8 项 Judge calibration contract tests 均执行通过。Round 4 IDA/ERA 报告 Schema 与 cross-field contract PASS，artifact #15071077843，SHA-256 `890e71e91b58d95f3ee7d551380db0606305e92cafb1d00bbbeaf9a8f24369f8`。IDA/ERA 仍 PARTIAL，3/15 Pilot，12 NOT_RUN，Judge NOT_RUN，composite NOT_VALIDATED；Builder production / independent-validation / Pilot / adjudication jobs 均 SKIPPED。
- RS-02/RS-03 的文献与方法复核任务已完成；外部数据许可/样本快照、专家盲评、缺陷盲测和真实运行验证仍分别由 EX-02/03/04/05/07 跟踪，不因研究文档完成而提前标记实验完成。
- PR #44 继续 Draft/Open；PR #38 与 main 未修改；不创建 tag/release。


### 任务质量审计报告（2026-11-26）
- 新增 [quality-report.md](quality-report.md)，逐项汇总 38 项任务状态、工程交付、CI/Artifact 证据、IDA/ERA 真实结果、科学效度缺口和发布建议。
- 任务表状态统计：21 DONE、0 IN_PROGRESS、15 BLOCKED、2 DEFERRED、0 TODO。DONE 只表示该项设计/工程交付完成，不表示关联实证实验或发布门禁通过。
- 当前结论：工程验证通过，实证效度部分完成，发布门禁未通过。PR #44 保持 Draft/Open，不创建 v0.0.2 tag/release。


### 最新完整文档 head 复验（2026-11-26）
- 最新报告/任务清单文档 head `87d3747444ddaa5e7391e202f7595121f1fa86a7` 对应 Run #1939（45720458350）Workflow SUCCESS：actionlint、正式 Skill 包、Benchmark、215/215 离线测试 PASS；Round 4 IDA/ERA 报告 Schema 与 cross-field contract PASS。
- Round 4 artifact #15072186678，SHA-256 `be681dfd0a61be229e66b7953b3f02f66366d31d700b8e33755e3719df739b44`。IDA/ERA PARTIAL，15 条用例中 3 条 Pilot、12 条 NOT_RUN，Judge NOT_RUN，composite NOT_VALIDATED。
- Builder production / independent-validation / Pilot / adjudication jobs 均 SKIPPED；本次没有新增真实运行或人工 Oracle 证据。
- 最新任务质量报告见 `quality-report.md`；当前共 38 项任务。PR #44 继续 Draft/Open。


### TASKS.md 最终审计记录 head 复验（2026-11-26）
- 精确 head `0f50a9cc9de97ec2778b026c34dfd69e2c1b8bf8` 对应 Run #1940（45720639140）Workflow SUCCESS：actionlint、正式 Skill 包、Benchmark、215/215 离线测试（含 8 项 Judge calibration contract tests）PASS；Round 4 IDA/ERA 报告 Schema 与 cross-field contract PASS。
- Round 4 artifact #15072316423，SHA-256 `8532534e9f923fb949484c66038523d011b4a5bafe788724b7a3e7b3d76904e0`。IDA/ERA 仍 PARTIAL，15 条中 3 条 Pilot、12 条 NOT_RUN；Judge NOT_RUN；composite NOT_VALIDATED。
- 本次生产 Builder、independent-validation、Pilot、adjudication Jobs 均 SKIPPED；没有新增真实运行、评审或 Oracle freeze。阶段性任务质量报告已归档于 `quality-report.md`。


### TASKS.md 与质量报告最终提交复验（2026-11-26）
- 精确 head `3a99fcc0de3609971d6c701bade210251c77fd04` 对应 Run #1941（45720784376）Workflow SUCCESS：actionlint、正式 Skill 包、Benchmark、215/215 离线测试 PASS；Round 4 IDA/ERA Schema 与 cross-field contract PASS。
- Round 4 artifact #15070789521，SHA-256 `729c0131446788b21a06aa280b8b75f48218e3e21e5b666a284ca9a59977c1e5`。IDA/ERA PARTIAL，15 条中 3 条 Pilot、12 条 NOT_RUN，Judge NOT_RUN，composite NOT_VALIDATED。
- Builder production、independent-validation、Pilot、adjudication jobs 均 SKIPPED；本次未新增真实运行、独立评审或 Oracle freeze。
- 当前任务质量报告：`quality-report.md`。38 项任务状态：21 DONE、0 IN_PROGRESS、15 BLOCKED、2 DEFERRED、0 TODO。


### 最新质量报告提交 head 复验（2026-11-26）
- 精确 head `122d38527a3af2e3d012598cbb6ac93b3b4ecfc0` 对应 Run #1944（45721014232）Workflow SUCCESS：actionlint、正式 Skill 包、Benchmark、215/215 离线测试（含 8 项 Judge calibration contract tests）PASS；Round 4 IDA/ERA Schema 与 cross-field contract PASS。
- Round 4 artifact #15070934643，SHA-256 `6ba0929eabd3354dbb06eedf43e55ff682b435320415b737c36063f2f8237ea1`。IDA/ERA PARTIAL，15 条中 3 条 Pilot、12 条 NOT_RUN，Judge NOT_RUN，composite NOT_VALIDATED。
- Builder production / independent-validation / Pilot / adjudication jobs 均 SKIPPED；没有新增真实运行、独立评审或 Oracle freeze。


### 质量报告与 CHANGELOG 最新 head 复验（2026-11-26）
- 精确 head `bca98059650afce9df752917553bcff98adeb91e` 对应 Run #1947（45721216859）Workflow SUCCESS：actionlint、正式 Skill 包、Benchmark、215/215 离线测试（含 8 项 Judge calibration contract tests）PASS；Round 4 IDA/ERA Schema 与 cross-field contract PASS。
- Round 4 artifact #15071653396，SHA-256 `153f702408de37fc4581e7441171b7f53916809be256563a89501c883f50bf80`。IDA/ERA PARTIAL，15 条中 3 条 Pilot、12 条 NOT_RUN；Judge NOT_RUN，composite NOT_VALIDATED。
- 生产 Builder、independent-validation、Pilot、adjudication Jobs 均 SKIPPED；没有新增真实运行、独立评审或 Oracle freeze。


### Judge Calibration 执行脚本契约集成（2026-11-26）
- 将 tests/calibrate_judge.py 从旧版 ad-hoc JSON 输出迁移为 v0.0.2 Judge Calibration Report 契约；脚本生成 suite SHA-256、case IDs、Judge endpoint/model、Judge prompt 与实现 SHA-256、workflow/commit 身份、逐案 Gold/Judge 状态和重算 summary。
- 执行脚本在写出报告前直接调用 scripts/validate_judge_calibration.py 的 validate_report()，并传入原始 suite 文件进行字节哈希和 case ID 一致性验证；synthetic fixture 被固定标记为 calibration_kind=synthetic_smoke、status=NOT_VALIDATED、independent_gold=false。
- 新增 tests/test_calibrate_judge_contract.py，覆盖契约输出、False Pass/False Fail/Abstention 重新计算、哈希和执行身份记录。相关提交：33bd883（runner integration）、bbb2d85（integration tests）、98f9e66（test import correction）。
- PR #44 精确 head 98f9e66f63a3c6c6d3343e8e704145b4e0a83488 的 CI Run #1953（45731724029）已创建，当前待完成；在 CI 完成前不宣称本次集成测试通过。
- IM-03 继续 IN_PROGRESS：本次完成的是执行脚本与机器契约集成，不构成独立 Gold Judge 校准，不改变 Round 4 Judge=NOT_RUN 的实证结论。


### Judge Calibration 首轮集成测试修复（2026-11-26）
- Run #1953（45731724029，head 98f9e66）actionlint、正式 Skill 包和 Benchmark PASS；离线测试运行 218 项，其中 217 PASS / 1 FAIL。失败点是新测试把包含多个 UNKNOWN 的原始夹具误当成只有一个弃权，属于测试预期错误，不是报告计算逻辑失败。
- 已修正集成测试：按 Gold 状态定位 PASS/FAIL/UNKNOWN 案例，并将其他 UNKNOWN Gold 案例的 Judge 输出设置为非 UNKNOWN，从而构造可审计的单一 abstention 测试情形。修复 commit cd95707。
- 当前 PR head `cd95707df7e6adf147b8f74098918c39e1452abc` 的 CI 尚未返回；在该精确 head 完整验证前，不标记新增集成测试通过。


### Judge Calibration 集成修复后的完整 CI 验收（2026-11-26）
- 最新完整 head `f4d2cc2fadc2c8136a8c5d405a3d6a47eee5efb2` 对应 Run #1958（45731888915）Workflow SUCCESS。
- Validate Job：actionlint、正式 Skill 包、Benchmark 贯通样例、218/218 离线测试 PASS；新增 3 项 Judge runner integration tests 全部 PASS。
- Round 4 real-evidence-assessment Job SUCCESS，Round 4 IDA/ERA 报告 Schema 与 cross-field contract validation PASS；artifact #15077441739，SHA-256 `02e7d5a2386f0ea6e1f57a8382c6af64bd1f4a661f81e934cab569e74e4aa004`。
- Builder production、independent-validation、Pilot、adjudication 等 Job 均 SKIPPED；本轮没有新的真实 Builder 执行、Judge API 校准、独立评审或 Oracle freeze。
- IM-03 仅完成执行脚本与报告契约的工程集成；独立 Gold/held-out/盲法实证校准仍未完成，IM-03 继续 IN_PROGRESS。


### 最新 TASKS/质量报告/CHANGELOG 文档 head 复验（2026-11-26）
- 精确 head `5b108084f65cfb0e00b8552744267ccdc5e51f58` 对应 Run #1961（45732037841）Workflow SUCCESS：actionlint、正式 Skill 包、Benchmark、218/218 离线测试和 Round 4 IDA/ERA 报告 Schema/cross-field contract validation 全部 PASS。
- Round 4 artifact #15077885154，SHA-256 `fd3187c4a98a158b2dfe7b63fd2594c2c30540ab94a2e429886c6c11e72be122`。
- Builder production、independent-validation、Pilot、adjudication 等受上游门禁保护的 Jobs 均 SKIPPED；本次没有新增生产执行或人工评审证据。Run #1961 仅证明当前代码和文档基线通过 CI。


### Capability 测量分析器工程原型（2026-11-26）
- 新增 `scripts/analyze_capability_measurement.py`：仅纳入有效运行且有 independent_oracle / expert_adjudication Gold 来源的二元 Agent 结果；要求单一数据集身份、完整平衡 Configuration×Case 设计，拒绝重复单元格和缺失单元格。
- 实现探索性 Rasch 1PL 联合最大似然估计（配置能力位置、题目难度、局部信息近似标准误、题目/测试信息曲线），并对完全分离、不收敛和信息退化 fail-closed。
- 实现平衡双 facet Person×Item G-study 方法矩估计、Person/Item/Person×Item+Residual 方差分量、相对 G、绝对 Phi 和 D-study 题目数量画像；负方差分量保留 raw 估计并明确警告。
- 新增报告 Schema `schemas/capability-measurement-report.schema.json`、方法/边界说明 `capability-measurement-analysis.md` 和 `tests/test_analyze_capability_measurement.py`（5 项测试）。
- 工程估计器不证明模型假设或构念效度；不支持 2PL、多维 IRT、DIF、多 facet Seed/Environment/Judge、非平衡或重复测量设计。缺少 independent Gold 时输出 NOT_ASSESSED，不以 0 代替缺失。IM-05 保持 IN_PROGRESS，等待 CI 与真实数据/参数恢复验证。


### Capability 测量原型与文档基线 CI 复验（2026-11-26）
- 代码/测试精确 head `52093376778d428145e9b968df38ba54e9d26d4f` 对应 Run #1968（45732528514）SUCCESS：actionlint、正式 Skill 包、Benchmark、223/223 离线测试（含 5 项新 Capability measurement tests）和 Round 4 IDA/ERA 报告契约均 PASS；artifact #15077900941，SHA-256 `6fbcc3496f66f2aad9bc2a2057b8380523b19d6c8cbb4fdacb85bf48c2f9ed5e`。
- TASKS、质量报告和 CHANGELOG 更新后的精确 head `c1babc7ec9d51de6ac0c3cdb36232573c32f53bb` 对应 Run #1972（45732657722）Workflow SUCCESS：actionlint、正式 Skill 包、Benchmark、223/223 离线测试和 Round 4 IDA/ERA 报告 Schema/cross-field validation 全部 PASS；artifact #15077358259，SHA-256 `af22544c66e638472b91f9e2d0a85f237e916a44ee3ebe082b20c4a3c099ea57`。
- 本轮 Builder production、independent-validation、Pilot、adjudication jobs 均 SKIPPED；没有新增生产执行或独立 Gold 数据。IM-05 继续 IN_PROGRESS，原型输出仅 ESTIMATED_EXPLORATORY。


### Capability Rasch 参数恢复模拟实验（2026-11-26）
- 新增 `scripts/run_capability_measurement_monte_carlo.py`：固定随机种子、已知 Rasch 1PL 数据生成机制、重复估计、分离/失败计数、参数相关与 RMSE 汇总，并报告跨重复分布分位数。
- 新增 `tests/test_capability_measurement_monte_carlo.py`：执行 30 次 × 80 配置 × 25 用例的确定性模拟；门禁有效重复数及能力/难度相关、RMSE 范围，避免仅断言“算法能运行”。
- 固定设计模拟：26/30 次可估计；能力与题目难度平均相关约 0.867/0.961，RMSE 约 0.492/0.268 logits。4 次失败因完全分离被 fail-closed。
- 该证据等级仅为 SIMULATION_ONLY；分位数是模拟重复分布，不是现实置信区间，也不证明模型适配、DIF、测量不变性或外部效度。G-Theory 参数恢复仍未完成，因此 IM-05 保持 IN_PROGRESS。
- 本轮实现提交：`bb7cc26378cdc262c5560f49f358a258a00de367`；TASKS 记录提交：`3acad40fb2ecb1846aa7619ad0905cebf92894bc`。
- Run #1977（45756867922）在精确 head `3acad40fb2ecb1846aa7619ad0905cebf92894bc` 上 SUCCESS：actionlint、正式 Skill 包、Benchmark、224/224 离线测试（含 30-replication Monte Carlo 参数恢复测试）PASS；Round 4 IDA/ERA 报告 Schema/cross-field validation PASS；artifact #15088650704。真实数据仍为 IDA/ERA PARTIAL、15 条中 3 条 Pilot / 12 条 NOT_RUN、Judge NOT_RUN、composite NOT_VALIDATED。该 Run 的 Builder production / independent-validation / Pilot / adjudication jobs 均 SKIPPED。
- 更新任务台账后的精确 head `2979a43652b6f0548769c5e81458d8cfa35f496c` 由 Run #1978（45757021210）Workflow SUCCESS 再次验证：actionlint、正式 Skill 包、Benchmark、224/224 离线测试和 Round 4 IDA/ERA 报告契约 PASS；Round 4 artifact 需以 Run #1978 的 artifact 清单为准。Builder production / independent-validation / Pilot / adjudication jobs 均 SKIPPED。


### G-Theory D-study 诊断性测试（2026-11-26）
- 新增确定性 crossed Configuration×Case 二元响应测试，检查 D-study 相对 G 与绝对 Phi 系数在增加题目数时有界且单调不减。
- 新增负方差分量回归测试，确认 raw method-of-moments 估计被保留、展示分量截断并显式发出警告。
- Run #1980（45757275859）在精确代码 head `e195afdca502f5fcd10fffc7334d6f90ce115e7a` 上 SUCCESS：actionlint、正式 Skill 包、Benchmark、226/226 离线测试（含 Rasch Monte Carlo 与 G-Theory 新增测试）PASS；Round 4 IDA/ERA 报告契约 PASS。该 G-Theory 测试是数值性质/失败安全测试，不是 G-Theory 参数恢复或实证效度证明。
- IM-05 仍 IN_PROGRESS：还缺 G-Theory Monte Carlo 参数恢复、正式模型拟合诊断、DIF/测量不变性及真实外部效标验证。


### EX-06 真实证据导入与 IDA/ERA 运行完成（2026-11-26）
- 强化 `scripts/import_dsh_pilot_records.py`：要求 runner 的 evidence_files manifest 明确包含 DSH `dsh-events.jsonl`，逐项验证 SHA-256；拒绝空清单、重复/不安全路径、路径穿越和符号链接逃逸；逐行解析 JSONL 并检查可用的 case_id/run_id 身份字段。
- 将每条 Runtime Record 的 `trace_sha256` 纳入 `runtime-record.schema.json`，并将核验后的 DSH trace digest 写入记录及导入 metadata，形成从规范记录到原始轨迹的可复核绑定。
- 新增 4 项导入器安全/完整性测试，覆盖 trace 哈希绑定、缺失 manifest、哈希错配和路径穿越；并验证 trace digest 输出。
- 代码提交：`e7245d2d4725c5c2e07fcd0e68f63a56a19a07bb`；测试修正提交：`d899ea3fab0b0f27a9d8fc1c57e78ade28492683`。
- Run #1983（45800505196）在精确 head `d899ea3fab0b0f27a9d8fc1c57e78ade28492683` 上 SUCCESS：actionlint、正式 Skill 包、Benchmark、230/230 离线测试 PASS；Round 4 evidence Job 成功导入 3 条真实 Pilot，IDA/ERA Schema 与 cross-field contract PASS；artifact #15105794918，ZIP SHA-256 `0d703863f965f99e34f721c00895ada15acd25ef0495015d4492826407962e03`。
- 任务验收边界：EX-06 DONE 仅代表现有冻结 Builder/DSH/Runner/Oracle 证据已被安全规范化并完成 IDA/ERA 运行。结果仍为 IDA/ERA PARTIAL、15 条中 3 条 Pilot / 12 条 NOT_RUN、Judge NOT_RUN、composite NOT_VALIDATED；不表示完整 Capability/Regression 或科学效度验证完成。


### EX-05 Capability / Regression 真实效标实验外部阻塞核查（2026-11-26）
- 复核 GitHub Issue #43：目前仅有项目方发布的盲审招募公告，无独立评审者报名或提交；12-case Oracle freeze 尚不能执行，EX-07 前置条件未满足。
- 现有真实数据仅 WB-02/WB-10/WB-12 三条 Pilot，独立 Oracle 3/3 PASS，但它们来自单一 Skill revision / 单一模型运行配置 / 每 case 一次运行；不能识别 Agent/Task/Seed/Environment 方差，也不能构成 Regression baseline/candidate 配对。
- Run #1983（45800505196）中 production Builder、independent validation、Pilot、adjudication jobs 均 SKIPPED；OpenRouter preflight PASS 不等于生产执行授权，也没有新增运行样本。
- 因主要验收条件依赖独立 Oracle freeze、额外运行环境/权限和多配置配对数据，EX-05 从 IN_PROGRESS 调整为 BLOCKED。解除条件见任务行；不降低实验标准、不用模拟数据冒充真实效标。


### IM-03 Judge 校准接口完成、实证校准外部阻塞（2026-11-26）
- 新增 manual / LLM 共用的 observations 输入 Schema 和导入器，绑定冻结 suite SHA-256、完整 case IDs、独立 Gold 来源、held-out split、blind/independent-review 声明、Judge 类型/Provider/Model/Prompt/Implementation 身份、逐案 Gold/Judge evidence refs、匿名 reviewer/adjudicator IDs，以及原始 observations 文件 SHA-256。
- Validator 对 independent_empirical 强制检查每条观测 evidence_validated、Gold/Judge evidence ref 和对应匿名评审/仲裁者 ID；Builder/synthetic labels 不得作为独立 Gold。Importer 对 empirical 输入只产生 PARTIAL，不能自动输出 VALIDATED_FOR_SCOPE。
- 支持预注册重复 Judge 运行。重复结果按唯一 case 聚合 majority accuracy（平票为 UNKNOWN），False Pass/False Fail 采用保守 case-level 规则，abstentions 以 judgement 为单位；报告 case_count、observation_count、repeat disagreement 和 repeat agreement，避免将重复判断伪装成独立样本。
- 新增 manual/LLM 导入、suite hash、case 覆盖、Gold 来源、逐案证据、重复运行与伪重复防护测试；Run #1993（45802577224）精确 head `4067dba939a4e5171864c85cde413c46e934ee65`：238/238 离线测试 PASS；Round 4 IDA/ERA job SUCCESS，Artifact #15108810359，ZIP SHA-256 `d899391a3603954a14959fe78568fed9e3b503c10959154a08dc022318686d9f`。
- 实证边界：当前只有 synthetic_smoke/NOT_VALIDATED；没有独立 held-out Gold 集、真实人工/LLM Judge 观测或外部审计。Issue #43 盲审招募帖目前无独立评审者响应。IM-03 调整为 BLOCKED，而不是将接口实现误报为 Judge 有效性验证完成。


### IM-05 Capability / Regression 测量性质推进与外部数据阻塞（2026-11-26）
- Rasch 1PL 增加 Person/Item infit 与 outfit mean-square 描述诊断；不设通用阈值、不输出推断性 fit p-value。报告显式将 DIF 和 measurement invariance 标记为 NOT_ASSESSED，原因是缺少预注册分组变量及多组 held-out 矩阵。
- G-Theory 参数恢复实验：logistic crossed random-effects Bernoulli DGP；真值由独立 observed-score-scale Monte Carlo integration 得到；每种 DGP 100 次重复，四种条件（balanced moderate、low prevalence、low person variance、high item variance），比较 20×10、40×25、80×50 三种配置/题目设计。
- 20×10 设计的 G/Phi RMSE 约 0.1638–0.2292，低人方差场景 raw Person 分量负值率 41%；40×25 RMSE 约 0.0602–0.1490，低人方差负值率 23%；80×50 RMSE 约 0.0283–0.1103，低人方差负值率降至 2%。这些是模型条件下的模拟采样分布，不是现实置信区间或普遍样本量门槛。
- Run #2002（45804426404）精确 head `61fd978f496a3eb2db00eeb89a4bf696b84ddbf5`：actionlint、正式包、Benchmark、241/241 离线测试 PASS；3 种 G-Theory 样本设计模拟 PASS；Round 4 IDA/ERA 和 Capability 报告契约 PASS。Artifact #15107584570（G-Theory，ZIP SHA-256 `c9e7f8f7788439932e88658318c1cd9fbf39a415ac141ad7fce115618a3db90b`）；Artifact #15108548510（真实证据与 Capability 报告，ZIP SHA-256 `d02e9557b071febdac9bc93e53b4306727033e35a0394492ad498e36c9615e1b`）。
- 真实 Round 4 Capability 诊断读取 3 条真实 Runtime Record，得到 1 configuration × 3 cases；Rasch 需要至少 3 persons × 3 items，G-study 至少 2 persons × 2 items，因此两者均 NOT_ASSESSED；DIF 和测量不变性也 NOT_ASSESSED。没有将缺失估计写成 0。
- IM-05 调整为 BLOCKED：自主可完成的估计器、描述诊断、模拟参数恢复和真实数据契约已实现；解锁仍需多配置/多组 held-out 真实数据、独立外部效标、足够重复运行及配对 baseline/candidate 版本。当前模拟只验证指定 DGP 下的 observed-score estimand，不证明实际 Skill 能力测量有效。


### IM-07 Skill 质量标准与按需引用完成，正式版本升级受发布门禁阻塞（2026-11-26）
- Skill 内 quality-standard.md/yaml 已声明方法标准 2.0.0、适用 Builder release 0.0.2；IDA、ERA、Runtime Record、Formula Validation、Expert Review schemas 已纳入 Skill references。
- SKILL.md 明确按任务场景按需读取 16 个 references；validate_skill.py 检查引用集合与实际文件完全一致、无缺失/多余文件、无二级 reference 依赖、Schema Draft 2020-12 有效。
- Run #2004（45804838674，精确 head `013c351812b801554faa72fd360b208b9b553bb4`）actionlint、Skill package validation、Benchmark、241/241 离线测试 PASS；Round 4 evidence analysis PASS。
- 当前正式 Skill package VERSION 和 SKILL.md metadata.version 均为 0.0.1。由于 v0.0.2 尚未通过 Release Gate，且用户明确禁止擅自合并 PR/创建 Release，不升级正式版本元数据。IM-07 状态调整为 BLOCKED，解除条件是所有 Release Gate 通过并取得明确发布批准。


### 用户决策：暂缓独立专家评审（2026-11-26）
- 用户明确决定暂时取消独立专家评审/仲裁任务。EX-03 与依赖独立盲审的 EX-07 状态调整为 DEFERRED，而非 DONE 或 NOT_APPLICABLE；其评审协议、评分 Schema、盲审包生成器和既有实现保留。
- 停止把公开招募、等待报名或专家盲评组织作为当前迭代的执行路径；不再重复检查 Issue #43 是否有人报名。
- 此决策仅暂缓专家评审工作，不构成科学效度验证通过，也不授权用 LLM 自评、内部自评、模拟或确定性单测替代独立证据。凡依赖独立专家效标的结论继续标记为 NOT_ASSESSED / NOT_VALIDATED；相关发布门禁不得因此自动放行。


### QA-02 离线 IDA 评估器确定性敏感性验证完成、语义验证外部阻塞（2026-11-26）
- 新增 `scripts/run_ida_mutation_validation.py`，按 defect-mutation-catalog.yaml 对 IDA-M01–M08 运行八种确定性控制缺陷，并设置格式变化、Case ID 重命名、Case 顺序变化、未引用来源登记四种 negative controls。
- 每个 mutation/control 都重新生成 IDA report，验证 IDA report Schema/cross-field contract，记录数据集 SHA-256、报告 SHA-256、预期信号、观察信号和结构错误。
- Run #2011（45806101196，精确 head `9cb0e46cd78193a9419929f90c73817a0ac511c3`）：243/243 测试 PASS；8/8 确定性缺陷检出，Wilson 95% CI 0.676–1.000；0/4 negative-control false positive，Wilson 95% CI 0–0.490。Artifact #15108859637，ZIP SHA-256 `bb45162be43dd87e2b0587e8d35ae80c2b4328870bc2689debf23a594d323a1e`。
- IDA-M09–M12（歧义任务、错误 Gold、构念错配、答案泄漏）仍 NOT_ASSESSED，必须依赖盲法专家、独立 Oracle 或污染审计。4 个 negative controls 样本量太小，不能将 0/4 解读为一般 false-positive rate 接近 0。
- Round 4 真实数据 IDA 报告为 PARTIAL；G01 PASS，G02–G04 NOT_ASSESSED，G05/G07 UNKNOWN，composite NOT_VALIDATED。没有把结构性规则敏感性误报为内容效度。
- QA-02 调整为 BLOCKED：自主工程验证与控制缺陷敏感性实验完成；解除条件是独立专家盲评、独立 Gold/Oracle、语义缺陷和泄漏审计结果导入并完成独立复核。


### QA-03 真实运行端到端证据更新与生产运行外部阻塞（2026-11-26）
- Run #2011（45806101196）重新导入冻结的 DSH Round 4 记录，执行 IDA、ERA 和 Capability measurement analysis，并验证所有报告 Schema/cross-field contract。
- 当前真实 Pilot：3/15 条；Agent outcome 3/3 PASS，Process outcome 3/3 PASS，independent Gold 3/3 PASS。只有 1 条 mutation fault（search-case-sensitive），且 fault_detected=true；其余 2 条无注入。该极小且不平衡的样本不能估计一般故障检出率或误报率。
- 12/15 条 NOT_RUN；所有 grader_outcome UNKNOWN，grader_validation NOT_RUN；pair_id、repeat_group_id、seed、cost_usd 缺失；Regression analysis 为 null；composite NOT_VALIDATED。Capability 只有 1 configuration × 3 cases，描述性 PARTIAL，Rasch/G-Theory NOT_ASSESSED。
- Round 4 artifact #15110340499，ZIP SHA-256 `4fe6f5f2bf4de10f7befd4ad2a6a6a70a1b4293e84e0c9e15d5593bd109124ed`。
- 生产运行、额外 Pilot、重复执行、独立 Judge/仲裁和 baseline/candidate 配对需要真实环境、预算与外部授权。相关 production/pilot/adjudication workflow jobs 均 SKIPPED；没有擅自触发收费或生产执行。QA-03 调整为 BLOCKED。


### DOC-01 文档同步完成、正式版本号升级受发布门禁阻塞（2026-11-26）
- 根 README 与研发 README 已同步当前 v0.0.2 分支状态、最新 IDA/ERA/Capability 证据、G-Theory 模拟、IDA mutation 结果和外部依赖限制；新增 controlled-mutation 与 Capability analysis 文档入口。
- CHANGELOG、TASKS 和 quality-report 已记录 Run #2011 的 243/243 测试、8/8 deterministic mutation detection、0/4 negative-control false positives、G-Theory 20×10/40×25/80×50 敏感性实验和 Round 4 3/15 Pilot 状态。
- 正式根 VERSION 与 Skill frontmatter metadata.version 保持 0.0.1，和已发布 Release 一致。v0.0.2 尚未达到发布条件，且未获发布批准；不得提前改写正式版本号、创建 tag/release 或合并 PR。DOC-01 调整为 BLOCKED，仅剩 release-stage version transition。


### QA-02 metamorphic negative-control validation completed（2026-11-27）

- 为四种 negative controls 增加 baseline-vs-transformed invariant signature，比较 overall status、gate status/severity 与 metric status/value/unit/numerator/denominator/interval；原始数据集 SHA-256 不纳入不变量比较。
- 若控制样本触发硬 FAIL 或改变不变量签名，则计为 false positive。四种控制均通过：formatting-only、consistent case ID rename、case order reversal、unused source registry entry；4/4 指标签名完全一致。
- Run #2023（45892053327，精确 head `49613acf6d540f5ef494335a45eebca65077a64b`）SUCCESS：actionlint、Skill package、Benchmark、243/243 tests、G-Theory 20×10/40×25/80×50、IDA controlled mutation、Round 4 real-evidence contract 均 PASS。
- 8/8 deterministic mutations detected（Wilson 95% CI 0.676–1.000）；0/4 negative-control false positives（Wilson 95% CI 0–0.490）；invariant metric failures 0/4。Artifact #15152600525，ZIP SHA-256 `bdc08d2a95efcffa5ec1c8bbaa43b9432c27e9b639b09795fcefb9c6e76125ef`。
- QA-02 仍 BLOCKED：此结果仅证明对八种指定合成变异的实现敏感性，以及四种预设语义保持变换下的指标不变性；不证明真实语义缺陷检出、构念效度、Gold 正确性或污染抵抗能力。IDA-M09–M12 继续 NOT_ASSESSED。


### 本轮任务收敛审计（2026-11-27）

- 已复核本任务清单全部 37 项：20 DONE、15 BLOCKED、2 DEFERRED；没有将 BLOCKED/DEFERRED 改写为 DONE。
- 最近一次完整 PR workflow：Run #2025（45892463427），在精确 head `7b4ffa5ae8f0b9232ef1b8392d9863b22b6871a4` 上 SUCCESS。该 Run 验证的是该提交对应的 CI 工作流，不代表任何被跳过的生产执行或外部实证任务完成。
- 本分支可由现有代码、合成夹具、离线测试和文档独立完成的工程工作已完成并保留对应证据；剩余 BLOCKED 项均有明确外部解除条件：独立 Gold/语义标签与污染审计、合法且锁定的参考数据资产、真实多配置/重复/配对 Agent 运行及预算/环境授权、独立 Judge 校准数据、独立开发/验证集，以及正式发布门禁。
- EX-03 与 EX-07 继续 DEFERRED，遵循用户暂缓独立专家评审的决定；不招募、不分发盲审包、不等待报名。
- 当前阻塞任务：FM-03、EX-02、EX-04、EX-05、IM-03、IM-05、IM-07、IM-09、QA-01、QA-02、QA-03、QA-04、DOC-01、REL-01、REL-02。各项不得仅因工程接口、模拟、Schema 或 CI 通过而解除。
- 版本元数据仍为 0.0.1；PR #44 仍保持 Draft/Open。未执行 merge、tag 或 Release。v0.0.2 只有在对应实证门禁满足并取得必要发布批准后才能发布。


### BLOCKED / DEFERRED 任务永久不可完成性复审（2026-11-27）

- 复审原则：只有存在可证明的永久性、不可逆客观障碍，且不存在合理替代路径时，才从任务清单删除。缺少当前资源、授权、数据、评审者或发布批准均属于条件性阻塞，不构成“100% 无法完成”。
- 复审结论：本清单中 15 项 BLOCKED 与 2 项 DEFERRED，**没有任何一项满足永久不可完成的删除标准；本次删除 0 项**。保留任务不是承诺本迭代一定能完成，而是防止把未验证的验收要求从项目范围中悄然移除。
- BLOCKED 项逐项复审：
  - FM-03：独立效度验证可在取得独立效标、盲测缺陷与冻结验证集后执行；当前是证据资源缺失，不是方法不可执行。
  - EX-02：参考数据集可通过逐资产许可核验、版本锁定、Oracle 建立与合法快照构建；部分候选数据源不适用不代表所有候选永久不可用。
  - EX-04：缺陷注入识别实验可在独立确认基线、变体和冻结标签后执行；现有确定性变异测试不替代该实验。
  - EX-05：真实 Capability/Regression 实验可在取得运行授权、独立 Gold、足够配置/重复和配对执行后完成；现有 3 条 Pilot 不足不等于实验不可能。
  - IM-03：Judge 校准接口已实现；独立 Gold held-out 数据与真实 Judge 观测可由未来合规数据来源提供，当前校准结果仍不可声称有效。
  - IM-05：统计模块和模拟已实现；真实多配置、多组、重复与外部效标数据可在合适实验设计下采集，当前真实测量性质仍未验证。
  - IM-07：Skill 质量标准和引用集已准备；版本升级受发布门禁约束，是可在门禁满足后完成的发布步骤。
  - IM-09：候选公式比较可在独立开发集、验证集和效标齐备后执行；当前不估计权重/阈值是正确的证据保护措施。
  - QA-01：元评测集可在许可数据、独立标签和切分方案确认后建立；专家评审暂缓不使数据集建设永久不可能。
  - QA-02：M01–M08 工程敏感性验证已完成；M09–M12 的语义/Gold/泄漏验证可由独立 Oracle、合法外部审计或未来恢复评审后完成。现阶段保持 BLOCKED，不得将合成结果等同语义效度。
  - QA-03：真实端到端验证可在获得预算、运行环境、额外 Pilot、重复、Judge 和配对版本后继续；生产执行被跳过是授权边界，不是技术上的永久障碍。
  - QA-04：综合公式验证可在独立效标、盲测缺陷和冻结验证集齐备后执行；当前 composite 继续 NOT_VALIDATED / null。
  - DOC-01：研发文档已同步；剩余正式版本转换可在发布门禁通过且取得批准后完成，不应提前修改版本。
  - REL-01：发布候选审查可在适用质量门禁满足后开展；当前 Draft 状态是保护措施，不是永久无法审查。
  - REL-02：Tag/Release 可在 REL-01 通过并取得用户明确批准后执行；这是有意保留的授权门禁，不应删除。
- DEFERRED 项逐项复审：
  - EX-03：独立专家内容效度/评分者一致性实验由用户决定暂缓。没有证据证明永远无法组织；保留 DEFERRED，停止当前招募与执行，未来只有用户明确恢复时才重启。
  - EX-07：依赖独立 Gold/仲裁的 Round 4 12-case 盲审同样暂缓。12 条仍 NOT_RUN；不以现有 Builder 结果冒充独立 Gold。保留 DEFERRED，未来需用户恢复评审并具备资源后再执行。
- 不删除的具体理由：删除 BLOCKED 项会丢失尚未满足的验收义务；删除 DEFERRED 项会把“暂时取消”错误解释为永久放弃。若未来用户正式缩减产品范围，应通过显式 scope-change 决策将任务标记为 NOT_APPLICABLE，并记录替代验收依据，而不是伪称其不可能完成。
- 本次审查不改变任何任务状态，不改变科学结论，不解除任何发布门禁；当前 37 项状态仍为 20 DONE、15 BLOCKED、2 DEFERRED。


### IDA 畸形输入安全加固（2026-11-27）

- 发现 IDA 离线检查器在 Schema 已识别字段类型错误后，后续统计仍可能对畸形嵌套字段调用 `.get()`、对非列表字段迭代或将非字符串 bucket 当作哈希键，导致评价器异常退出而不是生成结构失败报告。
- 加固 `scripts/assess_dataset_quality.py`：对 `coverage_tags`、`source_refs`、`scenario_bucket`、`grading.criteria` 和 Manifest coverage dimensions 做防御式类型检查；非法 source registry ID 明确拒绝；不改变有效输入的统计定义或科学结论。
- 新增 3 项回归测试，覆盖畸形嵌套成员、错误集合字段类型和畸形 Manifest coverage dimensions。
- 代码提交：`b0eae3305ba92dc6aaaede341dc24bbe8ed484b4`、`c223fc483b03e61b1220c5d4d63a13ea358ea07b`、`660453f2b5ffd4d0aa5c78aa98ffbd99dca774f4`；测试提交：`708c111b93c81e06bed70bf004b6e5490a6d277a`、`868350c02a710292415a06f6ac78f65427448e9e`。该批次净改动仅涉及 IDA evaluator 和对应测试。
- Run #2034（[45916033576](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45916033576)，精确 head `ee0e03bbc0731acf4ca814a4d4a8b113f0ecad88`）SUCCESS：actionlint、Skill package、Benchmark、246/246 离线测试、G-Theory 三种设计模拟、IDA controlled-mutation、Round 4 IDA/ERA/Capability contracts 全部 PASS。三项新增畸形输入测试均通过；IDA mutation artifact #15162172012，Round 4 evidence artifact #15162087227，G-Theory artifact #15162201977。P0-ROBUST-01 据此标记 DONE。
- 此修复只改善畸形输入处理的工程鲁棒性，不改变 IDA 对语义效度、独立 Gold、污染审计或综合分的判断；QA-02 继续 BLOCKED，composite 继续 NOT_VALIDATED。


### 精确 PR head 完整复验（2026-11-27）

- 最新 PR head `93dce24092908d8f569804d2c14c7372339b26b1` 对应 Run #2036（[45916212402](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45916212402)）SUCCESS。
- actionlint、正式 Skill 包、Benchmark、246/246 离线测试、G-Theory 40×25 / 20×10 / 80×50 模拟、IDA controlled-mutation 和 Round 4 IDA/ERA/Capability report contracts 全部 PASS。
- 新增 3 项 IDA 畸形输入回归测试全部 PASS；Run #2036 的 Round 4 artifact #15162063803、IDA mutation artifact #15162118788、G-Theory artifact #15161964062。
- production Builder、独立验证、Pilot、adjudication 和 upstream asset audit jobs 均 SKIPPED；本次只复验既有冻结证据，没有新增生产运行、Pilot 或独立 Gold。
- 当前 38 项任务：21 DONE、15 BLOCKED、2 DEFERRED；PR #44 仍 Draft/Open，正式版本仍 0.0.1。


### Run #2036 — PR head 验证编号校正（2026-11-27）

- GitHub Actions API 确认 workflow run ID `45916212402` 的正式 run_number 为 **2036**（此前文档误写为 #2035）；精确执行 head 为 `93dce24092908d8f569804d2c14c7372339b26b1`。
- Run #2036 SUCCESS：actionlint、Skill package、Benchmark、246/246 离线测试、G-Theory 三种设计模拟、IDA controlled mutation 与 Round 4 IDA/ERA/Capability report contracts 均 PASS。
- Artifacts：Round 4 #15162063803、IDA mutation #15162118788、G-Theory #15161964062。production Builder、independent validation、Pilot、adjudication、upstream asset audit 均 SKIPPED；没有新增生产运行、Pilot 或独立 Gold。
- 本次仅校正 run 编号，不改变 38 项任务状态（21 DONE、15 BLOCKED、2 DEFERRED），也不改变 3/15 Pilot、12 NOT_RUN、Judge NOT_RUN、composite NOT_VALIDATED 的证据边界。


### D-008 执行范围收敛（2026-11-27）

- 用户明确要求：真正剩余任务中，团队可自主完成的继续完成；依赖外部的任务全部不做。
- 因此当前自主执行队列仅包括可由仓库现有代码、冻结证据和离线环境完成的工程修复、测试、契约/静态检查、证据复现和文档一致性审计。
- 外部依赖任务清单：FM-03、EX-02、EX-03、EX-04、EX-05、EX-07、IM-03 的独立校准、IM-05 的真实测量验证、IM-07 的正式版本升级、IM-09、QA-01、QA-02 的语义/Gold 验证、QA-03 的新增真实运行、QA-04、DOC-01 的正式版本转换、REL-01、REL-02。全部停止执行，不招募、不等待、不触发第三方数据/运行/审计或发布流程；原状态 BLOCKED / DEFERRED 保留，不删除、不伪装完成。
- 已完成的工程子组件继续保留其 DONE 证据；工程接口或模拟不能解除实证门禁。若后续发现新的可完全自主完成的子任务，继续直接执行并更新本清单。
- 版本仍为 0.0.1；PR #44 仍 Draft/Open；不执行 merge、tag、Release 或收费/生产运行。
- 本决策不改变 3/15 Pilot、12 NOT_RUN、Judge NOT_RUN、IDA M09–M12 NOT_ASSESSED、composite NOT_VALIDATED 的事实状态。


### P0-ROBUST-02 全仓库 JSON 严格解析与非有限数值拒绝（2026-11-27）

- 审计分支内 Python 脚本的 JSON/JSONL 读取入口，发现除既有报告验证器外，IDA/ERA 数据导入、Capability 分析、Round 4 盲审包、DSH Pilot 导入、Judge evidence importer、Skill package validator、release evidence verification 等路径仍使用 Python 默认 JSON decoder。默认 decoder 接受 `NaN`、`Infinity`、`-Infinity`，与 JSON 标准不符，并可能使 schema/统计路径接收非标准数值。
- 对上述数据输入、Schema、冻结套件、API/Artifact release evidence 和本地 fixtures 增加严格 `parse_constant` 拒绝；已有报告验证器继续递归检查嵌套数值 `math.isfinite`。Round 4 freeze validator 复用严格 blind-review JSON loader。
- 新增回归测试覆盖 IDA/ERA JSONL、DSH JSONL、Round 4 冻结数据、Judge observations 和各报告验证器的非法常量拒绝。
- Run #2065（[45947894476](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45947894476)，精确 head `2b238f9a18482f10429d9b04180952b89735675f`）SUCCESS：validate job PASS，Round 4 real-evidence assessment job PASS。Production Builder、Pilot、independent validation、adjudication 与 upstream asset audit 未执行/按 workflow 条件 SKIPPED；本次只验证代码、离线测试和已有冻结证据。
- 该任务属于工程输入健壮性与标准兼容性，不代表构念效度、语义效度、独立 Gold 正确性或综合分有效性已验证；QA-02、QA-03、QA-04 等原有状态不变。


### D-009 当前迭代范围收缩：移除全部外部依赖任务（2026-11-27）

- 用户明确要求：将依赖外部条件、当前无法由项目自主解决的任务从当前任务清单中清除。
- 因此从上方当前执行任务表移除以下 17 项：FM-03、EX-02、EX-03、EX-04、EX-05、EX-07、IM-03、IM-05、IM-07、IM-09、QA-01、QA-02、QA-03、QA-04、DOC-01、REL-01、REL-02。
- 这是一项明确的产品/迭代范围收缩，不是将任务标记为 DONE 或 NOT_APPLICABLE。它们不再属于当前 v0.0.2 执行范围；历史研究、已完成工程子组件、真实数据状态、科学限制和发布门禁证据继续留档。
- 已完成的自主工程能力仍以代码、测试、Schema、报告和历史 CI 证据保留；不得将其扩张解释为独立效度、语义效度、Gold 正确性、Judge 校准、真实 Capability/Regression 效度或综合分有效性已验证。
- 当前表中保留的任务均为 DONE；本次没有合并 PR #44、修改正式版本号、创建 tag/release，也没有触发收费或生产运行。
- D-009 取代 D-008 中“外部依赖任务继续保留在任务表”的要求；D-008 关于停止招募、停止等待、停止外部触发和发布边界的要求继续有效。


## 0.0.2 发布准备状态（2026-11-27）

- 自主工程任务：22/22 DONE；没有剩余当前范围内的 BLOCKED/DEFERRED 任务。
- 外部依赖任务：17 项已按 D-009 从当前任务队列移除；移除不等于完成或科学验证通过。历史证据与未验证限制保留。
- 新增发布准备基线：根目录 RELEASE-PREP-0.0.2.md 和 RELEASE-GATE-0.0.2.md；新增仅手动触发、confirm_publish 默认 false 的 .github/workflows/publish-release-v0.0.2.yml。
- 旧 v0.0.1 发布脚本保持独立；本分支 VERSION 与 Skill frontmatter 已同步为 0.0.2，main 仍为 0.0.1。元数据更新后的最终 head CI 尚待验证，尚未冻结正式 RC。
- 最新已确认精确 head CI：Run #2067 SUCCESS，head 5192144a497bdfede1d45c5d39dd2cdf187cd9a4；新增发布准备文档后需对新 head 重新执行完整 CI。
- 过程产物审计删除过时的 .github/publish-release-trigger.txt，并将 v0.0.1 发布工作流改为手动显式确认；未发现其他可安全删除的已跟踪临时文件。测试夹具、研究协议、历史证据和工具均为受控研发资产，予以保留。盲审包未提交仓库，且不得重新分发/招募。
- 未合并 PR #44、未创建 v0.0.2 Tag/Release、未触发收费或生产运行。

- 新增 v0.0.2 发布工作流尚待当前精确 head 的 actionlint/完整 CI 验证；未触发该工作流，不创建 Tag/Release。

- Run #2080（[45966113423](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45966113423)，精确 head `6d75987763bb4a6e3a89b425e865faa288a9d0cc`）SUCCESS：actionlint、Skill package、Benchmark、263/263 离线测试、G-Theory 三种设计模拟、IDA controlled mutation、Round 4 IDA/ERA/Capability contracts PASS。production Builder、独立评审、Pilot、adjudication 与 upstream audit 按授权/条件 SKIPPED，不计为 PASS。此 Run 验证的是发布工作流代码/测试，不代表 VERSION 已升级或 Release 已批准。

- 0.0.2 候选版本元数据已在 PR 分支同步：VERSION=0.0.2，Skill frontmatter metadata.version=0.0.2；main 正式版本仍为 0.0.1。
- Run #2089（[45967184024](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45967184024)，精确 head `71acd49be6a65754f048a147723b1e40c660bbf6`）SUCCESS：actionlint、Skill package、Benchmark、264/264 离线测试、G-Theory 三种设计模拟、IDA controlled mutation、Round 4 IDA/ERA/Capability contracts 全部 PASS。Production Builder、独立评审、Pilot、adjudication 和 upstream audit 均按授权/条件 SKIPPED。

- 新增 .github/workflows/package-release-candidate.yml：每次 PR 更新均对精确 head 执行 Skill validator，构建 ZIP 并与 EXPECTED_SKILL_FILES 白名单逐项比较；Package run #3（[45968288702](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45968288702)）SUCCESS，Artifact #15184151507，17 个运行时文件，ZIP 44,025 bytes，SHA-bound artifact 名称对应 head `f9aa8822bf55458e76087ee9658c75bf96956226`。
- Run #2095（[45968288724](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45968288724)，精确 head `f9aa8822bf55458e76087ee9658c75bf96956226`）SUCCESS：actionlint、Skill package、Benchmark、265/265 离线测试、G-Theory 三种设计模拟、IDA controlled mutation、Round 4 IDA/ERA/Capability contracts PASS。production Builder、Pilot、independent review、adjudication 等按范围 SKIPPED。
