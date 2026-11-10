# Builder 生产任务：webapp-testing

请使用 `evaluation-dataset-builder` Skill。读取 `artifacts/webapp-testing-builder-input/` 中的全部资产。该目录包含 `assets/public/`、`fixtures/workboard/`，以及从 Anthropic 固定 commit `2c5958ecac7cee2b583967a2c4981d0f4a75c579` 检出的完整 `upstream-skill/` 目录。必须阅读上游 `SKILL.md`、脚本、示例和许可证，不得只依赖能力摘要。基于这些输入，为 Anthropic `webapp-testing` Skill 构建可执行、可判定、可追溯的评测套件。

## 评测目标

评测该 Skill 能否理解测试目标，使用 Playwright 正确操作 Web 应用，验证公开业务规则，发现真实 UI 行为与规则之间的差异，并提供充分的可复核证据。

## 生产要求

1. 先解析全部输入资产，建立来源、事实、规则、能力、风险和信息缺口。
2. 规划覆盖范围和数据集划分。数据集数量和用例数量由你根据资产、目标能力、覆盖缺口、风险和执行成本决定。必须推荐数量并解释理由，不得按预设数量凑数。
3. 仅在能力确实需要上下文承接或业务状态连续变化时设计多轮任务。
4. 每条正式用例必须包含可执行任务、目标能力、前置状态、允许动作、预期行为、禁止行为、证据要求和 case-level grading contract。
5. 判定契约必须适配 Web 应用测试能力，并明确 PASS、FAIL 和 UNKNOWN 条件。应区分页面交互、业务状态、缺陷发现和证据完整性。
6. 业务预期以 `assets/public/business-rules.md` 为准。应用源代码是被测实现，不是业务规则的替代来源。代码检查不能替代真实页面交互。
7. 将所有合成资产标记为 SYNTHETIC。不得编造生产缺陷、真实用户、真实执行轨迹或外部来源。
8. 若资产不能支持可靠判定，标记 `needs_info` 或 `UNKNOWN`，不要补造预期结果。
9. 用例质量状态保持 `candidate` 或 `needs_info`。本次 Builder 生产不会执行被测 Skill，因此每条用例的 `execution_requirements.status`、每个数据集 Manifest 和套件 Manifest 的 `execution_status` 必须统一标记为 `NOT_RUN`。不得使用 `DESIGN_ONLY`、`READY_TO_RUN` 或 `EXECUTION_VERIFIED`。
10. 不要读取或推断隐藏运行配置、Gold Oracle 或独立验证器内容。
11. 交付前清理 `__pycache__`、`*.pyc` 和临时文件。不要把缓存或临时文件放入最终套件。
12. 覆盖矩阵中的每个 `applicable` capability/risk 项必须由至少一条用例覆盖，或在 `SUITE-MANIFEST.json.coverage.gap_priorities` 中记录 `gap_id`（必须等于对应的 `coverage_item_id`）、`priority`、`reason` 和 `planned_action`。若该行为由测试运行器负责，或当前 fixture 无法触发，应基于来源将其标记为 `not_applicable` 并说明理由。相关 capability 与 risk 项的适用性必须保持一致，不得一边标记适用、一边以运行器代管为由留空。
13. 本轮执行器只支持已启动的本地 Workboard fixture。每条用例的 `execution_requirements.environment.app_url` 必须为 `http://127.0.0.1:4173`，`case_timeout_seconds` 必须为 1 至 900 的整数，`server_state_at_start` 若提供必须为 `running`。不要生成 stopped-server 用例。

## 机器验证契约（必须遵守）

独立验证器按文件名和字段读取产物。不要自行发明等价字段名。使用以下精确路径和键名：

1. 每个数据集输出一个 JSONL，文件名由数据集 ID 决定，例如 `wb-core.jsonl`；另输出对应 Manifest，文件名必须以 `.manifest.json` 结尾，例如 `wb-core.manifest.json`。
2. `SUITE-MANIFEST.json` 必须包含非空字符串 `suite_id`、`version`、`built_at`、`evaluation_target`，以及 `case_count`、`quality_status`、`execution_status`、`coverage`。不要用 `created_at` 替代 `built_at`。
3. `SUITE-MANIFEST.json.datasets` 中每个数据集对象必须包含 `dataset_id`、`purpose`、`quality_status`、`execution_status`、`case_count`、`jsonl` 和 `manifest`。其中 `jsonl`、`manifest` 是相对套件目录的实际文件路径；不要使用 `path` 或 `manifest_path` 代替。
4. 输出唯一的 `coverage-matrix.json`。顶层必须包含 `suite_id`、`version`、非空 `items` 和 `dimensions`。每个 dimension 汇总对象必须包含 `dimension`、`total`、`covered`、`coverage_rate`、`uncovered`。其中 total 只统计 `applicability=applicable` 的项目；covered 只统计被至少一条 `quality_status=candidate` 用例覆盖的项目；uncovered 使用字符串数组，元素格式为 `<coverage_item_id> <value>`。
5. 覆盖项 `items` 必须包含唯一的 `coverage_item_id`、`dimension`、`value`、`applicability`。可选状态仅为 `applicable`、`not_applicable`、`needs_info`。非 applicable 项必须提供非空 `notes`，且不得被任何用例的 `coverage_tags` 引用。若某项只有 needs_info 用例涉及，不得把它标成已覆盖；将该项标记为 `needs_info`，从用例 coverage_tags 中移除该项，并在套件 gap_priorities 中记录对应缺口。
6. `SUITE-MANIFEST.json.coverage.dimensions` 与 `coverage-matrix.json.dimensions` 必须使用相同的维度集合和汇总值。两处 `uncovered` 均使用 `<coverage_item_id> <value>` 格式。每个未覆盖的 applicable 项都必须在 `coverage.gap_priorities` 中有唯一记录，且 `gap_id` 必须等于 `coverage_item_id`，并提供 `priority`、`reason`、`planned_action`。
7. `coverage-matrix.json.version` 必须等于 `SUITE-MANIFEST.json.version`。不要用 `suite_version` 替代 `version`。
8. 用例覆盖统计以正式 JSONL 中的 `coverage_tags` 为准。只有 candidate 用例才计入 fully covered；needs_info 用例不得让覆盖率虚高。


## 输出

在 `artifacts/webapp-testing-builder-output/` 中交付：

- 一个或多个符合当前 Dataset Schema 的 JSONL 数据集。
- 对应的数据集 Manifest。
- 能力和场景覆盖矩阵。
- 来源映射、假设和信息缺口。
- 质量审查报告。
- 报告模板。

输出数量、数据集划分和用例分布由你决定并论证。不要手工预设用例列表，不要把任务说明本身当作正式评测用例。
