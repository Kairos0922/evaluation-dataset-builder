# 独立外部评测集候选登记表

**状态：** 桌面研究初筛，尚未导入数据、执行运行或完成许可法务审查。本文只登记可供独立效标与缺陷实验使用的候选来源，不代表这些 Benchmark 已被认定为“黄金标准”。

## 1. 候选选择原则

外部参考集的作用是降低 Builder 自我验证偏差，并覆盖不同 Agent / Skill 构念。不能把不同平台、不同评分器、不同任务域的数据直接合并成一个总分。

纳入前逐项核验：
1. **独立来源**：不是由本仓库 Builder 生成，也不是同一数据集的近重复派生。
2. **任务与效标**：任务定义、初始状态、Ground Truth / Verifier、失败类别可审计。
3. **可运行性**：环境可重置、版本可固定、运行结果可复现；若是静态问答集，明确其不测量交互执行过程。
4. **许可边界**：分别核对代码、任务数据、环境镜像、第三方依赖和派生内容的许可；仓库 LICENSE 不自动覆盖数据和环境。
5. **泄漏风险**：区分公开开发集、隐藏测试集、加密任务、已进入训练语料的公开样本。
6. **统计独立性**：按来源家族、任务模板和环境切分，禁止近重复样本跨开发/验证/外部测试分区。

## 2. 候选矩阵

| 候选 | 主要构念 / 任务类型 | Oracle / 评分形式 | 许可与访问核验 | 初步用途判断 |
|---|---|---|---|---|
| AppWorld | 多 App、API 调用、跨步骤状态变更、交互式编码 Agent | 以数据库最终状态为基础的 evaluation programs；任务有 setup / solution / evaluation 程序 | 仓库代码公开部分 Apache-2.0；任务、App/API 实现与测试在加密 bundle 中，公开再分发及派生内容须保持加密 | **优先候选**：适合作为 Agent + 多工具工作流的独立外部效标；需先确认访问与加密数据处理合规，不能把任务明文复制进本仓库 |
| AgentDojo | 多工具 Agent 的提示注入防御、安全与效用 | 模拟环境中的用户任务效用和攻击目标成功情况；以环境状态评估，而非只评文本 | 官方仓库 LICENSE 为 MIT；依赖和外部模型调用仍需分别审查 | **优先候选（安全子域）**：用于风险覆盖、工具调用边界和缺陷注入；不能代表通用能力全域 |
| WebArena / WebArena-Verified（BrowserGym / AgentLab 生态） | 浏览器多站点、多步骤 Web Agent 任务 | 自托管网站环境、任务配置和执行轨迹；可运行任务级环境评价 | WebArena 与 BrowserGym 代码仓库 LICENSE 为 Apache-2.0；各 benchmark 数据、实例、网站镜像和第三方依赖仍需单独审查 | **优先候选（Web 子域）**：与现有 webapp-testing Skill 相关，但需防止同生态任务模板造成领域过拟合 |
| OSWorld / OSWorld-Verified | 桌面 GUI、多应用、多步骤操作 | 真实桌面 VM 中执行任务；提供本地评价流程和 Verified 版本 | OSWorld 代码仓库 LICENSE 为 Apache-2.0；VM 镜像、软件、外部账户和具体任务资产需逐项核验；公开 Verified Leaderboard 有维护者审核流程 | **第二阶段候选（Desktop 子域）**：有助于检验跨环境泛化，基础设施成本较高 |
| GAIA | 通用助手任务，涉及网页、工具、文件、图像等 | 以明确答案为核心的任务评价；分级任务，包含附件 | 官方 Hugging Face 数据集为 gated；测试答案和元数据受访问条件约束，维护者要求不要以可爬取形式重新分享 | **外部效标候选，不作直接任务导入**：适合检验多模态/工具使用问答结果；不等同于可重置的状态型工作流环境 |
| WorkArena / WorkArena++ | 企业知识工作、ServiceNow 浏览器流程、组合规划 | BrowserGym 环境任务；WorkArena++ 组合任务覆盖规划、推理与记忆 | WorkArena 代码仓库 LICENSE 为 Apache-2.0；ServiceNow 实例数据需要申请 gated access | **可选候选（企业工作流）**：任务域有价值，但环境访问和实例数据门槛较高 |

## 3. 证据与源链接

### AppWorld
- 官方仓库与任务环境说明：https://github.com/StonyBrookNLP/appworld
- 任务数据结构与状态评价：README 说明每个任务含 initial DB state 和 ground_truth；evaluation 以数据库状态为基础，而不是只看 Agent 进程输出。
- 许可说明：https://github.com/StonyBrookNLP/appworld#-license
- 关键限制：任务、App/API 实现、evaluation tests 等敏感部分存放于加密 bundle；不得将解密后的任务数据或派生内容以明文公开。

### AgentDojo
- 官方仓库：https://github.com/ethz-spylab/agentdojo
- 官方文档：https://agentdojo.spylab.ai/\n- 官方结果页：https://agentdojo.spylab.ai/results/（包含 utility、utility under attack、targeted ASR 和轨迹查看；官方明确说明结果组合不完整，不能视作公平排行榜）
- LICENSE：https://github.com/ethz-spylab/agentdojo/blob/main/LICENSE
- 关键限制：主要测量 prompt injection 下的安全与效用，不应将其安全结果外推为一般任务能力。

### WebArena / BrowserGym / AgentLab
- WebArena：https://github.com/web-arena-x/webarena
- BrowserGym：https://github.com/ServiceNow/BrowserGym
- AgentLab：https://github.com/ServiceNow/AgentLab
- BrowserGym 支持 MiniWoB、WebArena、WebArenaVerified、VisualWebArena、WorkArena 等不同任务包；每个任务包都需要独立安装与环境配置。
- 关键限制：框架统一不等于数据许可统一；每个 benchmark 的数据、环境镜像、站点和依赖都需要单独做许可与版本审计。

### OSWorld
- 官方仓库：https://github.com/xlang-ai/OSWorld
- README：https://github.com/xlang-ai/OSWorld/blob/main/README.md
- 关键限制：需要桌面 VM 和可复现初始状态；官方 Verified Leaderboard 的公开验证有维护者审核要求，不能把本地运行直接说成官方 Verified 结果。

### GAIA
- 官方数据集卡：https://huggingface.co/datasets/gaia-benchmark/GAIA
- 关键限制：数据集 gated；公开开发数据与隐藏测试数据要分开处理，禁止重新公开受保护测试内容。

### WorkArena
- 官方仓库：https://github.com/ServiceNow/WorkArena
- 关键限制：ServiceNow 实例数据需单独申请；仓库代码许可证不等于实例数据的访问授权。

## 4. 建议的验证集分层

不要把上述候选混成一个大样本池。建议先按任务与环境分层，独立报告：
- **API / Stateful workflow**：AppWorld。
- **Web browser workflow**：WebArena-Verified。
- **Security / prompt injection**：AgentDojo。
- **Desktop GUI**：OSWorld-Verified。
- **General assistant / multimodal QA**：GAIA（仅按其访问条款使用，不导入受保护测试数据）。

第一阶段优先取得 AppWorld、AgentDojo、WebArena-Verified 的许可与环境可行性确认。若 AppWorld 加密数据访问或许可不满足要求，则保留为不可用候选，不绕过加密或复制明文数据。

## 5. 如何用于本项目的实证验证

- **IDA 外部检验**：抽取任务说明、构念标签、Oracle/Verifier 规格、版本和来源元数据；由独立审查者评估任务清晰度、可解性、Ground Truth 支持、Rubric 对齐和覆盖声明。不要把原始受保护任务复制到本仓库。
- **ERA 外部效标**：在获准环境中运行冻结 Agent / Skill；保存原始轨迹、环境状态、Verifier 输出和配置哈希。将外部 Benchmark 作为独立数据集家族，避免与 Builder 自生成数据混合报告。
- **缺陷实验**：在允许修改的本地副本或自建 fixture 上进行非等价缺陷注入；不修改受保护测试集，不将外部 Benchmark 的任务答案用于 Builder 提示。
- **公式验证**：按来源家族留出，至少有一个完整 Benchmark 家族只用于外部验证；同一 Benchmark 的任务模板和近重复实例不得跨分区。
- **报告**：分别列出每个 Benchmark 的许可状态、覆盖范围、样本数、Oracle 类型、环境复现性、置信区间和限制；不先合并为单一“外部质量分”。

## 6. 当前结论

当前最有价值的组合不是寻找一个“万能 Benchmark”，而是建立跨任务族的外部效标：
- AppWorld 提供状态型多 App/API 工作流；
- WebArena-Verified 提供浏览器交互任务；
- AgentDojo 提供安全与提示注入任务；
- OSWorld-Verified 扩展到桌面 GUI；
- GAIA 补充通用工具使用与多模态问答结果。

本登记表仅完成桌面初筛。下一步必须逐个锁定具体数据版本、访问条款、数据哈希、Oracle 实现、环境镜像和可复现执行脚本，之后才可将候选升级为可用的独立参考集。
