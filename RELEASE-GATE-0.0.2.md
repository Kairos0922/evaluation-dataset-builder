# v0.0.2 发布门禁（范围收缩版）

**适用版本：** 0.0.2  
**文档状态：** 已执行；v0.0.2 正式发布于 2026-11-27  
**批准边界：** 本门禁通过不自动合并 PR、创建 Tag 或发布 GitHub Release。

## 1. 发布定位与范围

0.0.2 是 Evaluation Dataset Builder Skill 的质量评价工程能力增强版本，交付内容包括 IDA 离线数据集检查、ERA 运行记录分析、机器可读报告契约、Capability/Regression 分析设计与探索性工具、证据导入/校验工具及配套文档。

本次按用户决定收缩发布范围：当前迭代不承诺完成独立专家内容效度、外部 Gold/Oracle 扩展、第三方 Benchmark 全量接入、完整 Judge 校准、完整真实 Capability/Regression 效度、综合公式效度或宿主平台认证。这些事项不属于本版本当前交付范围，不得在发布说明中暗示已验证。

## 2. 必须通过的工程门禁

1. **精确提交身份**：Release Candidate 必须绑定 PR #44 最终 head SHA；合并后必须证明 main merge commit 的 Git tree 与候选 head tree 完全一致，或在最终提交上重新执行全部适用检查。
2. **正式 Skill 包**：scripts/validate_skill.py 通过；运行时目录仅包含白名单文件；frontmatter、VERSION 和文档版本一致。
3. **Schema 与数据契约**：全部 JSON Schema 可被 Draft 2020-12 validator 检查；IDA/ERA/Runtime Record/Formula/Judge/Capability/Oracle 等适用报告契约通过。
4. **离线回归**：完整 unittest 测试套件通过；Benchmark fixture 验证通过；actionlint 通过。
5. **安全与输入健壮性**：严格 JSON/JSONL 解析、非有限数值拒绝、路径/哈希校验和畸形输入失败安全回归测试通过。
6. **冻结证据复现**：Round 4 已归档数据的导入、IDA/ERA 分析和报告契约验证通过；不得启动新生产运行或把 SKIPPED 任务算作 PASS。
7. **文档一致性**：README、CHANGELOG、RELEASE.md、TASKS、质量报告和本门禁在版本范围、已知限制、指标状态上无矛盾。
8. **包清洁度**：安装包不包含开发脚本、测试、CI、私有证据、盲审协调资料或临时运行产物；Skill package validator 的白名单是最终依据。

## 3. 必须披露的证据限制

- Round 4 数据集 15 条用例中仅 3 条完成真实 Pilot，12 条仍 NOT_RUN。
- IDA 与 ERA 结果均为 PARTIAL；结构/引用检查 PASS 不证明语义正确、构念效度或来源主张支持。
- Judge 独立校准为 NOT_RUN。
- Regression 没有有效 baseline/candidate 配对记录。
- 真实数据不足以拟合 IRT、DIF、测量不变性或 G-Theory。
- IDA M01–M08 的 8/8 结果属于合成确定性变异敏感性测试；四个 negative controls 的 4/4 不变性结果样本很小，不证明语义缺陷检出或污染抵抗能力。
- Rasch/G-Theory 模拟仅为指定数据生成模型下的模拟参数恢复证据。
- 综合分、权重和阈值保持关闭：NOT_VALIDATED，value 为 null。
- Codex、Claude Code、claude.ai、Claude API 均未完成逐平台兼容性认证。

## 4. 发布流程

1. 用户确认本文件定义的收缩版产品范围与限制披露。
2. 完成版本元数据同步和 0.0.2 Release Candidate 文档。
3. PR #44 最终 head 完整 CI 成功，发布审查记录精确 SHA 与所有适用门禁。
4. PR #44 经用户明确批准后合并至 main。
5. 验证 merge commit tree 与 Release Candidate tree 一致；不一致则重新验证。
6. 用户明确批准后，创建 v0.0.2 Tag 并发布 GitHub Release。
7. Release 资产仅包含正式 Skill 包和本版本发布说明；研究/运行过程文件不作为安装包内容。

## 5. 明确禁止

- 不得把范围移除解释为科学验证通过。
- 不得把 CI、Schema、模拟或合成变异结果解释为真实效度。
- 不得重新启用外部评审招募、外部数据获取、收费模型调用或生产运行。
- 未取得明确批准，不得合并 PR、创建 Tag、创建/编辑 GitHub Release。

## 6. 正式发布执行结果（2026-11-27）

- PR #44 已合并；候选 SHA `4362ab14e01e7b694851eef95877f238f7e2d8cc` 与 merge commit `f6b722ca630dacf0fa73bacba110cff1fafff0f` 的 Git tree 一致。
- PR #45 修复了发布执行路径；正式发布工作流 [Run #45972007647](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45972007647) SUCCESS。
- Tag `v0.0.2` 已创建并指向 `f6b722ca630dacf0fa73bacba110cff1fafff0f`；GitHub Release 已发布：[v0.0.2](https://github.com/Kairos0922/evaluation-dataset-builder/releases/tag/v0.0.2)。
- 正式资产：Skill ZIP（44,025 bytes，SHA-256 `a7de57496e9beeb7b776361d712af81a6b0a6c7ed42bd900d95d8c08081c7fc4`）和 `RELEASE-NOTES-0.0.2.md`。
- 发布后审计保留本文件的原始门禁标准及科学限制，不将 17 项范围外任务或未验证实证条件记作通过。
