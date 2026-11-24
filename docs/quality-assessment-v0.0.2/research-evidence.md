# v0.0.2 研究证据库

> 本文区分正式发表研究、标准/方法指南、开源工程实践和预印本。文献提出的方法不自动等于适用于本项目；所有迁移均需说明适用范围和验证限制。

## 1. Agent Benchmark 有效性

### 1.1 Agentic Benchmark Checklist（ABC）

- 论文：Zhu et al., Establishing Best Practices in Building Rigorous Agentic Benchmarks
- 发表：NeurIPS 2025 Datasets and Benchmarks Track
- DOI：https://doi.org/10.52202/085713-5547
- 论文页：https://proceedings.neurips.cc/paper_files/paper/2025/hash/f316275b44ee2de533102913828a8107-Abstract-Datasets_and_Benchmarks_Track.html
- Checklist：https://uiuc-kang-lab.github.io/agentic-benchmarks/

**证据与贡献：** 研究分析 Agentic Benchmark 的 Task Validity 与 Outcome Validity 风险，并给出可操作的 Benchmark Reporting 建议。论文指出，任务设计或奖励设计缺陷可导致相对性能估计出现最高 100% 的偏差；在 CVE-Bench 上应用 ABC 后，性能高估减少 33%。

**适用性：** 直接支持离线任务有效性、判定器/Outcome 有效性、运行环境和报告质量的审查设计。

**限制：** ABC 是检查清单，不是经过验证的通用 Dataset Quality 加权评分公式；个别条目需要按 Agent / Skill 任务形态适配。

### 1.2 Construct Validity Checklist

- 论文：Bean et al., Measuring what Matters: Construct Validity in Large Language Model Benchmarks
- 发表：NeurIPS 2025 Datasets and Benchmarks Track
- DOI：https://doi.org/10.52202/085713-0590
- 论文页：https://proceedings.neurips.cc/paper_files/paper/2025/hash/1967e0fc3aa6cbbace562f5cb8e3954e-Abstract-Datasets_and_Benchmarks_Track.html
- Checklist：https://oxrml.com/research/measuring-what-matters/checklist/

**证据与贡献：** 29 名专家参与系统性审查 445 个 LLM Benchmark，提出八项构念效度建议：定义现象、只测目标现象、代表性样本、说明数据复用限制、污染防护、统计比较、错误分析、效度论证。

**适用性：** 为“任务是否测量目标能力，而非混入无关能力”提供直接依据；适用于 Agent 与 Skill。

**限制：** 该研究审查的是 LLM Benchmark，不提供本项目的权重、阈值或通用评分公式。

### 1.3 BetterBench

- 论文：BetterBench: Assessing the Quality of AI Benchmarks
- 发表：NeurIPS 2024 Datasets and Benchmarks Track
- 入口：https://arxiv.org/abs/2407.21579

**适用性：** Benchmark 生命周期、设计、实现、文档、维护和退役的系统性检查。

**限制：** 评价对象是 Benchmark 整体生命周期，不等价于单条 Agent 任务的运行效力；条目评分不构成本项目公式的效度证据。

## 2. 测量学与效度论证

### 2.1 Standards for Educational and Psychological Testing

- 联合发布：AERA、APA、NCME
- 官方入口：https://www.apa.org/science/programs/testing/standards
- NCME：https://ncme.org/resources/books/testing-standards/

**核心原则：** 效度是对分数解释和用途的证据支持，而不是测试本身拥有一个永久不变的“有效”标签。证据涉及测试内容、反应过程、内部结构、与其他变量的关系以及测试后果。

**适用性：** 本项目必须声明分数用于什么判断，并为该判断收集多来源证据。Capability 与 Regression 的分数解释不同，不能共用未经论证的阈值。

### 2.2 效度证据框架

- Current Concepts in Validity and Reliability：https://pubmed.ncbi.nlm.nih.gov/16443422/
- PROM validity argument 方法综述：https://pmc.ncbi.nlm.nih.gov/articles/PMC5997725/

**适用性：** 用于组织内容、反应过程、内部结构、外部关系和后果证据。

**限制：** 心理测量工具与 Agent Benchmark 的对象不同；只能迁移效度论证结构，不能直接迁移心理量表阈值。

### 2.3 CTT、IRT 与 Generalizability Theory

- 心理/行为测量量表方法综述：https://pmc.ncbi.nlm.nih.gov/articles/PMC11798685/

**适用性：**
- CTT：观察分数包含测量误差的基本框架。
- IRT：在满足模型和数据条件时估计题目难度、区分度和能力区间的信息量。
- Generalizability Theory：将任务、Agent、运行种子、环境和评分者等误差来源分解。

**限制：** IRT 需要足够的 Agent × Task 响应数据和模型适配检验；G-Theory 需要明确交叉/嵌套设计；Alpha / Omega 不应被当作所有多维形成性质量指标的通用质量分。

## 3. 复合指标构建

### OECD / European Commission Joint Research Centre

- Nardo et al., Handbook on Constructing Composite Indicators: Methodology and User Guide
- 官方 PDF：https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf
- 欧盟 JRC 工具页：https://knowledge-for-policy.ec.europa.eu/publication/tools-composite-indicators-building-0_en

**核心贡献：** 复合指标需要明确理论框架、指标选择、缺失值处理、标准化、权重、聚合、相关性、补偿性，并执行不确定性与敏感性分析。应比较多种建模方案，而非把专家权重视为客观真值。

**适用性：** 作为候选综合分模型构建与稳健性验证的主要方法依据。

**限制：** OECD/JRC 手册是复合指标方法指南，不会自动给出 Agent Dataset 的正确权重或聚合函数。

## 4. 真实运行与回归测试有效性

### 4.1 Mutation Score 与真实故障检出

- Just et al., Are Mutation Scores Correlated with Real Fault Detection? A Large Scale Empirical Study
- ICSE 2018
- DOI：https://doi.org/10.1145/3180155.3180183

**主要发现：** 控制测试套件大小后，Mutation Score 与真实故障检出的相关性较弱；变异测试可指导测试集改进，但不能替代真实故障检出效标。

**适用性：** Regression Evaluation 可将变异缺陷检出作为一种实验信号，但不得将 Mutation Score 直接当作质量总分或真实故障检出率。

### 4.2 SkillsBench

- 论文入口：https://arxiv.org/abs/2602.12670
- GitHub：https://github.com/benchflow-ai/skillsbench

**证据与贡献：** 论文初始快照报告 86 个任务、11 个领域、7 种 Agent-model 配置和 7,308 条轨迹；采用无 Skill、精选 Skill、自生成 Skill 三种条件配对比较，并使用确定性 verifier。研究报告精选 Skill 平均提升 16.2 个百分点，但 84 个任务中有 16 个任务出现负向变化。该论文为 arXiv 预印本，不能表述为同行评审正式发表。

**当前版本注意：** SkillsBench 官网在 2026-11-24 标注 v1.1 为 87 个任务、8 个领域；其任务集与论文初始快照不是同一版本。官网：https://www.skillsbench.ai/ ，v1.1 发布说明：https://www.skillsbench.ai/blogs/skillsbench-1-1 。报告研究数字时必须绑定具体数据集版本，不能混用 86/11 与 87/8。

**适用性：** 真实 Skill 任务、Oracle、Verifier、Agent 条件对照和任务级效应异质性。

**限制：** 该基准面向 Skill 效用，不等价于通用 Dataset Quality 标准。

## 5. LLM Judge / Evaluator 验证

### 5.1 Validating LLM-as-a-Judge Systems under Rating Indeterminacy

- 发表：NeurIPS 2025
- DOI：https://doi.org/10.52202/085713-3751
- 论文页：https://proceedings.neurips.cc/paper_files/paper/2025/hash/a309239c11a28c597d050bd4a1752d32-Abstract-Conference.html

**贡献：** 指出人工评分本身可能存在多个合理解释，不能简单把多数票当作唯一无误的 Gold Label。Judge 验证需要处理评分不确定性。

### 5.2 Reliability without Validity（预印本，需持续跟踪）

- arXiv：https://arxiv.org/abs/2606.19544
- eScholarship：https://escholarship.org/uc/item/5gx838hq

**报告结果：** 对 21 个 Judge、多个 Benchmark 和约 54.1 万次判断进行研究，指出高重测一致性可以与位置偏差同时存在，且 Judge 排名会随 Benchmark 变化。

**适用性：** Judge 需分别检查一致性、偏差、与人工判断的关系和跨任务泛化。

**限制：** 预印本证据不应表述为同行评审正式发表；其建议中的样本次数和阈值不能未经实验直接变成通用门槛。

### 5.3 LLM Judge survey

- A survey on LLM-as-a-judge
- DOI：https://doi.org/10.1016/j.xinn.2025.101253
- 开放全文：https://pmc.ncbi.nlm.nih.gov/articles/PMC13237853/

**适用性：** Judge 校准、偏差、可靠性与 Meta-evaluation 的方法梳理。

## 6. 研究结论与当前禁止推断

目前证据支持建立多维质量评价、关键门禁、Judge 校准、真实故障检出、重复运行和效度论证流程；但尚不足以直接确定一个通用 Agent / Skill Dataset 的固定权重和阈值。

以下推断明确禁止：
- Alpha 高不等于数据集质量高。
- Mutation Score 高不等于真实缺陷检出能力高。
- Judge 重测一致性高不等于 Judge 无偏或有效。
- Schema 全通过不等于任务有效。
- 专家偏好权重不等于经过外部效标验证的权重。
- 某 Benchmark 上有效不等于跨 Agent / Skill、模型和领域有效。
- 运行通过率高不等于数据集质量高；可能是题目过易、覆盖不足或 Judge 宽松。

## 7. 后续补充研究要求

任务执行中需要进一步核实：
- IRT / G-Theory 在 Agent Benchmark 的适用设计与最小数据需求。
- Content Validity Index / Content Validity Ratio 的适用条件与专家样本设计。
- Krippendorff's Alpha、Cohen's Kappa、Gwet AC1 在低基率和多评审场景下的选择。
- Regression 的历史故障回放与缺陷注入效标之间的互补性。
- 数据集分层、域外验证和 contamination audit 的具体协议。
- 候选综合模型的非补偿聚合、模型不确定性和决策阈值选择。
