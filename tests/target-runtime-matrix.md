# 目标宿主验证矩阵（0.0.1）

## 当前声明边界

README 已提供以下四种环境的安装或启用说明。这表示仓库提供对应的安装指导，**不表示已经验证运行兼容性**。截至本矩阵更新，四种环境均为 `DOCUMENTED_NOT_VERIFIED`；没有真实宿主执行证据，不得把任何一项标记为 PASS。

| 宿主 | README 中的安装/启用方式 | 当前验证状态 | 0.0.1 发布要求 |
|---|---|---|---|
| Codex | 用户级或项目级 `.agents/skills` 目录 | DOCUMENTED_NOT_VERIFIED | 必须实测通过 |
| Claude Code | 用户级或项目级 `.claude/skills` 目录 | DOCUMENTED_NOT_VERIFIED | 必须实测通过 |
| claude.ai | 上传完整 Skill ZIP 并启用 | DOCUMENTED_NOT_VERIFIED | 必须实测通过 |
| Claude API | Skills API 上传并在 Messages API 启用 | DOCUMENTED_NOT_VERIFIED | 必须实测通过 |

如未来缩小对外支持范围，必须同步调整 README 的安装声明、本矩阵和发布门禁；不得仅在验证报告中删掉未通过的平台。

## 每个宿主必须执行的检查

1. **发现（discovery）**：按 README 指定方式安装后，宿主能够识别 Skill 名称、描述和入口；记录宿主版本、安装方式、发现界面/日志。
2. **正向触发（positive_trigger）**：使用与评测数据集构建任务明确匹配的请求，确认宿主加载该 Skill；记录测试 ID 和触发证据。
3. **负向触发（negative_trigger）**：使用无关请求，确认不会错误触发该 Skill；记录测试 ID 和未触发证据。
4. **参考资料读取（reference_loading）**：至少验证业务模型、场景桶、覆盖指南、来源证据政策、评分器指南、用例 Schema、清单 Schema、质量标准和变更修复指南等关键资源的按需读取。记录实际读取路径、不可读取路径及证据。PASS 时不可存在不可读取的必需路径。
5. **真实任务执行（task_execution）**：运行至少一个端到端构建任务，记录用例 ID、输入、输出、工具/文件访问轨迹、初始与最终状态。
6. **副作用检查（side_effect_check）**：确认未修改未授权文件、未访问未授权系统、没有未声明的外部写入或其他副作用。
7. **清理检查（cleanup_check）**：确认测试数据清理、状态重置、临时文件处理和失败清理按计划完成。

## 证据要求

- 每个 PASS、FAIL 或 BLOCKED 检查必须有至少一项证据引用；NOT_RUN 必须说明未运行原因。
- 每份证据记录 evidence_id、所属宿主、所属检查项、不可变 HTTPS URI、SHA-256、文件名、媒体类型、采集时间和描述。
- 所有检查项的 evidence_refs 必须能解析到证据清单，且宿主/检查项归属一致。
- 可下载的证据包可用 `--evidence-dir` 执行本地 SHA-256 校验；仅填写哈希字符串不等于已经验证了文件内容。
- 独立审查人必须打开证据源，检查来源、时间、宿主身份、候选包标识和观察内容。结构校验与哈希格式检查不能单独证明证据真实。
- 对外公开证据前必须清理 API 密钥、令牌、客户信息、个人数据和其他敏感内容。

## 报告文件与发布绑定

验证报告必须作为独立证据提交，不能与它所验证的候选提交形成自引用。建议路径：

`tests/runtime-evidence/<candidate_sha>.json`

报告提交后，在独立 PR 审查中使用固定 commit SHA 的 GitHub 文件永久链接：

`https://github.com/<owner>/<repo>/blob/<evidence_commit_sha>/tests/runtime-evidence/<candidate_sha>.json`

发布程序将按该不可变链接从同一仓库读取报告，并核对：

- 报告 candidate_sha 等于发布 PR 的 head SHA；
- 报告 skill_tree_sha 等于候选提交的 Skill 目录树 SHA；
- 四个宿主均有且仅有一份报告；
- 每个宿主的状态与各检查项推导状态一致；
- 所有证据引用均存在且归属正确；
- overall_status 与各宿主检查结果一致；
- 0.0.1 发布要求四个宿主所有门禁均为 PASS。

独立审查意见必须包含 `target-runtime: PASS <固定文件永久链接>`。链接、报告、SHA 或状态任一缺失/不匹配，发布必须 BLOCKED。
