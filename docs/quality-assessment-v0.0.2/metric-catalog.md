# v0.0.2 候选指标字典（待验证）

**状态：** 候选指标定义；未赋权、未设通过阈值、未证明可以汇总为单一分数。  
**关联：** [需求](requirements.md) · [方法论](methodology-design.md) · [公式验证协议](formula-validation-protocol.md)

## 1. 使用规则

每个指标必须绑定：
- 数据集 ID、版本、文件 SHA-256；
- 评测用途（Capability / Regression / Both）；
- 适用对象和目标能力；
- 计算单位与分母定义；
- 数据来源、采集时间和验证者；
- 运行/静态/专家判断等证据类型；
- 不确定性、缺失值和适用性状态。

下表中的公式是指标定义，不是总分公式。不得把不同性质的指标直接平均。

## 2. 独立离线评价（IDA）指标

| ID | 指标 | 操作性定义 / 计算 | 证据来源 | 指标类型 | 限制 |
|---|---|---|---|---|---|
| IDA-STR-00 | Manifest Schema Conformance | 通过清单 Schema 的状态及违反项 | JSON Schema Validator | 确定性门禁 | 结构通过不证明声明内容真实 |
| IDA-STR-01 | Case Schema Conformance | 满足用例 Schema 约束的用例数 / 被检查用例数 | JSON Schema Validator | 确定性门禁 | 结构通过不证明语义正确 |
| IDA-STR-02 | Identifier Integrity | 唯一 case_id 数 / 用例总数，并检查 dataset_id 与 manifest 一致、case_count 一致 | Case IDs、Manifest | 确定性门禁 | 不等于语义去重 |
| IDA-STR-03 | Source Registry Referential Integrity | 能在独立来源注册表解析且身份字段一致的 source_ref 数 / 待解析 source_ref 总数 | 独立 Source Registry | 确定性门禁 | 不证明来源真实或支持主张；无注册表时 UNKNOWN |
| IDA-EVD-00 | Source Reference Presence | 至少有一条 source_ref 的用例数 / 用例总数 | Case source_refs | 描述性 | 仅测引用是否存在，不证明来源真实性或主张支持 |
| IDA-COV-00 | Coverage Consistency Profile | 比较 Manifest 声明的 covered/total/rate 与 Case 标签中的 coverage_item_id 统计 | Manifest、Case coverage_tags | 描述性 | 只检查内部一致性，不证明覆盖全集完整 |
| IDA-DIV-01 | Scenario Distribution | 按 scenario_bucket 统计用例数量 | Case metadata | 描述性 | 分布均匀不天然等于代表性 |
| IDA-RED-00 | Exact Duplicate Payload Rate | 去除 case_id 后，规范化 JSON 完全相同的冗余用例数 / 用例总数 | Canonical case payload | 描述性 | 不识别语义重复 |
| IDA-RUB-00 | Grading Criteria Inventory | 统计评分标准数量及其分布 | Case grading.criteria | 描述性 | 数量不证明完整性或效度 |
| IDA-EVD-01 | Source Claim Support | 经独立核验确实支持对应主张的引用数 / 抽审引用数 | 原始来源、盲审 | 专家/证据判断 | 必须说明抽样方法和评审一致性 |
| IDA-EVD-02 | Ground Truth Correctness | 经独立 Oracle/专家确认正确的参考结果数 / 已核验参考结果数 | Oracle、专家、确定性状态 | 门禁/效标 | 没有可信参考标准时为 NOT_ASSESSED |
| IDA-CON-01 | Construct Alignment | 专家判断任务确实需要目标能力的比例及分歧分布 | 目标构念蓝图、盲审 | 内容效度 | 不能只由生成模型自评 |
| IDA-CON-02 | Construct-Irrelevant Load | 任务成功是否被非目标能力/环境因素主导的审查结果 | 专家审查、反事实变体 | 构念诊断 | 需要按目标能力解释 |
| IDA-TASK-01 | Task Clarity | 输入、目标、约束、初始状态和成功条件的歧义审查 | 专家盲审、歧义缺陷注入 | 内容效度/门禁 | 评分锚点需通过评审者校准 |
| IDA-TASK-02 | Solvability Evidence | Oracle/独立专家能否在规定条件下完成任务；记录成功、失败和原因 | Oracle 轨迹、环境预检、专家 | 可解性证据 | Oracle 失败不一定说明题目不可解，需区分环境和 Oracle 缺陷 |
| IDA-RUB-01 | Rubric Coverage | 任务要求中被评分条件覆盖的要求数 / 可评分要求总数 | 要求到 criterion 映射 | 内容完整性 | 分母必须由独立任务分解定义 |
| IDA-RUB-02 | Rubric Observability | 通过/失败条件是否能由明确证据观察与复核 | 轨迹、状态、输出、人工复核 | 判定契约质量 | LLM 主观判断不能冒充确定性断言 |
| IDA-RUB-03 | Rubric-Target Alignment | 每条 criterion 是否评价预先声明的同一评分主体和目标 | grading contract、盲审 | 门禁 | 多主体评价应拆分 |
| IDA-COV-01 | Applicable Coverage | 对已定义适用范围全集，覆盖项数 / 适用项总数 | Coverage Universe、Manifest | 形成性/描述性 | 必须公开全集、适用性和缺口；不得用题目数代替覆盖 |
| IDA-COV-02 | Critical Gap Register | 未覆盖且被标为关键/高影响的要求和风险清单 | 风险模型、业务规则、专家审查 | 非补偿门禁 | 不在没有风险依据时人为设置统一比例 |
| IDA-DIV-01 | Scenario Distribution | 按任务类型、来源、风险、流程、工具依赖等分层报告计数和比例 | Case metadata | 描述性 | 均匀分布不天然等于代表性 |
| IDA-DIV-02 | Source Diversity | 按来源家族/来源类型分层报告，不将多个复制来源当成独立来源 | Source registry | 描述性 | 来源多不等于质量高 |
| IDA-RED-01 | Semantic Redundancy | 在经盲审确认的重复簇中，冗余样本数 / 样本总数 | 语义候选簇 + 人工裁定 | 形成性/诊断 | embedding 相似度只用于候选检索 |
| IDA-RED-02 | Incremental Information | 删除候选样本后，覆盖/缺陷类别/测量信息变化 | Leave-one-out / subset ablation | 实证诊断 | 需要基线任务/缺陷集，不能只看文本相似度 |
| IDA-LEAK-01 | Leakage Audit | 按预先定义的泄漏攻击/相似度/答案暴露检查报告结果 | 盲测集、源材料、审计日志 | 风险门禁 | 无法检测到泄漏不等于证明绝对无污染 |
| IDA-OPS-01 | Execution Readiness | 环境、权限、工具、数据、初始状态、清理和失败清理要求的完整性 | 执行契约检查 | 确定性/人工门禁 | READY 不等于实际运行成功 |
| IDA-MNT-01 | Change Traceability | 来源/规则/能力变更能否定位到受影响用例与判定契约 | Change log、引用图 | 工程质量 | 需要实际变更案例检验 |

## 3. 真实环境运行评价（ERA）共享指标

| ID | 指标 | 操作性定义 / 计算 | 证据来源 | 指标类型 | 限制 |
|---|---|---|---|---|---|
| ERA-GRD-01 | Grader False Pass Rate | 实际失败却被判通过数 / 经 Oracle 确认的失败数 | 独立 Gold labels、Judge output | 评分器效度 | 报告分层结果和置信区间 |
| ERA-GRD-02 | Grader False Fail Rate | 实际通过却被判失败数 / 经 Oracle 确认的通过数 | 独立 Gold labels、Judge output | 评分器效度 | 多个合理答案需定义 indeterminacy |
| ERA-GRD-03 | Grader Abstention Rate | 无法判定/UNKNOWN 数 / 所有评分请求数 | Judge response、parser | 可判定性 | UNKNOWN 不得自动归入 FAIL 或 PASS |
| ERA-GRD-04 | Human-Judge Agreement | 与独立人工标注的原始一致率及适合尺度的 chance-corrected agreement | 双盲评分 | 评分者一致性 | Kappa 受基率影响，必须同时报告混淆矩阵 |
| ERA-GRD-05 | Judge Test-Retest | 同一冻结轨迹重复评分的分歧率/ICC（按尺度选择） | 冻结轨迹、多轮 Judge | 重复性 | 高一致性不排除系统性偏差 |
| ERA-GRD-06 | Judge Bias Audit | 位置、措辞、长度、格式、模型自偏好等反事实扰动导致的判断变化 | 配对扰动实验 | 偏差诊断 | 只测试预先声明的偏差族 |
| ERA-RUN-01 | Valid Run Rate | 有效执行且满足协议的运行数 / 启动运行数 | Runner、环境日志 | 执行质量 | 必须区分环境失败和 Agent 失败 |
| ERA-RUN-02 | Environment Failure Rate | 由于环境/工具/外部依赖而无效的运行数 / 启动运行数 | 环境健康检查 | 误差分解 | 不能将其归因于数据集 |
| ERA-RUN-03 | Agent Outcome Rate | Agent 达到预定义结果条件的任务比例 | Oracle / 状态断言 | Agent 表现 | 是被测 Agent 结果，不是数据集质量总分 |
| ERA-RUN-04 | Process Compliance | 满足必要过程/权限/工具/顺序要求的运行比例 | Trace assertions、状态检查 | Agent 表现/安全 | 必须与 Outcome 分开报告 |
| ERA-RUN-05 | Failure Exposure | 已确认的故障/错误状态中，被任务和评分器暴露为可观察失败的比例 | Fault replay、状态和报告证据 | 测试效力 | 与故障检出能力不是同一属性 |
| ERA-RUN-06 | Run Cost | 每个有效任务的时间、Token、工具调用和费用分布 | Runtime telemetry | 工程效率 | 不可与质量正确性直接相加 |

## 4. Capability 专属指标

| ID | 指标 | 操作性定义 / 计算 | 限制 |
|---|---|---|---|
| CAP-00 | Observed Item Pass-Rate Profile | 每道题在指定 Agent/配置/环境总体中的观察通过率及运行数 | 仅为描述性统计，不等于 IRT 难度参数 |
| CAP-01 | Empirical Item Difficulty | 在明确 Agent/配置总体中估计任务通过概率或 IRT 难度参数 | 依赖样本总体和模型假设；不可直接视为题目质量 |
| CAP-02 | Item Discrimination | 题目对目标能力差异的区分参数/相关 | 需足够能力范围；检查局部依赖和混淆因素 |
| CAP-03 | Test Information | 给定能力区间的测试信息函数 | 需要拟合适当 IRT 模型 |
| CAP-04 | Conditional Measurement Error | 各能力区间的条件标准误/区间宽度 | 必须报告估计不确定性 |
| CAP-05 | Ability Estimate Stability | Agent 跨任务抽样/种子/环境下能力估计变化 | 应分解随机来源 |
| CAP-06 | Differential Item Functioning | 控制目标能力后，不同模型/工具/语言组的题目差异 | 分组必须有理论依据和足够样本 |
| CAP-07 | External Capability Validity | 数据集能力估计与独立任务/已知组/真实任务效标关系 | 相关性不能证明因果或全域泛化 |

## 5. Regression 专属指标

| ID | 指标 | 操作性定义 / 计算 | 限制 |
|---|---|---|---|
| REG-01 | Historical Fault Detection | 检出的已确认历史缺陷数 / 回放的有效历史缺陷数 | 需要独立确认缺陷和回放可行性 |
| REG-02 | Mutation Detection | 检出的非等价变异数 / 有效非等价变异总数 | 与真实故障检出分开报告 |
| REG-03 | Paired Regression Delta | 同一任务新旧版本配对结果差异；二元结果使用配对列联表/合适检验 | 报告任务级变化和不确定性 |
| REG-04 | Critical Regression Escape | 已确认关键退化但测试未暴露的案例数/比例 | 需定义关键风险全集 |
| REG-05 | Regression False Pass / False Fail | 新旧版本变化经 Oracle 确认后，回归判定器的误放行/误报 | 不能只报告总体 accuracy |
| REG-06 | Flakiness / Discordance | 同一版本、任务和协议的重复运行结果不一致程度 | 分解 Agent、环境、Judge 方差 |
| REG-07 | Historical Fault Failure Exposure | 在历史真实故障回放中，已确认失败被暴露为可观察证据的比例 | 与检测率不同；必须只使用经独立确认的历史故障 |
| REG-08 | Cost per Detected Fault | 发现一个已确认缺陷的执行成本分布 | 不能替代检出质量 |

## 6. 计量与缺失处理约束

- 比例指标必须报告分子、分母和区间；分母为零时输出 NOT_APPLICABLE，不返回 0。
- 没有真实运行数据时，ERA 指标为 NOT_RUN，不得推断。
- 证据不充分时为 NOT_ASSESSED / UNKNOWN，不以零分代替缺失。
- 同一来源复制出来的案例不能视为独立样本。
- 任务嵌套于数据集、数据集嵌套于领域时，统计区间需尊重聚类结构。
- 多维指标不自动满足内部一致性假设；不得默认计算 Alpha 后作为总质量信度。
- 只有通过独立验证的指标/模型才允许标记 VALIDATED_FOR_SCOPE。
