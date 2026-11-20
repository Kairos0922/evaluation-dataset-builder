# webapp-testing 双 Skill 实验契约

**状态：** 当前已完成三用例 Pilot 阶段：P0 资产冻结 PASS；P1 Builder 正式生产 PASS；P2 对真实 Builder 产物的独立验证 PASS；P3 三条真实 Skill Pilot 已执行；P4 修正后的独立 Gold Oracle 对三条用例的业务行为判定为 3/3 PASS。P5 已完成历史 DSH Trace 成本审计、Runner Token/步骤/时间预算控制，以及剩余 11 个 Builder 用例语义角色的离线 Selector/Gold Oracle 扩展。最新代码验证 run 44756938809 通过 185 项离线测试、Oracle 自检和产物审计；Runner preflight run 44756928738 通过。**新增 11 个角色只表示代码路径已覆盖并经合成证据自测，不表示 11 条真实 Builder 用例已执行。它们仍全部为 NOT_RUN。** 历史 WB-CORE-14 的实际 DSH wall-clock 未被旧 Runner 单独记录，其 240 秒预算合规状态为 UNKNOWN。**本状态仍只代表三用例 Pilot 真实执行完成，不代表 14 条用例全部执行，也不代表完成 A0/A1、B0/B1 全交叉回归。** PR 默认不触发付费模型调用；后续付费执行须显式授权。  
**实验对象：** Anthropic `webapp-testing`  
**Builder：** Evaluation Dataset Builder `0.0.1`  
**实验运行环境：** GitHub Actions + DSH Headless  
**本文件用途：** 约束资产、生产、消费、验证、评判和回归的责任边界。本文不是评测用例集，也不替代 Builder 生成正式评测套件。

## 1. 实验目标与成功主张

本实验检验两个独立问题：

- **A：评测生产能力。** Evaluation Dataset Builder 能否从冻结的 Skill 与配套应用资产中，生成有依据、覆盖合理、可执行、可判定的评测套件。
- **B：被测能力。** 在固定宿主、工具和运行环境下，`webapp-testing` 是否能正确理解并完成 Builder 生成的 Web 应用测试任务，且提供充分证据。

只有同时具备 Builder 实际调用证据、Builder 生成产物、独立套件验证结果、被测 Skill 实际调用证据、执行证据和独立判定结果，才可将一次运行计入正式实验。

本实验不证明 Skill 在所有宿主、模型或 Web 应用上的普遍能力。结论必须限定到记录的版本和运行配置。

## 2. 不可违反的原则

1. **正式评测用例唯一生产者是 Evaluation Dataset Builder。** 人工不得直接编写、补写、挑选或改写正式 JSONL 用例。
2. 人工可以准备原始资产、应用夹具、实验约束、独立 Oracle 和验证程序。这些是 Builder 的输入或外部验证设施，不是正式评测用例。
3. Builder 的实际调用必须由 DSH Trace 证明；仅运行脚本、复制示例或手工创建 JSONL 不构成生产证据。
4. 被测 `webapp-testing` 只能消费 Builder 产出的正式任务，不得读取隐藏 Oracle、Gold 结果或独立验证器内部数据。
5. 生成的判定契约必须由 Builder 产出。独立程序只负责执行可确定的检查、验证契约质量和对照 Oracle；不得暗中替 Builder 生产或修订判定标准。
6. 评测器不得自证正确。Builder 生成的判定契约与独立 Oracle 必须交叉核验。
7. 任何人工修订都必须回到 Builder 输入资产或 Skill 规则中，通过重新调用 Builder 重新生产；不得直接修补正式用例后仍标记为 Builder 产物。
8. 所有资产、产物、运行配置和证据必须可追溯到不可变版本或内容哈希。

## 3. 角色与责任矩阵

| 角色 | 责任主体 | 允许输入 | 必须产出 | 禁止事项 |
|---|---|---|---|---|
| 资产策展者 | 实验准备流程 | 上游 Skill、应用说明/源码、公开工具说明、运行约束 | 冻结资产包及来源清单 | 手工编写正式评测用例 |
| 评测生产者 | Evaluation Dataset Builder（经 DSH 调用） | 已批准的公开资产包 | 多个数据集、用例判定契约、清单、覆盖矩阵、质量报告、来源映射 | 读取隐藏 Oracle；伪造执行记录 |
| 套件验证者 | 独立确定性验证程序 + 独立审查 | Builder 产物、公开资产、独立能力目录 | Schema、来源、覆盖、执行就绪和泄漏检查结果 | 生成或修补正式用例 |
| 评测消费者 | DSH Agent + `webapp-testing` | 已验收的正式用例、应用测试入口、授权工具 | Playwright 脚本、真实执行结果和证据 | 读取 Gold Oracle 或修改评测标准 |
| 执行证据采集者 | Actions 采集步骤 | DSH Trace、脚本输出、浏览器事件、服务端审计 | 不可变证据清单及哈希 | 将 Agent 自述当作实际状态 |
| 判定契约生产者 | Evaluation Dataset Builder | 公开业务/应用资产 | 每条用例中的 `grading` 判定契约 | 输出未经要求的独立评分器服务 |
| 判定执行者 | 独立运行器 | Builder 的 `grading` 契约、执行证据 | 契约判定结果（PASS/FAIL/UNKNOWN） | 更改契约以迎合实际结果 |
| Oracle 审核者 | 独立 Gold Oracle 程序 | 隐藏预期行为、服务端状态和审计记录 | Oracle 结果及与契约判定的差异 | 将 Oracle 内容暴露给 Builder 或被测 Skill |
| 回归执行者 | GitHub Actions | 冻结版本、已验收套件、固定运行配置 | 运行报告、成本、重复性与版本对比 | 无记录地改变运行因子 |

### 3.1 “Evaluator”的准确含义

当前 Builder 的数据集 Schema 将判定规则放在每条用例的 `grading` 字段中；Skill 规范明确将其定义为用例内部判定契约，不要求另建独立评分器产品、注册表或运行服务。因此，本实验中的“Builder 生成的 Evaluator”首先指**Builder 为每条用例生成的判定契约**。若未来需要可执行判定程序，应作为独立的运行适配器实现，并且只能解释/执行该契约，不得另行发明判定规则。

Manifest 的 `grader_refs` 是历史兼容字段，新数据集不应依赖它。

## 4. 资产边界与冻结要求

### 4.1 Builder 可见的公开输入资产

公开输入资产至少包括：

- `webapp-testing` 上游仓库地址、固定 commit、Skill 目录文件、逐文件 SHA-256、许可证及来源记录。
- Skill 的完整 `SKILL.md`、脚本、示例和其引用的资源。
- 测试应用的功能说明、页面/交互说明、公开业务规则、接口约定和启动方式。
- 测试应用源代码与依赖锁文件，用于理解被测系统和复现环境。
- DSH、Node、Python、Playwright、浏览器和 Actions runner 的固定版本/配置说明。
- 工具可用性、权限边界、网络边界、副作用限制、资源与费用上限。
- 公开的能力范围目录及来源映射要求。

Builder 可见资产必须具有稳定的 `asset_id`、来源、版本/commit、内容哈希、采集时间和可定位路径。

### 4.2 仅供独立验证者使用的隐藏资产

以下内容不得进入 Builder 的输入目录，也不得被 DSH Agent 读取：

- Gold Oracle 的预期状态、隐藏断言和答案数据。
- 用于校验误报/漏报的隐藏应用状态标签。
- 隐藏回归任务的判定结果。
- 独立验证器内部阈值和用于防止针对性优化的留出信息。

隐藏 Oracle 应从独立的、预先冻结的应用行为规范和确定性服务端状态构建，而不是从 Builder 生成的用例反向生成。它可验证 Builder 用例引用的能力、操作和预期终态是否符合真实夹具行为，但不得替代 Builder 生成用例。

GitHub Actions 应将公开输入与隐藏 Oracle 放在不同目录/权限边界。执行 DSH 的工作目录不得挂载 Oracle 路径；Oracle 步骤应在 DSH 进程结束后独立运行。

### 4.3 不得进入实验的资产

- 真实生产客户数据、凭证、访问令牌和个人信息。
- 未经授权的线上系统写操作。
- 未冻结版本或来源不明的 Skill 文件。
- 无法复现且没有记录的外部依赖。

首轮仅使用合成或明确脱敏的测试资产。

## 5. Builder 生产契约

### 5.1 调用要求

GitHub Actions 必须安装固定版本 DSH，在项目级 Skill 目录加载 Builder，并通过 DSH Headless 实际触发 `evaluation-dataset-builder`。任务指令必须明确引用已冻结的输入资产目录，并要求按 Skill 工作流完成资产解析、能力建模、覆盖规划、缺口驱动生成、判定契约设计和质量审查。

不得在 Actions 中用人工编写的 JSONL、预制用例或独立脚本替代 Builder。独立脚本只可做格式验证、哈希、证据采集和 Oracle 检查。

### 5.2 生产产物

正式产物至少应包含（具体数量和数据集划分由 Builder 根据资产决定并解释）：

- 一个或多个符合现有 `dataset-schema.json` 的 JSONL 数据集。
- 每个数据集对应的 `dataset-manifest-schema.json` 清单。
- 能力/场景覆盖矩阵及覆盖缺口。
- 来源映射、假设、冲突和信息缺口记录。
- 质量审查报告与质量状态。
- 每条用例内的判定契约（`grading`）。
- 报告模板或报告结构。

不得预先规定正式用例数量、各类用例配额或多轮任务比例。Builder 必须根据资产与能力覆盖推荐数量并说明依据。若输入资产不足，应标记 `needs_info` 或 `UNKNOWN`，不得通过编造规则补齐。

### 5.3 生产真实性证据

每次 Builder 生产必须归档：

- DSH session/run ID、候选 commit SHA、Builder Skill tree SHA。
- Trace 中实际调用 Builder Skill 的事件。
- 输入资产清单及哈希。
- 完整原始输出和最终产物。
- Schema 校验结果、文件 SHA-256、产物清单。
- Builder 调用成本和耗时（若宿主可观察）。

没有 Builder Skill 调用事件或产物无法与该次调用对应时，生产门禁失败。

## 6. 套件独立验收契约

独立验收不替 Builder 生成内容。它检查：

1. 所有数据集、用例和清单符合仓库当前 Schema。
2. 用例 ID 唯一，清单数量与实际用例数一致，引用可解析。
3. 每条用例可追溯到公开输入资产，推断/合成内容明确标记。
4. 每条用例的目标能力、前置条件、允许动作、预期行为和证据要求相互一致。
5. 每条可执行用例具有可复现的环境、权限、步骤、预期终态、断言、禁止副作用和清理方案。
6. `grading` 的方法适合目标行为；通过、失败和 UNKNOWN 条件明确且可观察。
7. 用例覆盖映射到预先定义的能力范围目录；未覆盖和不适用项均有说明。
8. 没有通过人工改写正式用例来弥补 Builder 缺陷。
9. 被测 Skill 不会获得隐藏 Oracle、答案或隐藏集信息。
10. 数据集划分无泄漏；若声明 `heldout`，必须提供独立性检查证据。

验收结果为 PASS、FAIL 或 BLOCKED，并逐项引用证据。关键缺陷不得由平均分抵消。未通过时，应修订输入资产或 Builder，再重新调用 Builder 生产；不得直接手工修复 JSONL。

## 7. 消费与执行契约

仅当套件独立验收通过后，才允许执行被测 Skill。

- DSH Trace 必须证明 `webapp-testing` 被实际发现、加载和调用。
- Agent 必须读取 Builder 产出的任务内容；不得执行人工替代任务。
- 任务执行脚本必须由 Agent 在任务执行过程中按 Skill 指引创建/调用。预置服务夹具和独立 Oracle 脚本不算被测 Skill 的产物。
- 应用状态必须在每条用例前重置到定义的初始状态。
- 记录脚本、命令、退出码、浏览器事件、截图、服务端请求/审计日志、前后状态和清理结果。
- 将“脚本成功退出”“断言通过”“任务满足评测目标”作为不同事实记录。
- 缺少必要证据时不得推定成功；按用例契约判为 UNKNOWN 或 NOT_RUN。

## 8. 双路判定与独立 Oracle

每条已执行用例至少形成两份判定：

**A. 契约判定：** 独立判定运行器读取 Builder 生成的 `grading` 字段，依据执行证据给出 PASS、FAIL 或 UNKNOWN，并解释证据映射。

**B. Gold Oracle：** 独立 Oracle 根据隐藏预期、应用真实状态和审计日志给出参考结果。它不读取 Agent 的最终自述作为事实来源，也不依赖 Agent 自己的断言作为唯一证据。

比较两路结果，记录：

- True Pass / True Fail；
- False Pass（契约错误放行）；
- False Fail（契约错误拒绝）；
- UNKNOWN（证据不足或契约无法执行）。

Oracle 无法确定的情况应保持 UNKNOWN，不得强制归入 PASS/FAIL。契约判定与 Oracle 不一致时，先隔离该用例，不得立即将问题归因于被测 Skill；需要区分用例错误、判定契约错误、执行证据缺失和被测行为失败。

## 9. 回归与双 Skill 进化

冻结基线：Builder A0、被测 Skill B0、资产快照、应用夹具、DSH/模型/工具/浏览器配置和正式数据集。

每次进化只允许沿各自失败证据改进：

- A 侧只根据资产解析、能力覆盖、用例有效性、来源追溯、判定契约准确性和报告质量缺陷改进 Builder。
- B 侧只根据任务理解、操作正确性、同步等待、缺陷发现、证据完整性和安全边界缺陷改进 `webapp-testing`。
- A 的改动不得修改 B 的实现；B 的改动不得修改 A 的规则、数据集或 Oracle。
- 重新生产的数据集必须由新 Builder 版本真实生成，并保留输入快照和产物哈希。
- 固定回归集可用于调试；隐藏集不得用于调优，且不得向被测 Skill 暴露。
- A0/A1 与 B0/B1 交叉比较，区分 Builder 改进、被测 Skill 改进和二者交互效应。

建议的最小交叉矩阵：

| Builder | 被测 Skill | 用途 |
|---|---|---|
| A0 | B0 | 原始基线 |
| A1 | B0 | 单独测量 Builder 改进 |
| A0 | B1 | 单独测量被测 Skill 改进 |
| A1 | B1 | 测量组合效果及交互影响 |

只有固定资产、固定配置和同一评测口径下的结果才可直接比较。模型、宿主、工具或浏览器变化必须记录为实验因子，不得归因于 Skill 本身。

## 10. 指标与报告边界

不得过早合并成单一总分。至少独立报告：

### A. Builder 生产质量

- 来源提取准确性与可追溯率；
- 目标能力覆盖率（按风险/重要性加权时公开权重）；
- 用例有效率、可执行率、重复率；
- 判定契约与 Oracle 的一致性；
- False Pass、False Fail、UNKNOWN 比例；
- 产物完整性、成本与耗时。

### B. 被测 Skill 执行质量

- 任务成功率；
- 操作和状态验证正确率；
- 缺陷检出率与误报率；
- Selector/等待/交互稳健性；
- 证据完整率；
- 违反禁止行为或产生未授权副作用的次数。

### C. 实验可信度

- Builder/被测 Skill 实际调用证据完整率；
- 环境固定程度和环境漂移；
- 重复运行的判定一致性；
- 有效样本量、失败/UNKNOWN 样本量；
- 成本、耗时和 CI 基础设施失败率。

所有比率必须同时报告分子、分母和样本量。样本量不足时不得宣称统计显著或普遍泛化。重复性报告区分判定结果一致性与自然语言解释一致性。

## 11. GitHub Actions 阶段门禁

| 阶段 | 工作 | 通过条件 | 失败处理 |
|---|---|---|---|
| P0 资产冻结 | 固定上游 Skill、应用和运行配置 | 完整资产清单、哈希、运行时预检和 Builder 输入包均已由 Actions 验证 | PASS；run 42484433238 |
| P1 Builder 生产 | DSH Headless 调用 Builder | Trace 证明真实调用，正式产物可追溯 | PASS；run 44726278657，Builder artifact 14624897819 |
| P2 套件验收 | 对真实 Builder 输出执行 Schema、来源、覆盖和执行契约验证 | 独立验证器 PASS；不得手工补写用例 | PASS；run 44726278657，validator artifact 14624652990 |
| P3 B0 消费 | DSH Headless 调用 webapp-testing | 三条 Builder 用例由真实 Skill 执行并保存原始证据 | PASS；run 44726278657，Pilot artifacts 14625780995、14625492287、14625534646 |
| P4 双路判定 | 执行 Builder grading 契约并运行独立 Gold Oracle | 三条业务行为判定均 PASS，差异有证据 | 业务行为 PASS 3/3；离线重判 run 44733891829。WB-CORE-14 历史 DSH 时间预算状态 UNKNOWN |
| P5 回归报告与成本 | 固化结果、成本、环境、差异；为后续执行设置硬预算 | Trace 统计、运行预算、停止策略、剩余用例 Selector/Oracle 离线分支和自检可复核 | 离线门禁 PASS：run 44756938809（185 项测试 + Gold Oracle 自检 + 归档产物检查），runner preflight run 44756928738 PASS；11 个新增角色仅用合成证据自测；Runner 预算尚未经新的付费 DSH Pilot 实测 |

CI 运行成功不等于评测成功；依赖安装成功不等于 Skill 运行成功；Builder 产物通过 Schema 不等于评测套件有效。

## 12. 当前证据、未决事项与执行边界

### 已获得的证据

- **P0 资产冻结：** 固定上游 Skill 的完整 Git tree 和文件清单已冻结；Actions 已验证 DSH 0.2.2-rc.1、Node 24.9.0、Python 3.12.16、Playwright 1.64.1 和 Chromium 156.0.8078.4。公开输入包含 18 个文件并通过来源与哈希审计。历史 P0 run：42484433238。
- **P1 Builder 正式生产：** run 44726278657 的 Builder job 实际调用 Evaluation Dataset Builder，并生成正式数据集、Manifest、覆盖矩阵、来源映射和质量报告。Builder artifact：14624897819。
- **P2 独立套件验证：** 同一 run 的独立验证器对真实 Builder 产物 PASS，核验 Schema、来源引用和执行契约。Validator artifact：14624652990。
- **P3 真实 Skill Pilot：** WB-CORE-02、WB-CORE-12、WB-CORE-14 均由 DSH 调用上游 webapp-testing Skill 执行，原始证据分别归档为 14625780995、14625492287、14625534646。
- **P4 Gold Oracle：** 首次 3/3 FAIL 被定位为 Oracle 报告检查过度要求规则 ID 字面量，并混合原始报告与最终报告。修正后对同一批不可变 Builder/Pilot 证据离线重判，业务行为 PASS 3/3；run 44733891829。未重跑 Builder 或 Pilot。
- **成本审计：** 三条 Pilot 的累计 Trace Token Usage 为 634,679、680,321、2,625,818。WB-CORE-14 的 40 条 usage 记录是一个 DSH turn 内的 40 个模型步骤，不是 40 个对话轮次。详细分段和成本归因见 `benchmarks/reports/builder-output-offline-review-2026-11-20.md`。
- **运行器改进：** Runner 现在统计模型步骤/turn、工具调用和 Token 用量；执行期间监控并在超限时终止 DSH；实际记录 DSH 起止时间；有效 DSH wall-clock 上限不得超过 Builder 用例声明的 case timeout。离线测试覆盖预算计算、超限终止和 turn/step 口径。剩余 11 条用例的场景分类与 Oracle 缺口见 `benchmarks/reports/remaining-pilot-readiness-2026-11-20.md`。
- **CI 验证：** 最新完整 PR 验证 run [44756938809](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44756938809) 通过，执行 185 项离线测试，并通过 Gold Oracle 自检、真实 Builder 产物审计与 selector 自检。Runner preflight run [44756928738](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44756928738) 通过。该 PR run 中的 runtime-preflight、Builder production、independent-validation、resolve-pilot-matrix、webapp-testing-pilot 和 adjudicate-pilot 付费/运行阶段均为 skipped；本阶段没有发起新的 DSH 或模型调用。

### 已知限制与未决事项

- 14 条 Builder 用例中只有 3 条完成真实 Pilot；其余 11 条尚未执行。本轮三用例 Pilot 的通过结果不得推广为整套 14 条用例全部通过。
- WB-CORE-14 的旧 Runner 只记录了 `case_timeout_seconds=240` 和配置的 `dsh_timeout_seconds=1500`，没有记录 DSH 进程自己的起止时间。整个 Runner wall-clock 为 362.596 秒，超过 240 秒，但包含夹具启动和清理，因此不能据此直接断言 DSH 本身超时；历史时间预算合规状态为 UNKNOWN。
- 新 Runner 的预算监控和硬停止已通过离线测试，但尚未通过新的付费 Pilot 实测。不能把代码测试等同于真实 DSH 环境下的预算控制实证。
- **真实执行范围仍为三条 Pilot。** 其余 11 条 Builder 正式用例尚未执行，不能从离线代码测试推断它们真实通过。
- **离线 Selector 扩展：** resolve_pilot_matrix.py 增加 11 种额外语义角色，只有显式传入 --include-remaining-candidates 才会解析；默认角色集合仍严格限定为三条已验收 Pilot。分流以结构化 test_data.kind 为主条件，并要求业务规则和工作流引用交叉匹配。
- **离线 Gold Oracle 扩展：** 为初始状态、描述搜索、空搜索、状态过滤、组合过滤、可访问名称、可见标题映射、成功创建、拒绝创建、80 字符边界和删除取消增加独立判定分支。Oracle 根据服务端请求审计、前后状态和渲染 DOM 快照判定，不把 Skill 自述作为唯一事实来源。缺少关键 DOM、审计或状态证据时返回 UNKNOWN。
- **独立自测边界：** 185 项测试使用合成的审计/状态/HTML 证据验证 Oracle 分支；这些夹具不是 Builder 正式产物，也不是 webapp-testing 的真实运行，不得将自测 PASS 记入 11 条用例的执行结果。
- **DOM 证据要求：** 对 WB-CORE-07 和 WB-CORE-13，正式执行必须归档打开对话框与取消后的 HTML/DOM 快照；Oracle 需要核对语义名称、Cancel/Delete 按钮、对话框关闭状态和目标行保留。只有截图或 Skill 报告不足以证明可访问名称和对话框语义。
- 当前没有 DeepSeek 实际账单导出，因此 Trace Token Usage 不可直接换算为美元费用。
- `BR-09-RF` 请求失败分支仍为 `needs_info`，不得伪造故障注入条件补齐。

### 后续执行约束

1. PR #38 保持 Draft/Open，不得合并或关闭；`run-builder-production` 标签保持移除。
2. 不重新生成已经通过独立验证的 Builder 数据集，除非 Builder 输入或规则发生实质变化且用户明确授权新的付费生产。
3. 新的 Pilot 必须使用已提交的 Runner 硬预算，并逐条执行、逐条审查成本；不得并发启动一批模型任务而失去累计成本控制。
4. 剩余 11 条用例的离线 Selector/Oracle 分支和合成自测已完成，但它们仍全部是 NOT_RUN。只有取得额外付费执行的明确授权后，才可考虑逐条启动；离线自测不得作为真实执行证据。
5. 如果触发任何 Token、模型步骤或时间上限，Runner 应停止 DSH、保存部分证据并将该用例标记为 BLOCKED；禁止自动重试或自动模型修复。
6. 实际美元成本必须从模型提供方账单/用量导出中核对，不能从缓存读取 Token 数量推断。
