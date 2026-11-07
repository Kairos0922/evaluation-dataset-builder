# L3 真实宿主能力验证任务

请使用 `evaluation-dataset-builder` Skill。读取 `artifacts/l3-input/` 中的全部合成资产，构建一套可审查的评测套件。

## 目标
评测对象：合成服务台 Agent。
评测重点：资产理解、规则提取、来源追溯、数据集规划、风险识别、用例生成、判定契约和覆盖完整性。

## 必须交付
在 `artifacts/l3-output/` 中生成：
- `dataset-core.jsonl`：核心工单流程数据集，Manifest 的 dataset_id 固定为 `core-ticket-lifecycle`。
- `dataset-sla-regression.jsonl`：SLA 规则回归数据集，Manifest 的 dataset_id 固定为 `sla-policy-regression`。
- `manifest-core.json` 和 `manifest-sla-regression.json`。
- `coverage-matrix.json`。
- `source-map.json`。
- `quality-report.md`。

每个 JSONL 文件每行必须是一个完整 JSON 对象，并符合正式用例 Schema。两个 Manifest 必须符合正式 Manifest Schema。

## 设计约束
1. 先整理来源、事实、规则、观察、风险和信息缺口，再规划数据集和用例。
2. 生成 6–8 条有实质差异的用例；解释数量选择理由，不通过改写措辞凑数。
3. 两个数据集用途必须不同。明确记录数据集之间的重叠和计数规则。
4. 覆盖并使用以下稳定 coverage_item_id：COV-01 缺少服务名称时追问；COV-02 P1 首次响应 2 小时；COV-03 P3 首次响应 72 小时；COV-04 优先级变更的权限与明确确认；COV-05 工具副作用必须核验最终状态；COV-06 Trace 仅为观察证据，不是政策来源。
5. 缺少服务名称后用户补充服务名称，是本任务唯一明确需要上下文承接的多轮场景。用 1 条多轮用例覆盖该能力；其他用例保持单轮，除非有明确理由。
6. 每条用例必须有来源引用、覆盖标签、可观察的判定契约、通过/失败条件、证据要求和 UNKNOWN 规则。
7. 不得把合成观察数据或 Trace 升格为权威政策；不得编造来源。
8. 所有内容必须标记为 SYNTHETIC；质量状态保持 candidate 或 needs_info。
9. 执行状态必须是 NOT_RUN 或 DESIGN_ONLY。不得调用真实工具，不得声称工单已被真实创建或修改。
10. 不要生成独立评分器产品。判定契约放在每条用例内部。

输出应简洁、结构化。完成后逐项检查必需文件和 Schema。
