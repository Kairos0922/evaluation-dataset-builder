# 离线测试与开发验收说明

## 测试范围

本目录包含评测数据集构建 Skill 的静态样例、离线单元测试和可选的行为评测程序。

普通 PR CI 只运行不调用模型的检查：

1. 正式包结构与清单验证。
2. Schema、测试数据和质量标准的静态检查。
3. 使用模拟响应的离线单元测试。
4. GitHub Actions workflow 静态检查（Actionlint）。

## 目录说明

- `self-eval-cases.json`：Skill 构建行为的离线评测样例。
- `trigger-evals.json`：Skill 适用范围的正负触发样例。
- `test_*.py`：离线单元测试。涉及网络请求的测试使用模拟响应，不访问真实服务。
- `run_eval.py`：可选的外部行为评测运行器。执行该程序会调用外部模型服务，必须按正式发布流程明确授权，并确认候选 SHA、预算、密钥和停止条件。

## 本地离线检查

Python 3.10 或更高版本。安装离线验证依赖：

```bash
python -m pip install pyyaml jsonschema
```

```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py" -v
```

这些检查不需要配置模型密钥，也不需要访问模型服务。

## 目标宿主运行验证

目标宿主验证不是模型行为评测。四种安装环境的步骤和当前状态见 `tests/target-runtime-matrix.md`。报告模板为 `tests/target-runtime-report.template.json`，Schema 为 `tests/target-runtime-report.schema.json`。

可对模板进行结构校验。这只证明报告格式合法，不证明宿主通过：

```bash
python scripts/validate_target_runtime_report.py \
  --report tests/target-runtime-report.template.json \
  --candidate-sha 0000000000000000000000000000000000000000 \
  --skill-tree-sha 0000000000000000000000000000000000000000
```

逐平台认证时，必须使用真实报告并传入 `--require-pass`；如已下载证据包，再传入 `--evidence-dir <目录>` 核对文件 SHA-256。**逐平台兼容性认证不是 0.0.1 发布门禁**，除非发布说明另行承诺某个平台已认证。

## 外部行为评测

外部行为评测仅在正式发布流程中针对精确候选 SHA 运行。报告须满足两次完整运行、匹配基线、行为/触发阈值、稳定性和完整可判定性要求。发布候选发生变化后，应重新执行受影响的门禁；未执行或证据不完整的结果必须标记为 NOT_RUN/UNKNOWN，不能报告为通过。

模型调用结果不能替代宿主兼容性证据。未执行的评测必须标记为未运行，不得报告为通过。
