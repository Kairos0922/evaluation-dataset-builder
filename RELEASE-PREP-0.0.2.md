# Evaluation Dataset Builder v0.0.2 发布准备审计

**审计日期：** 2026-11-27  
**工作分支：** feat/quality-assessment-v0.0.2  
**开发 PR：** [#44](https://github.com/Kairos0922/evaluation-dataset-builder/pull/44)  
**基线版本：** 0.0.1（已正式发布）  
**目标版本：** 0.0.2  
**结论：** 工程研发任务已完成；发布准备正在进行；当前尚未形成可发布的 Release Candidate，也未获发布批准。

## 1. 当前阶段总览

| 项目 | 当前状态 |
|---|---|
| 自主工程任务 | 22/22 DONE |
| 外部依赖任务 | 17 项按用户决定移出当前范围，不作为 DONE |
| PR #44 | Draft / Open / 未合并 |
| 当前正式版本 | 0.0.1 |
| 0.0.2 版本元数据 | PR 分支 VERSION 与 Skill frontmatter 已同步为 0.0.2；main 稳定版本仍为 0.0.1 |
| 0.0.2 专属发布门禁 | 已建立；手动发布工作流和精确 SHA 包构建工作流均通过 CI |
| 最近完整 CI | Run #2083 SUCCESS，head a8071fd68c708bffcc1979518b74982552008bee；其后 VERSION/frontmatter 已升级为候选 0.0.2，Run #2089 已在版本元数据更新后的精确候选 head 上完成完整验证 |
| Release Candidate | 尚未批准/冻结 |
| Tag / GitHub Release | 未创建 |

## 2. 0.0.2 当前交付内容

### 用户可安装的正式 Skill

- 更新后的数据集构建流程、来源治理、覆盖设计、评分契约和变更影响修复方法。
- IDA/ERA 质量标准及机器可读报告 Schema。
- Runtime Record、Formula Validation、专家评审记录等契约。
- 运行时目录由 scripts/validate_skill.py 的白名单严格限定。

### 仓库研发与验证资产（不属于安装包）

- IDA 确定性离线评价器及报告验证器。
- ERA Runtime Record 导入、运行统计和报告验证工具。
- Capability 探索性 Rasch 1PL / G-Theory 分析器及模拟参数恢复工具。
- Judge Calibration 证据导入和报告契约。
- Round 4 Oracle/盲审资料包/Freeze Gate 工具。
- JSON/JSONL 严格解析、非有限数值拒绝、路径/哈希校验和失败安全测试。
- 完整研究协议、方法矩阵、实验设计、架构基线和证据报告。

## 3. 任务台账审计

当前 TASKS.md 活跃任务表保留 22 项，全部 DONE：需求 2、研究 3、设计 4、公式设计 2、实验设计/现有证据规范化 2、方案 1、实现 3、工程鲁棒性/CI 5。

17 项依赖外部资源、授权或独立证据的事项已依据 D-009 从当前执行范围移除。它们不再是本版本待办，但历史证据和未验证边界继续归档；不得将其描述为 DONE、NOT_APPLICABLE 或验证通过。

## 4. 真实证据与禁止推断

- Round 4：15 条用例中 3 条 Pilot，12 条 NOT_RUN；3 条已完成的独立 Gold Oracle 判定为 3/3 PASS。
- IDA：PARTIAL；Schema 15/15、来源引用 61/61 可解析、精确重复 0，但语义构念、可解性、Gold、Rubric 和泄漏等并未全部验证。
- ERA：PARTIAL；Judge NOT_RUN；Regression 无配对；重复运行稳定性未测量。
- Capability：当前真实数据仅 1 个配置 × 3 个用例，不能据此作总体能力或测量不变性结论。
- IDA mutation：8/8 合成确定性变异检出；4/4 预设 negative controls 保持指标投影不变。仅为工程敏感性/不变性证据。
- Rasch/G-Theory：只有指定模拟 DGP 下的参数恢复与样本设计敏感性证据，不是现实测量效度。
- 综合分、权重和阈值：NOT_VALIDATED，value=null；不得输出已验证总分。
- 四种宿主安装环境均为 DOCUMENTED_NOT_VERIFIED。

## 5. 过程产物清理审计

对工作分支递归 Git tree 检查：

- 根目录不存在被跟踪的 artifacts/ 临时输出目录。
- 运行时报告、模拟输出和测试生成文件通过脚本/CI 在执行时生成；不作为 Skill 运行时包内容。
- Round 4 盲审 ZIP 与 coordinator crosswalk 未作为仓库文件提交；仓库仅保留生成器、Schema、协议、哈希和审计说明。由于评审被用户暂缓，不分发、不招募、不再生成新的盲审包。
- tests/ 下 JSON/JSONL、Benchmark fixtures、模板和报告 Schema 均是回归测试输入，不是临时产物，必须保留。
- docs/ 下研究协议、证据索引、历史报告和决策记录是可审计研发资产，不作为安装包内容，不因“过程文件”名义删除。
- Skill 安装包以 validate_skill.py 的白名单为准；CI 必须证明无额外文件。
- 已删除过时的 .github/publish-release-trigger.txt，并将 v0.0.1 发布工作流改为仅支持显式确认的手动触发，避免合并分支时因旧 trigger 文件变化意外重跑旧版本发布流程。
- 当前未发现其他可安全删除的已跟踪临时构建产物；因此未删除测试夹具、协议或历史证据。

## 6. 发布前仍需完成的仓库内工作

1. 验证新增 .github/workflows/publish-release-v0.0.2.yml：Run #2095（45968288724，精确 head f9aa8822bf55458e76087ee9658c75bf96956226）已通过 actionlint、Skill package、Benchmark、265/265 离线测试、G-Theory 三种设计模拟、IDA controlled mutation 和 Round 4 IDA/ERA/Capability contracts；工作流仅 workflow_dispatch，confirm_publish 默认 false，并核验 PR 合并、候选 SHA、tree identity、精确 CI 与 VERSION。
2. 已在 PR 分支将 VERSION 与 Skill frontmatter 同步为 0.0.2，并同步 README、CHANGELOG、RELEASE.md；main 正式版本仍是 0.0.1。
3. 新增 package-release-candidate.yml，在每次 PR 更新时按精确 head 构建 Skill ZIP，并校验归档只含 17 个运行时白名单文件；当前候选 ZIP artifact 已生成，包内无脚本、测试、CI 或研究过程文件。
4. 对最终提交继续执行完整 CI，并核对最新精确 SHA 的候选包 artifact。
5. 用户批准后再合并、打 Tag 和发布；本次准备阶段不执行这些不可逆发布动作。

## 7. 发布判定

当前判定：**READY FOR FINAL REVIEW — NOT PUBLISHED**。Run #2095 已对精确 head 完成 265/265 测试、actionlint、Skill 包验证、Benchmark、G-Theory 模拟、IDA mutation 和 Round 4 IDA/ERA/Capability contracts；package workflow 已生成仅含 17 个运行时文件的 exact-SHA ZIP。手动发布 workflow 已通过 actionlint/CI，但未触发。PR 分支 VERSION/frontmatter 已同步为 0.0.2，main 稳定版本仍为 0.0.1。

尚未发布的原因是 PR #44 仍为 Draft/Open，尚未取得最终合并/发布批准；当前精确候选已具备工程验证和可下载的 Skill 包 artifact。当前科学限制必须作为产品范围说明披露，不得被版本准备工作抹除。

下一步按 RELEASE-GATE-0.0.2.md 执行。