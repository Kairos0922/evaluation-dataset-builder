# 版本变更记录

## 0.0.2 — Unreleased（研发中）

> 本节记录开发分支已实现的工程资产，不代表发布批准或实证效度通过。正式版本号仍为 0.0.1。

- 建立 IDA 离线质量检查器、ERA Runtime Record 与统计分析器、机器可读报告 Schema 和跨字段验证器；DSH Pilot 导入器现强制校验 trace JSONL evidence manifest、SHA-256、case/run 身份与安全路径，并将 trace digest 写入 Runtime Record。
- 建立 Capability 与 Regression 的用途专属分析设计；新增探索性 Rasch 1PL 与平衡 Person×Item G-study 分析器、报告 Schema 和方法边界文档；增加固定 seed 的 30-replication Rasch 1PL 参数恢复模拟与回归测试（26/30 有效，能力/题目难度平均相关约 0.867/0.961），以及 G-Theory D-study 单调性/系数边界和负方差失败安全测试；综合公式、权重和阈值保持 NOT_VALIDATED。
- 建立专家内容效度盲评协议、评分记录 Schema、Judge 校准证据报告 Schema 与验证器；新增 manual/LLM Judge observations 导入器，绑定 suite/observations SHA-256、逐案 Gold/Judge evidence refs 和匿名 reviewer/adjudicator ID；支持重复 Judge 运行并按 case 聚合，避免伪重复。
- 建立 Round 4 独立 Oracle 双盲评审包、提交比较器、hash-bound 执行前冻结门禁。
- 增加 ERA 真实运行执行协议、架构与验收基线、外部 Benchmark 候选及许可限制登记。
- 最新 Judge 校准接口代码验证：Run #1993（45802577224，精确 head 4067dba939a4e5171864c85cde413c46e934ee65），actionlint、正式 Skill 包、Benchmark、238/238 离线测试 PASS；Round 4 IDA/ERA contract PASS；Artifact 15108810359。该验证证明导入器/契约/测试通过，不证明任何真实 Judge 的经验有效性。
- EX-05 因缺少 12-case 独立 Oracle freeze、额外真实运行授权/环境、多配置和版本配对数据，已明确调整为 BLOCKED；Issue #43 招募帖尚无独立评审者响应。
- IM-03 的 manual/LLM Judge 证据导入接口已实现，支持 held-out/blinded 独立 Gold、逐案证据、重复 Judge 运行及 case-level 非伪重复统计；由于尚无真实独立 Judge 校准样本，任务保持 BLOCKED，synthetic smoke 仍 NOT_VALIDATED。
- IM-05 新增 Rasch infit/outfit 描述诊断、显式 NOT_ASSESSED DIF/measurement-invariance 输出，以及 G-Theory 参数恢复和 20×10/40×25/80×50 样本设计敏感性实验；Run #2002（45804426404）241/241 测试、三种模拟、真实 Round 4 Capability 报告契约 PASS。真实数据仅 1 configuration × 3 cases，Rasch/G-Theory/DIF/measurement invariance 均 NOT_ASSESSED，IM-05 保持 BLOCKED。
- IM-07 Skill quality standard 2.0.0 与 16 个按需 references 已更新并通过 Skill package validator；正式 VERSION/frontmatter 仍为已发布的 0.0.1，待 v0.0.2 Release Gate 和明确发布批准后再升级，IM-07 当前 BLOCKED。
- QA-02 新增 IDA-M01–M08 八种确定性缺陷和四种 negative controls 的受控变异实验；8/8 检出，Wilson 95% CI 0.676–1.000；0/4 negative-control false positive，Wilson 95% CI 0–0.490。M09–M12 仍 NOT_ASSESSED，缺独立专家语义评审/Oracle/污染审计，QA-02 保持 BLOCKED。Run #2011（45806101196）243/243 tests PASS，mutation artifact #15108859637。
- QA-03 Round 4 实际 Pilot 为 3/15，3/3 Agent/Process/Gold PASS，但仅 1 条 mutation fault、无重复/配对/成本、Judge NOT_RUN、Regression null、composite NOT_VALIDATED；12 条 NOT_RUN。production/pilot/adjudication jobs 均 SKIPPED，因真实环境/预算授权缺失 QA-03 保持 BLOCKED。\n- DOC-01 同步根 README、研发 README、CHANGELOG 和质量报告；文档已反映 G-Theory 模拟、IDA mutation 8/8 和真实 Pilot 3/15。正式 VERSION/frontmatter 保持 0.0.1，待所有 Release Gate 通过和明确批准后再升级，DOC-01 当前 BLOCKED。
- EX-06 真实 Builder/DSH/Runner/独立 Oracle 证据规范化与 IDA/ERA 执行已完成；Run #1983（45800505196，精确 head d899ea3）230/230 离线测试与 Round 4 evidence Job PASS，Artifact 15105794918。该完成状态仅覆盖现有 3 条 Pilot 证据，不代表剩余用例或科学效度门禁完成。
- 实证边界：15 条 Round 4 用例中仅 3 条真实 Pilot，12 条 NOT_RUN；独立 Gold Judge 校准仍 NOT_RUN（synthetic smoke 仅验证执行/报告契约）；IDA/ERA PARTIAL；综合分 NOT_VALIDATED。专家评审、Oracle 冻结、盲测缺陷实验、Capability/Regression 完整效标和公式独立验证仍未完成。
- 发布限制：尚无 v0.0.2 Release Candidate、最终发布审查或用户发布批准；不得创建 v0.0.2 tag/release。

## 0.0.1 — 发布候选

- 建立通用评测数据集构建 Skill。
- 增加中文质量标准、用例 Schema、评分器规范、覆盖设计和证据治理规则。
- 按 Agent Skills 开放格式将 Skill 本体整理为独立目录，入口和参考资料可直接作为一个 Skill 安装。
- 将用户安装与使用说明保留在仓库根目录 README，不混入 Skill 本体。
- 明确简体中文输出要求，统一评测领域术语和质量状态。
- 重构验证器，检查 Agent Skills 元数据、目录命名、按需资源引用、Schema 和测试集结构。
- 完善离线测试与发布门禁。

- 增加业务场景模型与适用性场景桶，建立业务规则、流程、状态、风险和可观察证据之间的映射。
- 将覆盖规划升级为缺口驱动生成，明确覆盖全集、优先级、覆盖统计和缺口报告。
- 增加数据集清单 Schema，并扩展用例 Schema 的覆盖标签、来源类型、可观察断言、轨迹约束和变更关联。
- 增强独立质量门禁，纳入业务模型追溯、合成案例标记、断言/轨迹证据和变更影响追溯。
- 增加来源混合治理、Agent/Skill 轨迹评分和变更影响分析/局部修复规范。
- 扩展正式包验证器与离线测试，检查新增规范文件、Schema 字段和数据集级质量检查项。
- 将场景桶、来源类型和覆盖标签设为每条用例的必填元数据，并要求至少关联一个覆盖项。
- 修复发布工作流将 PR 编号硬编码为 `2` 的问题，文档更新步骤现在使用实际输入的候选 PR 编号。
- 明确区分用例来源字段 `case_origin` 与来源证据字段 `source_refs[].source_type` 的合成场景枚举。

### 发布边界

版本保持 **0.0.1**。本次改造用于完善 0.0.1 发布候选，不代表发布门禁已通过。

结构验证、离线测试、行为评测、独立审查和目标运行环境验证是不同的证据。未完成的门禁必须明确标记，不得将发布候选描述为正式发布。
