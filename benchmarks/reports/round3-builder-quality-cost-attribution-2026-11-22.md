# Round 3 Pilot：Builder 质量、执行可行性与成本归因审查（2026-11-22）

## 审查范围与证据

本审查只基于 Round 3 正式 Builder 输出（run 44910360571）、其独立验证 PASS（run 44914032444）、三个不可变真实 Pilot 证据包（run 44914129348）及独立 Gold Oracle（run 44916378935）。不生成或修改正式用例、不重跑 Builder/Skill、不新增模型调用。

## 结论摘要

**Builder 产物在来源、结构和判定契约方面有良好基础；本轮没有证明被测 Skill 能完成三项任务。与此同时，执行可行性和成本预算存在可验证缺口，不能只把 Pilot 失败归因于目标 Skill。**

| 维度 | 结论 | 证据 |
|---|---|---|
| 来源可追溯、结构、独立验证 | PASS | 15 cases；Validator PASS；92 source evidence refs verified |
| 业务规则与可判定契约 | 设计层面 PASS / 有缺口 | 清晰 PASS/FAIL/UNKNOWN 双分支；BR-09B 保留 needs_info |
| 代表性 Pilot 选择 | 合理但有限 | 搜索 mutant、状态循环 clean、确认删除 clean，覆盖只读/状态变更/危险写操作 |
| Pilot 执行可行性 | NOT DEMONSTRATED | 三次 DSH 均未正常结束；C02/C06 未完成任务，C08 在截止前完成错误删除但未结束报告 |
| 执行成本预算 | NEEDS IMPROVEMENT | case timeout 与实际执行相贴近；C06 未声明/未匹配 Runner 的输出 Token 硬限制 |
| Builder 整体验收 | **NOT PASS** | 结构验证通过不等于执行可行或目标 Skill 能力通过 |

## 1. 分开归因：数据集问题 vs 被测 Skill 问题 vs Runner 问题

### WB-C02 搜索 mutant

- Builder 合约本身明确三个查询、清空恢复、只读副作用预算和偏差报告规则，判定条件可观察且可复核。
- Pilot 在 149.119 秒/150 秒 case deadline 被终止；17 model steps、27 tool calls、462,328 tokens。
- Skill 已生成 543 行 Python 测试脚本并成功导航、networkidle、截图和发现搜索框，但其候选选择器逻辑没有找到真实任务行；在输入任何 query 前中止。
- 因此：**测试任务未完成，BR-02 应为 UNKNOWN**。这是目标 Skill 的脚本发现/定位缺陷；但 150 秒执行预算不足以容纳本次模型调用和脚本探索，属于 Runner/资源预算风险，不能把预算问题归咎于 Builder 的业务规则定义。

### WB-C06 状态循环 clean

- Builder 合约规定 3 次状态变更、每一步核对状态与摘要、最多 1 次脚本、420 秒 case timeout。
- Pilot 实际 DSH elapsed 315.440 秒；23 model steps、43 tool calls、1,127,840 tokens。Skill 生成 49,415-byte Python 脚本，但脚本执行次数为 0。
- Runner 的输出 Token 限制是 55,000；实际 Output Token 56,145，超过 1,145，触发预算阻断。没有 PATCH、状态变更或证据截图。
- 因此：**BR-07 业务行为 UNKNOWN**。直接阻断因素是 Runner 的输出 Token hard cap；Skill 生成的脚本/输出体积是该资源超限的贡献因素。Builder 合约虽声明 420 秒，但未表达或校准 Runner 的 output-token cap，执行可行性只在时间预算上描述，属于 Builder/Runner contract integration gap。

### WB-C08 确认删除 clean

- Builder 合约明确目标为 WB-102 / Update onboarding guide，允许一次确认删除，必须保留其他四条任务。
- Skill 在 179.117 秒/180 秒 deadline 内执行了 1 次 DELETE，但错误删除 WB-101 / Reset password flow。服务端审计和 post-state 独立证实：WB-101 被删，WB-102 仍存在，摘要为 4/1/2/1。
- Skill 的定位 helper 对 Delete 按钮逐层向上寻找包含目标标题的祖先节点，命中包含整个任务表的祖先，随后取第一个 Delete 按钮。这是目标 Skill 的错误定位/选择策略。Builder 对目标标题和不得误删其他任务的约束清楚，未发现目标选择契约歧义。
- 180 秒 deadline 在任务操作后几乎立即终止。虽然错误删除本身已经发生并足以判业务 FAIL，但 Skill 没有完成最终报告/turn close。
- 因此：**明确业务 FAIL（误删），并伴随 Runner/timeout 导致 DSH 未完成**。不能因执行中断而抹掉已发生的错误写操作。

## 2. Pilot 资源预算与成本观察

| Case | Deadline | DSH elapsed | Model steps | Tool calls | Total tokens | Output tokens | 任务脚本执行 |
|---|---:|---:|---:|---:|---:|---:|
| C02 | 150 s | 149.119 s | 17 | 27 | 462,328 | 1 次；查询未执行 |
| C06 | 420 s（合约） | 315.440 s | 23 | 43 | 1,127,840 | 0 次；输出 Token 超限 |
| C08 | 180 s | 179.117 s | 10 | 17 | 259,299 | 1 次；错误删除已发生 |
| **合计** | — | **643.676 s** | **50** | **87** | **1,849,467** | — |

Input tokens 41,483；Output tokens 98,528；Cache-read tokens 1,699,456。无可核验 USD 费用，不估算美元成本。

资源问题具有共同模式：Skill 花费大量调用生成和修正测试脚本，时间接近 case deadline；C06 的脚本输出还超过 Runner hard cap。仅把 timeout 放宽不是质量解决方案，也可能显著增加成本。

## 3. Builder 输出质量的实际评价

### 已证实的优点

1. 业务规则、合成数据、权限和副作用边界都有明确来源引用。
2. C02、C06、C08 目标、动作、失败分支、预算和证据要求足够具体。
3. 用例评分主体是 Skill；应用偏差与 Skill 漏检/误报被区分。
4. C08 明确指定唯一标题和禁止误删其他任务，Oracle 能通过服务端审计判定错误目标。
5. 15 条候选覆盖 9 capabilities、11 applicable business rules、7 applicable scenario buckets 和 13 risk items；BR-09B 诚实标记 needs_info，没有虚构故障注入。

### 尚未证明 / 需要改进

1. **执行可行性并未被独立验证。** Validator 主要验证结构、来源与语义约束，未验证在真实 DSH runtime token/time limits 下，目标 Skill 能完成这些任务。
2. **成本/复杂度与 Runner 限制缺少统一契约。** C06 只在 case timeout 写 420 秒，未在 Builder 可见 contract 中约束输出 Token 55,000。实际 script 49 KB，模型输出超限，零执行。
3. **复杂度没有可校准的预估。** 3-query 搜索任务、3-step state cycle 和 destructive delete 均在 150–420 秒范围，但当前只声明执行次数、mutating action 和 case seconds，没有 token/output/tool-call预算或 feasibility rationale。
4. **Pilot 任务执行策略成本过高。** 543-line C02 script、49 KB C06 script 表明目标 Skill 倾向于生成大型 bespoke harness。此结果不代表 Builder 用例本身错误，但应作为执行可行性/成本约束反馈，而不是只扩大 Runner 时间。

## 4. 建议的下一步（不立即付费重跑）

优先级 P0：

- 将 Builder 的执行预算与 Runner 实际硬限制统一：在 Builder 输入/运行契约中明确可用 model steps、input/output/cache/total tokens、case wall-clock、tool-call 约束；正式输出必须声明这些预算或标记 needs_info。
- Independent Validator 增加预算一致性检查：用例声明不得超过 Runner limit；若预算未声明/来源缺失，execution feasibility 不得 PASS。
- Pilot Runner 将 timeout、token-limit、tool-budget 阻断分类清晰，报告实际执行到哪一步；C06 这种输出超限必须归为资源阻断而非普通用例 timeout。

优先级 P1：

- Builder prompt/Skill 加入“最小充分测试实现”要求：优先简短可复用的 Playwright 操作、避免为每条 case 生成长型探索框架；但不减少用例要求的观察点或证据质量。
- 依据本轮失败 traces 做一份非付费的 feasibility review，先选低成本且能够产生完整 Oracle 证据的 candidate pilot；不能通过手工修改 Builder case 代替正式生成。
- 不立即调高所有 timeout。先分析目标 Skill 的模型调用策略和脚本复杂度；仅当任务设计本身合理且时间预算被证明不足时，针对单 case 调整。

## 5. Gate 状态与保全要求

- Round 3 Builder output：保持不可变。
- Validator PASS：保留原始证据。
- 三个 Pilot：保留不可变原始证据，未重跑。
- Oracle：独立判定 3/3 contract FAIL；business behavior 2 UNKNOWN、1 FAIL。
- PR #38：Draft/Open；不得合并、关闭或绕过门槛。

**决策：暂停付费 Pilot。先完成 Builder–Runner 预算契约与执行可行性审查，再决定是否需要正式 Builder 重新生成候选。**
