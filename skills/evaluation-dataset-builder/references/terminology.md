# 评测数据集构建术语表

本术语表统一评测数据集构建过程中的核心概念。自然语言说明使用统一中文名称；机器字段、枚举和固定 ID 保留原样。

| 机器标识或英文术语 | 统一中文名称 | 定义 |
|---|---|---|
| Evaluation Dataset | 评测数据集 | 用于系统化验证目标能力的一组结构化评测用例 |
| Evaluation Case | 评测用例 | 具有独立目标、输入、预期行为和判定方法的最小评测单元 |
| Evaluation Target | 评测对象 | 被评估的系统、Agent、Skill、API、工作流或能力 |
| Objective | 评测目标 | 需要通过评测验证的具体行为或能力 |
| Coverage | 覆盖度 | 已覆盖范围相对于预先定义范围的情况 |
| Coverage Universe | 覆盖范围全集 | 覆盖率计算所依据的完整范围和统计口径 |
| Grading Contract | 判定契约 | 单条用例内部的判定目标、方法、条件、证据和不确定性处理规则 |
| Deprecated Grader Reference | 已弃用的评分器引用 | 为历史清单兼容而保留的可选引用字段；新数据集不应生成独立评分器产品 |\n| Reference Outcome | 参考结果 | 用于判定结果的可信预期值或预期行为 |
| Ground Truth | 已核实的判定依据 | 有权威来源支持、可用于判定的事实或结果 |
| Provenance | 来源追溯 | 记录结论、数据和材料的来源、版本和定位信息 |
| Evidence | 证据 | 支持或否定某项判定的可核验材料 |
| Baseline | 对照基线 | 用于比较的参照系统或参照结果 |
| Regression | 回归 | 修改后原有能力或行为发生退化 |
| Semantic Deduplication | 语义去重 | 根据意图、能力、条件、动作和结果识别重复用例 |
| Incremental Update | 增量更新 | 仅更新受到规则或资料变化影响的内容 |
| Held-out Dataset | 独立留出集 | 不参与构建调优、用于独立验收的数据集 |
| Critical Gate | 关键质量门禁 | 不允许由其他评分抵消的强制质量条件 |
| Unknown | 未知 | 当前证据不足以作出肯定或否定判定 |
| Synthetic | 合成示例 | 为说明或测试而构造、不代表真实业务的数据 |
| Manifest | 数据集清单 | 记录数据集用途、版本、数量、覆盖、来源和状态的文件 |
| JSONL | JSON 行格式 | 每行包含一个独立 JSON 对象的文本格式 |
| Trace | 执行轨迹 | 记录工具调用、步骤和观察结果的过程信息 |

## 固定状态和字段

以下值属于结构化数据接口，必须保持原样：

- 质量状态：candidate、validated、approved、needs_info、rejected。
- 执行状态：DESIGN_ONLY、READY_TO_RUN、EXECUTION_VERIFIED、NOT_RUN。
- 修复状态：BLOCKED、READY_FOR_RETEST、VERIFIED、RERUN_REQUIRED。
- 判定结果：PASS、FAIL、UNKNOWN、NOT_RUN。
- 核心字段：case_id、dataset_id、evaluation_target、objective、expected_behavior、forbidden_behavior、source_refs、grading、quality_status。
- 稳定用例编号示例：SE01、SE02。

质量状态、执行状态、修复状态和判定结果是不同维度，不得互相替代。例如，质量状态为 approved 不代表执行状态为 EXECUTION_VERIFIED。
