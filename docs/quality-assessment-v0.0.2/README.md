# v0.0.2 质量评价开发资产

本目录记录 v0.0.2 的需求、研究、方法论、指标、公式验证和实验设计。它是仓库研发证据，不是正式 Skill 的运行时依赖。

## 当前实现状态

- IDA：已提供第一版确定性离线检查器，尚未完成语义专家审查模块。
- ERA：已定义报告契约，尚未完成真实运行收集器和统计分析器。
- 综合分：未验证。当前不输出总分、权重或通过阈值。
- Capability / Regression：分别定义指标和实验路径，端到端验证尚未完成。

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

## 测试

```bash
python -m unittest discover -s tests
```

发布前必须在精确 PR head 上执行完整 CI，并记录 workflow run 和 artifact。

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

分析器当前计算描述性通过率、Judge false pass/false fail/abstention、历史故障与变异检出、配对版本差异、McNemar exact p-value、重复运行不一致和成本画像。它不会自动执行 Agent，也不会把统计量解释为合格阈值。Capability 的 IRT、DIF、测量不变性和 G-Theory 仍需单独建模与验证。
