# v0.0.2 任务质量报告

**报告日期：** 2026-11-26  
**任务依据：** `docs/quality-assessment-v0.0.2/TASKS.md`  
**工作分支：** `feat/quality-assessment-v0.0.2`  
**需求 Issue：** [#43](https://github.com/Kairos0922/evaluation-dataset-builder/issues/43)  
**开发 PR：** [#44](https://github.com/Kairos0922/evaluation-dataset-builder/pull/44)  
**报告性质：** 阶段性质量审计，不是 Release Approval，也不是综合公式效度证明

## 1. 执行结论

v0.0.2 已完成需求基线、研究与方法论设计、IDA/ERA 核心工程实现、报告契约、确定性检查、Round 4 Oracle 执行前冻结工具、盲审资料包生成/比较工具、Judge 校准证据契约，以及架构/ERA 执行协议。

**工程与契约层：阶段性通过。** 最新代码验证 Run #1933 在精确代码 head `878303fba7d4db75df979073d97c9d529b70d74e` 上通过 actionlint、正式 Skill 包验证、Benchmark 贯通样例和 215/215 离线测试；Round 4 真实证据重新导入、IDA/ERA 报告 Schema 与 cross-field contract validation 通过。

**科学效度层：证据不足。** 当前真实 Round 4 数据只有 15 条用例中的 3 条完成 Pilot 和独立 Gold Oracle 判定；其余 12 条未运行。专家内容效度、Judge 独立校准、盲测缺陷识别、完整 Capability/Regression 效标和公式冻结验证均未完成。

**发布准备度：不通过 / 暂不发布。** v0.0.2 尚未形成 Release Candidate；PR #44 继续 Draft/Open。不能把工程 CI 成功解释为测量效度通过。

## 2. TASKS.md 完成度

当前任务清单共 37 项。按本次核对后的状态：

| 状态 | 数量 | 解释 |
|---|---:|---|
| DONE | 20 | 设计/工程任务已有可复核文档、代码或 CI 证据 |
| IN_PROGRESS | 7 | 已有部分实现或部分真实证据，验收条件尚未全部满足 |
| BLOCKED | 10 | 需要独立人员、外部许可/数据、Oracle 或用户发布批准 |
| TODO | 0 | 尚未启动的任务已转为明确阻塞状态，避免掩盖依赖 |
| **合计** | **37** | |

说明：DONE 仅表示该任务定义的设计/工程交付完成，不表示关联实验或更高层质量结论已通过。例如 DS-03/DS-04 的统计方案已设计完成，但 IRT/G-Theory 拟合和 Regression 真实配对实验仍未完成。

## 3. 工程交付与证据

### 3.1 已完成的关键交付

- **需求与架构：** requirements.md、decision-log.md D-001 至 D-007、architecture-and-acceptance-baseline.md。
- **研究与方法：** research-evidence.md、methodology-design.md、methodology-matrix.md、metric-catalog.md、formula-validation-protocol.md、experimental-design.md。
- **IDA：** `scripts/assess_dataset_quality.py`、IDA report Schema、质量报告契约验证器和测试。
- **ERA：** Runtime Record / ERA report Schema、`scripts/import_dsh_pilot_records.py`、`scripts/assess_runtime_quality.py`、报告验证器和测试。DSH trace importer 强制校验原始 JSONL evidence manifest、SHA-256、case/run identity 和安全路径，并将 trace digest 保存在规范 Runtime Record。新增 `scripts/analyze_capability_measurement.py`，提供基于独立 Gold 的探索性 Rasch 1PL 与平衡 Person×Item G-study，输出题目/配置参数、信息函数、方差分量、G/Phi 与 D-study；并配套报告 Schema、说明文档和 5 项测试。
- **Judge：** 专家评审协议与评分记录 Schema；新增 Judge Calibration Report Schema、`scripts/validate_judge_calibration.py` 和 8 项验证器契约测试。现已将 `tests/calibrate_judge.py` 接入该报告契约，生成 suite SHA/case IDs、Judge prompt/implementation SHA、运行身份、逐案结果和重算指标，并在落盘前调用验证器及 suite 哈希校验；新增 3 项执行脚本集成测试。synthetic smoke 被固定标记为 NOT_VALIDATED，不能冒充独立 Gold 校准。
- **Round 4 Oracle：** 独立判定计划、Oracle Record Schema、A/B 盲审资料包生成器、提交 Schema、比较器、hash-bound Freeze Manifest Schema 和验证器。
- **运行协议：** runtime-assessment-protocol.md 定义执行前冻结、失败归因、Judge/Gold 独立性、Capability/Regression 分支、重复和停止规则。
- **外部 Benchmark：** external-benchmark-candidates.md 登记 AppWorld、AgentDojo、WebArena-Verified、OSWorld-Verified、GAIA、WorkArena，并区分代码许可证与数据/镜像/实例授权。

### 3.2 CI 验证记录

| Run | 精确代码 head | 结果 | 测试 | Round 4 artifact |
|---|---|---|---:|---|
| [#1930](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45714388411) | `8930dcc656288e1b6fd7bc672202bbec520b92b9` | SUCCESS | 207/207 | #15069091920 |
| [#1933](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45719605220) | `878303fba7d4db75df979073d97c9d529b70d74e` | SUCCESS | **215/215** | #15071077843 |
| [#1939](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45720458350) | `87d3747444ddaa5e7391e202f7595121f1fa86a7` | SUCCESS | **215/215** | #15072186678 |
| [#1940](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45720639140) | `0f50a9cc9de97ec2778b026c34dfd69e2c1b8bf8` | SUCCESS | **215/215** | #15072316423 |
| [#1941](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45720784376) | `3a99fcc0de3609971d6c701bade210251c77fd04` | SUCCESS | **215/215** | #15070789521 |
| [#1944](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45721014232) | `122d38527a3af2e3d012598cbb6ac93b3b4ecfc0` | SUCCESS | **215/215** | #15070934643 |
| [#1947](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45721216859) | `bca98059650afce9df752917553bcff98adeb91e` | SUCCESS | **215/215** | #15071653396 |\n| [#1983](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45800505196) | `d899ea3fab0b0f27a9d8fc1c57e78ade28492683` | SUCCESS | **230/230** | #15105794918 |

Run #1933 的 Round 4 artifact SHA-256：

`890e71e91b58d95f3ee7d551380db0606305e92cafb1d00bbbeaf9a8f24369f8`

Run #1933 中 Builder production、independent-validation、webapp-testing-pilot、adjudicate-pilot 等受上游门禁保护的 Job 均为 SKIPPED。该 Run 验证代码、离线测试及既有冻结证据分析，不代表新的 Builder 生产执行、独立评审或 Pilot 扩容。

## 4. 真实数据与测量证据

### 4.1 数据集与 IDA

- 数据集：`wb-core`，15 条用例。
- JSONL SHA-256：`000d38b110b60eae902f86737ea6bd1368f98c6632c42a47bb9470a4a08bfc45`。
- 数据集摘要 SHA-256：`cc949f0e9d9c60e6d2ad405749c3829aacc7a2fcbee75fa57e570b56de1f2141`。
- Schema / 结构检查：15/15；source refs 解析：61/61；精确重复：0/15。
- IDA 总体状态：**PARTIAL**。
- 来源引用可解析不证明来源真实，也不证明引用支持具体业务主张。
- G02 构念对齐、G03 可解性、G04 Gold 有效性等仍缺少独立语义证据；Rubric 有效性和污染状态仍有 UNKNOWN / NOT_ASSESSED。

### 4.2 ERA

- 有效真实 Pilot：3/3，分别为 WB-02、WB-10、WB-12；独立 Gold Oracle 结果 3/3 PASS。
- 数据集剩余 12/15 用例：**NOT_RUN**，不是失败，也不是通过。
- 当前 3/3 的 95% Wilson 区间约为 [0.4385, 1.0000]，样本过小，不能支持总体可靠性或泛化结论。
- Judge validation：**NOT_RUN**，无独立 Judge 校准结果。
- Regression：没有 baseline/candidate 配对记录，不能计算有效配对回归结论。
- IRT / DIF / G-Theory：未拟合。
- 综合分：**NOT_VALIDATED，value=null**。

## 5. 主要质量发现与风险

| 优先级 | 发现 | 影响 | 解除条件 |
|---|---|---|---|
| P0 | 12 条 Round 4 Oracle 未冻结 | 无法安全执行剩余用例，也无法完成 15 条数据集的运行效标 | 两位独立盲审者、第三位独立仲裁者、12-case hash-bound freeze 通过 |
| P0 | 专家内容效度尚无真实评分 | 无 CVI/CVR/Aiken's V 或评分者一致性实证 | 完成独立专家招募、盲评、仲裁并归档原始记录 |
| P0 | Judge 无独立 Gold 校准实证 | 无法量化 Judge False Pass/False Fail、Abstention 和重复性 | 独立 Gold/held-out 校准集、盲法协议、Judge 报告及独立复核 |
| P1 | 缺陷注入只有确定性单测 | 不能声称对盲测真实缺陷有检出效度 | 独立确认基线/变体、盲测、控制样本、按缺陷类别报告区间 |
| P1 | Capability/Regression 真实效标不足 | 无完整能力矩阵、无配对 Regression、无跨 Agent/Skill 泛化证据 | 多配置真实运行、配对版本、历史故障与重复运行 |
| P1 | 外部 Benchmark 数据资产授权未全部确认 | 不能安全导入/再分发/运行所有候选资产 | 锁定版本、逐文件许可、镜像/软件/服务授权、哈希和 Oracle |
| P1 | 综合公式缺少独立开发/验证集 | 权重、阈值和标量分数没有科学依据 | 预注册、独立效标、分组隔离、冻结验证、敏感性和外部复现 |
| P2 | v0.0.2 版本元数据未升级 | 当前正式版本仍是 0.0.1 | 所有适用发布门禁完成后建立 RC 并同步 VERSION/Skill metadata |

## 6. 任务状态的科学解释

- 结构 Schema PASS 只表示输入输出符合机器契约。
- 207/207 或 215/215 单测 PASS 只表示当前测试集覆盖的代码行为通过。
- 61/61 source refs resolved 只表示引用身份可解析，不证明来源主张真实。
- 3/3 Pilot PASS 只适用于这三条任务、当前 Skill revision、模型、Harness 和环境。
- Mutation 单测通过不等于盲测缺陷检出有效。
- Judge 校准 Schema/validator 通过不等于 Judge 已经校准。
- 公式可计算不等于公式具有构念效度或预测效度。

## 7. 发布建议

**建议：继续保持 PR #44 Draft/Open，不创建 v0.0.2 Tag 或 GitHub Release。**

发布前必须至少完成：
1. 独立专家内容效度与评分者一致性；
2. Round 4 12-case Oracle 冻结和后续真实运行；
3. Judge 独立 Gold 校准；
4. 盲测缺陷注入；
5. Capability 与 Regression 的用途专属真实效标；
6. 公式独立验证；若证据不足，则以分项画像和 NOT_VALIDATED 作为诚实交付，不强行给总分；
7. 精确 Release Candidate SHA 的完整 CI、审查和用户批准。

## 8. 复核入口

- [TASKS.md](TASKS.md)：唯一任务状态事实来源。
- [Round 4 真实证据结果](round4-real-evidence-results.md)
- [Round 4 独立 Oracle 计划](round4-independent-oracle-plan.md)
- [Round 4 盲审包指南](round4-blind-review-packet-guide.md)
- [外部 Benchmark 候选与许可边界](external-benchmark-candidates.md)
- [架构与验收基线](architecture-and-acceptance-baseline.md)
- [ERA 真实运行执行协议](runtime-assessment-protocol.md)

**最终结论：** v0.0.2 的工程骨架和机器契约已具备可审计性，但科学效度证据尚不充分。当前质量等级应表述为“工程验证通过、实证效度部分完成、发布门禁未通过”，而不是“v0.0.2 全部完成”。


### 最新文档基线复验

Run #1939 在包含任务质量报告、TASKS 状态统计、README/CHANGELOG 和方法协议文档的精确 head `87d3747444ddaa5e7391e202f7595121f1fa86a7` 上再次通过完整验证：actionlint、Skill 正式包、Benchmark、215/215 离线测试和 Round 4 IDA/ERA 报告契约均 PASS。Round 4 artifact #15072186678，SHA-256 `be681dfd0a61be229e66b7953b3f02f66366d31d700b8e33755e3719df739b44`。受保护的 Builder production、independent-validation、Pilot 和 adjudication Jobs 仍 SKIPPED；本次仍是既有证据复核，没有新增真实运行。


### 最终任务台账提交复验

Run #1940（45720639140）在精确 head `0f50a9cc9de97ec2778b026c34dfd69e2c1b8bf8` 上完成完整验证并 SUCCESS：actionlint、正式 Skill 包、Benchmark、215/215 离线测试（含 8 项 Judge calibration contract tests）和 Round 4 IDA/ERA 报告契约均 PASS。Round 4 artifact #15072316423，SHA-256 `8532534e9f923fb949484c66038523d011b4a5bafe788724b7a3e7b3d76904e0`。Builder production / independent-validation / Pilot / adjudication Jobs 均 SKIPPED；本次仍只复核已有真实证据，没有新增真实执行。


### TASKS 与质量报告记录提交复验

Run #1941（45720784376）在精确 head `3a99fcc0de3609971d6c701bade210251c77fd04` 上 Workflow SUCCESS：actionlint、Skill 正式包、Benchmark、215/215 离线测试及 Round 4 IDA/ERA 报告契约 PASS。Round 4 artifact #15070789521，SHA-256 `729c0131446788b21a06aa280b8b75f48218e3e21e5b666a284ca9a59977c1e5`。生产 Builder、独立验证、Pilot 和 adjudication Jobs 均 SKIPPED，没有新增真实运行。

### 变更记录更新后的最终 head 复验

Run #1944（45721014232）在精确 head `122d38527a3af2e3d012598cbb6ac93b3b4ecfc0` 上 Workflow SUCCESS：actionlint、正式 Skill 包、Benchmark、215/215 离线测试（含 8 项 Judge calibration contract tests）和 Round 4 IDA/ERA 报告契约均 PASS。Round 4 artifact #15070934643，SHA-256 `6ba0929eabd3354dbb06eedf43e55ff682b435320415b737c36063f2f8237ea1`。Builder production、independent-validation、Pilot、adjudication Jobs 均 SKIPPED；未新增真实执行或人工评审证据。


### 最新文档/变更记录 head 复验

Run #1947（45721216859）在精确 head `bca98059650afce9df752917553bcff98adeb91e` 上 Workflow SUCCESS：actionlint、正式 Skill 包、Benchmark、215/215 离线测试（含 8 项 Judge calibration contract tests）和 Round 4 IDA/ERA 报告契约全部 PASS。Round 4 artifact #15071653396，SHA-256 `153f702408de37fc4581e7441171b7f53916809be256563a89501c883f50bf80`。Builder production / independent-validation / Pilot / adjudication Jobs 均 SKIPPED；没有新增真实执行。


### Judge Calibration 执行链路集成（2026-11-26）

- 已完成 `tests/calibrate_judge.py` 到 v0.0.2 Judge Calibration Report Schema/validator 的接入；不再只输出旧版 ad-hoc JSON。
- 新报告绑定校准 suite 原始字节 SHA-256、case IDs、Judge endpoint/model、Judge prompt SHA、Judge 实现 SHA、workflow run/commit 身份，并逐案记录 Gold/Judge 状态、证据验证标志与输出 SHA。
- Summary 由逐案结果重新计算 adjudicable denominator、exact matches、False Pass、False Fail、Abstention 和 accuracy；写出前调用正式 `validate_report()`，并校验 suite 哈希与 case IDs。
- 新增 3 项执行脚本集成测试，覆盖 synthetic report 合约、错误类型计数和身份哈希。相关提交：`33bd883`、`bbb2d85`、`98f9e66`。
- Run #1953（45731724029，head `98f9e66`）中 actionlint、正式 Skill 包和 Benchmark PASS；218 项离线测试中 217 PASS / 1 FAIL。唯一失败是集成测试对夹具中多个 UNKNOWN 的预期值写错，已在 commit `cd95707` 修复。修复后的精确文档/代码 head `f4d2cc2fadc2c8136a8c5d405a3d6a47eee5efb2` 由 Run #1958（45731888915）完整验证成功：actionlint、正式 Skill 包、Benchmark、218/218 离线测试和 Round 4 IDA/ERA 报告契约全部 PASS；artifact #15077441739，SHA-256 `02e7d5a2386f0ea6e1f57a8382c6af64bd1f4a661f81e934cab569e74e4aa004`。
- **IM-03 仍 IN_PROGRESS。** 这次完成工程执行链路，不产生独立 Gold、盲法 held-out 样本、人工仲裁或真实 Judge 有效性结论；Round 4 Judge 仍为 NOT_RUN。


### 集成测试首轮失败与修复记录

- 首轮 Run #1953 的唯一失败发生在测试 `test_runner_recomputes_false_pass_false_fail_and_abstention`：原测试没有考虑夹具里存在多个 Gold=UNKNOWN 的 case，因此实际 Judge UNKNOWN 数为 2，而断言写成 1。
- 修复后的测试显式控制非目标 UNKNOWN case 的 Judge 输出，确保该测试只包含一个 Judge abstention，同时仍分别覆盖 False Pass、False Fail 和 Gold UNKNOWN 排除于 adjudicable denominator 的规则。修复提交 `cd95707`；TASKS 记录提交 `6a3f2f5`。
- 该修复只改变测试夹具构造，不改变校准统计定义或生产逻辑。最新文档提交 head 仍需重新通过完整 CI，才能确认修复验收。


### 修复后精确 head 的完整 CI 结果

- Run #1958（45731888915）在精确 head `f4d2cc2fadc2c8136a8c5d405a3d6a47eee5efb2` 上 Workflow SUCCESS；actionlint、正式 Skill 包、Benchmark、218/218 离线测试全部通过，新增 3 项 Judge runner integration tests 均 PASS。
- Round 4 real-evidence-assessment Job SUCCESS，IDA/ERA 报告 Schema 与 cross-field contract validation PASS；artifact #15077441739，SHA-256 `02e7d5a2386f0ea6e1f57a8382c6af64bd1f4a661f81e934cab569e74e4aa004`。
- Builder production、independent-validation、Pilot、adjudication 等 Job 均 SKIPPED；没有新增生产执行、真实 Judge 校准、专家盲评或 Oracle freeze。
- 该 CI 结果仅覆盖 head `f4d2cc2`。TASKS.md 与质量报告随后追加本次 Run 结果，形成新的文档提交；新文档 head 仍需精确 CI 复验。


### 最新完整文档基线复验（Run #1961）

- TASKS/质量报告/CHANGELOG 更新后的精确 head `5b108084f65cfb0e00b8552744267ccdc5e51f58` 由 Run #1961（45732037841）完整验证成功：actionlint、正式 Skill 包、Benchmark、218/218 离线测试和 Round 4 IDA/ERA 报告契约均 PASS。
- Round 4 artifact #15077885154，SHA-256 `fd3187c4a98a158b2dfe7b63fd2594c2c30540ab94a2e429886c6c11e72be122`。Builder production / independent-validation / Pilot / adjudication jobs 均 SKIPPED。
- 该验证确认 Judge runner 契约集成没有破坏既有 IDA/ERA 证据管线；但没有新增真实 Judge 校准、Oracle 或生产运行证据。


### Capability 测量分析工程原型（2026-11-26）

- 新增 `scripts/analyze_capability_measurement.py`，只使用有效运行且具备 independent_oracle / expert_adjudication Gold provenance 的 Agent 二元响应；严格要求单一数据集身份与完整平衡 Configuration×Case 设计，拒绝重复单元格和缺格。
- Rasch 部分实现 1PL 联合最大似然探索性估计、配置能力位置、题目难度、局部 Fisher 信息标准误近似、题目信息和测试信息；完全分离或不收敛时返回 NOT_ASSESSED。
- G-Theory 部分实现平衡 Person×Item 双 facet ANOVA 方法矩估计、Person/Item/Person×Item+Residual 方差分量、相对 G、绝对 Phi 和 D-study 题目数量规划。
- 新增 `schemas/capability-measurement-report.schema.json`、`capability-measurement-analysis.md` 和 5 项单测。
- **科学边界：** 当前仅为探索性估计原型；不实现 2PL/多维 IRT、DIF、Seed/Environment/Judge 多 facet、非平衡/重复设计或模型拟合诊断。没有独立 Gold 时输出 NOT_ASSESSED。成功估计不代表单维性、局部独立、测量不变性或构念效度成立，也不启用综合分。
- IM-05 继续 IN_PROGRESS，待 CI 验收、Monte Carlo 参数恢复、真实数据精度验证和独立外部效标实验。


### Capability 测量原型 CI 证据

- 精确代码/测试 head `52093376778d428145e9b968df38ba54e9d26d4f` 的 Run #1968（45732528514）SUCCESS：actionlint、Skill 包、Benchmark、223/223 离线测试和 Round 4 IDA/ERA 报告契约全部 PASS；新增 5 项 Capability measurement tests 全部通过。artifact #15077900941，SHA-256 `6fbcc3496f66f2aad9bc2a2057b8380523b19d6c8cbb4fdacb85bf48c2f9ed5e`。
- 包含 TASKS/质量报告/CHANGELOG 更新的精确 head `c1babc7ec9d51de6ac0c3cdb36232573c32f53bb` 由 Run #1972（45732657722）再次完整验证成功，223/223 测试通过；artifact #15077358259，SHA-256 `af22544c66e638472b91f9e2d0a85f237e916a44ee3ebe082b20c4a3c099ea57`。
- 两个 Run 的生产 Builder、独立验证、Pilot 与 adjudication jobs 均 SKIPPED；这证明工程实现和契约测试通过，不证明已有足够独立 Gold 数据或 Rasch/G-Theory 模型适配效度。


### EX-06 真实证据导入器完整性修复与验收（2026-11-26）

- 修复前的 importer 会检查已声明 evidence_files 的哈希，但未强制 DSH trace 本身必须出现在清单中，也未将 trace digest 写入 Runtime Record。现在要求每条 Pilot 的 `dsh-events.jsonl` 被 runner evidence manifest 明确绑定并通过 SHA-256 验证；同时检查 JSONL 行结构、可用的 case_id/run_id、重复路径、路径穿越和符号链接逃逸。
- Runtime Record Schema 新增可选 `trace_sha256`，真实导入时强制写入；导入 metadata 同步记录各 Pilot trace digest。
- 精确 head `d899ea3fab0b0f27a9d8fc1c57e78ade28492683` 的 Run #1983（45800505196）SUCCESS：actionlint、正式 Skill 包、Benchmark、230/230 离线测试 PASS；Round 4 evidence Job SUCCESS，实际导入 3 条真实 Pilot 并运行 IDA/ERA；报告 Schema/cross-field contract PASS。
- Artifact #15105794918，ZIP SHA-256 `0d703863f965f99e34f721c00895ada15acd25ef0495015d4492826407962e03`。
- EX-06 标记 DONE 的严格含义是：当前实际存在的 Builder/DSH/Runner/独立 Oracle 冻结证据已安全规范化并完成 IDA/ERA 运行。数据集仍只有 3/15 Pilot，12 NOT_RUN，Judge NOT_RUN，composite NOT_VALIDATED；这些未完成科学效度工作不由 EX-06 的工程交付状态覆盖。
