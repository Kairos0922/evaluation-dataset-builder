# Round 3 Builder Pilot：真实执行与独立判定报告（2026-11-21）

## 结论

- 正式 Builder 产物来自 run [44910360571](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44910360571)，15 条用例，未手工修改。
- 原始产物的独立验证来自 run [44914032444](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44914032444)，状态 PASS。
- 三个真实 Skill Pilot 来自 run [44914129348](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44914129348)，均实际调用了目标 Skill，但 DSH 均未正常结束。
- 独立 Gold Oracle 使用原始 Builder 产物和三个不可变 Pilot 证据包完成判定，run [44916378935](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44916378935)，报告状态 **FAIL，3/3 contract verdict FAIL**。业务行为判定为 2 UNKNOWN、1 FAIL。
- 没有再次调用 Builder 或目标 Skill，没有再次消耗模型执行预算。
- PR #38 仍为 Draft/Open，未合并。

## 独立 Oracle 汇总

| Case | Oracle | Business behavior | 主要观察 |
|---|---|---|---|
| WB-C02 | FAIL | UNKNOWN | 测试脚本未识别任务行，查询未执行；随后 DSH 达到 150 秒用例超时 |
| WB-C06 | FAIL | UNKNOWN | 生成了测试脚本但没有执行；DSH 输出 Token 超过 55,000 上限 |
| WB-C08 | FAIL | FAIL | 测试脚本定位到错误的祖先容器，实际删除 WB-101，而非 Builder 指定的 WB-102 |

所有三个 Pilot 的证据文件 SHA-256 清单、Runner/Trace/服务端审计 run-id 关联均通过独立检查。失败不是证据包损坏或跨运行串包。

### WB-C02：搜索查询没有执行

- DSH：149.119 秒；17 个模型步骤；27 次工具调用；462,328 总 Token。
- Runner：BLOCKED，exit 124；150 秒 case timeout。
- 目标 Skill 生成并执行了一次 wb_c02_search_test.py。
- 脚本成功导航、等待 networkidle、定位搜索框 #task-search，但行选择器候选只识别到 4 个摘要 article，没有使用页面真实任务行 tbody#task-rows > tr。
- 脚本在输入第一个查询前中止。PASSWORD、screenshot、no-such-task-zz 均未执行，服务端审计中没有带查询参数的请求。
- 因此本次没有证据判断 Workboard 搜索功能是否符合 BR-02。失败归因是被测 Skill 生成的测试脚本元素发现缺陷，不是应用搜索功能失败。

### WB-C06：测试脚本未执行，输出预算超限

- DSH：315.440 秒；23 个模型步骤；43 次工具调用；1,127,840 总 Token。
- Output Token 为 56,145，超过 55,000 上限 1,145 Token。
- Runner：BLOCKED，exit 124；原因是 output_tokens=56145 exceeds limit 55000，不是 420 秒 case timeout。
- 证据包只有生成的 wb_c06_test.py 及其编译缓存；独立 Oracle 从 DSH Trace 确认测试脚本实际执行次数为 0。
- 没有截图、DOM、报告、PATCH 请求或状态变更。状态循环业务行为为 UNKNOWN。

### WB-C08：错误删除了其他任务

- DSH：179.117 秒；10 个模型步骤；17 次工具调用；259,299 总 Token。
- 生成的脚本执行一次，发出一次 DELETE，符合数量预算，但目标错误。
- Builder 指定目标：WB-102 Update onboarding guide。
- 实际请求：DELETE /api/tasks/WB-101，HTTP 200，删除了 Reset password flow。
- 操作后列表仍包含 WB-102，缺少 WB-101；摘要为 4/1/2/1。该摘要与实际剩余任务集合一致，但不符合删除 WB-102 后应有的 4/2/1/1。
- 脚本定位函数对每个 Delete 按钮向上遍历最多 8 层祖先，并在祖先文本包含目标标题时返回该祖先。第一个 WB-101 的 Delete 按钮最终命中了包含整个任务表的祖先容器，随后选择了第一个 Delete 按钮。因此误删 WB-101。
- 操作后截图确认对话框已关闭；报告中的 confirm_dialog_closed_after 失败，是因为脚本统计隐藏在 DOM 中的 Delete task 按钮，而不是检查对话框可见状态。这是脚本断言的误报，不改变错误删除这一明确失败事实。
- 这是合成 Workboard fixture 内的错误操作，不涉及真实业务数据。

## 模型执行成本

| Case | 总 Token | Model steps | Tool calls | DSH elapsed |
|---|---:|---:|---:|---:|
| WB-C02 | 462,328 | 17 | 27 | 149.119 s |
| WB-C06 | 1,127,840 | 23 | 43 | 315.440 s |
| WB-C08 | 259,299 | 10 | 17 | 179.117 s |
| **合计** | **1,849,467** | **50** | **87** | **643.676 s** |

合计 Input Token 41,483，Output Token 98,528，Cache-read Token 1,699,456。当前证据未提供可核验的美元费用，因此不估算 USD 成本。

## Gold Oracle 修复

本次独立判定暴露了一个 Oracle 解析缺陷：Builder 的状态循环契约使用 rule_expected.steps[].action/status/summary，Oracle 旧逻辑只读取 from/to，会得到空状态转换。

已修复 benchmarks/webapp-testing/scripts/gold_oracle.py：当步骤提供目标 status 而未提供显式 from/to 时，从 Builder 声明的初始状态顺序推导每个转换；若结构化步骤不完整，则回退到既有解析路径。新增回归测试覆盖 Open → In progress → Done → Open。

修复后的 runner preflight run [44916378978](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44916378978) PASS；PR CI run [44916380884](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44916380884) PASS。修复后的 Oracle 重跑 run [44916378935](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44916378935) 成功完成，并正确报告预期转换；Pilot 的最终 verdict 仍为 FAIL/UNKNOWN，不因 Oracle 修复而被人为改成 PASS。

## Builder 质量与下一步

本轮证明 Builder 能生成来源可追溯、结构通过独立验证且包含明确安全边界的候选用例；但 3 个真实 Pilot 没有达到可验收的执行闭环。失败主要来自目标 Skill 生成测试脚本的定位/执行质量及 DSH 输出预算，而不是 Builder 产物的结构验证失败。

目前不应重新付费重跑这三个用例，也不应手工修补正式数据集。下一步应先对 Builder 的产物质量与目标 Skill 的执行能力分开归因，再决定是否调整测试执行预算、脚本复杂度约束或试点用例选择。任何新一轮目标 Skill 调用都应避免复用这次已经失败的脚本策略。

## 状态边界

- 正式 Builder 产物保持不可变。
- 三个 Pilot 原始证据包保持不可变。
- 本报告只记录独立审查结论，不修改或重评分任何正式用例。
- PR #38 保持 Draft/Open，不合并、不关闭。
