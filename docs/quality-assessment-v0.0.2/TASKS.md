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
| RS-02 | 研究 | 深入复核内容效度、评分者一致性、IRT/G-Theory、复合指标和阈值方法 | IN_PROGRESS | research-evidence.md、methodology-matrix.md、formula-validation-protocol.md 已覆盖 CVI/CVR、Aiken's V、ICC/Kappa/Alpha、IRT、G-Theory、敏感性和样本量规划；新增 expert-review-protocol.md（commit 3fd46df），明确盲评流程、评分锚点、统计定义、区间/功效设计和不设统一阈值原则；仍需专家实证和真实数据验证 |
| RS-03 | 研究 | 复核通用 Agent / Skill 运行效标、历史故障、变异和 Judge 验证实践 | IN_PROGRESS | ABC、SkillsBench、Agentic Skills at Scale、SkillForgeBench、Judge 验证和 fault exposure 已记录；新增独立 Benchmark 候选矩阵，涵盖 AppWorld、AgentDojo、WebArena-Verified、OSWorld-Verified、GAIA、WorkArena；仍需锁定具体版本、访问许可、Oracle 和可复现环境，并细化跨域效标验证 |
| DS-01 | 设计 | 完成离线独立质量评价方法和维度操作定义 | IN_PROGRESS | methodology-design.md + metric-catalog.md 已建立 IDA 指标候选；仍需定义审查锚点、评分者校准和内容效度流程；metric catalog commit 4b91a78 |
| DS-02 | 设计 | 完成真实运行评价方法，区分 Agent / 环境 / Judge 误差 | IN_PROGRESS | methodology-design.md + metric-catalog.md 定义 ERA 与共享运行指标；formula-validation-protocol.md 规定验证证据；仍需形成可执行运行协议 |
| DS-03 | 设计 | 设计 Capability 专属评价与统计方案 | IN_PROGRESS | 已定义观察题目通过率画像、IRT 难度/区分度、Test Information、DIF、测量不变性和 G-Theory 的用途与限制；当前 analyzer 仅输出描述性通过率，IRT/G-Theory 估计与假设检验未完成 |
| DS-04 | 设计 | 设计 Regression 专属评价与统计方案 | IN_PROGRESS | 已定义同 case/model/environment/seed 配对、McNemar exact、历史故障、Mutation、失败暴露和重复运行不一致；需用真实故障集验证代表性和检出效度 |
| FM-01 | 公式 | 定义构念蓝图、指标类型和候选公式模型族 | DONE | methodology-design.md §3、§5；formula-validation-protocol.md §2、§5；commit f84ef13 + b6cd238 |
| FM-02 | 公式 | 设计公式构建、权重来源、阈值选择与敏感性分析协议 | IN_PROGRESS | formula-validation-protocol.md 已明确规范性/经验性/混合权重、损失驱动阈值、模型比较和敏感性分析；仍需冻结预注册分析计划和实际效标 |
| FM-03 | 公式 | 建立独立效度验证实验与证明报告 | TODO | 执行专家盲评、缺陷注入、外部效标、泛化和不确定性验证；当前仅有协议设计 |
| EX-01 | 实验 | 完成公式验证实验设计与样本量/效标规划 | DONE | experimental-design.md；定义 E0–E7 阶段、分组隔离、专家盲评、缺陷注入和真实运行方案；commit 4b2f0d3 |
| EX-02 | 实验 | 建立独立参考数据集与缺陷注入样本 | IN_PROGRESS | defect-mutation-catalog.yaml 已建立 IDA-M01–M12 / ERA-M01–M08，并有确定性单测；新增 external-benchmark-candidates.md（commits e34a5dc + a693120），初筛 AppWorld、AgentDojo、WebArena-Verified、OSWorld-Verified、GAIA、WorkArena。仅完成桌面候选登记，尚未导入外部任务；待核实数据/环境许可、版本哈希、Oracle、独立标签和盲测变体 |
| EX-03 | 实验 | 完成专家内容效度与评分者一致性实验 | IN_PROGRESS | 已新增可执行盲评协议 expert-review-protocol.md（commit 3fd46df）及匿名专家评分记录 JSON Schema（docs + Skill reference，commits b5d644c + 78d2b44），测试覆盖四点评分/必要性三分类、盲评/仲裁阶段和隐私字段约束（test commit cc4b5c2）。尚未招募专家或产生评分，CVI/CVR/Aiken's V/ICC 等均 NOT_RUN |
| EX-04 | 实验 | 完成缺陷注入识别实验 | TODO | 盲测结果、按缺陷类型的检出/误报和置信区间 |
| EX-06 | 工程/实验 | 将真实 Builder、DSH Trace、Runner 和独立 Oracle 证据转换为规范 Runtime Record，并运行 IDA/ERA | IN_PROGRESS | importer commit 53d5b47；provenance commit da19614；ERA missing-Judge / denominator 修复 commits 5169120 + b1ad36c；cache/token fields commit 77b4e4b，Skill schema mirror 931b0ea；真实证据 Job commit 93857faf。Run #1847（45594508903，head 0366be3）真实证据导入、IDA、ERA、JSON Schema 与跨字段契约校验 PASS，Artifact 15012860922；IDA PARTIAL（15 cases，61/61 source refs resolved）；ERA PARTIAL（3/15 pilot，3/3 Oracle PASS，12 NOT_RUN，Judge NOT_RUN，composite NOT_VALIDATED）。已从冻结 artifact 复核 15 条原始用例及 fixture 资产；剩余 12 条仍 NOT_RUN。详见 round4-real-evidence-results.md 和 round4-independent-oracle-plan.md |
| EX-05 | 实验 | 完成 Capability / Regression 真实运行效标实验 | IN_PROGRESS | PR #38 前置条件已核验：Builder artifact 14729741906（run 44959366258）包含 15 条 Builder 原始用例；独立输出验证 run 44968128127 PASS，冻结产出复验 run 45291624154 PASS。Builder production Job 本身曾失败（启发式误报），不得写成 PASS。三条真实 Skill Pilot（WB-02/WB-10/WB-12）及 Gold Oracle 3/3 PASS 归档于 run 45189512695 / artifact 14824967038。当前仅 3/15 执行，12 条 NOT_RUN；完整 Capability/Regression 统计仍未完成 |
| EX-07 | 实验 | 为 Round 4 剩余 12 条用例建立独立 Gold Oracle 规则和执行前门禁 | IN_PROGRESS | 独立 Oracle 计划、记录 Schema、hash-bound validator、盲审包生成器、双评审提交 Schema 与比较器已实现。新增执行前冻结 manifest Schema（f6fabb9）、冻结验证器（517d484）、9 项测试（dd3e8d9）。Run #1918（45629438803，代码 head dd3e8d9c769b04cfd742224f4ace2d261afdc5b3）与最新文档 head Run #1919（45629744208，head 550acfcf6fd997c938c70a948b9d786e28583c58）均 actionlint、正式 Skill 包、Benchmark、205/205 离线测试、Round 4 IDA/ERA 与报告契约验证 PASS；生产/Pilot 前置 Jobs 依范围保护 SKIPPED。冻结验证器绑定两份原始提交、比较报告、coordinator crosswalk、数据集/计划/逐 case SHA，重新计算比较报告并核验逐字段一致；要求评审者与仲裁者身份独立，任何案例未冻结则整体不得 FROZEN。评审者仍未招募/提交，无真实评分或仲裁，Oracle 未冻结；12 条仍 NOT_RUN，WB-15 application outcome 固定 UNKNOWN |
| SC-01 | 方案 | 冻结 v0.0.2 需求、架构和验收标准 | TODO | 需求评审决议、设计基线 commit |
| IM-01 | 实现 | 设计并实现 IDA 报告 Schema / 机器可读契约 | DONE | schemas/ida-report.schema.json；JSON 语法检查通过；commit f47905e |
| IM-02 | 实现 | 实现独立离线评价器和确定性检查 | DONE | scripts/assess_dataset_quality.py 实现 Manifest/Case Schema、ID、来源注册表、覆盖一致性、分布、精确重复和报告契约检查；扩展身份错配、来源缺失/解析、覆盖不一致测试；run #1793 在精确 head 885444a 上 155 项测试 PASS |
| IM-03 | 实现 | 实现人工/LLM Judge 校准与证据记录接口 | TODO | 独立校准集协议、Judge 结果契约 |
| IM-04 | 实现 | 实现 ERA 运行结果 Schema / 机器可读契约 | DONE | schemas/era-report.schema.json + schemas/runtime-record.schema.json；Skill references 已同步；精确数据集 SHA、Agent/模型/Harness/环境、Run/Trace、Judge、Capability/Regression 字段已定义；JSON 语法检查通过；commits ef7515c、5030629、f18e010 |
| IM-05 | 实现 | 实现 Capability / Regression 统计分析模块 | IN_PROGRESS | scripts/assess_runtime_quality.py 已实现 Judge 混淆指标、Wilson CI、配对版本差异、McNemar exact、历史/变异故障检出、重复运行不一致和成本画像；IRT/G-Theory 与真实运行验证未完成；tests/test_assess_runtime_quality.py 已添加，待 CI 执行 |
| IM-06 | 实现 | 实现公式验证证据 Schema 和独立验证器 | DONE | Schema、Skill reference、验证器及契约测试已实现；修复 split-level sample_count 契约错误；commit b6740f9 + a2dc04e；run #1808（45550108441）在 head a2dc04e 上 162 项测试 PASS。此状态仅表示报告结构/逻辑契约验证器完成，不代表公式实验有效 |
| IM-07 | 集成 | 更新 Skill 质量标准、按需加载引用和版本到 0.0.2 | IN_PROGRESS | quality-standard.md/yaml 已替换旧固定权重；IDA/ERA/Runtime Record/Formula Validation Schema 已加入 Skill references，SKILL.md 已引用；validate_skill.py 检查所有 Draft 2020-12 Schema；版本元数据待发布候选阶段更新，最新正式包验证待 CI |
| IM-09 | 实现 | 比较候选综合公式并执行权重/聚合敏感性分析 | TODO | 需独立开发集和外部效标；不得用同一批专家标签同时拟合和验证 |
| QA-01 | 质量 | 建立元评测数据、已知缺陷注入和专家盲评样本 | IN_PROGRESS | 已有缺陷目录与确定性单测；新增 external-benchmark-candidates.md 和 expert-review-protocol.md；专家原始记录 Schema 已建立并有单测。尚缺经许可确认的真实参考集快照、专家盲评原始数据、分组数据切分、独立缺陷标签和审计记录 |
| QA-02 | 质量 | 完成离线评价器验证与报告 | IN_PROGRESS | IDA 结构检查器、报告契约和历史 CI 测试已通过；专家评分 Schema 新增后，Run #1874 暴露 Skill 文件白名单遗漏，已修复（commits c0bf1cd、dc96108），等待完整 CI 复验；语义内容效度、专家一致性、独立缺陷识别实验尚未完成 |
| QA-03 | 质量 | 完成真实运行评价的端到端验证 | IN_PROGRESS | Run #1847 的 Round 4 真实证据 Job、IDA/ERA 报告 JSON Schema 和 cross-field contract validation PASS，artifact 15012860922；IDA PARTIAL、ERA PARTIAL，三条 Pilot 均有独立 Oracle PASS；12/15 NOT_RUN、Judge NOT_RUN、无 Regression 配对、IRT/G-Theory 未拟合。报告已记录于 round4-real-evidence-results.md；尚需扩展真实运行和外部效度证据 |
| QA-04 | 质量 | 完成综合公式独立验证；若证据不足则明确 NOT_VALIDATED | IN_PROGRESS | 已有公式验证协议和向量画像定义；尚缺专家效标、缺陷注入数据、真实运行效标与冻结验证集。证据不足时保持 NOT_VALIDATED，不得发布标量总分 |
| P0-CI-01 | 工程 | 修复 CI #1807 中 Formula Validation Validator 对 datasets[].sample_count 的错误读取，并增加回归测试 | DONE | Schema 将 sample_count 定义在 split 层；验证器改为校验来源数据集非空并使用 split 总样本量；commit b6740f9（验证器）、a2dc04e（回归测试）；run #1808（45550108441）精确 head a2dc04e：actionlint、Skill 正式包、Benchmark 贯通样例 PASS，162/162 离线测试 PASS。Builder production / independent-validation jobs 按 PR 条件 SKIPPED |
| CI-01 | 工程 | 增加 CI、Schema、单测和端到端离线验收 | DONE | Run #1890（45606669627，精确 head d38d797cfd3476e0e28cb8155f599e70920bff13）完整验证 PASS：actionlint、正式 Skill 包、Benchmark、185/185 离线测试、Round 4 冻结证据导入/IDA/ERA/报告 JSON Schema 与 cross-field validation 全部 PASS；真实证据 artifact 15017663406。此前 Run #1885 在 validator 加入前 177/177 PASS；Run #1890 包含新增 Oracle validator 与 8 项测试。PR #38 Builder production / independent-validation / pilot Jobs 按范围保护 SKIPPED，不计作本次验证通过 |
| DOC-01 | 文档 | 更新 README、CHANGELOG、版本和限制说明 | TODO | v0.0.2 内容一致 |
| REL-01 | 发布 | 建立发布候选 PR 并完成审查 | TODO | 所有适用验收门禁通过，PR 记录证据 |
| REL-02 | 发布 | 用户批准后创建 v0.0.2 Tag 和 GitHub Release | TODO | Release 指向精确验证过的提交，证据齐全 |

## 外部依赖与阻塞

- PR #38 已关闭。历史 run #1662 的 skipped 状态已被后续 Round 4 证据取代，不再作为当前阻塞依据。
- Builder 原始输出来自 run #44959366258 / artifact #14729741906；该 production Job 结论为 failure（启发式误报），但 Builder 输出 artifact 已产生。独立验证 run #44968128127 PASS，冻结产出复验 run #45291624154 PASS。只有在此限定下，认定“正式 Builder 输出 + 独立 Validator PASS”前置条件满足；不把 Builder Job 说成 PASS。
- 三条真实 Pilot 与独立 Oracle 证据来自 run #45189512695 / artifact #14824967038：WB-02、WB-10、WB-12，Oracle 3/3 PASS。数据集共 15 条，另外 12 条仍未执行；Manifest 仍为 quality_status=needs_info、execution_status=NOT_RUN。
- PR #44 通过 importer 和 CI 下载冻结证据，不重复运行历史 Builder/Pilot/Oracle，不修改 PR #38，不使用合成轨迹冒充真实结果。
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
- [x] 扩展缺陷注入测试后，在精确 head 885444a 上通过 actionlint、正式包、Benchmark 样例和 155 项离线单测（run #1793）。
- [x] 修复 Formula Validation Validator 与 Schema 的 sample_count 层级错配；在精确 head a2dc04e 上通过 actionlint、正式 Skill 包、Benchmark 贯通样例和 162 项离线测试（run #1808，45550108441）。
- [x] 核实 PR #38 后续 Round 4 Builder/独立验证/Pilot/Oracle 原始证据，确认三条真实 Pilot 已完成；12/15 数据集用例仍 NOT_RUN。
- [x] 增加真实 DSH Pilot Runtime Record importer、缓存 Token/Model Step 字段、缺失 Judge 与 abstention 区分修复及回归测试；增加 PR #44 冻结证据 IDA/ERA CI Job，等待首次执行结果。

## 当前不代表已完成的事项

- 候选指标尚未完成系统文献复核。
- 任何综合公式、权重、阈值均未验证。
- 未建立专家盲评或缺陷注入数据。
- 未完成独立评价器和真实运行评价器实现。
- 未进行 v0.0.2 版本发布。

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
- 已在 Issue #43 发布独立评审招募说明（comment 7165679690）：招募两位互不交流的独立评审者，并说明资格、12-case 评审范围、UNKNOWN 规则、禁止协调、隐私和交付要求。发布时 Issue 尚无评论或志愿者；截至本次核查尚无评审提交或仲裁人选，因此 EX-03 / EX-07 的人工证据仍 BLOCKED。
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
