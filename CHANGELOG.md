# 版本变更记录

## 0.0.2 — Unreleased（发布准备中；尚未形成 Release Candidate）

- 当前自主工程任务 22/22 DONE；17 项外部依赖事项依据 D-009 移出当前迭代范围，不计为完成。
- 新增 0.0.2 收缩版发布门禁与发布准备审计：RELEASE-GATE-0.0.2.md、RELEASE-PREP-0.0.2.md。
- 清理过时的 v0.0.1 push trigger 文件并将旧发布流程改为手动显式确认；未发现其他可安全删除的已跟踪临时文件。测试夹具、协议和历史证据继续保留，安装包严格按 Skill 白名单构建。
- 当前真实证据仍为 IDA/ERA PARTIAL、3/15 Pilot、12 NOT_RUN、Judge NOT_RUN、Regression 无配对、综合分 NOT_VALIDATED。范围收缩不代表科学验证通过。
- 当前正式版本仍为 0.0.1；0.0.2 版本元数据、发布工作流适配、最终精确 head CI 和发布批准尚未完成。


> 本节记录开发分支已实现的工程资产，不代表发布批准或实证效度通过。正式版本号仍为 0.0.1。
- 最新 PR head 验证：Run #2036（workflow run ID 45916212402，执行 head `93dce24092908d8f569804d2c14c7372339b26b1`）SUCCESS，actionlint、Skill package、Benchmark、246/246 离线测试、G-Theory 三种设计模拟、IDA controlled mutation 和 Round 4 IDA/ERA/Capability contracts PASS。Run 编号已按 GitHub API 正式 run_number 校正；本次没有新增生产运行或独立 Gold。
- IDA 畸形输入安全加固：离线评价器现在对错误类型的 coverage/source/scenario/grading/manifest 嵌套字段进行防御式处理，非法 source registry ID 明确拒绝；新增 3 项回归测试。Run #2034（45916033576，精确 head `ee0e03bbc0731acf4ca814a4d4a8b113f0ecad88`）246/246 离线测试 PASS，IDA mutation 与 Round 4 IDA/ERA/Capability contracts PASS；P0-ROBUST-01 标记 DONE。仅为工程鲁棒性验证，不代表科学效度通过。

- QA-02 加强 negative-control metamorphic invariance：除不触发硬 FAIL 外，四种语义保持变换必须保持 overall status、gate status/severity 与 metric values/statuses 不变。Run #2023（45892053327，head `49613acf6d540f5ef494335a45eebca65077a64b`）243/243 测试 PASS；8/8 deterministic mutations detected，4/4 negative controls 指标不变，0/4 false positives；artifact #15152600525（SHA-256 `bdc08d2a95efcffa5ec1c8bbaa43b9432c27e9b639b09795fcefb9c6e76125ef`）。这仍是合成实现敏感性验证，QA-02 保持 BLOCKED，M09–M12 NOT_ASSESSED。
- 用户于 2026-11-27 决定暂缓独立专家评审；EX-03 与依赖其盲审/仲裁的 EX-07 调整为 DEFERRED。评审协议、Schema 和 Oracle 工具保留；12 条用例仍 NOT_RUN，科学效度结论不因此升级。
- 建立 IDA 离线质量检查器、ERA Runtime Record 与统计分析器、机器可读报告 Schema 和跨字段验证器；DSH Pilot 导入器现强制校验 trace JSONL evidence manifest、SHA-256、case/run 身份与安全路径，并将 trace digest 写入 Runtime Record。
- 建立 Capability 与 Regression 的用途专属分析设计；新增探索性 Rasch 1PL 与平衡 Person×Item G-study 分析器、报告 Schema 和方法边界文档；增加固定 seed 的 30-replication Rasch 1PL 参数恢复模拟与回归测试（26/30 有效，能力/题目难度平均相关约 0.867/0.961），以及 G-Theory D-study 单调性/系数边界和负方差失败安全测试；综合公式、权重和阈值保持 NOT_VALIDATED。
- 建立专家内容效度盲评协议、评分记录 Schema、Judge 校准证据报告 Schema 与验证器；新增 manual/LLM Judge observations 导入器，绑定 suite/observations SHA-256、逐案 Gold/Judge evidence refs 和匿名 reviewer/adjudicator ID；支持重复 Judge 运行并按 case 聚合，避免伪重复。
- 建立 Round 4 独立 Oracle 双盲评审包、提交比较器、hash-bound 执行前冻结门禁。
- 增加 ERA 真实运行执行协议、架构与验收基线、外部 Benchmark 候选及许可限制登记。
- 最新 Judge 校准接口代码验证：Run #1993（45802577224，精确 head 4067dba939a4e5171864c85cde413c46e934ee65），actionlint、正式 Skill 包、Benchmark、238/238 离线测试 PASS；Round 4 IDA/ERA contract PASS；Artifact 15108810359。该验证证明导入器/契约/测试通过，不证明任何真实 Judge 的经验有效性。
- EX-05 因缺少 12-case 可审计独立 Gold、额外真实运行授权/环境、多配置和版本配对数据，保持 BLOCKED。独立专家评审与依赖其盲审/仲裁的 EX-07 已按用户决定暂缓（DEFERRED）；不再以 Issue #43 招募或等待报名作为当前执行路径。
- IM-03 的 manual/LLM Judge 证据导入接口已实现，支持 held-out/blinded 独立 Gold、逐案证据、重复 Judge 运行及 case-level 非伪重复统计；由于尚无真实独立 Judge 校准样本，任务保持 BLOCKED，synthetic smoke 仍 NOT_VALIDATED。
- IM-05 新增 Rasch infit/outfit 描述诊断、显式 NOT_ASSESSED DIF/measurement-invariance 输出，以及 G-Theory 参数恢复和 20×10/40×25/80×50 样本设计敏感性实验；Run #2002（45804426404）241/241 测试、三种模拟、真实 Round 4 Capability 报告契约 PASS。真实数据仅 1 configuration × 3 cases，Rasch/G-Theory/DIF/measurement invariance 均 NOT_ASSESSED，IM-05 保持 BLOCKED。
- IM-07 Skill quality standard 2.0.0 与 16 个按需 references 已更新并通过 Skill package validator；正式 VERSION/frontmatter 仍为已发布的 0.0.1，待 v0.0.2 Release Gate 和明确发布批准后再升级，IM-07 当前 BLOCKED。
- QA-02 新增 IDA-M01–M08 八种确定性缺陷和四种 negative controls 的受控变异实验；8/8 检出，Wilson 95% CI 0.676–1.000；0/4 negative-control false positive，Wilson 95% CI 0–0.490。M09–M12 仍 NOT_ASSESSED，缺独立专家语义评审/Oracle/污染审计，QA-02 保持 BLOCKED。Run #2011（45806101196）243/243 tests PASS，mutation artifact #15108859637。
- QA-03 Round 4 实际 Pilot 为 3/15，3/3 Agent/Process/Gold PASS，但仅 1 条 mutation fault、无重复/配对/成本、Judge NOT_RUN、Regression null、composite NOT_VALIDATED；12 条 NOT_RUN。production/pilot/adjudication jobs 均 SKIPPED，因真实环境/预算授权缺失 QA-03 保持 BLOCKED。
- DOC-01 同步根 README、研发 README、CHANGELOG 和质量报告；文档已反映 G-Theory 模拟、IDA mutation 8/8 和真实 Pilot 3/15。正式 VERSION/frontmatter 保持 0.0.1，待所有 Release Gate 通过和明确批准后再升级，DOC-01 当前 BLOCKED。
- EX-06 真实 Builder/DSH/Runner/独立 Oracle 证据规范化与 IDA/ERA 执行已完成；Run #1983（45800505196，精确 head d899ea3）230/230 离线测试与 Round 4 evidence Job PASS，Artifact 15105794918。该完成状态仅覆盖现有 3 条 Pilot 证据，不代表剩余用例或科学效度门禁完成。
- 实证边界：15 条 Round 4 用例中仅 3 条真实 Pilot，12 条 NOT_RUN；独立 Gold Judge 校准仍 NOT_RUN（synthetic smoke 仅验证执行/报告契约）；IDA/ERA PARTIAL；综合分 NOT_VALIDATED。专家评审与 12-case Oracle 盲审/仲裁暂缓（EX-03/EX-07=DEFERRED）；盲测语义缺陷、Capability/Regression 完整效标和公式独立验证仍未完成。
- 发布限制：尚无 v0.0.2 Release Candidate、最终发布审查或用户发布批准；不得创建 v0.0.2 tag/release。

## 0.0.1 — 发布候选

- 建立通用评测数据集构建 Skill。
- 增加中文质量标准、用例 Schema、评分器规范、覆盖设计和证据治理规则。
- 按 Agent Skills 开放格式将 Skill 本体整理为独立目录，入口和参考资料可直接作为一个 Skill 安装。