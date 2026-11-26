# 版本变更记录

## 0.0.2 — Unreleased（研发中）

> 本节记录开发分支已实现的工程资产，不代表发布批准或实证效度通过。正式版本号仍为 0.0.1。

- 建立 IDA 离线质量检查器、ERA Runtime Record 与统计分析器、机器可读报告 Schema 和跨字段验证器。
- 建立 Capability 与 Regression 的用途专属分析设计；新增探索性 Rasch 1PL 与平衡 Person×Item G-study 分析器、报告 Schema 和方法边界文档；增加固定 seed 的 30-replication Rasch 1PL 参数恢复模拟与回归测试（26/30 有效，能力/题目难度平均相关约 0.867/0.961），以及 G-Theory D-study 单调性/系数边界和负方差失败安全测试；综合公式、权重和阈值保持 NOT_VALIDATED。
- 建立专家内容效度盲评协议、评分记录 Schema、Judge 校准证据报告 Schema 与验证器；Judge 校准执行脚本已接入报告契约，输出数据集/Prompt/实现哈希、逐案结果和重算统计，并在落盘前进行契约校验。
- 建立 Round 4 独立 Oracle 双盲评审包、提交比较器、hash-bound 执行前冻结门禁。
- 增加 ERA 真实运行执行协议、架构与验收基线、外部 Benchmark 候选及许可限制登记。
- 最新代码/文档基线验证：Run #1972（45732657722，精确 head c1babc7ec9d51de6ac0c3cdb36232573c32f53bb），actionlint、正式 Skill 包、Benchmark、223/223 离线测试（含 Judge Calibration 与 Rasch/G-Theory 新增测试）PASS，Round 4 IDA/ERA 报告契约验证 PASS；Artifact 15077358259。此前 Run #1968 在测量分析代码 head 上同样以 223/223 测试通过。TASKS/质量报告随后追加 Run #1958 记录，文档 head 的最终复验待完成。
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
