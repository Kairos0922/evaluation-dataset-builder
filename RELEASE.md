# 0.0.1 发布候选说明

**状态：** 发布候选，尚未正式发布。当前候选已完成 Round 4 Builder 正式生产、独立验证、三条真实试运行和 Gold Oracle 3/3 PASS；行为评测已对候选 SHA `c3ef8e5c9cfd156cec29ed7d63a803f32bb536ad` 完成并通过。后续仅因本次发布证据文档提交改变了候选 head SHA，需要在最终 head 上完成精确 SHA 行为评测绑定。发布仍需明确批准。

## 范围

通用 Agent Skill，用于评测数据集规划、生成、质量审查、修复和维护。正式安装包仅包含 `skills/evaluation-dataset-builder/`；仓库中的 `scripts/`、`tests/`、`.github/`、Benchmark 和发布设施属于开发与验证资产。

## 安装

可安装的 Skill 本体位于 `skills/evaluation-dataset-builder/`。将该目录整体复制或上传到目标宿主支持的 Skills 目录，保持 `SKILL.md` 与 `references/` 的相对路径不变。不同宿主的安装方式见根目录 `README.md`。

## 0.0.1 行为评测配置

- 生成、行为判分与触发分类均使用 DeepSeek V4.1 Flash，API 模型 ID 为 `deepseek-flash`，端点为 `https://api.deepseek.com`。
- 生成、Judge 和 Trigger Classifier 是分开的评测角色与调用流程，但使用相同模型身份。**本版本不宣称跨模型独立 Judge。**
- 每次候选 SHA 至少执行两次完整评测；匹配基线必须完整；所有检查均须可判定。
- 每次运行行为通过率至少 90%；Trigger Precision 和 Recall 均至少 95%；各指标重复运行波动不超过 5 个百分点。
- Trigger 评测至少 40 个样例；所有自动门禁、报告与检查点均绑定精确候选 SHA。
- 行为评测费用保护上限为 10 美元估算值。缺少凭证、模型预检失败、额度不足、预算超限或 UNKNOWN 均停止并阻断发布；不得自动切换第三方模型。
- 核心行为评测不要求在 Codex、Claude Code、claude.ai 和 Claude API 上重复运行。四种宿主安装说明不是兼容性认证。

## 宿主运行验证状态

| 宿主 | 当前状态 |
|---|---|
| Codex | DOCUMENTED_NOT_VERIFIED |
| Claude Code | DOCUMENTED_NOT_VERIFIED |
| claude.ai | DOCUMENTED_NOT_VERIFIED |
| Claude API | DOCUMENTED_NOT_VERIFIED |

逐平台安装、发现、参考资料加载、工具调用、权限和清理兼容性认证不是 0.0.1 发布门禁。不得把未实测环境标记为 PASS，也不得将单一宿主结果推广到其他宿主。

## 发布门禁

- [x] Skill 目录符合 Agent Skills 元数据、命名和结构要求。
- [x] 入口文件的按需资源引用完整，目录中无无关文件。
- [x] Schema、质量标准、引用路径、Actionlint 和离线测试通过。
- [x] Builder 正式生成的评测套件通过独立验证。
- [x] 三条真实 Skill 试运行完成并有可复核证据。
- [x] 独立 Gold Oracle 对三条试运行全部 PASS。
- [x] 两次行为评测均达到预设阈值（对最终 candidate head 的精确 SHA 复验/绑定待完成）。
- [x] 匹配基线完整，稳定性检查通过。
- [x] Builder 证据 Skill tree 与发布候选 Skill tree 完全一致。
- [ ] 发布 PR head 与最终 merge commit 的 Git tree 完全一致（合并后核验）。
- [ ] 发布标签绑定已验证的 merge commit（发布时核验）。

只有全部门禁通过并经明确发布批准后，才创建 `v0.0.1` 标签并发布 GitHub Release。结构验证或历史候选评测通过不等于正式发布批准。

## 当前候选状态

- Release PR #42：Draft/Open，目标 `main`；Builder 证据 PR #38：Draft/Open，保留实验记录，不合并。
- Round 4 formal Builder：15 cases；独立验证 PASS，0 schema errors，61 source refs verified；三条真实 pilot 和独立 Gold Oracle 3/3 PASS。证据复用审计见 `docs/release-evidence/round4-evidence-reuse-audit.md`。
- 评测数据集质量状态仍为 `needs_info`，原因是 BR-09 request-failure/error-recovery evidence gap。此限制已记录；不影响已完成三条 pilot 的结果，但不应对数据集完整性作过度承诺。
- 精确候选行为评测（SHA `c3ef8e5c9cfd156cec29ed7d63a803f32bb536ad`）：两次完整运行行为通过率 98.25% / 100%；Trigger precision/recall 100%/100%（40 cases）；基线完整；稳定性 spread 1.75 pp；所有自动门禁 PASS。Run 1 的 SE07 semantic-dedup criterion 失败，Run 2 通过，透明记录于 `docs/release-evidence/behavioral-evaluation-candidate-2026-11-24.md`。
- 行为评测范围仅加载 `SKILL.md`，未加载 `references/*`；不是宿主兼容性认证。本版本不宣称跨模型独立 Judge。
- 评测工作流 run `45224190260` 已成功完成，artifact `14842388182`；候选 head 因新增证据文档变更为 `977123bb6f6e311b4165941873952d5b67b041d6`，需在最终候选 head 上重新完成精确 SHA 评测。
- 当前没有 `v0.0.1` 标签或正式 GitHub Release。发布工作流仅在显式批准并核验所有门禁后执行。
