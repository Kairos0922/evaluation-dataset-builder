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
| DONE | 19 | 设计/工程任务已有可复核文档、代码或 CI 证据 |
| IN_PROGRESS | 8 | 已有部分实现或部分真实证据，验收条件尚未全部满足 |
| BLOCKED | 10 | 需要独立人员、外部许可/数据、Oracle 或用户发布批准 |
| TODO | 0 | 尚未启动的任务已转为明确阻塞状态，避免掩盖依赖 |
| **合计** | **37** | |

说明：DONE 仅表示该任务定义的设计/工程交付完成，不表示关联实验或更高层质量结论已通过。例如 DS-03/DS-04 的统计方案已设计完成，但 IRT/G-Theory 拟合和 Regression 真实配对实验仍未完成。

## 3. 工程交付与证据

### 3.1 已完成的关键交付

- **需求与架构：** requirements.md、decision-log.md D-001 至 D-007、architecture-and-acceptance-baseline.md。
- **研究与方法：** research-evidence.md、methodology-design.md、methodology-matrix.md、metric-catalog.md、formula-validation-protocol.md、experimental-design.md。
- **IDA：** `scripts/assess_dataset_quality.py`、IDA report Schema、质量报告契约验证器和测试。
- **ERA：** Runtime Record / ERA report Schema、`scripts/import_dsh_pilot_records.py`、`scripts/assess_runtime_quality.py`、报告验证器和测试。
- **Judge：** 专家评审协议与评分记录 Schema；新增 Judge Calibration Report Schema、`scripts/validate_judge_calibration.py` 和 8 项契约测试。该验证器重新计算分母、准确率、False Pass、False Fail 和 Abstention，校验 suite SHA/case IDs，并禁止 synthetic smoke 被标为 VALIDATED_FOR_SCOPE。
- **Round 4 Oracle：** 独立判定计划、Oracle Record Schema、A/B 盲审资料包生成器、提交 Schema、比较器、hash-bound Freeze Manifest Schema 和验证器。
- **运行协议：** runtime-assessment-protocol.md 定义执行前冻结、失败归因、Judge/Gold 独立性、Capability/Regression 分支、重复和停止规则。
- **外部 Benchmark：** external-benchmark-candidates.md 登记 AppWorld、AgentDojo、WebArena-Verified、OSWorld-Verified、GAIA、WorkArena，并区分代码许可证与数据/镜像/实例授权。

### 3.2 CI 验证记录

| Run | 精确代码 head | 结果 | 测试 | Round 4 artifact |
|---|---|---|---:|---|
| [#1930](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45714388411) | `8930dcc656288e1b6fd7bc672202bbec520b92b9` | SUCCESS | 207/207 | #15069091920 |
| [#1933](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45719605220) | `878303fba7d4db75df979073d97c9d529b70d74e` | SUCCESS | **215/215** | #15071077843 |
| [#1939](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45720458350) | `87d3747444ddaa5e7391e202f7595121f1fa86a7` | SUCCESS | **215/215** | #15072186678 |

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
