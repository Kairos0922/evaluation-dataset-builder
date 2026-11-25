# Round 4 真实证据 IDA / ERA 结果

**状态：** 已由 PR #44 CI 自动分析并归档。本报告是冻结证据的分析结果，不是 v0.0.2 全量验收，也不证明综合公式有效。

## 1. 可复核来源

| 证据 | GitHub 引用 | 结果 |
|---|---|---|
| Builder 原始产出 | [Run 44959366258](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258), artifact 14729741906 | 15 条用例已生成；Builder production Job 本身 failure（artifact emitted），不得记为 Job PASS |
| 独立输出验证 | [Run 44968128127](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127) | PASS |
| 冻结产出复验 | [Run 45291624154](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45291624154) | PASS |
| 三条真实 Skill Pilot / Oracle | [Run 45189512695](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45189512695), artifact 14824967038 | WB-02 / WB-10 / WB-12；独立 Gold Oracle 3/3 PASS |
| IDA / ERA 自动分析 | [PR #44 Run 1847](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45594508903), artifact 15012860922 | validate Job 与 round4-real-evidence-assessment Job PASS |

数据集：`wb-core@1.0.0`  
Dataset digest：`cc949f0e9d9c60e6d2ad405749c3829aacc7a2fcbee75fa57e570b56de1f2141`  
原始 JSONL SHA-256：`000d38b110b60eae902f86737ea6bd1368f98c6632c42a47bb9470a4a08bfc45`

## 2. IDA：Independent Dataset Assessment

**总体状态：PARTIAL。** 不输出综合分数。

| 项目 | 观察结果 | 解释边界 |
|---|---:|---|
| Manifest Schema | 1/1 PASS | 仅证明结构符合 Schema |
| Case Schema | 15/15 PASS | 不证明语义正确或任务可解 |
| Case ID 完整唯一 | 15/15 PASS | 不证明语义去重 |
| 来源注册表解析 | 61/61 PASS | 可解析不等于来源真实或主张有证据支持 |
| 每条用例具备来源引用 | 15/15 | 不等于 claim support 已审核 |
| 精确重复 | 0/15 | 仅检查规范化 payload 精确重复 |
| Rubric 清单 | 60 条 criteria / 15 cases | 数量不证明评分标准完整或有效 |

关键 Gate：
- G01 Source Provenance：PASS，仅限 ID 和注册表解析。
- G02 Construct Alignment：NOT_ASSESSED。
- G03 Task Solvability：NOT_ASSESSED。
- G04 Ground Truth Validity：NOT_ASSESSED。
- G05 Rubric Validity：UNKNOWN。
- G06 Safety / Authorization：NOT_ASSESSED。
- G07 Integrity / Leakage：UNKNOWN。
- G08 Runtime Auditability：NOT_APPLICABLE（属于 ERA 范围）。

Manifest 的数据集质量状态仍为 `needs_info`，BR-09 request-failure / error-recovery 证据缺失。业务规则和 Workboard Lite 应用 Fixture 为合成材料；本轮不能作为生产业务数据的外部效度证据。

## 3. ERA：Environment-based Runtime Assessment

**Capability 分析状态：PARTIAL。** 当前仅有一个 Skill revision、一个模型/运行配置、三个不同用例各一次运行。

| 观测 | 结果 | 95% Wilson 区间或说明 |
|---|---:|---|
| 有效运行 | 3/3 | 0.4385–1.0000 |
| 环境失败 | 0/3 | 0.0000–0.5615 |
| Agent Outcome PASS | 3/3 | 0.4385–1.0000 |
| Process Compliance PASS | 3/3 | 0.4385–1.0000 |
| 独立 Gold Oracle PASS | 3/3 | 三条均由独立 Oracle 记录支持 |
| Judge 验证 | NOT_RUN | 没有可关联的 Judge 输出 |
| 已注入缺陷的失败暴露 | 1/1 | 单一缺陷样本，不具备稳定检出率推断能力 |

三个用例为 WB-02、WB-10、WB-12。仅 WB-02 带有一个 fixture mutation（`search-case-sensitive`），其故障被检测并暴露。该结果不能等同于评测集缺陷注入检出能力已通过验证。

运行成本画像（描述性）：
- Duration median：89.426 秒；P95：118.0388 秒。
- Total tokens median：292,536。
- Model steps median：15；Tool calls median：21。
- USD cost：未提供，不估算。

## 4. 尚未测量及禁止推断

- 其余 12/15 用例仍为 NOT_RUN。
- Judge False Pass / False Fail / Abstention / Accuracy：NOT_ASSESSED。
- IRT 难度、区分度、Test Information、DIF：NOT_ASSESSED。
- G-Theory 方差分量、G 系数、Phi 系数：NOT_ASSESSED。
- Regression：没有 baseline/candidate 配对，`regression_analysis = null`。
- 重复运行稳定性：没有 repeat group。
- 运行种子：原始证据未提供，记录为 null。
- 外部任务效标、专家盲评、独立缺陷标签：尚未完成。
- IDA 和 ERA 的 composite 均为 `NOT_VALIDATED`，value 为 null。

3/3 的观测通过率区间仍很宽，不能据此宣称该 Skill 的总体能力通过，也不能把 Agent 表现归因于数据集质量。

## 5. CI 结果和下一步

Run #1847（精确 head `0366be3bad636051c1d7c2375874acb335650009`）：
- actionlint：PASS。
- Skill 正式包验证：PASS。
- Benchmark 贯通样例：PASS。
- 离线测试：167/167 PASS。
- Round 4 真实证据导入、IDA、ERA 和报告边界断言：PASS。\n- IDA / ERA 报告通过正式 JSON Schema 与跨字段契约验证：PASS。\n- 报告归档 Artifact：15012860922。
- 其他依赖 PR #38 生产前置条件的 Jobs 为 SKIPPED，不计为通过。

后续动作：
1. 将 IDA/ERA 报告 JSON Schema 和跨字段契约校验纳入真实证据 Job 的强制步骤。
2. 扩展 12 条未运行用例的真实执行，先处理环境/业务规则证据缺口。
3. 单独设计多配置、多任务、重复运行和版本配对实验；不得用当前三条 Pilot 拟合 IRT 或 G-Theory。
4. 获取独立 Judge 输出与专家标签后再评价 Judge。
5. 在独立外部数据、盲评和缺陷注入证据到位前，保持综合公式 `NOT_VALIDATED`。
