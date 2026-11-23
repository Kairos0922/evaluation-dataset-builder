# 0.0.1 发布候选说明

**状态：** 发布候选，尚未正式发布。Round 4 Builder 正式生产、独立验证、三条真实试运行和 Gold Oracle 3/3 PASS 已完成并复核。候选 SHA `99d07f20d81a144fd52ab47eb6f7934c44ab5601` 的精确 SHA 双轮行为评测 run `45281006259` 已完成并 PASS；该 SHA 上 CI run `45281016111` 也 PASS。发布仍需明确批准，尚未合并、打标签或发布。

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
- [x] 最终候选 SHA 的两次行为评测均达到预设阈值，自动门禁 PASS。
- [x] 匹配基线完整，稳定性检查通过。
- [x] Builder 证据 Skill tree 与发布候选 Skill tree 完全一致。
- [ ] 发布 PR head 与最终 merge commit 的 Git tree 完全一致（合并后核验）。
- [ ] 发布标签绑定已验证的 merge commit（发布时核验）。

只有全部门禁通过并经明确发布批准后，才创建 `v0.0.1` 标签并发布 GitHub Release。结构验证或历史候选评测通过不等于正式发布批准。

## 当前候选状态

- Release PR #42：Draft/Open，目标 `main`；Builder 证据 PR #38：Draft/Open，保留实验记录，不合并。
- Round 4 formal Builder：15 cases；独立验证 PASS，0 schema errors，61 source refs verified；三条真实 pilot 和独立 Gold Oracle 3/3 PASS。证据复用审计见 `docs/release-evidence/round4-evidence-reuse-audit.md`。
- 评测数据集质量状态仍为 `needs_info`，原因是 BR-09 request-failure/error-recovery evidence gap。此限制已记录；不影响已完成三条 pilot 的结果，但不应对数据集完整性作过度承诺。
- 最终候选 SHA `99d07f20d81a144fd52ab47eb6f7934c44ab5601` 的精确双轮评测 run [45281006259](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45281006259)：行为通过率 100% / 100%（12 cases/run）；Trigger precision/recall 100% / 100%；baseline 完整，平均 uplift +2.63 pp（两轮 uplift 0 / +5.26 pp）；重复运行稳定性 spread 0 pp；所有自动门禁 PASS，UNKNOWN=0。197 次 API 请求，token 总计 375,001，估算费用 $0.21665。
- 行为评测范围仅加载 `SKILL.md`，未加载 `references/*`；不是宿主兼容性认证。本版本不宣称跨模型独立 Judge。
- 精确候选行为报告 artifact `14869342620`，SHA256 `64c27164c4b053c16600dfe7c4fdb964cc4e6590c071a6a46cee46da8752bcec`；包含完整报告与检查点。
- 当前没有 `v0.0.1` 标签或正式 GitHub Release。发布工作流仅在显式批准并核验所有门禁后执行。


## Exact-head verification update (2026-11-24)
- Final evaluated head SHA: `99d07f20d81a144fd52ab47eb6f7934c44ab5601`.
- CI run `45281016111` and behavioral run `45281006259` both completed successfully on this exact SHA.
- Two repeats × 12 cases; behavior 100% / 100%; Trigger precision and recall 100%; baseline complete; mean uplift +2.63 percentage points; stability spread 0; no UNKNOWN; automated gates PASS.
- Report artifact `14869342620`; artifact ZIP digest `sha256:64c27164c4b053c16600dfe7c4fdb964cc4e6590c071a6a46cee46da8752bcec`; estimated API cost $0.21665.
- Documentation has been refreshed after that evaluated SHA. This documentation-only commit creates a new candidate head and must receive exact-head CI and behavioral gate before release verification can be considered current. Do not merge or tag without explicit approval.
