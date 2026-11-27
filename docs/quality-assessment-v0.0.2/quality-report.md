# v0.0.2 任务质量报告

**报告日期：** 2026-11-27  
**任务依据：** `docs/quality-assessment-v0.0.2/TASKS.md`  
**工作分支：** `feat/quality-assessment-v0.0.2`  
**需求 Issue：** [#43](https://github.com/Kairos0922/evaluation-dataset-builder/issues/43)  
**开发 PR：** [#44](https://github.com/Kairos0922/evaluation-dataset-builder/pull/44)  
**报告性质：** 阶段性质量审计，不是 Release Approval，也不是综合公式效度证明

## 1. 执行结论

v0.0.2 已完成需求基线、研究与方法论设计、IDA/ERA 核心工程实现、报告契约、确定性检查、Round 4 Oracle 执行前冻结工具、盲审资料包生成/比较工具、Judge 校准证据契约，以及架构/ERA 执行协议。

**工程与契约层：阶段性通过。** 最新完整验证为 Run #2035（[45916212402](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45916212402)，精确 PR head `93dce24092908d8f569804d2c14c7372339b26b1`）：actionlint、Skill package、Benchmark、246/246 离线测试、G-Theory 三种样本设计模拟、IDA controlled mutation 和 Round 4 IDA/ERA/Capability report contracts 全部 PASS。新增 3 项 IDA 畸形输入回归测试通过。该 Run 没有启动生产 Builder、独立评审或新增 Pilot；不代表新增科学效度证据。

**科学效度层：证据不足。** 当前真实 Round 4 数据只有 15 条用例中的 3 条完成 Pilot 和独立 Gold Oracle 判定；其余 12 条未运行。独立专家内容效度与 Round 4 Oracle 评审已按用户决定暂缓；Judge 独立校准、盲测语义缺陷识别、完整 Capability/Regression 效标和公式冻结验证仍未完成。暂缓不等于通过。

**发布准备度：不通过 / 暂不发布。** v0.0.2 尚未形成 Release Candidate；PR #44 继续 Draft/Open。不能把工程 CI 成功解释为测量效度通过。

## 2. TASKS.md 完成度

当前任务清单共 38 项。按本次核对后的状态：

| 状态 | 数量 | 解释 |
|---|---:|---|
| DONE | 21 | 设计/工程任务已有可复核文档、代码或 CI 证据 |
| IN_PROGRESS | 0 | 已有部分实现或部分真实证据，验收条件尚未全部满足 |
| BLOCKED | 15 | 需要外部许可/数据、Gold/Oracle、真实运行授权或用户发布批准 |
| DEFERRED | 2 | 独立专家评审与依赖其仲裁的 12-case Oracle 工作按用户决定暂缓，不计为完成 |
| TODO | 0 | 尚未启动的任务已转为明确阻塞状态，避免掩盖依赖 |
| **合计** | **38** | |

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
| [#1947](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45721216859) | `bca98059650afce9df752917553bcff98adeb91e` | SUCCESS | **215/215** | #15071653396 |
| [#1983](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45800505196) | `d899ea3fab0b0f27a9d8fc1c57e78ade28492683` | SUCCESS | **230/230** | #15105794918 |
| [#2023](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45892053327) | `49613acf6d540f5ef494335a45eebca65077a64b` | SUCCESS | **243/243** | #15152600525 (IDA mutation) |

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
| P0 | Round 4 剩余 12 条 Oracle 未冻结（EX-07 DEFERRED） | 12 条继续 NOT_RUN；不能形成完整 15-case 运行效标 | 若未来重启该工作，先确认独立 Gold 来源、审查资源与授权，再通过 12-case hash-bound freeze |
| P0 | 专家内容效度尚无真实评分（EX-03 DEFERRED） | 无 CVI/CVR/Aiken's V 或评分者一致性实证；当前不得声称内容效度已验证 | 本轮暂不推进；未来如重新启动，需另行确认专家资源、盲评与仲裁方案 |
| P0 | Judge 无独立 Gold 校准实证 | 无法量化 Judge False Pass/False Fail、Abstention 和重复性 | 独立 Gold/held-out 校准集、盲法协议、Judge 报告及独立复核 |
| P1 | IDA-M01–M08 仅完成合成确定性变异；M09–M12 语义类缺陷未评估 | 不能声称对真实盲测语义缺陷有检出效度 | 独立 Gold / 语义缺陷标签或未来重启独立评审；污染审计与 held-out 评估 |
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
- **IM-03 当前 BLOCKED。** 工程执行链路已完成，但没有独立 Gold、盲法 held-out 样本、真实 Judge 观测或独立审计；Round 4 Judge 仍为 NOT_RUN。


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
- IM-05 当前 BLOCKED：CI、Monte Carlo 参数恢复和分析器工程实现已完成；真实多配置/多组数据、DIF/测量不变性与外部效标仍未提供。


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


### EX-05 Capability / Regression 真实效标实验阻塞状态（2026-11-26）

- 独立专家评审与 12-case Oracle 盲审/仲裁已按用户决定暂缓（EX-03、EX-07=DEFERRED）；不再以 Issue #43 报名情况作为当前推进动作。原公告已标注暂停。
- 当前仅 WB-02、WB-10、WB-12 三条 Pilot，3/3 独立 Gold PASS；单一 Skill revision、单一模型配置、每 case 一次运行，不足以形成 Capability 多配置响应矩阵或估计 Agent/Task/Seed/Environment 方差，也没有同 case baseline/candidate Regression 配对。
- Run #1983 的生产 Builder、independent validation、Pilot 和 adjudication jobs 均 SKIPPED。OpenRouter preflight 成功只说明预检步骤通过，不代表生产运行已执行或获得额外运行授权。
- EX-05 仍 BLOCKED：EX-07 暂缓，12-case Oracle 不会在当前迭代中冻结；此外还缺真实运行授权/环境、多配置/重复运行和配对版本数据。若未来重启 Oracle 工作，需先确定独立 Gold 来源与审查资源。
- 这不是把 3/3 Pilot 结果判为失败；它们仍是有限 Pilot 证据，不能外推为总体能力或回归效度。


### IM-03 Judge calibration interface and empirical blocker（2026-11-26）

- 已实现 human/manual 与 LLM Judge 共用的独立校准导入管线：冻结 suite 哈希和完整 case coverage、independent Gold source、held-out/blinding 声明、Judge 身份哈希、逐案 Gold/Judge evidence refs、匿名 reviewer/adjudicator ID、source observation hash。
- 支持 preregistered repeated Judge observations；accuracy 按唯一 case 计算，abstention 按 judgement 计数，重复分歧单独报告。case-level majority ties 映射为 UNKNOWN；False Pass/False Fail 采用保守 case-level 标记，避免将同一 case 的重复 Judge 输出当成独立样本。
- Run #1993（[45802577224](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45802577224)，精确 head `4067dba939a4e5171864c85cde413c46e934ee65`）238/238 离线测试 PASS；Round 4 IDA/ERA contract PASS，Artifact #15108810359，ZIP SHA-256 `d899391a3603954a14959fe78568fed9e3b503c10959154a08dc022318686d9f`。
- 仍无独立 held-out Gold Judge 校准集、真实人工/LLM Judge 观测或外部审计。独立专家评审已暂缓（EX-03=DEFERRED）；当前 synthetic smoke 仍 NOT_VALIDATED；IM-03 保持 BLOCKED。Importer/schema/tests 通过不等于 Judge 有效。


### IM-05 Capability / Regression measurement analysis（2026-11-26）

- Rasch 1PL 增加 person/item infit 与 outfit mean-square 描述诊断；没有使用未经验证的统一阈值。DIF 和 measurement invariance 在输出中明确为 NOT_ASSESSED。
- G-Theory 参数恢复实验在 4 个 logistic crossed-random-effects DGP 情景下各运行 100 次，并比较 20×10、40×25、80×50 三种设计。所有结果均是 observed binary-score scale 的模拟参数恢复，不能解释为 latent logistic variance 或真实 Skill 人群的置信区间。

| 设计 | 场景 | G bias / RMSE | Phi bias / RMSE | raw Person/Item 负分量率 |
|---|---|---:|---:|---:|
| 20×10 | balanced moderate | -0.0410 / 0.1827 | -0.0381 / 0.1794 | 2% / 10% |
| 20×10 | low prevalence | -0.1102 / 0.2292 | -0.1088 / 0.2246 | 8% / 16% |
| 20×10 | low person variance | +0.0501 / 0.1697 | +0.0487 / 0.1638 | 41% / 10% |
| 20×10 | high item variance | -0.0240 / 0.1794 | -0.0167 / 0.1723 | 4% / 1% |
| 40×25 | balanced moderate | -0.0011 / 0.0602 | -0.0003 / 0.0611 | 0% / 0% |
| 40×25 | low prevalence | -0.0403 / 0.0966 | -0.0398 / 0.0972 | 0% / 2% |
| 40×25 | low person variance | -0.0101 / 0.1490 | -0.0088 / 0.1433 | 23% / 0% |
| 40×25 | high item variance | -0.0178 / 0.0835 | -0.0154 / 0.0883 | 0% / 0% |
| 80×50 | balanced moderate | +0.0038 / 0.0283 | +0.0044 / 0.0294 | 0% / 0% |
| 80×50 | low prevalence | -0.0257 / 0.0452 | -0.0259 / 0.0458 | 0% / 0% |
| 80×50 | low person variance | -0.0112 / 0.1103 | -0.0097 / 0.1072 | 2% / 0% |
| 80×50 | high item variance | -0.0039 / 0.0292 | -0.0033 / 0.0322 | 0% / 0% |

- 20×10 在这些条件下明显不稳定；40×25 在一般条件下较好，但低 Person 方差时仍有较高 RMSE 和 23% 负 raw Person 分量；80×50 改善明显，但低 Person 方差场景 RMSE 仍约 0.11。不能据此制定普遍样本量门槛，真实项目必须按预期方差结构和设计重新做 preregistered power/precision simulation。
- Run #2002（[45804426404](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45804426404)，精确 head `61fd978f496a3eb2db00eeb89a4bf696b84ddbf5`）241/241 离线测试 PASS，三种样本设计模拟和 Round 4 真实 Capability 报告契约均 PASS。
- Round 4 真实数据只有 1 configuration × 3 cases：Rasch 与 G-Theory 均 NOT_ASSESSED；DIF 与 measurement invariance NOT_ASSESSED。当前没有真实多组效度或外部 criterion 数据，IM-05 因此 BLOCKED。


### IM-07 Skill packaging and release-version boundary（2026-11-26）

- Method standard and machine-readable standard are updated inside the Skill package: standard version 2.0.0, applies to Evaluation Dataset Builder 0.0.2. IDA, ERA, Runtime Record, Formula Validation and Expert Review schemas are included.
- SKILL.md references all 16 on-demand reference assets directly. Package validator verifies exact reference inventory, no missing/extra files, no second-level reference dependency, valid Draft 2020-12 schemas and version consistency.
- Run #2004（[45804838674](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45804838674)，exact head `013c351812b801554faa72fd360b208b9b553bb4`）passed actionlint, Skill package validation, Benchmark, 241/241 offline tests and Round 4 evidence analysis.
- Root VERSION and SKILL frontmatter metadata.version remain 0.0.1, the already released package version. Upgrading to 0.0.2 before release gates and explicit approval would violate the release boundary. IM-07 is therefore BLOCKED only on the formal version transition; no tag, release or merge was created.


### QA-02 Offline IDA evaluator controlled-mutation validation（2026-11-26）

The new controlled mutation experiment executed eight deterministic defect operators and four negative controls. Every case regenerated an IDA report and validated the report contract.

| Result | Observed | Uncertainty / interpretation |
|---|---:|---|
| Deterministic mutation detection | 8/8 (100%) | Wilson 95% CI: 0.676–1.000 |
| Negative-control false positives | 0/4 (0%) | Wilson 95% CI: 0–0.490; four controls are far too few for a general false-positive guarantee |
| Nondeterministic mutation classes | 4 NOT_ASSESSED | M09–M12 require experts, independent Gold/Oracle or contamination audit |

Detected deterministic mutations: missing required field, duplicate case ID, manifest count mismatch, dataset ID mismatch, unresolved source reference, missing source references, exact duplicate payload and coverage declaration mismatch. Negative controls: formatting-only changes, consistent case ID rename, case order reversal and an unused source-registry entry.

Run #2011（[45806101196](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45806101196)，exact head `9cb0e46cd78193a9419929f90c73817a0ac511c3`）passed 243/243 offline tests and uploaded mutation artifact #15108859637 (ZIP SHA-256 `bb45162be43dd87e2b0587e8d35ae80c2b4328870bc2689debf23a594d323a1e`).

This establishes implementation sensitivity to the eight specified synthetic mutations only. It does not establish semantic content validity, construct validity, source claim support, Gold correctness, or contamination resistance. The actual Round 4 IDA report remains PARTIAL: G01 PASS, G02–G04 NOT_ASSESSED, G05/G07 UNKNOWN, composite NOT_VALIDATED. QA-02 remains BLOCKED pending independent blind expert review and external Oracle/contamination evidence.


### QA-03 End-to-end real runtime evidence（2026-11-26）

Run #2011 re-imported the frozen Round 4 DSH evidence and passed IDA, ERA and Capability report schema/cross-field validation. The observed ERA evidence is partial:

- 3/15 Pilot cases executed; 3/3 Agent outcomes PASS, 3/3 process outcomes PASS, 3/3 independent Gold outcomes PASS.
- Only one mutation fault was injected (search-case-sensitive) and detected. The other two runs had no injected fault. This is insufficient to estimate fault detection, false-positive or generalization rates.
- 12/15 cases remain NOT_RUN.
- All three Judge outcomes are UNKNOWN; grader_validation is NOT_RUN.
- pair_id, repeat_group_id, seed and cost_usd are missing; Regression analysis is null.
- Capability evidence is one configuration × three cases and remains descriptive PARTIAL; Rasch/G-Theory are NOT_ASSESSED.
- Composite remains NOT_VALIDATED.

Artifact #15110340499, ZIP SHA-256 `4fe6f5f2bf4de10f7befd4ad2a6a6a70a1b4293e84e0c9e15d5593bd109124ed`.

Production execution, the remaining 12 pilots, repeated runs, independent Judge/adjudication, paired baseline/candidate regression and cost collection require an authorized runtime, budget and external approval. The production/pilot/adjudication jobs were SKIPPED. No paid or production run was triggered without authorization. QA-03 remains BLOCKED.


### DOC-01 Documentation and release-version boundary（2026-11-26）

Root README, v0.0.2 development README, CHANGELOG, TASKS and quality-report now reflect the current implementation and evidence boundary: Judge evidence importer, exploratory Rasch/G-Theory estimators, G-Theory sample-size sensitivity, deterministic IDA mutation validation, 3/15 real Pilot runs, 12 NOT_RUN cases, NOT_RUN Judge validation, unavailable paired Regression evidence and unvalidated composite. The new offline mutation and Capability analysis reports are linked from the development README.

Run #2011（[45806101196](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45806101196)，exact code head `9cb0e46cd78193a9419929f90c73817a0ac511c3`）passed 243/243 offline tests, actionlint, Skill package validation, Benchmark, three G-Theory design simulations, IDA mutation validation and Round 4 IDA/ERA/Capability report contracts.

The root VERSION and Skill frontmatter metadata.version remain 0.0.1, matching the already published release. The formal version transition to 0.0.2 is intentionally blocked until all release gates pass and explicit release approval is obtained. No release tag, Release or merge was created.


### 用户决策与任务基线更新（2026-11-27）

- 用户决定暂时取消独立专家评审。EX-03（专家内容效度/评分者一致性）与依赖其双盲评审和仲裁的 EX-07（Round 4 剩余 12 条用例 Oracle 冻结）均标记为 DEFERRED；这表示暂缓，不是 DONE，也不是 NOT_APPLICABLE。
- 已停止把 Issue #43 招募、等待报名和盲审包分发作为当前执行路径。原招募评论已更新为暂停说明。
- 任务状态以 `TASKS.md` 当前台账为准：20 DONE、0 IN_PROGRESS、15 BLOCKED、2 DEFERRED、0 TODO（共 37 项）。
- 独立专家证据缺失的科学边界不变：内容效度、语义缺陷标签、独立 Gold / Judge 校准与综合公式效度仍不得宣称通过；12 条用例继续 NOT_RUN，综合分继续 NOT_VALIDATED/value=null。
- 当前仍可独立推进的工作限定为代码质量、可复现性、契约/安全测试、文档一致性和不需要伪造外部效标的工程验证。不得擅自触发收费/生产运行、合并 PR、升级正式版本或发布。
- 台账最近一次 CI：Run #2020（[45843892531](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45843892531)，head `a4494182e35d75fee61d34beac60fff69e07f87f`）SUCCESS。该次验证覆盖台账更新，不代表新增科学效度证据。


### QA-02 negative-control metamorphic invariance strengthening（2026-11-27）

- 在既有四种 negative controls 上增加基线签名比较：对 overall status、全部 gate results 和全部 metric results 生成规范化 SHA-256 签名。
- Negative control 只有在不触发硬 FAIL 且指标签名与基线完全一致时才判定 PASS；数据集原始字节 SHA 不纳入不变量比较，因为格式/身份变换可合法改变字节摘要。
- 报告 Schema 新增 `invariant_metrics_preserved`、基线/观察签名和 `invariant_metric_failure_count`；单测断言四种控制全部保持指标不变。
- 该改进增强的是四个预设控制的回归保护，不增加控制样本量，也不把 0/4 解释为一般误报率保证；语义有效性仍 NOT_ASSESSED。


### Run #2023 — IDA metamorphic negative-control invariance（2026-11-27）

- 精确 head `49613acf6d540f5ef494335a45eebca65077a64b` 的 Run #2023（[45892053327](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45892053327)）SUCCESS：243/243 tests，actionlint、Skill package、Benchmark、G-Theory sensitivity simulations、IDA mutation validation 和 Round 4 IDA/ERA/Capability contracts PASS。
- 8/8 deterministic mutations detected（100%；Wilson 95% CI 0.676–1.000）。
- 4/4 negative controls 保持 overall status、gate statuses/severity 和 metric values/statuses 不变；0/4 false positives，invariant metric failures 0/4。Wilson 95% CI for negative-control false-positive rate remains 0–0.490.
- Artifact #15152600525，ZIP SHA-256 `bdc08d2a95efcffa5ec1c8bbaa43b9432c27e9b639b09795fcefb9c6e76125ef`.
- Production Builder、independent-validation、Pilot 和 adjudication jobs 均 SKIPPED；该验证没有新增真实运行或独立语义标签。


### IDA malformed-input robustness hardening（2026-11-27）

A code audit found that malformed nested collection fields could pass through schema-error collection and then raise an uncaught exception in later descriptive calculations. The offline evaluator now defensively handles malformed `coverage_tags`, `source_refs`, `scenario_bucket`, `grading.criteria`, and manifest coverage dimensions; invalid source registry identifiers are rejected explicitly. Three regression tests were added for malformed nested members, wrong collection types, and malformed manifest coverage dimensions.

Run #2034（[45916033576](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45916033576)，exact head `ee0e03bbc0731acf4ca814a4d4a8b113f0ecad88`）completed SUCCESS. All three new malformed-input regression tests passed within 246/246 offline tests; actionlint, Skill package, Benchmark, G-Theory simulations, IDA controlled mutation and Round 4 IDA/ERA/Capability report contracts also passed. Artifacts: IDA mutation #15162172012; Round 4 evidence #15162087227; G-Theory #15162201977. P0-ROBUST-01 is now DONE. This remains an engineering robustness result only; no empirical-validity or composite-score status changes. Production Builder, independent validation, Pilot and adjudication jobs were skipped.


### Run #2035 — 完整 PR head 复验（2026-11-27）

- 精确 PR head `93dce24092908d8f569804d2c14c7372339b26b1` 的 Run #2035 SUCCESS：actionlint、Skill package、Benchmark、246/246 tests、G-Theory 三种设计模拟、IDA controlled mutation、Round 4 IDA/ERA/Capability contracts 全部通过。
- 新增的 3 项畸形 IDA 输入测试均在全量测试套件中通过。
- Round 4 artifact #15162063803；IDA mutation artifact #15162118788；G-Theory artifact #15161964062。
- 生产 Builder、独立验证、Pilot、adjudication 和 upstream asset audit 均 SKIPPED；既有 Round 4 证据仍是 3/15 Pilot、12 NOT_RUN，Judge NOT_RUN，Regression 未配对，composite NOT_VALIDATED。
