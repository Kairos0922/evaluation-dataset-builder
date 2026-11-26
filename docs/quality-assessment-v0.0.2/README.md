# v0.0.2 质量评价开发资产

本目录记录 v0.0.2 的需求、研究、方法论、指标、公式验证和实验设计。它是仓库研发证据，不是正式 Skill 的运行时依赖。

## 当前实现状态

- IDA：确定性离线检查器、报告 Schema 和跨字段验证器已实现；语义专家审查和内容效度实证未完成。
- ERA：Runtime Record Schema、历史 Pilot 导入器、统计分析器和报告验证器已实现；现有真实证据仅 3/15 Pilot，完整运行验证未完成。
- 综合分：未验证。当前不输出总分、权重或通过阈值。
- Capability / Regression：已实现探索性 Rasch 1PL、双 facet G-study、Rasch infit/outfit 描述诊断、G-Theory 参数恢复与样本设计敏感性模拟；真实 Pilot 仅 1 configuration × 3 cases，Rasch/G-Theory 实际估计 NOT_ASSESSED，DIF/测量不变性 NOT_ASSESSED，Regression 缺少配对版本效标。

## 独立离线评价

输入：
- 符合 Skill 数据格式的 manifest JSON；
- 每行一条用例的 JSONL；
- 可选的独立来源注册表 JSON。

示例：

```bash
python scripts/assess_dataset_quality.py \
  --manifest path/to/manifest.json \
  --cases path/to/cases.jsonl \
  --output artifacts/ida-report.json \
  --evaluation-purpose both
```

如果有独立来源注册表：

```bash
python scripts/assess_dataset_quality.py \
  --manifest path/to/manifest.json \
  --cases path/to/cases.jsonl \
  --source-registry path/to/source-registry.json \
  --output artifacts/ida-report.json \
  --evaluation-purpose capability
```

来源注册表可采用以下任一形式：
- JSON 数组，每项至少包含 source_id；
- 对象中的 sources 数组；
- 以 source_id 为键的对象。

注册表解析只证明 ID 和部分身份字段能够匹配，不证明来源真实或支持对应主张。

输出是 IDA 报告，包含：
- Manifest / Case Schema 状态；
- case_id、dataset_id 和 case_count 一致性；
- 来源引用存在性和可选注册表解析；
- Manifest 覆盖统计与用例 coverage_tags 的内部一致性；
- scenario_bucket 分布；
- 忽略 case_id 后的精确 JSON 重复；
- grading criteria 数量画像；
- 关键门禁、问题清单和证据缺口。

该工具不会判断语义重复、构念效度、来源主张支持、任务可解性、Ground Truth 正确性、Rubric 语义有效性、安全性、污染或真实 Agent 表现。上述项目必须由独立专家或 ERA 运行证据补充。

### 数据集摘要 SHA-256

IDA 报告中的 dataset.sha256 采用以下固定算法：

SHA256(
  UTF8("evaluation-dataset-builder-ida-v0.0.2") + NUL +
  raw_manifest_bytes + NUL +
  raw_cases_jsonl_bytes
)

它绑定 Manifest 和 JSONL 原始字节，不代表语义等价的数据集具有相同摘要。

### 验证报告契约

```bash
python scripts/validate_quality_assessment.py --report artifacts/ida-report.json
```

报告契约通过仅表示结构和交叉字段约束有效，不证明评价结论有效。

## 新增执行协议与证据契约

- [架构与验收基线](architecture-and-acceptance-baseline.md)：明确 IDA/ERA 边界、证据等级、模块数据流和验收含义。
- [ERA 真实运行执行协议](runtime-assessment-protocol.md)：规定冻结清单、单次运行、失败归因、Capability/Regression 分析和停止规则。
- [专家盲评协议](expert-review-protocol.md)：规定内容效度、盲评、仲裁和一致性统计。
- [Judge Calibration Report Schema](schemas/judge-calibration-report.schema.json) 与 `scripts/validate_judge_calibration.py`：校验 Judge 校准证据包；合成 smoke 结果不得标记为有效度通过。

## 测试

```bash
python -m unittest discover -s tests
```

发布前必须在精确 PR head 上执行完整 CI，并记录 workflow run 和 artifact。

## 质量审计报告

本轮按 TASKS.md 执行的阶段性任务质量审计见 [quality-report.md](quality-report.md)。报告区分工程验证与科学效度，不把 CI PASS 当作实证有效性证明。

## 参考文档

- [需求规格](requirements.md)
- [研究证据](research-evidence.md)
- [方法论设计](methodology-design.md)
- [候选指标字典](metric-catalog.md)
- [公式验证协议](formula-validation-protocol.md)
- [实验设计](experimental-design.md)
- [设计决策](decision-log.md)
- [持久化任务清单](TASKS.md)

## 真实运行评价

每行一条运行记录，必须符合：
- docs/quality-assessment-v0.0.2/schemas/runtime-record.schema.json
- Skill 内 references/runtime-record.schema.json

Capability 示例：

```bash
python scripts/assess_runtime_quality.py \
  --records path/to/runtime-records.jsonl \
  --output artifacts/era-report.json \
  --dataset-version 1.0.0 \
  --target-name my-agent \
  --evaluation-purpose capability
```

Regression / Both 需要明确配对比较的两个版本：

```bash
python scripts/assess_runtime_quality.py \
  --records path/to/runtime-records.jsonl \
  --output artifacts/era-report.json \
  --dataset-version 1.0.0 \
  --target-name my-agent \
  --evaluation-purpose both \
  --baseline-revision BASE_SHA \
  --candidate-revision CANDIDATE_SHA
```

记录必须包含精确的数据集 SHA、Agent/Skill 目标版本、模型、Harness、环境、工具、运行状态、轨迹、结果、Agent/Process/Judge/Gold outcomes、故障注入信息和成本字段。

分析器当前计算描述性通过率、Judge false pass/false fail/abstention、历史故障与变异检出、配对版本差异、McNemar exact p-value、重复运行不一致和成本画像。它不会自动执行 Agent，也不会把统计量解释为合格阈值。ERA 分析器本身只提供描述性 Capability/Regression 汇总；独立的 `analyze_capability_measurement.py` 提供探索性 Rasch/G-Theory 估计与诊断。真实多配置数据不足以拟合；DIF、测量不变性和外部效标仍未验证。

## 受控缺陷变异验证

运行离线 IDA 的确定性缺陷敏感性实验：

```bash
python scripts/run_ida_mutation_validation.py --output artifacts/ida-mutation-validation.json
```

该实验覆盖 IDA-M01–M08 八种确定性结构/来源/覆盖缺陷及四种 negative controls；negative controls 除检查不触发硬失败外，还逐项验证 overall status、gate results 和 metric results 与基线完全一致（metamorphic invariance）；输出契约见 [ida-mutation-validation-report.schema.json](schemas/ida-mutation-validation-report.schema.json)，实验方法和边界见 [offline-evaluator-mutation-validation.md](offline-evaluator-mutation-validation.md)。8/8 检出只证明对这些合成变异算子的敏感性，不证明语义有效性；M09–M12 仍需独立专家/Oracle/污染审计。

## Capability / G-Theory 参数恢复实验

```bash
python scripts/run_g_theory_parameter_recovery.py --persons 40 --items 25 --output artifacts/g-theory-parameter-recovery.json
```

实验报告契约见 [g-theory-monte-carlo-report.schema.json](schemas/g-theory-monte-carlo-report.schema.json)，方法和样本设计敏感性结果见 [capability-measurement-analysis.md](capability-measurement-analysis.md)。模拟仅支持 DGP 条件下的 observed-score 参数恢复，不构成真实 Skill 测量效度或普遍样本量门槛。

## 综合公式验证证据

任何候选综合分都必须附带独立验证报告，报告格式由 `schemas/formula-validation.schema.json` 定义，并由 Skill 随包提供的同名 Schema 约束。

校验命令：

```bash
python scripts/validate_formula_validation.py path/to/formula-validation-report.json
```

验证器会检查：
- 开发、校准、验证和外部数据集家族是否隔离；
- 是否有独立、盲法专家评审和评分者一致性证据；
- 是否有受控缺陷检出结果；
- 是否有独立外部效标；
- 是否完成权重、标准化、聚合和维度敏感性分析；
- 若启用标量分数，是否有基于决策损失的阈值验证；
- 是否保留可复现代码、commit、随机种子和证据引用。

未完成这些证据时，验证报告状态应为 NOT_VALIDATED，标量分数必须保持关闭。验证器的结构通过仅证明证据包符合契约，不代表证据本身真实或结论有效，仍需独立审计。


## 当前 Round 4 证据边界

最新已完成完整工程验证的代码 head 为 `9cb0e46cd78193a9419929f90c73817a0ac511c3`，Run #2011（45806101196）243/243 离线测试 PASS，actionlint、Skill package、Benchmark、三种 G-Theory 样本设计模拟、IDA-M01–M08 controlled mutation、IDA/ERA/Capability report contract 均 PASS。该 Run 未启动新的 Builder production、independent-validation、Pilot 或 adjudication；它重新分析既有冻结证据。当前 15 条用例中 3 条真实 Pilot、12 条 NOT_RUN，IDA/ERA PARTIAL，Judge NOT_RUN，Regression 无配对，Capability 为 1 configuration × 3 cases，Rasch/G-Theory NOT_ASSESSED，DIF/测量不变性 NOT_ASSESSED，综合分 NOT_VALIDATED。
