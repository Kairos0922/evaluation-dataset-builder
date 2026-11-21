# Evaluation Dataset Builder：第二轮正式产物质量、试运行与成本审查

**审查对象：** Evaluation Dataset Builder 正式生成的 `webapp-testing-workboard-suite` 1.0.0  
**正式生产运行：** [44901698634](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44901698634)  
**审查范围：** Builder 输出质量、独立结构验证、三条真实消费试运行、独立判定、生成过程成本与可优化项。  
**不计入 Builder 收益：** 目标 Skill 的表现、Runner/CI 工程收益、Oracle 工程覆盖或基础设施工作。  
**结论状态：** 结构验证 PASS；质量状态 needs_info；三条 Pilot 的独立判定为 1 PASS / 2 FAIL。不得将结构验证 PASS 解释为套件质量 PASS。

## 1. 不可变产物与独立结构验证

| 项目 | 结果 |
|---|---|
| Builder 生产运行 | `44901698634` |
| Builder 正式输出 artifact | `14706494963` |
| 独立验证 artifact | `14706599576` |
| Builder DSH Skill 调用 | 1 次，DSH exit 0，final reason `completed` |
| DSH Trace | 988 个事件；187 条模型 usage 记录 |
| 正式数据集 | 1 个：`wb-core` |
| 正式用例 | 15 条；14 candidate、1 needs_info |
| 正式交付文件 | 9 个 |
| Schema 错误 | 0 |
| Source evidence | 86/86 条引用核验通过 |
| Builder 输入完整性 | 18/18 文件 SHA-256 核验通过；其中 6 个上游 Skill 文件 |
| 独立验证 | PASS |

本轮 Validator 确认：用例及 Manifest 符合当前 Schema；来源身份、路径、哈希和原文引用能够从冻结输入中复核；覆盖矩阵的声明与用例标签一致。输入包不包含正式评测用例或 Gold Oracle。

### 覆盖与质量状态

| 覆盖维度 | Applicable | Covered | 覆盖率 |
|---|---:|---:|---:|
| Capability | 16 | 16 | 100% |
| Business rule | 11 | 11 | 100% |
| Risk | 15 | 15 | 100% |
| Scenario | 10 | 10 | 100% |
| **合计** | **52** | **52** | **100%** |

覆盖全集共 64 项：52 项 applicable、11 项 not_applicable、1 项 needs_info。唯一未决项为 `BR-09-RF`，原因是冻结资产没有受支持的请求失败注入端点/契约。Builder 将 WC-15 标记为 needs_info，并将数据集与套件 Manifest 保持为 `quality_status=needs_info`、`execution_status=NOT_RUN`。这属于正确保留不确定性，不应为了覆盖率而臆造故障注入方式。

### Builder 输出哈希

以下 SHA-256 针对不可变输出目录中的正式文件。它们用于锁定本轮被审查产物，不能与其他 Builder 运行的文件混用。

| 文件 | SHA-256 |
|---|---|
| `wb-core.jsonl` | `758c7528944bfcacb546ee9f860a87f853e093cd7e12dbbb20f419c07143c1c5` |
| `wb-core.manifest.json` | `e5d6d1cbf705d41635a48f99b972fb52b398fd37850ae58853ae8949ae29a329` |
| `SUITE-MANIFEST.json` | `52057651c7a47b403025905b90eab4231752df7c0bfffd12b362fdb09a2d2b47` |
| `coverage-matrix.json` | `ae2557e6d3e934e1c49bd47ffef76df9e37ab0c34fae75de64ed8050b8dce692` |
| `source-map.json` | `4730869148bec84a6f03ba9f1e4fe3a1bb5d8d4bb9b5572bd131dac71f966417` |
| `QUALITY-REVIEW.md` | `545a0193d3e739ac75e6e741c852db5b8e27a136896b373fa00d567ab09d89b2` |
| `README.md` | `3555470b4e29f29740ade7981e46b590f835b9223b488fbe05d11ac69616fcc4` |
| `REPORT-TEMPLATE.md` | `32fa05388de11967e7a5648d7446a0b5803bec1aebdc41a1c722522eb6e62284` |
| `ASSUMPTIONS-AND-GAPS.md` | `5c16fae18d96c32c11f11a8393d8f4c7fe41345af2959d4f3c28060d9bc2f26a` |

## 2. 判定主体一致性复核

本轮 Builder Skill、判定指南和生产任务都已明确：本实验评价的是执行测试的 webapp-testing Skill，不是 Workboard 应用本身。Workboard 的异常行为是 Skill 应发现和报告的观察对象；准确发现并报告应用违反规则，应计为 Skill 的正确表现。

WC-03 的契约明确区分：应用实际返回 0 行是 BR-02 的被观察偏差；Skill 如实指出偏差并报告 BR-02 FAIL 是 Skill 的正确表现；观察到 0 行却报告 PASS 才是 Skill 的判定错误。

**更严格的通用语义 lint 对不可变 Round 2 JSONL 进行了二次检查，推翻了第一轮人工审阅“未发现同类矛盾”的结论。** 最新正式 Validator 在不修改 Builder 产物的情况下，发现 3 个 grading criterion 的 fail 条件直接把应用结果偏差当作 Skill 失败。证据来自 [Archived Builder Artifact validation run 44909794116](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44909794116)，输入是原始 Builder artifact `14706494963`。

| Case / criterion | 原始 fail 条件 | 冲突证据 | 问题 |
|---|---|---|---|
| WC-09 / C3-OBSERVE-TITLE | “优先级/状态不一致” | Case 的 `reference_outcome` 明确规定：若独立观察发现优先级不是 Low、状态不是 Open，Skill 应如实报告对应 BR-05/BR-06/BR-01 FAIL，并提供实际值。 | 未说明是 Skill 报告值与 DOM/POST 不一致，还是应用实际值偏离预期。会把正确报告应用偏差误判为 Skill 失败。 |
| WC-12 / C3-STATUS-SEQUENCE | “状态/按钮序列与 DOM 不一致” | Case 的 `wrong-transition` 分支明确规定：若应用状态/按钮没有按预期推进，Skill 应报告 BR-07 FAIL，指出实际步骤和证据。 | 应判 Skill 是否准确报告实际状态，而不是把应用状态不符合预期直接作为 Skill 失败。 |
| WC-12 / C4-SUMMARY-SYNC | “摘要值与 DOM 不一致” | Case 的通过条件及 `stale-summary` 分支要求：若摘要不同步，Skill 应明确记录偏差、实际值并报告 FAIL。 | 与“摘要值与 DOM 不一致即 criterion FAIL”的条件直接冲突。 |

这 3 项是 **Builder 输出的判定契约缺陷**，不是目标 Skill 的运行失败，也不是 Oracle 的解析缺陷。修复方向是将 fail 条件写成“Skill 报告的值与同一步 DOM/响应不一致”“Skill 未指出摘要未同步”或“Skill 将观察到的偏差错误报告为 PASS”。当应用偏离预期但 Skill 准确报告时，Skill 应获得表现 PASS。

当前 validator 的语义 lint 是保守的规则检查，不是完整自然语言理解器。它按并列分句检查裸应用结果条件，已对当前不可变产物检出上述 3 条。该检查不证明未来产物无其他语义问题；人工复核和实际证据仍然必要。

## 3. 原始 Builder 产物的独立 Pilot 重判

重判使用原始 Builder artifact `14706494963` 和三份原始 Pilot 证据，没有再次调用 Builder 或目标 Skill。

- 重判工作流：[44908652144](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44908652144)
- 重判 artifact：`14709295258`（`webapp-testing-oracle-adjudication-corrected`）
- 判定 JSON SHA-256：`db4f6ecec37c159746c8bc9bdedaca75723f876cb8bcde8a90332e39a008969e`
- 重判工作流状态：成功生成并归档判定报告；判定报告自身结论仍为 FAIL。

### 逐例结果

| Builder 用例 | 脚本执行次数 / 预算 | 应用写操作 / 预算 | 业务表现 | 契约判定 | 归因 |
|---|---:|---:|---|---|---|
| WC-03 搜索大小写不敏感 | 1 / 1 | 0 / 0 | EXPECTED_VIOLATION_DETECTED | PASS | Skill 正确发现小写查询未返回应匹配标题，并如实报告 FAIL。 |
| WC-11 确认删除 | 2 / 1 | 1 / 1 | PASS | FAIL | Skill 首次脚本执行因目标行定位失败中止，随后编辑脚本并第二次执行。虽然最终仅确认删除 WB-105，且其他任务与摘要正确，但违反一次脚本执行和 no_retry 契约。 |
| WC-12 三步状态循环 | 1 / 1 | 1 / 3 | FAIL | FAIL | Builder 预期三步状态循环，实际仅完成 Open → In progress。脚本随后因 `NameError: initial_info is not defined` 中止。 |

### 关键证据及解释

**WC-03：** 原始 DSH Trace 中，测试脚本通过长 Bash heredoc 写入并执行；该 Trace 命令输入被截断，但同一 callId 的工具结果保留了 `[step]`、`=== SUMMARY ===` 和退出码。Oracle 将此验证为一次真实执行，而不是因截断错误计为零。搜索结果为 0 行，Skill 报告 BR-02 FAIL，符合应用 mutant 的预期违规。此例对 Builder 的正面证据是：生成的契约能够区分应用缺陷与 Skill 的正确缺陷报告。

**WC-11：** Trace 中两次直接运行 `wc11_delete_confirm_test.py`，事件索引分别为 43 与 79。第一次因无法定位目标行而退出，未产生写操作；第二次运行后产生一次 DELETE `/api/tasks/WB-105`，HTTP 200。最终任务数为 4，摘要为 4/2/1/1，其他四条任务保留。业务结果正确不抵消重复执行违反 Builder 明确预算的事实。此结果说明用例预算具有诊断能力，而不是 Builder 用例本身要求重复运行。

**WC-12：** Trace 仅显示一次 `python3 test_wc12.py`。独立解析出的 Builder 预期序列为 Open → In progress → Done → Open；服务端审计实际只有一次 PATCH，终态摘要为 5/1/3/1，而完整循环预期摘要为 5/2/2/1。运行日志明确记录脚本在第一步后因变量名错误中止。此处是目标 Skill 生成并执行的测试脚本错误，不是 Builder 对三步状态循环的错误描述。

### 重判汇总

| 指标 | 结果 |
|---|---:|
| Pilot cases | 3 |
| Oracle contract verdict PASS | 1 |
| Oracle contract verdict FAIL | 2 |
| Business behavior EXPECTED_VIOLATION_DETECTED | 1 |
| Business behavior PASS | 1 |
| Business behavior FAIL | 1 |

不能把 1/3 PASS 推广为整套 15 条用例已通过。其余 12 条没有进行真实 Pilot。本报告也不把 WC-11/WC-12 的目标 Skill 失败归因为 Builder 缺陷。

## 4. Builder 生产成本与调用结构

本轮 DSH 用量：

| 指标 | Builder 正式生产 |
|---|---:|
| Input tokens | 120,724 |
| Output tokens | 297,681 |
| Cache-read tokens | 52,279,936 |
| Cache-write tokens | 0 |
| **Total tokens** | **52,698,341** |
| 模型 usage 步骤 | 187 |
| 工具调用 | 210 |
| Bash / Edit / Read / Write / Skill | 114 / 54 / 32 / 9 / 1 |

另有独立的模型连通性探测，使用 5,610 tokens；它不是 Builder 正式生产调用，不计入 52,698,341。三条下游 Pilot 分别使用：
- WC-03：350,721 tokens；
- WC-11：631,600 tokens；
- WC-12：1,008,585 tokens；
- 三条合计：1,990,906 tokens。

以上为 Trace token telemetry，不是美元账单。没有取得 DeepSeek 计费账单或可核验 USD 单价，因此 **USD 成本未知**。Cache-read token 的实际计价可能与普通 input token 不同，不能用总 Token 数直接换算美元。

## 5. 生成效率审计：已有明确的可减少返工

本次调用结构表明，生成过程并非一次写入后少量修订：

1. 15 条用例先分多次写入 JSONL，随后又分 15 次单独编辑补齐 schema 必填的 `scenario_bucket`。这部分可以通过先完成 Schema 字段规划、一次生成完整记录来消除。
2. JSONL 共发生 35 次编辑。除最初的逐条用例写入外，仍有一批后续局部补丁，包括 scenario_bucket、criterion 修正、预算说明等。
3. `source-map.json` 被重复读取 5 次、编辑 5 次。来源注册表与引用映射可以先定稿，再用一轮确定性检查验证。
4. 共执行 114 次 Bash 工具调用。多个命令分别检查 JSON、覆盖、README、来源、Manifest、预算和状态词；其中一部分重复检查可以合并为一轮预先存在、经过审查的最终校验。

以上是操作次数的证据，不等于证明每次调用都无价值。部分局部修复确实解决了 schema、评分语义、来源版本和 Manifest 一致性问题。效率优化不能删除必要审查，也不能减少来源阅读、覆盖或判定质量。

### 下一次 Builder 生产应采用的改进

- **写入前冻结完整结构：** 在第一次写正式 JSONL 前完成 case 字段、枚举、scenario_bucket、evaluation_subject、预算、来源引用和 ID 规划。
- **按数据集一次生成权威 JSONL：** 15 条记录在首次写入时即满足 Schema，不再逐条追加字段补丁。
- **来源映射一次定稿：** 固定 source registry、locator 和版本后，再生成 case refs；将来源身份、哈希、locator、引用原文检查集中执行。
- **合并确定性检查：** 复用仓库已有验证器，避免在模型会话里反复进行相同的 jq/grep 检查。最终 Validator 仍须独立于 Builder 运行。
- **保留集中语义审查：** 逐项核对 subject、case-level PASS/FAIL 和 criterion-level PASS/FAIL。不得通过减少审查来减少 Token。
- **不盲目加大用例数量：** 当前 15 条用例、一个数据集的覆盖已完整覆盖 52 个 applicable 覆盖项。新增用例必须提供增量覆盖或新的诊断价值。

- 最新补充 Validator 检查：[run 44909794116](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44909794116)，使用 Round 2 不可变 artifact `14706494963`；因上述 3 条语义问题拒绝产物。输入哈希、DSH 调用 Trace 和来源校验仍通过。该失败是预期质量拒绝，不是 Runner/下载故障。

## 6. Builder 质量结论

本轮可支持的结论：
- Builder 生成了结构完整、来源可追溯、覆盖声明与数据一致的 15 条用例。
- 当前正式产物正确保留 1 项 needs_info，没有伪造失败注入能力。
- WC-03 的判定主体区分正确，但通用语义 lint 对 Round 2 额外发现 3 条同类评分契约缺陷：WC-09 C3、WC-12 C3、WC-12 C4。
- WC-03/11/12 的三条试运行显示，用例对搜索偏差、重复脚本执行和多步状态循环具有可观察、可判定的契约。
- 三条真实运行中，只有 WC-03 的 Skill 表现通过；WC-11 的最终业务结果正确但执行契约违规；WC-12 的目标 Skill 脚本中止。

尚不能支持的结论：
- 不能宣称 15 条用例整体执行通过；实际只有 3 条 Pilot。
- 不能将目标 Skill 的 2 条 FAIL 当作 Builder 的 2 个缺陷。
- 不能将 Validator PASS 或 Builder 自评的维度分数解释为独立质量批准。
- 不能根据一次 Builder 生产推断跨领域泛化、重复生成稳定性或统计质量。
- 不能报告美元成本。

**当前质量处置：** `needs_info`，不是 Approved。  
**下一步建议：** 暂停新的付费生产和额外 Skill Pilot；先将上述生成返工点转化为 Builder 任务/回归约束，并完善通用 grading-subject 语义门禁。只有在这两项离线改进完成且预计有明确增量质量收益时，再决定是否进行新一轮 Builder 正式生产。旧 Builder 与 Pilot artifact 必须保持不可变。

## 7. 证据链接

- 新 Builder 正式生产：[run 44901698634](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44901698634)
- 独立结构验证 artifact：`14706599576`
- 原始 Builder 输出 artifact：`14706494963`
- 原始三条 Pilot artifacts：WC-03 `14706634551`；WC-11 `14706733694`；WC-12 `14707142025`
- 离线重新判定：[run 44908652144](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44908652144)
- 重新判定 artifact：`14709295258`
- PR #38：[Draft/Open](https://github.com/Kairos0922/evaluation-dataset-builder/pull/38)
