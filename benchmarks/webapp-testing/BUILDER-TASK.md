# Builder 生产任务：webapp-testing

请使用 `evaluation-dataset-builder` Skill。读取 `artifacts/webapp-testing-builder-input/` 中的全部资产。该目录包含 `assets/public/`、`fixtures/workboard/`，以及从 Anthropic 固定 commit `2c5958ecac7cee2b583967a2c4981d0f4a75c579` 检出的完整 `upstream-skill/` 目录。必须阅读上游 `SKILL.md`、脚本、示例和许可证，不得只依赖能力摘要。基于这些输入，为 Anthropic `webapp-testing` Skill 构建可执行、可判定、可追溯的评测套件。

## 执行协议（强制，优先于默认工作习惯）

本任务采用一次规划、一次成稿、一次集中审查、局部修正的生产路径。目标是把模型调用用于业务理解、场景设计和判定质量，而不是让模型在运行期间临时开发和调试文档生成工具。

1. **一次性读取与建模**：按资产清单读取全部必需输入。先形成精简的事实/规则/能力/风险/来源索引和信息缺口，不要反复输出或复制整份源材料。对同一文件，除非发现具体冲突或定位问题，不得无理由重复通读。
2. **先定结构再写产物**：在创建正式文件前，一次性确定数据集划分、覆盖项 ID、用例 ID、文件清单、Manifest 关系和质量状态规则。先核对计划与本任务的机器验证契约，再开始写入。
3. **直接生成最终文件**：直接在目标输出目录创建 JSONL、Manifest、覆盖矩阵、来源映射和报告。不得创建临时 Python/JavaScript/Shell 程序、代码生成器或自定义校验器来拼装、转换、统计或反复重写交付物。不得把临时脚本、调试日志、草稿或中间版本放入正式输出目录。若当前工具确实无法直接创建或更新所需文件，应明确报告阻断，不得临时发明另一套生成流水线。
4. **一次集中质量审查**：全部正式文件写完后，进行一次统一审查，覆盖 Schema/字段契约、来源原文与定位、业务规则依据、用例可执行性、判定 PASS/FAIL/UNKNOWN、覆盖统计、质量状态和文件引用一致性。按审查清单列出具体缺陷，不要仅凭主观自评宣称通过。
5. **仅做有证据的局部修正**：只修改审查发现且能明确定位的缺陷文件或记录。禁止因局部问题重新生成全部数据集、覆盖矩阵和报告；禁止通过反复改写报告或统计口径掩盖用例缺陷。修正后只复核受影响字段及其依赖关系。
6. **明确停止条件**：完成一次集中审查及必要的局部修正后即停止。仍无法确认的事项标记为 `needs_info` 或 `UNKNOWN`，并记录证据缺口。不得为了让所有指标看起来完整而继续循环生成。
7. **保持质量优先**：上述步骤不是压缩分析深度或降低质量标准。不得减少必要的资产阅读、来源核验、业务推理、风险分析或用例判定要求；只消除重复读取、临时造工具、重复全量生成和无依据的循环修补。


## 评测目标

评测该 Skill 能否理解测试目标，使用 Playwright 正确操作 Web 应用，验证公开业务规则，发现真实 UI 行为与规则之间的差异，并提供充分的可复核证据。

## 生产要求

1. 先解析全部输入资产，建立来源、事实、规则、能力、风险和信息缺口。
2. 规划覆盖范围和数据集划分。数据集数量和用例数量由你根据资产、目标能力、覆盖缺口、风险和执行成本决定。必须推荐数量并解释理由，不得按预设数量凑数。
3. 仅在能力确实需要跨用户消息承接上下文或跨轮业务状态连续变化时设计多轮任务。只有当 `user_input` 是至少包含两条独立 `{turn_id, content}` 消息的数组，并且预期行为依赖前一条用户消息时，才可将 `scenario_bucket` 标记为 `multi_turn`。一条消息中包含多个点击、查询或状态变更步骤，不属于多轮对话。若输入资产不支持真正的跨消息能力，不得为了试点数量强行生成多轮用例。
4. 每条正式用例必须包含可执行任务、目标能力、前置状态、允许动作、预期行为、禁止行为、证据要求和 case-level grading contract。 每条 `source_refs` 必须包含可定位的 `title`、`locator` 和 `quoted_evidence`；`quoted_evidence` 必须是对应来源中的原文连续片段，不得写摘要、转述或自拟引文。
5. 判定契约必须适配 Web 应用测试能力，并明确 PASS、FAIL 和 UNKNOWN 条件。应区分页面交互、业务状态、缺陷发现和证据完整性。
6. 业务预期以 `assets/public/business-rules.md` 为准。应用源代码是被测实现，不是业务规则的替代来源。代码检查不能替代真实页面交互。
7. 将所有合成资产标记为 SYNTHETIC。不得编造生产缺陷、真实用户、真实执行轨迹或外部来源。
8. 若资产不能支持可靠判定，标记 `needs_info` 或 `UNKNOWN`，不要补造预期结果。
9. 用例质量状态保持 `candidate` 或 `needs_info`。本次 Builder 生产不会执行被测 Skill，因此每条用例的 `execution_requirements.status`、每个数据集 Manifest 和套件 Manifest 的 `execution_status` 必须统一标记为 `NOT_RUN`。不得使用 `DESIGN_ONLY`、`READY_TO_RUN` 或 `EXECUTION_VERIFIED`。
10. 不要读取或推断隐藏运行配置、Gold Oracle 或独立验证器内容。
11. 交付前清理 `__pycache__`、`*.pyc` 和临时文件。不要把缓存或临时文件放入最终套件。
12. 覆盖矩阵中的每个 `applicable` capability/risk 项必须由至少一条用例覆盖，或在 `SUITE-MANIFEST.json.coverage.gap_priorities` 中记录 `gap_id`（必须等于对应的 `coverage_item_id`）、`priority`、`reason` 和 `planned_action`。若该行为由测试运行器负责，或当前 fixture 无法触发，应基于来源将其标记为 `not_applicable` 并说明理由。相关 capability 与 risk 项的适用性必须保持一致，不得一边标记适用、一边以运行器代管为由留空。
13. 本轮执行器只支持已启动的本地 Workboard fixture。每条用例的 `execution_requirements.environment.app_url` 必须为 `http://127.0.0.1:4173`，`case_timeout_seconds` 必须为 1 至 900 的整数。若提供 `execution_requirements.environment.server_state_at_start`，其值必须严格等于字符串 `running`。若提供 `execution_requirements.initial_state.server_state`，其值也必须严格等于字符串 `running`，不得附加括号说明、中文解释或其他文字；补充说明请写入独立的 `notes` 字段或其他非状态字段。不要生成 stopped-server 用例。
14. 运行器在每条用例开始前负责执行一次 `POST /api/reset`，并确认初始数据和摘要。被测 Skill 不得调用 `POST /api/reset`，也不得通过其他方式重置应用状态。每条用例使用独立的 Workboard 服务进程；用例结束后运行器会关闭该服务进程，不需要也不得执行第二次 reset。每条用例的 `reset_plan` 必须准确描述这一生命周期；`forbidden_behavior` 必须明确禁止 Skill 调用 reset。

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
9. 质量状态必须按交付层级汇总：只要套件范围内存在未解决的权威依据缺口、`needs_info` 用例，或 `coverage-matrix.json` 中 `applicability=needs_info` 的覆盖项，套件 Manifest 的 `quality_status` 必须为 `needs_info`。数据集范围内存在未解决的 `needs_info` 用例或覆盖缺口时，该数据集 Manifest 的 `quality_status` 必须为 `needs_info`。只有不存在上述未解决事项时，才可将对应层级标记为 `candidate`；不得以大多数用例为 candidate 为由覆盖少数未解决缺口。 例如，只要 `BR-09-RF` 仍为 `needs_info`，即使其余 14 条用例均为 `candidate`，套件 Manifest 也必须为 `needs_info`。
10. `SUITE-MANIFEST.json.source_map_json` 必须指向套件目录中的唯一来源映射文件，文件名必须严格为 `source-map.json`。只允许输出这一份来源映射文件；不得另行输出 `SOURCE-MAP.json` 或任何仅大小写不同的副本。来源映射可以使用 `sources` 数组，或使用 `source_registry` 与 `files` 两个数组。后者必须为每个 `source_id` 提供 `title`、`source_type`、`path`，并在 `files` 中提供相同路径、SHA-256 和对应的 `source_ids`。独立验证器按 Manifest 路径定位文件，独立核对来源文件哈希，并将每条用例的 `quoted_evidence` 直接与映射的可信来源文件比对；不得仅信任 Builder 自报的引文或依赖文件名大小写。


## 输出

在 `artifacts/webapp-testing-builder-output/` 中交付：

- 一个或多个符合当前 Dataset Schema 的 JSONL 数据集。
- 对应的数据集 Manifest。
- 能力和场景覆盖矩阵。
- 来源映射、假设和信息缺口。
- 质量审查报告。
- 报告模板。

输出数量、数据集划分和用例分布由你决定并论证。不要手工预设用例列表，不要把任务说明本身当作正式评测用例。

## 来源定位格式补充（强制）

为保证每条来源引用可以脱离上下文独立追溯，所有 case-level `source_refs[].locator` 以及 `source-map.json` 中的 `locators[].locator`，必须同时包含**来源文件名和章节/行号定位**。统一格式：

`<相对于输入资产根目录的文件路径>#<章节标题、规则编号或行号>`

示例：
- `assets/public/application-overview.md#§3 初始数据 表`
- `assets/public/business-rules.md#BR-01 任务摘要`
- `upstream-skill/SKILL.md#L9`

不得只填写 `§3 初始数据 表`、`BR-01`、`第 3 节` 等脱离文件名的定位。来源文件路径必须与 `source-map.json` 中该 source_id 对应的 path 完全一致；引文仍须是该文件中的连续原文。不得为了通过验证而修改、缩短或转述引文。

每条 `quoted_evidence` 还必须是**有实质内容的连续原文片段**，不能只引用章节标题、列表引导语或短标签（例如 `首页包含：`）。按 NFKC 规范化、大小写折叠并合并空白后，引文长度必须至少为 6 个字符；优先引用能够直接支撑该用例事实或预期行为的完整句子/条款。若某个标题或短语不足以支撑结论，应引用其下方的具体条款或段落；不得拼接不连续文本、补写原文中不存在的内容，也不得为了满足长度要求而扩大到与结论无关的文字。无法找到充分原文时，应移除该来源引用或将依赖该证据的结论标记为 `needs_info`。
