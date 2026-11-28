# 通用 Agent 基准评测集 v1.0.0

本目录包含两套彼此独立、可用于 Capability Evaluation 与 Regression Evaluation 的通用 Agent / Skill 合成基准评测集。

| 数据集 | 用例数 | 用例文件 | Manifest |
|---|---:|---|---|
| Safety | 100 | [general-safety-v1.0.0.jsonl](general-safety-v1.0.0.jsonl) | [general-safety-manifest.json](general-safety-manifest.json) |
| Robustness | 100 | [general-robustness-v1.0.0.jsonl](general-robustness-v1.0.0.jsonl) | [general-robustness-manifest.json](general-robustness-manifest.json) |

## 规范和来源

- [benchmark-contracts.md](benchmark-contracts.md)：本批数据集的合成行为契约。
- [source-registry.json](source-registry.json)：Safety 合成来源注册表。
- [robustness-source-registry.json](robustness-source-registry.json)：Robustness 合成来源注册表。

所有用例均标记为 `synthetic_gap_fill`，来源类型为 `synthetic_scenario`。这些场景是本项目为覆盖通用行为构念而设计的合成样本，不是实际用户案例、事故记录、行业统一规范或独立 Gold Oracle。

## 构建约束

- 每个数据集 100 条，分别使用稳定 ID：`SAF-001..SAF-100` 和 `ROB-001..ROB-100`。
- 每个数据集按 10 个构念维度组织，每个维度 10 条；Manifest 覆盖统计按唯一 coverage item 计数。
- 每条用例包含目标、输入、预期行为、禁止行为、逐案判定标准、证据要求、UNKNOWN 规则和执行准备信息。
- 所有用例当前 `quality_status=candidate`、`execution_requirements.status=NOT_RUN`；未进行真实 Agent 执行。
- 不输出未经验证的综合分、权重或通过阈值。

## 输入与执行适配

`user_input` 可为字符串或结构化对象：

- 字符串：作为单轮用户输入原样提交。
- `messages`：按数组顺序重放多轮对话，保留 role 与内容；`task` 为最后评测任务。
- `context` / `document` / `files`：作为合成上下文或文件 fixture 装载，再执行对应 task。
- `tool_fixture`：配置模拟工具的成功、失败、超时或未知状态；按用例执行步骤重放，不连接真实支付、生产或外部副作用工具。

具体宿主需要一个薄的 harness adapter 将这些结构映射到其会话和 mock-tool 接口。该 adapter 不应改变用例语义或预期行为。

## 本地验证

在仓库根目录运行：

```bash
python -m unittest tests.test_general_benchmark_datasets -v
python scripts/assess_dataset_quality.py \
  --manifest datasets/general-safety-manifest.json \
  --cases datasets/general-safety-v1.0.0.jsonl \
  --source-registry datasets/source-registry.json \
  --output artifacts/general-benchmarks/safety-ida-report.json \
  --evaluation-purpose both

python scripts/assess_dataset_quality.py \
  --manifest datasets/general-robustness-manifest.json \
  --cases datasets/general-robustness-v1.0.0.jsonl \
  --source-registry datasets/robustness-source-registry.json \
  --output artifacts/general-benchmarks/robustness-ida-report.json \
  --evaluation-purpose both
```

然后分别运行 `python scripts/validate_quality_assessment.py --report <report-path>` 校验 IDA 报告契约。

IDA 自动检查只覆盖 Schema、标识符、来源注册表身份解析、覆盖统计内部一致性和精确重复等确定性项目。它不能证明来源主张真实、语义去重、构念效度、金标准正确性或安全策略适用性。来源注册表解析 PASS 不等于来源主张获得独立支持。

## 状态解释

初始版本属于候选数据集。CI / IDA 通过只表示确定性结构和契约检查通过；语义审查、独立专家内容效度、真实运行和跨 Agent 泛化仍需分别取得证据后才能更新状态。
