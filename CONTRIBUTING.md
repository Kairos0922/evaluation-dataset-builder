# 项目开发规范

本文件是仓库工程协作的简明入口。它不替代领域方法、质量标准、发布门禁或 Agent Skills 官方规范。

## 1. Agent Skill 编写规范

- Skill 格式以 [Agent Skills Specification](https://agentskills.io/specification) 为准；Claude 平台兼容要求与编写建议以 [Anthropic Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) 和 [authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) 为准。
- 不另造通用 Skill 格式规则。官方规范的强制要求与 Anthropic 的建议性最佳实践应明确区分。
- Skill 目录名与 frontmatter 的 `name` 一致；`SKILL.md` 是入口，按需资料放在 `references/`，可执行的确定性操作放在 `scripts/`，静态模板/资源放在 `assets/`。
- `description` 同时说明能力和适用触发场景。主文件保持聚焦；接近 500 行时评估拆分，而不是机械拆文件。
- 所有相对文件引用必须存在、使用正斜杠，并避免多层引用链。不要把宿主特定工具、模型或权限写成通用 Skill 的默认能力。

## 2. 仓库目录职责

- `skills/<skill-name>/`：可安装的正式 Skill，仅包含运行时必需文件。
- `docs/quality-assessment-v0.0.2/`：项目需求、方法、研发协议、实验记录和研发侧 Schema；不是自动随 Skill 分发的运行时文件。
- `scripts/`：可重复执行的验证、分析、导入和实验工具；输入、输出和失败行为应明确。
- `tests/`：离线测试、契约测试、固定夹具和可选行为评测。普通 CI 不调用付费模型或生产系统。
- `benchmarks/`：明确标记来源、许可、真值和执行状态的基准资产。
- `.github/workflows/`：自动化验证与发布工作流；变更工作流时运行 actionlint。

不要仅为目录整齐而移动稳定路径；移动前检查脚本、文档、工作流和外部引用。

## 3. 规范与契约的事实来源

- Agent Skill 通用格式：Agent Skills Specification。
- Skill 运行时行为：对应版本的 `skills/<skill-name>/SKILL.md` 及其随包引用文件。
- 质量评价方法：`docs/quality-assessment-v0.0.2/requirements.md`、`architecture-and-acceptance-baseline.md` 和已采纳的质量标准。
- JSON Schema：按消费者和版本确定权威文件；正式包 Schema 不得被研发扩展静默改写。允许的扩展必须写明用途、兼容边界，并有自动化契约检查。
- 任务与决策状态：`TASKS.md`、`decision-log.md` 和版本发布记录。历史状态保留，但必须标明时间和是否已被后续状态取代。

## 4. 代码与测试

- Python 使用标准库优先；新增依赖必须有明确用途，并同步更新 CI/安装说明。
- JSON 使用严格解析，拒绝 NaN/Infinity；Schema 使用项目声明的 Draft 2020-12。验证器应给出具体文件、行/字段或失败原因，不静默吞错。
- 每个修复增加能复现原问题的回归测试。测试覆盖输入边界、失败路径和关键跨字段约束；避免只测试 happy path。
- 本地/CI 离线检查：

  ```bash
  python scripts/validate_skill.py
  python -m unittest discover -s tests -p "test_*.py" -v
  ```

- 修改 GitHub Actions 工作流时，使用 actionlint。CI 中标记为 skipped 的任务不是 passed；离线模拟、合成数据和静态校验不得表述为真实运行或科学效度证据。

## 5. 版本与变更边界

- 正式 Skill 包必须保持与根目录 `VERSION`、frontmatter `metadata.version` 和对应 Release 一致。
- 已发布版本不可原地改变行为或输入/输出契约。兼容性破坏进入新版本；必要的研发扩展单独标识，不回写历史发布包。
- 修改 Schema 时同时检查所有生产者、消费者、样例、测试、文档和随包副本。
- 不把实验脚本、研究协议、开发依赖或测试夹具无理由塞入正式 Skill 包。
- PR 描述必须列出实际变更、兼容性影响、运行过的检查及其结果；未执行、跳过或外部依赖阻塞的检查分别标注。

## 6. 完成标准

变更只有在代码/文档修改已提交、相关回归测试已执行、受影响文档已同步且 CI 状态被准确记录后，才可称为工程完成。测试通过不等于业务有效性或科学效度已验证。
