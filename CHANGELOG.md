# 版本变更记录

## 0.0.2 — 已正式发布（2026-11-27）

- GitHub Release：[v0.0.2](https://github.com/Kairos0922/evaluation-dataset-builder/releases/tag/v0.0.2)；Tag 指向核心功能合并提交 `f6b722ca630dacf0fa73bacba1100cff1fafff0f`。
- 发布候选 PR #44 已合并；发布执行机制 PR #45 已合并。正式发布工作流 Run [#45972007647](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45972007647) SUCCESS。
- 正式资产：`evaluation-dataset-builder-0.0.2.zip`（44,025 bytes）与 `RELEASE-NOTES-0.0.2.md`；ZIP SHA-256：`a7de57496e9beeb7b776361d712af81a6b0a6c7ed42bd900d95d8c08081c7fc4`。
- 22 项自主工程任务全部 DONE；17 项外部依赖任务按 D-009 移出当前迭代，不计为完成。
- 科学证据边界保持不变：3/15 Pilot、12 NOT_RUN、IDA/ERA PARTIAL、Judge NOT_RUN、Regression 无配对数据、综合分 NOT_VALIDATED。发布不代表外部效度门禁通过。

> 下方 0.0.2 历史研发记录保留开发期间的阶段状态；正式发布结果以上述最终记录及 GitHub Release 为准。

## 0.0.1 — 发布候选

- 建立通用评测数据集构建 Skill。
- 增加中文质量标准、用例 Schema、评分器规范、覆盖设计和证据治理规则。
- 按 Agent Skills 开放格式将 Skill 本体整理为独立目录，入口和参考资料可直接作为一个 Skill 安装。