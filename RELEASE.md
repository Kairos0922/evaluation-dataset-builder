# Evaluation Dataset Builder 0.0.1
**状态：** 已正式发布。Git Tag v0.0.1 与 GitHub Release 已创建；候选 SHA e934a079c88f729d8d66abee50a717797d88f9c3，发布目标提交 cacf86c3b5b68098aef4b969b1e5caa4653708f1。Builder 证据 PR #38 继续保持 Draft/Open。

## 版本范围

0.0.1 交付的是 Evaluation Dataset Builder Skill：用于 Agent、Skill、API、工作流和其他软件系统的评测数据集规划、生成、质量审查、修复与维护。正式安装包仅包含 skills/evaluation-dataset-builder/。仓库中的脚本、测试、Benchmark、GitHub Actions 和发布设施属于开发与验证资产，不是安装包的一部分。

安装时整体复制或上传 skills/evaluation-dataset-builder/，保持 SKILL.md 与 references/ 的相对路径不变。宿主具体安装方法见根目录 README。

## 模型与行为评测范围

- 生成、行为 Judge、Trigger Classifier 均使用 DeepSeek V4.1 Flash，API 模型 ID 为 deepseek-flash，端点为 https://api.deepseek.com。
- 三个角色采用分开的评测流程，但模型身份相同。本版本不宣称跨模型独立 Judge。
- 自动行为评测只加载 SKILL.md，未加载 references/*。它是入口指令文本代理评测，不等于宿主真实加载、参考资料读取或工具执行认证。
- 每个候选至少两次完整评测；每轮行为通过率至少 90%；Trigger Precision 和 Recall 均至少 95%；重复运行指标波动不超过 5 个百分点；匹配基线完整；所有行为与基线检查必须可判定。
- Trigger 评测至少 40 个样例。所有自动门禁与报告必须绑定精确候选 SHA。
- 评测费用保护上限为估算 10 美元。密钥或模型预检失败、额度不足、预算超限、请求结果不确定或 UNKNOWN 均不得被解释为通过；不得自动切换其他模型。

## 宿主验证状态

| 宿主 | 状态 |
|---|---|
| Codex | DOCUMENTED_NOT_VERIFIED |
| Claude Code | DOCUMENTED_NOT_VERIFIED |
| claude.ai | DOCUMENTED_NOT_VERIFIED |
| Claude API | DOCUMENTED_NOT_VERIFIED |

逐平台安装、发现、参考资料加载、工具调用、权限和清理认证不是 0.0.1 发布门禁。本版本不声称上述宿主已认证。

## 已核实的 Builder 与真实试运行证据

### Builder 正式输出与独立验证

- 实际 Builder 生产运行：[44959366258](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258)，Artifact 14729741906。运行绑定的 Builder 源提交为 eb1fa5c21e7b2320e0904bb1cb72a38854b9cbd8。
- DSH Trace 验证 PASS：退出码 0、530 个事件、恰好一次 Builder Skill 工具调用，9 个正式输出文件已归档。
- 必须披露：该次工作流中的 builder-production Job 结论为 **failure**，原因是生成后的启发式语义诊断标记了 WB-03-C3、WB-04-C2、WB-14-C2 三条 fail-condition。原始 Builder 输出没有被人工修改。人工语义复核认为这三条诊断误把测试 Skill 对应用偏差的发现与报告评价为原始应用结果；独立验证和后续原始输出重验证均通过。该 Job 不能记为绿色，具体诊断、复核依据和处理边界见 [Round 4 证据复用审计](docs/release-evidence/round4-evidence-reuse-audit.md)。
- 官方独立验证运行：[44968128127](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127)，Artifact 14732232796：PASS，1 个数据集、15 条用例、0 个 Schema 错误、61 条来源引用验证通过。
- 在最终 Pilot / Oracle 归档中，对同一 Builder 输出再次执行的独立输出验证也 PASS：1 个数据集、15 条用例、0 个 Schema 错误、61 条来源引用验证通过。原始 Builder、重放归档和最终 Pilot / Oracle 归档中的 wb-core.jsonl、source-map.json、wb-core.manifest.json 与 SUITE-MANIFEST.json SHA-256 完全一致。
- 证据索引与运行、Artifact ID、文件摘要保存在 [round4-evidence-index.json](docs/release-evidence/round4-evidence-index.json)。发布验证器会比较 Builder 执行提交、PR #38 当前 Skill 目录和 PR #42 Skill 目录的完整 Git tree；不会要求文档或测试代码的提交 SHA 与历史 Builder 执行 SHA 相同。

### 三条真实 Skill 试运行与 Gold Oracle

- WB-02 搜索缺陷检测和 WB-10 状态循环试运行来自 [Replay run 44980451933](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44980451933)。两份成功 Pilot Artifact 在最终归档中逐文件 SHA-256 比对，内容完全一致。
- 该次 Replay 中 WB-12 因外部额度原因未完成，不能使用其失败的早期 Oracle 结果作为最终证据。WB-12 后续仅针对冻结的 Builder 输出执行定向重试：[run 45189512695](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45189512695)，最终 Artifact 14824967038。
- 最终归档包含 WB-02、WB-10、WB-12 三条试运行的原始 DSH Trace、Runner、状态、截图及证据文件。WB-12 完成了一次允许的删除请求，HTTP 200，无重复删除或无关变更。
- 最终独立 Gold Oracle 在 run 45189512695 中完成复核：**3/3 PASS，0 FAIL，0 UNKNOWN**。WB-02 的业务结果是 EXPECTED_VIOLATION_DETECTED，即 Skill 正确发现应用搜索缺陷；WB-10 和 WB-12 的业务行为均 PASS。
- 未重新生成 Builder 数据集；未重跑已完成的 WB-02/WB-10；WB-12 仅执行了原计划中的一次定向完成试验。没有用合成样例替代真实 Builder 输出。

## 数据集质量限制

正式 Builder 输出为 1 个数据集、15 条用例。独立验证 PASS 不代表数据集质量状态是完全通过。当前数据集质量状态仍为 **needs_info**，未解决的信息缺口是 **BR-09 request-failure / error-recovery evidence**。数据集执行状态仍记录为 **NOT_RUN**；三条 Pilot 只代表被选中的三条用例已执行，不得推广为全数据集执行完成。

此外，Builder 生产工作流中三条启发式诊断仍保留为可见的失败诊断，尽管人工复核与独立验证支持其为语义范围误报。不得把这些诊断从历史记录中删除，也不得宣称 Builder 生产工作流本身为 PASS。

## 行为评测摘要

修复 Judge 证据提取时对 Markdown 格式标记的剥离问题后，代码候选 SHA 6868d38efd8a29b9b153dd5e70040382e296f8d9 的行为评测 [run 45287365898](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45287365898) 完成 PASS，报告 Artifact 14872207908。

| 指标 | Run 1 | Run 2 |
|---|---:|---:|
| Skill 行为检查 | 57/57 PASS | 57/57 PASS |
| Skill 行为通过率 | 100% | 100% |
| Trigger Precision | 100% | 100% |
| Trigger Recall | 100% | 100% |
| UNKNOWN | 0 | 0 |

- 40 个 Trigger 样例全部可判定；匹配基线完整；稳定性 spread 为 0 pp；所有自动评测门禁 PASS。
- 匹配基线 Run 1 为 57/57 PASS；Run 2 为 56/57 PASS，唯一失败为 SE07 语义去重：基线输出报告去重后 4 条，但没有说明原始 6 条的数量及去重后数量不膨胀的原因。该 FAIL 已保留，不得改成 PASS 或隐藏。
- Skill 平均通过率 100%；匹配基线平均通过率约 99.12%；平均 uplift 约 +0.88 个百分点。
- 报告记录 390,834 tokens，峰值价格估算实际费用约 USD 0.222123；176 个请求结果由检查点恢复复用，未完成或结果不确定的请求数为 0。
- 该报告绑定的是上述代码候选 SHA，不是之后的文档最终 SHA。文档与证据索引提交后，行为评测工作流将从该成功检查点进行显式兼容恢复。正式发布验证器只接受 report.git_sha 与最终 PR #42 head SHA 完全一致、且 workflow_run_id 和 Artifact 均对应的报告；历史 SHA 报告不能代替最终 head 报告。最终 head 的报告 Artifact 以 PR #42 同 SHA 的 Actions 检查为准。

## 发布门禁与批准边界

- [x] 安装包结构、Skill Schema、Actionlint 和离线回归验证已通过；最终文档提交的 exact-head CI 仍以该提交对应的 PR Checks 为准。
- [x] 真实 Builder 输出存在，DSH 调用轨迹 PASS，正式独立验证和输出重验证均 PASS；Builder 工作流启发式诊断失败如实保留并复核。
- [x] 三条真实 Skill 试运行及独立 Gold Oracle 3/3 PASS。
- [x] Builder 输出、独立验证、Pilot 和 Oracle 的 Artifact 证据索引与 SHA-256 绑定已建立；发布脚本会跨工作流校验，不会要求无必要重复执行。
- [x] BR-09 needs_info、数据集 NOT_RUN、宿主未认证和 Builder 诊断限制均已披露。
- [x] 已取得用户对发布的明确批准。
- [x] PR #42 已合并；完整发布验证、v0.0.1 标签创建和 GitHub Release 发布均已完成。
- [x] v0.0.1 标签已创建并绑定最终 merge commit，GitHub Release 已正式发布。

行为评测与 Builder 证据均通过本次完整发布门禁，用户已明确批准发布。v0.0.1 已正式发布；Builder 证据 PR #38 继续保持 Draft/Open。


## Validator correction evidence (2026-11-24)

The archived Builder output was revalidated after fixing the independent validator's false-positive semantic lint. PR #38 exact head `7f34ddb1a7b7594a819f05584c7373b7b3cb5242` CI passed. Validation run [45291624154](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45291624154), artifact `14874193103`, passed on the original immutable Builder output: 15 cases, 0 schema errors, 61 source references verified. No Builder call, Skill trial, or model call was repeated. The original Builder-production Job failure remains historical and disclosed; it is not reclassified.

## Release evidence

- Candidate PR head SHA: e934a079c88f729d8d66abee50a717797d88f9c3
- Merged main commit / tag SHA: cacf86c3b5b68098aef4b969b1e5caa4653708f1
- Release workflow run: 45443113681
- Evaluation workflow run: 45293177102
- Generator: deepseek-flash; Independent Judge: deepseek-flash
- Behavior mean / spread: 100.0% / 0.0%
- Trigger Precision mean / spread: 100.0% / 0.0%
- Trigger Recall mean / spread: 100.0% / 0.0%
- Matched baseline mean uplift: +1.7%
- Builder evidence PR: #38 at eb1fa5c21e7b2320e0904bb1cb72a38854b9cbd8
- Builder production run: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258
- Independently validated datasets / cases: 1 / 15
- Real Skill trials: 3 PASS (WB-02, WB-10, WB-12)

This release does not claim that each documented host's installation, discovery, reference-loading, and tool-integration path has been independently verified.



## v0.0.2 发布准备状态（2026-11-27）

v0.0.2 正在独立分支 feat/quality-assessment-v0.0.2 准备。当前 22 项自主工程任务全部完成，但版本仍未发布，正式 VERSION 与 Skill frontmatter 仍保持 0.0.1。0.0.2 的范围收缩、工程交付、真实证据限制和发布门禁见 [RELEASE-PREP-0.0.2.md](RELEASE-PREP-0.0.2.md) 与 [RELEASE-GATE-0.0.2.md](RELEASE-GATE-0.0.2.md)。本节不是 0.0.2 Release Notes，也不代表发布批准。
