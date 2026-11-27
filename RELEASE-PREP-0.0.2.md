# Evaluation Dataset Builder v0.0.2 发布准备审计

**审计日期：** 2026-11-27  
**工作分支：** feat/quality-assessment-v0.0.2  
**开发 PR：** [#44](https://github.com/Kairos0922/evaluation-dataset-builder/pull/44)  
**基线版本：** 0.0.1（已正式发布）  
**目标版本：** 0.0.2  
**结论：** v0.0.2 已正式发布。发布前工程门禁、候选身份复核、安装包构建和发布执行均已成功；科学效度限制按发布说明保留。

## 1. 当前阶段总览

| 项目 | 当前状态 |
|---|---|
| 自主工程任务 | 22/22 DONE |
| 外部依赖任务 | 17 项按用户决定移出当前范围，不作为 DONE |
| PR #44 | 已合并（merge/tag commit `f6b722ca630dacf0fa73bacba1100cff1fafff0f`） |
| 当前正式版本 | 0.0.2（已发布） |
| 0.0.2 版本元数据 | main 的 VERSION 与 Skill frontmatter 已随 PR #44 合并为 0.0.2 |
| 0.0.2 专属发布门禁 | 已建立；手动发布工作流和精确 SHA 包构建工作流均通过 CI |
| 发布前精确候选 CI | Run #2099 SUCCESS；正式发布工作流 Run #45972007647 再次完成候选/合并/tree/CI/包验证并成功发布 |
| Release Candidate | 已通过精确 SHA 与 Git tree identity 核验 |
| Tag / GitHub Release | `v0.0.2` 已创建并正式发布 |

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

## 6. 发布执行记录

1. PR #44 已合并；候选 SHA `4362ab14e01e7b694851eef95877f238f7e2d8cc` 与合并提交 Git tree 完全一致。
2. PR #45 已合并，补齐在当前 GitHub 集成中可执行的 one-shot push trigger 路径；发布仍要求显式 `confirm_publish=true`、精确 PR #44 和候选 SHA。
3. 正式发布工作流 [Run #45972007647](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45972007647) SUCCESS：候选/merge/tree/CI 验证、依赖安装、包/Benchmark/离线测试、actionlint、正式 Skill ZIP 构建、Tag 与 Release 创建全部通过。
4. Tag `v0.0.2` 指向 `f6b722ca630dacf0fa73bacba110cff1fafff0f`；Release 地址为 [GitHub Release v0.0.2](https://github.com/Kairos0922/evaluation-dataset-builder/releases/tag/v0.0.2)。
5. 正式 ZIP 为 44,025 bytes，SHA-256：`a7de57496e9beeb7b776361d712af81a6b0a6c7ed42bd900d95d8c08081c7fc4`；包含 17 个白名单运行时文件。
6. 发布后审计 PR #46 已移除一次性 push trigger 和审批标记；保留手动显式确认入口，避免已完成的发布流程被误触发。

## 7. 发布判定

<badge>**PUBLISHED**</badge> v0.0.2 已正式发布。PR #44、PR #45 均已合并；发布工作流 Run #45972007647 SUCCESS；Tag、Release 与两项正式资产已通过 GitHub API 复核。

本审计记录的是工程发布完成，不代表被 D-009 移出当前范围的 17 项外部依赖任务已经完成，也不代表科学效度门禁已通过。真实证据边界继续以 RELEASE-NOTES-0.0.2.md 和质量报告为准。
