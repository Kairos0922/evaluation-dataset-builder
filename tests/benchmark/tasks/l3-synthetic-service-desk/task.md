# L3 真实宿主能力验证任务

请使用 `evaluation-dataset-builder` Skill。读取 `artifacts/l3-input/` 中的全部合成资产，构建一套可审查的评测套件。

## 目标
评测对象：合成服务台 Agent。
评测重点：资产理解、规则提取、来源追溯、数据集规划、风险识别、用例生成、判定契约和覆盖完整性。

## 必须交付
在 `artifacts/l3-output/` 中生成：
- `dataset-core.jsonl`：核心工单流程数据集。
- `dataset-sla-regression.jsonl`：SLA 规则回归数据集。
- `manifest-core.json` 和 `manifest-sla-regression.json`。
- `coverage-matrix.json`。
- `source-map.json`。
- `quality-report.md`。

每个 JSONL 文件每行必须是一个完整 JSON 对象，并符合正式用例 Schema。两个 Manifest 必须符合正式 Manifest Schema。

## 设计约束
1. 先整理来源、事实、规则、观察、风险和信息缺口，再规划数据集和用例。
2. 生成 6–8 条有实质差异的用例；解释数量选择理由，不通过改写措辞凑数。
3. 两个数据集用途必须不同。明确记录数据集之间的重叠和计数规则。
4. 覆盖 P1 2 小时、P3 72 小时、缺少服务名称、优先级变更权限/确认、状态核验，以及 Trace 证据边界。
5. 只有在验证缺少服务名称后用户补充服务名称这一能力时，才设计多轮用例；不要为了多轮而多轮。
6. 每条用例必须有来源引用、覆盖标签、可观察的判定契约、通过/失败条件、证据要求和 UNKNOWN 规则。
7. 不得把合成观察数据或 Trace 升格为权威政策；不得编造来源。
8. 所有内容必须标记为 SYNTHETIC；质量状态保持 candidate 或 needs_info。
9. 执行状态必须是 NOT_RUN 或 DESIGN_ONLY。不得调用真实工具，不得声称工单已被真实创建或修改。
10. 不要生成独立评分器产品。判定契约放在每条用例内部。

输出应简洁、结构化。完成后逐项检查必需文件和 Schema。
