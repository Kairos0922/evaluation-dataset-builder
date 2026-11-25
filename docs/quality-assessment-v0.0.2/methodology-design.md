# v0.0.2 方法论设计（候选方案，未验证）

## 1. 核心架构

本项目不是对“Agent 跑得好不好”直接打分，而是评价“这套数据集能否支持预定的测量和决策”。

采用两条相互关联但不可混同的评价路径：

1. **Independent Dataset Assessment（IDA）**：独立离线评价数据集本身。
2. **Empirical Runtime Assessment（ERA）**：在真实环境运行后评价测量效力和评分器质量。

两条路径分别产生结果。任何综合视图都必须保留两条路径的独立状态，不得用其中一条替代另一条。

方法选择、统计定义、适用前提、样本量/功效、不确定性和工程落地矩阵见 [methodology-matrix.md](methodology-matrix.md)。

## 2. 测量对象与输出

### 2.1 独立离线评价 IDA

输入：
- 数据集文件及 Manifest；
- 评测目标和用途声明；
- 来源注册表、原始依据或可审计的来源定位；
- 覆盖范围全集及能力/风险模型；
- 每条用例的输入、预期行为、Ground Truth、Grading Contract；
- 数据集版本、划分策略和污染/独立性说明。

输出：
- 结构与完整性检查；
- 证据与来源核验结果；
- 任务/目标/构念对齐审查；
- Ground Truth 与 Rubric 审查；
- 覆盖和分布画像；
- 重复性与样本独立信息分析；
- 执行可行性与可观察性检查；
- 缺陷列表、严重程度、证据与修复建议；
- 每个维度的分项分数或状态（证据不足时 NOT_ASSESSED）；
- Evidence Confidence / Evidence Sufficiency，独立于质量分数。

IDA 不得输出以下运行专属指标的伪值：Agent 能力区分度、真实故障检出率、真实 Judge 准确率、重测 ICC、Agent 稳定性、运行成本。

### 2.2 真实运行评价 ERA

输入：
- 已通过 IDA 适用门禁的数据集；
- 精确绑定的数据集、Agent/Skill、模型、提示、工具、环境、协议和执行版本；
- 运行轨迹、状态快照、结果产物和 Judge 证据；
- 运行失败分类和人工 Gold/Oracle 审查样本。

输出：
- Agent 任务表现（仅描述被测对象，不冒充数据集质量）；
- Outcome / Process Grader 的准确性和偏差；
- Judge 与专家一致性、Judge 重复性、Abstention；
- 重复运行方差及其来源；
- Capability 的难度、区分度、信息量、测量误差和跨 Agent 稳定性；
- Regression 的历史故障检出、变异缺陷检出、False Pass / False Fail、版本配对差异和 Flakiness；
- 置信区间、统计功效/精度说明和成本；
- 对 IDA 结论的外部验证或反证。

ERA 需把 Agent、环境、Judge 和采样误差分开记录，不能把全部波动归咎于数据集。

## 3. 共享的质量维度候选库

以下是候选维度，不是已经确认的总分因子，也不代表每个数据集都适用。

### A. 目标与构念
- Construct Definition：目标能力/行为是否有操作性定义。
- Construct Alignment：任务是否真正要求该目标能力。
- Construct Representation：目标范围是否被代表性采样。
- Construct-Irrelevant Variance：无关知识、格式、工具、语言或环境因素是否主导结果。

### B. 单题有效性
- Task Clarity：输入、目标、约束、成功条件是否清楚。
- Solvability / Feasibility：是否具备可解条件，Oracle/独立专家能否完成。
- Ground Truth Validity：参考结果是否正确、权威、可追溯。
- Rubric Validity：判定契约是否覆盖关键要求、允许合理变体并处理不确定性。
- Observability：结果和必要过程是否可被可靠观察。
- Safety / Authorization：任务和判定是否正确表达权限与副作用约束。

### C. 数据集结构与抽样
- Coverage：对定义的目标范围、能力和失败模式的覆盖。
- Representativeness：抽样是否匹配目标使用场景。
- Diversity：任务、来源、上下文和失败模式的有效多样性。
- Redundancy：语义重复、模板重复及测量信息重复。
- Distribution：任务类型、难度、来源、风险、结果标签分布。
- Contamination / Leakage：污染风险、调优泄漏和保留集独立性。

### D. 判定器与证据
- Grader Specification Completeness。
- Deterministic Verifiability。
- LLM Judge Calibration。
- False Pass / False Fail。
- Abstention / Unjudgeable Rate。
- Traceability / Auditability。

### E. 工程与维护
- Executability / Environment Readiness。
- Reproducibility。
- Versioning / Change Impact。
- Maintainability。
- Execution Cost / Resource Footprint。

各维度要根据评测用途、Agent 类型和数据集目标进行适用性声明；不适用项不记零分，未评估项不推定通过。

## 4. 用途专属测量

### 4.1 Capability Evaluation

目的：对目标能力水平和能力差异进行测量。

候选指标：
- Item Difficulty：任务难度参数/经验通过率。
- Item Discrimination：任务对能力差异的区分信息。
- Test Information / Conditional Standard Error：不同能力区间的测量精度。
- Ability Estimate Stability：Agent 能力估计的重测稳定性。
- Rank / Difference Uncertainty：排名和差异的置信区间。
- DIF / Invariance：不同模型家族、工具配置、语言或环境是否出现非目标差异。
- Domain Transfer：跨任务域和真实任务的外部泛化。

统计方法候选：
- IRT（先检验单维/多维结构、局部独立、拟合和样本条件）。
- Bootstrap / Bayesian uncertainty。
- Generalizability Theory（任务 × Agent × seed × environment × rater）。
- 对比已知组/已知能力基线和外部任务表现。

禁止：
- 仅凭任务难度高判定任务质量高。
- 在样本和模型条件不足时输出稳定的 IRT 参数。
- 用平均通过率或模型排名代替测量精度和构念效度。

### 4.2 Regression Evaluation

目的：判断系统变更是否引入目标行为退化或新失败。

候选指标：
- Historical Fault Detection：已知真实缺陷回放检出率。
- Mutation Detection：受控、非等价变异的检出率。
- False Pass / False Fail：基于独立 Oracle / 人工复核。
- Paired Change Effect：新旧版本同任务配对结果差异。
- Flakiness：同一版本/任务重复运行结果的波动。
- Critical Regression Exposure：关键行为/风险失败是否被发现。
- Failure Diagnosis：能否定位具体行为、规则或工具调用退化。
- Cost per Detected Fault：检出缺陷的执行成本。

统计方法候选：
- 二元配对结果：McNemar 或配对 Bootstrap。
- 连续/等级结果：适当的配对模型或 Bootstrap。
- 重复执行：混合效应模型、ICC 或 G-Theory，需说明设计和误差来源。
- 历史缺陷和变异缺陷分开报告；Mutation Score 不可替代真实故障检出。

禁止：
- 只比较总体平均分而忽略任务级和关键风险回归。
- 将 Agent 本身随机行为当作数据集 Flakiness。
- 把“未检出变异”直接等同于“真实缺陷检出能力”。

## 5. 公式与评分模型：先比较，后验证

### 5.1 指标数据结构

每项指标记录：
- metric_id、名称、构念归属、用途适用性；
- 操作定义、计算公式、单位和方向；
- 输入数据、分子/分母、样本单位；
- 归一化规则及边界；
- 缺失/不适用/不可评估处理；
- 证据等级、置信区间；
- 适用条件、模型假设和已知局限；
- 实现版本和测试用例。

### 5.2 候选模型族

在实证比较前，不选定唯一模型。至少比较：

1. **Gate + Profile**：关键门禁状态 + 多维分项画像，不做总分。
2. **Non-compensatory aggregation**：关键维度不能互相补偿的模型。
3. **Additive composite**：标准化指标的加权和。
4. **Geometric composite**：适用于有理由限制完全补偿性的场景。
5. **Latent-variable model**：仅在指标理论上反映同一潜在构念且数据支持时考虑。
6. **Purpose-specific model**：Capability 与 Regression 分别拟合、验证。

形成性指标与反映性指标必须区分。覆盖、来源真实性、执行稳定性等未必是同一个潜变量的可互换表现，因此不得默认以 Cronbach's alpha 或单因子 CFA 证明全部质量指标。

### 5.3 候选分数的基本形式（仅用于实验比较）

若候选模型采用加权聚合，可表示为：

S_m(D) = A_m(z_1(D), ..., z_k(D); theta_m)

其中：
- D 是指定版本的数据集；
- z_j 是经过明确定义和适当变换的指标；
- A_m 是候选聚合函数；
- theta_m 包括权重、参数和阈值。

该表达式仅定义模型族，不代表选择了线性加权，也不赋予任何维度权重。参数必须在开发集估计/设定，并在独立验证集冻结检验。

### 5.4 模型验证目标

- Content / Construct Validity：专家是否认为指标与目标构念匹配。
- Criterion / Predictive Validity：分数是否预测真实故障检出、专家质量判断或运行测量精度。
- Reliability：评审者、重复运行和分析流程是否足够稳定。
- Calibration：报告的风险/质量等级是否与实际结果匹配。
- Discrimination：能否区分已知质量水平和注入缺陷。
- Robustness：权重、指标、样本、标准化和数据缺失扰动下结论是否稳定。
- Generalization：在未参与开发的 Agent、Skill、任务域和环境中是否保持有效。
- Decision Utility：错误放行和错误拒绝的代价是否合理。

### 5.5 权重与阈值的选择

权重来源可包括理论约束、专家内容判断、统计模型估计或外部效标优化，但每种来源都必须说明它回答的是什么问题。不能把专家偏好权重称为客观真值。

阈值应通过预定用途和错误成本确定，并报告 ROC / PR、校准、置信区间、误放行/误拒绝代价及跨数据集稳定性。未获得足够证据时，状态应为 NOT_VALIDATED。

## 6. 证明 / 验证实验设计

1. **构念定义与蓝图冻结**：定义数据集质量、目标能力、用途和决策；绘制构念→指标→证据→结论映射。
2. **内容效度**：多名独立专家盲评指标必要性、相关性、覆盖完整性和可操作性；报告 I-CVI / S-CVI 或 CVR 及分歧，不预设未经论证的专家人数和阈值。
3. **反应过程**：让专家和自动审查器执行 think-aloud / 规则解释核对，识别指标歧义、评分漂移和证据误读。
4. **评分者一致性**：双人/多人独立评分；按数据类型选择 Kappa、Krippendorff's alpha、ICC 或其他统计量；同时报告原始分歧和区间。
5. **缺陷注入**：对样本注入歧义、错误 Ground Truth、错配 Rubric、伪造来源、重复、覆盖缺失、评分漏洞、污染和执行不可行等已知缺陷。
6. **运行效标**：执行真实 Agent/Skill，使用独立 Oracle、历史缺陷、变异缺陷、重复运行和真实任务迁移结果。
7. **模型开发/验证隔离**：按数据集/任务域/Agent 分组切分，避免同源近重复样本跨集合泄漏。
8. **模型比较**：在开发集比较模型族；在冻结的独立验证集评估效度、校准、排序/决策稳定性。
9. **稳健性**：对权重、标准化、缺失值、样本抽样和聚合函数执行敏感性/不确定性分析。
10. **外部复现**：在不同 Agent / Skill、任务域、模型家族和运行环境复现。
11. **后果分析**：审计错误批准/错误拒绝、被忽略的关键缺陷及资源成本。

## 7. 报告状态

每项评价必须使用以下状态语义：
- PASS：已执行且满足该项预先定义的判定条件。
- MEASURED：已计算描述性统计，但没有足够依据将其判定为质量通过或失败。
- FAIL：已执行且不满足判定条件。
- NOT_RUN：尚未执行。
- NOT_ASSESSED：该项未被评价。
- NOT_APPLICABLE：经说明后确认不适用。
- UNKNOWN：执行或证据存在不确定性，不能判定。
- NOT_VALIDATED：候选模型/阈值尚无足够独立验证证据。

不允许将 UNKNOWN、NOT_RUN、NOT_ASSESSED 或 NOT_VALIDATED 自动转换成 PASS 或零分。

## 8. 0.0.2 发布声明边界

若 v0.0.2 实验数据不足以支持一个跨类型综合分，仍可发布经过验证的离线检查、运行指标和用途专属报告，但必须明确：
- 哪些指标是确定性校验；
- 哪些依赖专家判断；
- 哪些依赖真实运行；
- 哪些公式/权重/阈值尚未验证；
- 哪些 Agent / Skill 类型和环境尚未覆盖。

不得为了版本号或产品展示需要而降低科学门槛。

## 11. 当前可发布的量化对象：用途条件化质量画像

在综合标量通过验证前，v0.0.2 使用可审计的向量质量画像，而不是伪造一个 0–100 总分。

令：
- D：固定版本的数据集，必须绑定 manifest + cases 的 SHA-256；
- p ∈ {capability, regression, both}：评测用途；
- A：被测 Agent / Skill 及其 revision；
- theta：模型、Harness、工具、环境、seed 等运行配置。

独立离线评价定义为：

`Q_IDA(D) = (G_IDA(D), M_IDA(D), E_IDA(D), U_IDA(D))`

其中：
- G_IDA：关键门禁状态向量；
- M_IDA：结构、来源、覆盖、冗余、Rubric 等指标画像；
- E_IDA：证据充分性与证据来源；
- U_IDA：未评估项、适用限制和不确定性。

真实运行评价定义为：

`Q_ERA(D, A, theta, p) = (R(D,A,theta), J(D,A,theta), C_p(D,A,theta), E_ERA, U_ERA)`

其中：
- R：运行有效性、环境失败、重测一致性等；
- J：Judge 与独立 Gold 的误判、拒绝和一致性；
- C_capability：能力测量证据；
- C_regression：回归检出、配对差异、历史故障和变异测试证据；
- E_ERA、U_ERA：证据充分性与不确定性。

两者的关系是并列证据，不是简单相加：

`Q(D,p) = (Q_IDA(D), Q_ERA(D,A,theta,p))`

这是一种结构化量化输出。它允许明确回答哪些维度已测量、哪些门禁失败、哪些证据缺失，以及结果适用于什么 Agent/环境/用途。

### 11.1 为什么当前不提供标量总分

未来候选标量形式：

`S_p(D) = f_p(G_IDA, M_IDA, R, J, C_p, E, U)`

只有在以下条件满足后才允许启用：
1. 指标定义与目标构念建立有效映射；
2. 权重/聚合规则在开发集上拟合或经规范性论证；
3. 对关键门禁采用非补偿逻辑；
4. 在独立数据集家族和冻结验证集上验证；
5. 与专家效标及真实缺陷检出结果具有可重复的外部关系；
6. 对权重、标准化、缺失数据、样本组成和阈值进行敏感性分析；
7. 报告置信区间、适用范围和失效边界。

在这些条件完成前，f_p 不定义，composite.status 必须保持 NOT_VALIDATED，composite.value 必须为 null。该规则不是缺少实现，而是避免未经验证的数值被误当成科学结论。
