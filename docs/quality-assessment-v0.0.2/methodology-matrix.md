# v0.0.2 评价方法论矩阵

**状态：** 可执行方法设计草案，待按真实数据预注册和验证。本文不设统一样本量、阈值或通过线，也不把统计量通过解释为构念效度已成立。

**适用范围：** 通用 Agent、Skill、Agent + Skill 和多工具多步骤工作流；分别支持 Capability Evaluation 与 Regression Evaluation。

**上位原则：** IDA 评价数据集自身的离线设计和证据；ERA 评价真实运行中的测量行为、评分器和被测系统表现。二者结果必须分开呈现。公式验证是第三条独立证据链。

## 1. 方法选择总览

| 研究问题 / 构念 | 首选方法 | 主要估计量 | 最低数据结构 | 关键假设 / 检查 | 不适用或不能推出 |
|---|---|---|---|---|---|
| 目标能力是否被任务内容代表 | 构念蓝图 + 独立专家内容审查 | I-CVI、S-CVI/Ave、S-CVI/UA、CVR、Aiken's V；分歧记录 | 能力/风险全集、任务到构念映射、逐专家逐条目评分 | 专家领域覆盖、评分锚点理解、独立盲评、内容全集边界 | 不能单独证明结构效度、预测效度或总分权重 |
| 题目是否区分目标能力水平 | IRT（仅 Capability 且假设适用时） | 难度 b、区分度 a、题目信息、能力估计及 SE | Agent/配置 × Task 的二元或有序响应矩阵；重复运行元数据 | 单/多维结构、局部独立、单调性、模型拟合、DIF、参数可识别 | 不能把难度或区分度直接当作题目质量；不适合小样本/强依赖数据硬拟合 |
| 结果波动来自哪些测量条件 | G-Theory G-study / D-study | 方差分量、相对 G 系数、绝对 Phi 系数、设计条件下的误差 | Agent × Task × Seed × Environment × Judge 的交叉或嵌套观测 | facet 的随机/固定定义、交叉/嵌套结构、方差分量可识别 | 不可将所有运行当作独立样本；不能脱离目标总体解释系数 |
| 连续评分的评分者一致性/重测 | ICC | ICC 及置信区间 | 同一对象由多个评分者/重复时点评分 | 明确模型、单次/平均测量、绝对一致/一致性 | 不可只报告 ICC；ICC 高不代表评分无偏或有效 |
| 分类/序数判断的一致性 | Kappa / Krippendorff's Alpha 等 | 原始一致率、机会校正一致性、混淆矩阵 | 同一对象多名评审者的类别判断 | 类别尺度、评审人数、缺失、类别基率 | 不得挑选数值最高的统计量；AC1 不应被当作 Kappa 的可互换替代 |
| LLM Judge 是否有效且校准 | 独立人工参考 + 多标签可接受答案 + 偏差实验 | Sensitivity、Specificity、False Pass/Fail、Brier、校准曲线、偏差效应 | 冻结轨迹、独立专家评分、Judge 输出/置信度、扰动条件 | 人工评分不确定性、盲法、参考集独立、Judge 版本冻结 | 一致性不等于效度；单一多数票可能抹去合理分歧 |
| 评价器能否检出已知缺陷 | 盲测缺陷注入 + 真实故障回放 | 按缺陷类别的检出率、漏检率、误报率、失败暴露率 | 基线数据集、非等价变异、独立确认标签、未变异对照 | 变异有效性/等价性审查、盲测、类别和严重度分层 | Mutation Score 不等于真实故障检出率 |
| 结果能否泛化到新数据集/Agent/域 | 外部效标验证 + 分组留出 | 相关/预测误差、校准、外部检出率、决策损失 | 不同来源家族/任务模板/Agent/领域的独立数据 | 分组切分、防泄漏、效标独立、适用范围预注册 | 不能把同源近重复拆到训练与测试两侧 |
| 样本量是否足以回答研究问题 | 目标参数精度规划 + Monte Carlo / Power Analysis | 预期 CI 宽度、功效、最小有意义效应 | 先验方差/基率/聚类结构/设计参数 | 规划假设透明、模拟覆盖真实设计、停止规则预注册 | 不存在跨方法统一的最小 N |
| 候选综合分是否值得启用 | 独立公式验证 | 外部预测增量、缺陷检出、决策损失、校准、稳健性 | 开发、校准、锁定验证、外部复现分组 | 无泄漏、冻结分析计划、基线对照、敏感性分析 | Schema Validator PASS 不证明公式有效 |

## 2. 内容效度与专家盲评

### 2.1 要测量的构念

内容效度关注评测任务和评分要求是否充分代表预先声明的目标能力、业务规则、风险或行为范围。它不是“专家是否喜欢这道题”，也不是把专家打分平均后得到一个质量总分。

每条任务至少审查：
- **相关性（relevance）**：任务是否需要目标能力/行为；
- **代表性（representativeness）**：任务是否覆盖构念蓝图中的重要方面；
- **清晰性（clarity）**：输入、约束、初始状态和成功条件是否明确；
- **必要性（essentiality）**：该任务/要求是否为测量目标所必需；
- **可观察性（observability）**：评分证据能否从输出、状态或轨迹中复核。

专家首轮应独立、盲评，不展示 Builder 自评、候选公式分数或其他专家评分。保留逐专家原始数据和理由；分歧先分析，不先强制仲裁成唯一标签。

### 2.2 统计定义

设 N 为专家数，某条目在四级相关性量表中被评为 3 或 4 的专家数为 n_e：
- I-CVI = n_e / N。
- S-CVI/Ave = 所有条目 I-CVI 的算术平均。
- S-CVI/UA = 获得全体专家一致认可的条目数 / 条目总数。
- Lawshe CVR = (n_essential - N/2) / (N/2)，其中 n_essential 是判断条目“必要”的专家数。
- Aiken's V = Σ(r_i - l_0) / [N(c - 1)]，其中 r_i 是评分，l_0 是量表最低分，c 是评分类别数。

这些统计量的评分问题不同：CVI 衡量相关性/内容覆盖意见，CVR 衡量必要性判断，Aiken's V 衡量有序评分相对量表范围的位置。不得互相替代，也不得将 S-CVI/Ave 直接解释为总构念效度。

### 2.3 样本量、区间与限制

- 专家人数应由构念覆盖、专家异质性、条目数量、评分成本和目标精度共同决定；不在产品层设统一 N。
- 小型专家组的比例统计不稳定。对 I-CVI 等二元认可比例报告分子、分母和 Wilson 或适用的精确区间；对 Aiken's V 报告适用的解析区间或基于专家/条目的分层重抽样区间，并说明方法。
- 同一专家评审多个条目时，条目评分并非完全独立。汇总不确定性时应考虑专家和条目的聚类结构。
- 记录专家招募标准、专业背景、利益冲突、评分培训、量表锚点、缺失、修改轮次和仲裁过程。
- 不将某个文献中针对特定专家数/量表设计的经验 cutoff 直接迁移为通用 Agent / Skill 门槛。

**工程落地：** 专家评审数据契约应存储匿名 reviewer_id、item_id、construct_id、rating_dimension、rating_scale、rating、reason、round、blind_status、adjudication_status；从原始记录计算项目级统计和区间，不能只存最终均值。

**主要证据：** [Lynn (1986), Determination and quantification of content validity](https://pubmed.ncbi.nlm.nih.gov/3640358/)；[Aiken (1985), Three Coefficients for Analyzing the Reliability and Validity of Ratings](https://doi.org/10.1177/0013164485451012)；[AERA/APA/NCME Standards](https://www.apa.org/science/programs/testing/standards)。

## 3. IRT：Capability 题目难度、区分度与信息量

### 3.1 构念和统计定义

IRT 的对象是目标能力水平与题目响应之间的概率关系。对于二元结果，可从 2PL 模型开始：

P(X_ij = 1 | θ_j) = 1 / [1 + exp(-a_i(θ_j - b_i))]

其中 θ_j 是 Agent / 配置 j 在预先界定能力构念上的潜在能力，b_i 是题目 i 的难度位置，a_i 是题目 i 对能力差异的区分度，P(X_ij=1) 是在模型条件下通过题目 i 的概率。

2PL 的题目信息为 I_i(θ) = a_i² P_i(θ)[1-P_i(θ)]；测试信息为 I(θ) = Σ_i I_i(θ)，条件标准误近似为 SE(θ) = 1 / √I(θ)。

### 3.2 适用前提与检查

- 明确能力构念；若数据实际上测量多个能力，不应强行拟合单维 IRT。
- 检查局部独立、单调性、维度结构、题目拟合、残差相关和参数可识别性。
- Agent × Task 的观测需记录模型、工具、环境、提示、种子和版本。相同 Agent 的重复运行、相似任务和共享环境可能产生依赖，不能简单当作独立 person-item response。
- 检查 DIF / 测量不变性：不同模型家族、工具权限、语言、领域或环境下，同等目标能力是否出现系统性题目差异。
- 先评估 1PL / Rasch、2PL 等模型的适配，再考虑更复杂模型。复杂模型必须证明额外参数可识别且有预测/测量收益。

### 3.3 样本量和不确定性

不采用“每题固定 100/200 个样本”之类统一规则。按预期题目参数、能力分布、题目难度覆盖、缺失机制、模型维度和目标估计精度开展 Monte Carlo 参数恢复模拟：
1. 定义数据生成模型和候选参数范围；
2. 模拟 Agent 能力分布、题目参数、响应和缺失；
3. 按计划模型拟合；
4. 评估参数偏差、RMSE、区间覆盖率、收敛和模型选择；
5. 改变 Agent 数、题目数、每个 Agent 重复运行数及能力覆盖；
6. 选择满足预先设定精度目标的设计，记录敏感性。

置信区间可使用模型标准误、参数 Bootstrap 或适当的贝叶斯后验区间。Bootstrap 重抽样单位必须尊重 Agent / 数据集 / 来源家族聚类。

### 3.4 不适用情况

- Regression 的主要目标是检出已知版本退化，不应以 IRT 取代配对回归检验。
- 题目极易/极难可能在目标能力范围内提供很少信息，但这不等于题目本身无效；要结合目标能力区间判断。
- 低区分度可能来自能力范围不足、样本太少、评分器噪声、任务混杂或构念不一致，不能单因 a_i 低就删除题目。
- 如果局部独立或维度假设明显不成立，改用分层/非参数分析并报告限制，不强行输出参数。

**工程落地：** ERA 收集可配对的 Agent × Task 响应矩阵；IRT 分析模块保存模型公式、拟合诊断、参数区间、DIF 结果、软件/版本和数据切分哈希。当前项目不应在缺少真实响应矩阵时输出 IRT 参数。

**主要证据：** [Vania et al. (2016), Building an Evaluation Scale using Item Response Theory](https://doi.org/10.18653/v1/D16-1062)；[Schroeders & Gnambs (2025), Sample-Size Planning in Item-Response Theory: A Tutorial](https://doi.org/10.1177/25152459251314798)。

## 4. Generalizability Theory：分解 Agent 运行误差

### 4.1 构念和设计

G-Theory 估计观测分数波动来自哪些 facet 及其交互。可考虑对象（Agent / Agent+Skill 版本）、Task、Seed / Occasion、Environment、Judge / Rater。这些 facet 可能是随机或固定，可能交叉或嵌套。设计应由预期推广范围决定，而不是为了套用模型将所有 facet 都声明为随机。

### 4.2 G-study 与 D-study

- G-study：在已执行设计上估计方差分量，如 Agent、Task、Seed、Environment、Judge 主效应及相关交互。
- D-study：使用 G-study 方差分量，模拟不同 Task 数、Seed 数、Judge 数和环境覆盖下的测量精度，回答“如果改变测量设计，误差会怎样变化”。

相对排序通常关注相对误差，对应 G coefficient；绝对决策还要考虑 Task / Rater / Environment 等 facet 的主效应，对应 Phi coefficient。概念上：

G = σ²_object / (σ²_object + σ²_relative_error)

Phi = σ²_object / (σ²_object + σ²_absolute_error)

具体误差方差项由 crossed / nested 设计和固定/随机 facet 决定，不能在未定义设计时套一个通用展开式。

### 4.3 样本量与区间

- 优先设计可识别主要误差来源的交叉数据，例如同一批 Agent 在共同任务上运行，并对共同轨迹使用多 Judge 评分。
- 若真实环境导致部分任务/环境只能嵌套，明确记录不可分离的方差项和混淆来源。
- G-study 的对象数、每个 facet 的水平数应通过方差分量估计精度模拟或先导数据决定；D-study 不能补救原始设计中不可识别的方差分量。
- 报告方差分量、标准误/区间、设计结构、目标 universe、相对/绝对决策类型和 D-study 假设。
- 当数据集/Agent/环境簇数量很少时，方差分量可能不稳定；应报告不确定性，不只报告一个 G/Phi 系数。

**工程落地：** Runtime Record 必须保留 task_id、agent_revision、model、seed、environment_id、judge_version、run_id 和有效性状态。先输出分层方差分析与设计说明，再实现通用 G-Theory 估计；不能把同一任务同一环境的多次运行当作独立任务样本。

**主要证据：** [Brennan / NCME Generalizability Theory module](https://dev.ncme.org/wp-content/uploads/2025/10/Module-14-Generalizability-Theory-Brennan-Winter-1.pdf)；[Generalizability Theory Made Simple(r)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6699529/)。

## 5. ICC、Kappa 与评分者一致性

### 5.1 连续/近似连续评分：ICC

ICC 用于连续评分的评分者间、评分者内或重测可靠性。报告时必须同时指定 Model（one-way random、two-way random 或 two-way mixed）、Type（single measure 或 average measure）、Definition（consistency 或 absolute agreement）、具体 ICC 形式及 95% CI，并说明评分者是否代表可推广的评分者总体、是否每个对象都由相同评分者评分。

例如，双向随机、绝对一致、单次评分常写作 ICC(2,1) / ICC(A,1)；双向混合、绝对一致或一致性设计需按实际目的选择对应形式。不能仅因常见就固定使用 ICC(2,k)。

### 5.2 分类/序数评分

- 两名评审者名义分类：Cohen's Kappa；
- 多名评审者：按设计考虑 Fleiss' Kappa 或 Krippendorff's Alpha；
- 序数类别：使用加权 Kappa 或序数 Krippendorff's Alpha，并预先说明权重距离；
- 存在缺失或评审者数不等时，优先选择能明确处理该数据结构的方法。

Kappa = (P_o - P_e) / (1 - P_e)，其中 P_o 为观察一致率，P_e 为边际分布下的机会一致率。必须同时报告原始一致率、类别基率、混淆矩阵和置信区间。

Gwet AC1 可作为对特定基率情形的补充敏感性分析，但其机会模型与 Kappa 不同，不可视为可互换替代，更不能挑选较高的一个作为主结果。

### 5.3 适用条件和工程实现

- 同一冻结轨迹由多位专家评分，才能估计 inter-rater agreement。
- 同一冻结轨迹在不同时间/重复 Judge 调用，估计 Judge test-retest；这不是 Agent 重复运行稳定性。
- 报告评分者构成、缺失、类别分布、CI 和分歧案例。
- 若评分标准本身允许多个合理解释，先建立可接受响应集合或多标签参考，再评价 Judge，不应强制单一多数票 Gold。

**主要证据：** [Koo & Li (2016), A Guideline of Selecting and Reporting Intraclass Correlation Coefficients](https://doi.org/10.1016/j.jcm.2016.02.012)；[Gwet AC1 comparison (2023)](https://pubmed.ncbi.nlm.nih.gov/37234937/)。

## 6. Judge 校准与有效性

### 6.1 要分别验证的属性

1. **准确性/效标一致性**：Judge 与独立人工/Oracle 参考之间的误判。
2. **可靠性**：同一冻结证据重复评分的一致性。
3. **校准**：Judge 给出的概率/置信度是否与实际正确频率相符。
4. **偏差**：位置、长度、措辞、格式、模型自偏好、工具轨迹可见性等是否系统改变判断。
5. **可判定性**：是否能正确 abstain / UNKNOWN，而非强制输出 PASS/FAIL。
6. **泛化**：在不同任务域、Agent/Skill、模型和 Rubric 上是否仍有效。

### 6.2 统计量

对于二元 Oracle 标签，报告完整混淆矩阵：
- False Pass Rate = 被 Oracle 判定为失败、但 Judge 判为 PASS 的数量 / Oracle 确认失败数量；
- False Fail Rate = 被 Oracle 判定为通过、但 Judge 判为 FAIL 的数量 / Oracle 确认通过数量；
- Sensitivity / Specificity、Precision / Recall 及其区间；
- Abstention Rate = UNKNOWN/无法判定数量 / 全部评分请求数。

若 Judge 输出经过验证的概率 p，可报告 Brier Score = mean[(p-y)²]、Log Loss、校准曲线和适当的分组校准分析。若 Judge 只输出标签，不得伪造概率或将自报 confidence 当作已校准概率。

对有合理多答案的评分任务，收集多名专家的可接受响应集合/评分分布。Judge 与该集合的关系应按预先定义的容忍规则评价，避免 forced-choice Gold 把合理解释错误地标为错误。

### 6.3 校准实验

- 按来源家族/任务模板划分校准集和锁定验证集。
- 冻结 Judge 模型、提示、Rubric、温度、工具和解析版本。
- 用独立人工数据做概率校准；任何温度/阈值调优只在校准集完成。
- 在锁定集上一次性报告误判、校准和偏差结果。
- 做位置互换、语义等价改写、证据顺序变化、输出长度扰动、关键证据删除等配对实验。
- 保留 abstention，不将其默认折算为通过或失败。

**主要证据：** [Guerdan et al. (NeurIPS 2025), Validating LLM-as-a-Judge Systems under Rating Indeterminacy](https://proceedings.neurips.cc/paper_files/paper/2025/file/a309239c11a28c597d050bd4a1752d32-Paper-Conference.pdf)；[Judging the Judges (GEM 2025)](https://aclanthology.org/2025.gem-1.33/)。

## 7. 缺陷注入与真实故障检出

### 7.1 指标定义

对非等价且经独立确认的注入缺陷：
- Defect Detection Rate = 检出的有效缺陷数 / 有效注入缺陷总数；
- Miss Rate = 未检出的有效缺陷数 / 有效注入缺陷总数；
- False Alarm Rate = 未注入缺陷的基线/对照样本中被错误报告缺陷的数量 / 未注入缺陷总数；
- Failure Exposure Rate = 已确认失败中产生了可观察、可审计失败证据的数量 / 已确认失败总数。

“发现缺陷”和“暴露失败”必须分开记录。结构检查器捕获预先编码的 JSON 错误，只能证明对应规则实现工作，不能证明语义缺陷检出能力。

### 7.2 设计要求

- 每个变异有唯一 ID、算子版本、目标字段、预期影响、独立确认者、严重度和等价性状态。
- 一次优先只注入一个缺陷；复合缺陷单独分层。
- 评价器和审查者不知道变异标签；保留未变异对照。
- 按缺陷类别、严重度、数据集家族报告检出和误报，不只报告总比例。
- 历史真实故障回放单独作为外部效标，不混入 mutation denominator。
- 同一来源派生的多个变异属于同一 cluster，统计时按来源家族聚类。

### 7.3 样本量和不确定性

二项检出率可报告 Wilson 或适用的精确二项区间。样本量由目标区间宽度或对比检出率差异的功效模拟决定；若同一基线生成多个变异，使用 cluster bootstrap / 分层模型，而非按变异条目独立计算窄区间。

**主要证据：** [Papadakis et al. (ICSE 2018), Are Mutation Scores Correlated with Real Fault Detection?](https://doi.org/10.1145/3180155.3180183)。该研究指出控制测试套件大小后，Mutation Score 与真实故障检出的相关性较弱；变异测试可用于指导改进，但不能代替真实故障效标。

## 8. 外部效标效度与候选公式验证

### 8.1 外部效标的独立性

可选外部效标包括独立专家盲评的内容/可执行性判断、独立 Gold Oracle 对真实 Agent 运行的结果与过程判定、历史生产故障检出与失败暴露、新旧版本配对回归的已确认退化，以及不同模型/环境/领域的能力测量精度。

效标必须独立于候选公式的输入和生成过程。若专家评分已经被用于构建权重，不得再将同一评分数据称为外部验证效标。

### 8.2 统计方法选择

| 效标类型 | 候选统计量 | 必须补充 |
|---|---|---|
| 二元通过/失败 | Sensitivity、Specificity、PR-AUC / ROC-AUC、Brier、校准曲线 | 基率、误放行成本、阈值独立验证、CI |
| 有序等级 | 加权 Kappa、序数回归、等级校准 | 等级边界、类别频率、分歧分布 |
| 连续效标 | Spearman / Pearson、MAE / RMSE、校准和残差 | 非线性、异常值、测量误差、区间 |
| 配对新旧版本 | McNemar exact / mid-p、配对差值区间、配对 Bootstrap | 不一致配对数、效应方向、任务级变化 |
| 缺陷检出 | 按类别的检出率、漏检、误报、成本 | 非等价变异确认、真实故障独立复核 |

相关性只说明关联，不证明因果，也不自动证明决策阈值有用。AUC 不替代概率校准；总体 Accuracy 不能掩盖低基率关键缺陷的漏检。

### 8.3 数据切分与泛化

按 Dataset Family、来源家族、任务模板、Agent/Skill 和领域分组，拆分开发、校准、锁定验证和外部复现。语义近重复、同一来源的派生样本和同一事故的变体不得跨分区泄漏。锁定验证失败后，修订公式必须使用新的独立验证数据。

**主要证据：** [OECD/JRC Handbook on Constructing Composite Indicators](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf)。

## 9. 样本量、统计功效与区间策略

### 9.1 规划原则

样本量规划的输入必须包括主要估计量/假设、最小有意义效应或目标区间半宽、预期基率/方差/类别不平衡、任务/来源/Agent/环境/Judge 的聚类或配对结构、缺失/无效运行/Abstention/重复运行率，以及显著性水平、目标功效和多重比较计划（仅适用于确认性假设检验）。

功效不是“样本够大”的同义词。对于估计目的，应优先按精度规划；对于假设检验，才按最小有意义效应和目标功效规划。不能在结果出来后反向选择样本量或主要终点。

### 9.2 常用设计的近似与首选方法

- 独立二项比例的粗略精度近似：n ≈ z²(1-α/2) p(1-p) / d²。该式只适用于简单独立抽样的初步估计；最终应使用 Wilson 区间宽度数值求解，并对聚类设计调整。
- 聚类设计可用 Design Effect ≈ 1 + (m-1)ρ 作初步近似，其中 m 是平均簇大小，ρ 是簇内相关；簇大小不等时需要更合适的设计效应或模拟。
- 配对连续差异的初步规划：n ≈ [(z_(1-α/2)+z_(1-β)) σ_d / Δ]²；σ_d 是配对差值标准差，Δ 是最小有意义差异。最终应模拟实际缺失和聚类。
- McNemar 检验的功效主要由不一致配对（b、c）数量及方向决定，不能用两个独立比例的公式代替；优先基于预期不一致比例进行 exact / simulation-based power。
- IRT、G-Theory、复杂分层模型和 Judge 校准优先 Monte Carlo：模拟数据生成过程、缺失和真实分层结构，检验偏差、RMSE、区间覆盖、收敛和目标功效。

### 9.3 区间和重抽样单位

| 数据结构 | 建议区间/方法 | 重抽样单位 |
|---|---|---|
| 独立二项比例 | Wilson score；极小样本/边界情况考虑 exact | 独立试验单位 |
| 配对二元结果 | McNemar exact / mid-p；配对差值适用的 score CI | 配对任务 |
| 连续/序数评分 | 模型区间或分层/聚类 Bootstrap | 评分对象或更高层级 cluster |
| 多任务嵌套于数据集/领域 | Cluster Bootstrap / hierarchical model | Dataset Family / Domain |
| IRT 参数 | 模型标准误、参数 Bootstrap / posterior interval | 按 Agent / 任务设计结构 |
| G-Theory 方差分量 | 方差分量区间或参数 Bootstrap | 按原始 crossed / nested 设计 |
| Judge 误判 | 二项区间 + 分层/聚类分析 | 独立轨迹/来源家族 |
| 多重缺陷注入 | 分层二项/层级模型或 cluster bootstrap | 基线数据集/来源家族 |

当独立 cluster 数量很少时，普通 cluster bootstrap 也可能不可靠；应披露限制，必要时仅做描述性报告或采用有明确假设的层级模型。所有比例必须同时报告分子、分母和缺失/排除数量。

## 10. 公式启用的证据门禁

候选综合公式要同时证明：
1. 内容效度：维度和条目代表预定构念；
2. 内部结构：仅在反映性模型有理论依据时检查因子/潜变量结构；
3. 外部效标：独立效标上的预测或决策表现；
4. 缺陷检出：盲测缺陷及真实故障回放；
5. Judge 有效性：评分器准确性、校准、偏差和可判定性；
6. 可靠性：评分者、任务、种子、环境的误差来源和重复性；
7. 稳健性：指标、权重、归一化、聚合、抽样变化下的排序/决策稳定性；
8. 阈值：由用途、基率和错误损失推导，并在锁定集验证；
9. 泛化：不同来源家族、Agent/Skill、模型和环境的外部复现；
10. 可重复性：数据、代码、环境、种子和分析计划可复现。

任何一项关键证据缺失时，不得以其他维度高分补偿。默认输出多维质量画像；标量分数保持 NOT_VALIDATED。

## 11. 参考文献与迁移边界

- [AERA, APA, NCME: Standards for Educational and Psychological Testing](https://www.apa.org/science/programs/testing/standards)：效度针对分数解释和用途的证据论证。
- [Lynn (1986)](https://pubmed.ncbi.nlm.nih.gov/3640358/)：内容效度量化基础；迁移时须注意专家数与量表设计。
- [Aiken (1985)](https://doi.org/10.1177/0013164485451012)：有序专家评分的 V 系数；不等同于构念权重。
- [Koo & Li (2016)](https://doi.org/10.1016/j.jcm.2016.02.012)：ICC 模型/类型/定义的选择和报告。
- [Gwet AC1 comparison (2023)](https://pubmed.ncbi.nlm.nih.gov/37234937/)：说明 AC1 与 Cohen's Kappa 的机会模型不同，不可互换。
- [Schroeders & Gnambs (2025)](https://doi.org/10.1177/25152459251314798)：IRT 样本量应基于 Monte Carlo 参数恢复和目标精度。
- [Brennan / NCME G-Theory module](https://dev.ncme.org/wp-content/uploads/2025/10/Module-14-Generalizability-Theory-Brennan-Winter-1.pdf)：G-study / D-study、facet 设计与方差分量。
- [Guerdan et al. (NeurIPS 2025)](https://proceedings.neurips.cc/paper_files/paper/2025/file/a309239c11a28c597d050bd4a1752d32-Paper-Conference.pdf)：Judge 验证需要处理 rating indeterminacy。
- [Papadakis et al. (ICSE 2018)](https://doi.org/10.1145/3180155.3180183)：Mutation Score 与真实故障检出之间存在混杂和有限预测力。
- [OECD/JRC Composite Indicators Handbook](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf)：复合指标构建、聚合、不确定性和敏感性分析。

以上心理测量、教育测量和软件测试方法是可迁移的研究工具，不是 Agent / Skill 数据集的现成行业标准。每个方法必须在本项目真实数据结构上重新检查假设。
