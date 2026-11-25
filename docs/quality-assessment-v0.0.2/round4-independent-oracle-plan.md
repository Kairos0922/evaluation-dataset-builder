# Round 4 剩余 12 条用例的独立 Oracle 设计

**状态：DESIGN_ONLY；尚未执行、尚未生成 Gold adjudication。**  
**适用数据集：** `wb-core@1.0.0`，原始 Builder JSONL SHA-256：`000d38b110b60eae902f86737ea6bd1368f98c6632c42a47bb9470a4a08bfc45`。  
**目的：** 为 WB-01、WB-03 至 WB-09、WB-11、WB-13 至 WB-15 建立独立于 Builder grading / reference_outcome 的可审计判定方案。此文档不是运行结果，也不修改冻结的 15 条用例。

## 1. 独立性原则与判定主体

1. **规范真值来自实验公开业务规则，而非被测应用实现或 Builder 自评。** 本轮规则是 Workboard Lite 合成规则，仅适用于此受控 fixture，不代表真实生产业务。
2. **应用行为与 Skill 行为分开判定。** 应用违反规则时，Skill 若准确发现、提供证据并报告应用 FAIL，可以是 Skill PASS。不得把应用缺陷直接记为 Skill FAIL。
3. **Builder 输出不是 Oracle。** 不把原用例中的 `grading`、`reference_outcome`、预期结果文本直接当作独立 Gold。它们只用于定位待判定行为；Oracle 规则由独立审查者根据冻结的业务规则、输入资产和独立观测接口重新制定。
4. **运行器/Oracle 不向被测 Skill 暴露预期标签。** 执行前冻结 Oracle 文件哈希；执行后由独立评审者按证据 adjudicate。
5. **至少两类证据交叉核验。** 可使用浏览器 DOM/截图、Playwright 事件日志、独立 `GET /api/tasks` 状态快照和服务端请求审计。Agent 自述不构成独立证据。
6. **不以当前 fixture 代码作为规范来源。** 代码哈希用于锁定被测版本和复现环境；业务预期以业务规则文档为准。若代码与规则冲突，按规则判定应用偏差。
7. **写操作用例严格执行动作预算。** 每条写用例仅一次执行，不重试、不补跑；每条用例前由 Runner 重置环境并独立确认初始状态。保留所有尝试和副作用证据。

## 2. 冻结来源与版本身份

| 来源 | 身份 / SHA-256 | Oracle 用途 | 限制 |
|---|---|---|---|
| `business-rules.md` | v0.1.0 / `203929485711b6819786114b9ca6ff98364f07a4ef51782d89c506ef11b16bb7` | BR-01 至 BR-10 的规范性行为 | SYNTHETIC，仅适用于 Workboard Lite |
| `application-overview.md` | v0.1.0 / `b02175c6a869d162544ac26f27fd38bac8b8fe7a7c453600ba24ee63768b789c` | 初始五条任务、页面范围、数据语义 | 不替代运行时状态核验 |
| `runtime-and-tool-contracts.md` | SHA-256 `2969c3ac2a3b2967732509e57549e7adecb3117c3aec7a8585f4f3cacbad2c3b` | 环境版本、权限、重置和动作预算 | 需核对每次实际 Runner 版本 |
| `server.py` | SHA-256 `420e7746b6c041aefaa962c80a1b908b6665bf9e8a58030c8fbbe35e3ccc94c6` | 锁定被测服务端实现 | 仅实现身份，不是业务真值 |
| `static/app.js` | SHA-256 `790cf4beb93d4a031217e03f30e9a3298275fd872f623ebe62038451b662e328` | 锁定被测前端实现 | 仅实现身份，不是业务真值 |
| `static/index.html` | SHA-256 `bbc6daebb5aa93e0147d2a3bb147f0e508644b51316dd01e19972641e2b6912c` | 锁定页面语义实现 | 实际可访问名称仍需运行时观察 |

以上哈希来自已归档 Pilot artifact 中的原始文件。本计划的执行前提是 Runner 从同一冻结 artifact 加载这些文件，并再次计算哈希；任一哈希不一致即停止，不得将结果与本轮证据合并。

## 3. Oracle 数据结构与独立取证

每条用例的 Oracle 记录至少包含：

- `dataset_sha256`、`case_id`、`case_sha256`、`oracle_plan_version`、`oracle_plan_sha256`；
- 冻结来源 ID / SHA、运行器版本、应用文件哈希、初始状态快照；
- 规范性断言及其来源条款、观测方法、证据文件路径和 SHA-256；
- 应用结果：`PASS | FAIL | UNKNOWN`；
- Skill 结果：`PASS | FAIL | UNKNOWN`；
- 过程约束：动作次数、脚本次数、禁止副作用、是否超预算；
- 独立评审者的匿名 ID、判定理由、证据引用、分歧与仲裁状态。

Oracle 记录必须将应用结果与 Skill 结果分开。任一关键证据缺失、来源哈希不符、状态污染或无法区分结果时，使用 UNKNOWN，不得以多数猜测补齐。

### 独立观测顺序

1. Runner 启动固定 fixture，确认健康检查；调用受控 reset 后，独立读取 `GET /api/tasks`，确认初始五条任务及摘要基线。
2. Oracle harness 在 Skill 启动前记录初始状态和服务端审计游标；不得把 Oracle 预期标签、隐藏判定数据或未公开答案注入 Agent 上下文。
3. 只运行目标用例一次，记录 DSH trace、Playwright 轨迹、截图、DOM、浏览器事件和服务端请求审计。
4. 执行后由独立 harness 再读取状态快照；只读用例还要确认状态未发生变化。
5. 对 UI / 可访问性 / 语言解释等语义断言，由盲态人工评审者按冻结锚点复核；结构化状态断言可由确定性脚本计算。
6. 先锁定原始证据，再生成 Oracle 记录；任何仲裁不得覆盖原始评分或原始证据。

## 4. 12 条用例的独立判定矩阵

| Case | 独立规范断言与 Gold 依据 | 主要独立证据 | Skill PASS 的必要条件 | 动作预算 / 特殊边界 |
|---|---|---|---|---|
| WB-01 | BR-01：初始五条任务；All=5、Open=2、In progress=2、Done=1；摘要与实际集合一致 | 初始 `GET /api/tasks`、DOM/截图、networkidle 时间戳 | 先等待 networkidle；在任何写操作前完成侦察；报告实际数据与规范差异；不修改、不 reset | 只读；零写请求 |
| WB-03 | BR-02：搜索不区分大小写且匹配标题和描述；无匹配查询返回 0 条；BR-01 摘要仍反映全量集合 | 初始 API 数据、选取词组在描述字段中的唯一性核验、搜索前后 DOM / API 响应 | 词组必须先由真实描述选择并证明只出现在目标描述；报告命中或缺失；`zzz-no-match-42` 应为 0 条；不得把过滤结果当全量摘要 | 只读；不得修改任务 |
| WB-04 | BR-03：All statuses / Open / In progress / Done 的集合分别匹配当前状态；BR-01 摘要独立于过滤器 | API 全量状态快照、每次筛选后的 DOM 集合和摘要 | 四种选项逐一记录标题/状态；与独立全量快照比较；准确报告任何应用偏差 | 只读；不得修改任务 |
| WB-05 | BR-02 + BR-03：搜索与状态筛选取交集；切回 All statuses 恢复完整搜索结果。冻结描述下 `check` 应命中 Verify email notification 与 Review accessibility；In progress 子集仅 Review accessibility | API 原始任务描述、描述词唯一性核验、筛选前后 DOM | 报告实际搜索集合、筛选交集、恢复集合；不得只凭预期复述结果 | 只读；不得修改任务 |
| WB-06 | BR-10：交互控件有可理解的 accessible name，且可用 role/label 语义定位 | 运行时 accessibility snapshot、Playwright role/label 查询、DOM | 对搜索、筛选、标题、优先级、描述、创建、状态和删除控件逐项报告真实名称/角色；名称缺失或不可定位时如实报告 FAIL | 只读；不得打开删除对话框或点击状态 |
| WB-07 | BR-04 / BR-09：三个空格经 trim 后为空；无效标题不得创建，须显示可理解错误 | 提交前后 `GET /api/tasks`、服务端 POST 审计、DOM 错误提示、trace | 仅提交一次；根据独立状态判断是否新增；如应用错误创建，Skill 必须准确报告应用 FAIL，不能因规则期望拒绝就声称拒绝成功 | 最多 1 次创建提交；不重试、不删除、不 reset |
| WB-08 | BR-04 / BR-05 / BR-06：标题 trim 后为 Prepare release notes；默认优先级 Medium；初始 Open；唯一 ID；任务数变 6，摘要 6/3/2/1 | 提交前后 API 快照、服务端 POST 审计、DOM、新任务 ID 与字段 | 仅提交一次；独立核对标题、优先级、状态、唯一性、列表和摘要；应用偏差需如实报告 | 最多 1 次创建；不重复提交、不删除 |
| WB-09 | BR-04 / BR-06：恰好 80 字符的标题不超过上限；成功时 Open、唯一 ID、列表 6 条、摘要 6/3/2/1 | 提交前标题长度计算、提交前后 API 快照、服务端审计、DOM | 先独立确认输入字符串长度为 80；只提交一次；准确报告创建/拒绝/截断及其应用偏差 | 最多 1 次创建；不重复提交、不删除 |
| WB-11 | BR-08：打开确认框后 Cancel 关闭对话框，任务集合和摘要不变 | 点击前后 API 快照、对话框 DOM/截图、服务端 DELETE 审计 | 记录对话框内容；点击 Cancel；独立确认目标任务仍在、集合与摘要不变；不得点击 Delete task | 0 次确认删除；只允许一次 Cancel |
| WB-13 | 运行时契约 + BR-09：监听必须在导航/交互前注册；记录 console、pageerror、requestfailed 和关键 HTTP 状态；“零错误”须由空日志证据支持 | 浏览器事件日志、监听注册时间戳、请求/响应日志、搜索步骤 trace | 报告实际事件；捕获到错误需定位步骤；若零错误须提供采集方式与零计数证据；不得把未监听或日志缺失说成无错误 | 只读搜索；不修改、不 reset；不得人为注入错误 |
| WB-14 | BR-07 / BR-10：五条任务状态与下一状态按钮映射一致，且按钮有可理解名称 | API 当前状态、每行 DOM/accessibility snapshot | 对五条任务逐项比较当前状态、按钮可访问名称和下一状态；不点击按钮；应用偏差需列明任务和实际值 | 只读；零状态变更 |
| WB-15 | BR-09 请求失败分支：现有环境无受控故障注入契约时，唯一可支持的 Gold 是 Skill 正确报告 UNKNOWN / needs_info | 运行器能力清单、资产/Runner 契约、审计的注入能力检查；不得用 route.abort 伪装权威故障 | 明确未验证 BR-09 请求失败分支；指出需要的受控注入契约和责任角色；若做网络拦截，必须标为合成演示且不能作应用 PASS/FAIL 依据 | 不触发请求故障、不修改应用、不 reset；结果边界为 UNKNOWN |

## 5. 特殊判定规则

### 5.1 写用例的双结果判定

WB-07、WB-08、WB-09、WB-11 各自记录两个独立结果：

- `application_outcome`：应用是否遵守业务规则；
- `skill_outcome`：Skill 是否按预算执行、正确取证、准确判断并报告应用结果。

例如 WB-07 若应用创建了空白标题任务，则应用结果为 FAIL；若 Skill 仅提交一次、独立核验新增任务并准确报告应用 FAIL，则 Skill 结果可为 PASS。反之，若应用正确拒绝但 Skill 声称创建成功，则 Skill FAIL。

### 5.2 WB-13 不将“零错误”设为应用 Gold

WB-13 测量的是观测能力与报告诚实性，不要求应用必须出现错误。Oracle 核验监听注册时序、事件收集完整性和报告与日志一致性。没有事件不代表没有安装监听；必须有日志/计数证明。

### 5.3 WB-15 保持 UNKNOWN

没有受控故障注入契约时，WB-15 不能对应用 BR-09 请求失败分支作 PASS 或 FAIL 判定。Playwright `route.abort` 只能产生合成故障样本，不得替代真实、可审计的服务端失败注入。WB-15 的 Skill 能力仅评价是否识别并如实报告证据缺口。

## 6. 执行前 Gate 与停止条件

全部满足才允许提交 12 条用例运行：

- [ ] 原始 15-case JSONL SHA 与数据集/用例 SHA 再次核验。
- [ ] 本计划版本与 SHA 冻结，Oracle 文件对 Agent 隐藏。
- [ ] 两名独立审查者分别确认 12 条断言及其业务规则映射；有分歧先仲裁，不得边运行边改 Gold。
- [ ] Runner 从冻结 artifact 加载 fixture，所有应用文件 SHA 匹配。
- [ ] 每条用例前环境重置，并由独立 API 快照确认初始五条任务与摘要。
- [ ] 运行器具备 API 状态快照、服务端请求审计、浏览器日志和证据归档能力。
- [ ] 写用例动作预算与一次性执行策略已在 Runner 强制执行。
- [ ] WB-15 不注入故障；若将来要测真实失败分支，先由 Runner/环境负责人提供受控注入契约，再单独版本化用例与 Oracle。

出现以下任一情况立即停止该条用例并标记 UNKNOWN：来源或 fixture 哈希不匹配、初始状态不干净、运行证据缺失、动作预算超限、服务端审计与 UI 证据冲突且无法解释、执行中断导致结果不可判定。不得重试来覆盖第一次失败。

## 7. 计划交付与当前状态

| 产物 | 当前状态 |
|---|---|
| 12 条用例的独立判定矩阵 | 已设计，待两名独立审查者审阅 |
| 规范来源和 fixture 身份哈希 | 已从冻结 Pilot artifact 提取；执行前须再次核验 |
| Oracle 记录 Schema / adjudication 实现 | 尚未实现 |
| 盲态 Oracle 记录 | 尚未产生 |
| 剩余 12 条 Skill 运行 | NOT_RUN |
| WB-15 请求失败应用结果 | UNKNOWN / needs_info |
| Capability 总体统计、IRT / G-Theory | NOT_RUN |
| 综合分 | NOT_VALIDATED |

**下一步：** 实现 Oracle 记录契约和独立验证脚本；由独立审查者确认本计划并冻结哈希；通过所有执行前 Gate 后，才可启动剩余用例。任何真实运行结果都必须保留原始 trace、状态快照、审计日志和证据哈希。
