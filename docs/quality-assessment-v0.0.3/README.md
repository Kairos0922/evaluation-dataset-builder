# v0.0.3：将真实轨迹证据融入现有评测数据集构建流程

**开发分支：** `feat/trajectory-driven-v0.0.3`  
**基线：** v0.0.2（保持不变）  
**跟踪 Issue：** [#51](https://github.com/Kairos0922/evaluation-dataset-builder/issues/51)  
**开发 PR：** [#52](https://github.com/Kairos0922/evaluation-dataset-builder/pull/52)

## 目标

v0.0.3 不建立一套平行的轨迹评测产品。它在现有 Evaluation Dataset Builder 中增加一个**可选的真实轨迹证据入口**：帮助发现值得研究的业务任务，经过审查后转成现有数据集的标准 Case，再由现有 IDA / ERA 评价数据集和真实运行。

没有真实轨迹的用户，仍可完整使用原有业务资料驱动的 Builder 流程。

## 与现有项目的融合

- 轨迹来源复用 Case 的 `case_origin=execution_trace` 和 `source_refs[].source_type=trace_log`。
- 任务目标、输入、期望行为、判定契约、质量状态和信息缺口复用现有 Case Schema。
- 执行条件复用 Case `execution_requirements`、现有 Manifest 和 Runtime Record。
- clean-run 复用现有 ERA 执行协议、Runtime Record、Judge Calibration 和独立 Oracle。
- 最终数据集复用现有 IDA；真实运行复用现有 ERA。
- Candidate、Qualification、Slice 仅作为摄取/审查阶段的中间材料，不形成第二套正式用例生命周期。

具体字段映射与不自动推断边界见 [integration-contract-map.md](integration-contract-map.md)；整体模块边界见 [architecture.md](architecture.md)。用户自行执行真实 Harness 的步骤、输出格式与复核清单见 [harness-execution-guide.md](harness-execution-guide.md)。

## 方法论原则

1. 真实工作轨迹是候选来源，不是自动判失败的依据。
2. 区分 Agent 决策问题、上下文缺失、任务歧义、工具/环境故障、随机波动和未知原因。
3. 任务切片围绕最小完整任务契约，而不是轨迹长度。
4. 只记录必要证据引用和哈希；原始轨迹遵循授权、脱敏和最小化原则。
5. 只有需要复现的任务才补充环境细节；不另建强制 Runner 或第二套 Manifest。
6. 新上下文复测和独立 Verifier / Oracle 复用现有 ERA 证据体系。
7. 没有真实样本或独立效标时明确 NOT_RUN / UNKNOWN / NOT_VALIDATED；不新增未经验证的评分指标或综合分。

## 当前验证边界

最近一次完整 CI 验证为 Run #2170 / 46094733042（validate PASS，含 Harness 产物适配专项测试与全量离线测试）；v0.0.2 正式 Skill 包候选 Run #78 / 46094733044 PASS actionlint、正式 Skill 包、Benchmark、轨迹候选发现、v0.0.3 证据链、Case adapter、轨迹 Case→IDA、无轨迹 Case→IDA、IDA 报告契约、全量离线测试、G-Theory 模拟和 IDA controlled-mutation。轨迹 Case draft、轨迹 JSONL、两种路径的 IDA report 已归档为 GitHub Actions artifact `trajectory-to-ida-integration`（90 天）。

本次 PR CI 中 Builder production、independent validation 和 Pilot 等受保护任务按条件 SKIPPED；没有真实轨迹导入或真实 Agent Pilot。合成样例只证明工程链路，不构成真实轨迹方法的有效性证据。

## 交付阶段

详见 [TASKS.md](TASKS.md)。已实现 Candidate / Qualification / Slice 到现有 Case Schema 的草稿转换器（`scripts/build_case_draft_from_slice.py`），并在 CI 中完成现有 IDA CLI 端到端验证。IDA 能解析轨迹来源身份，同时明确将构念对齐、任务可解性保留为 `NOT_ASSESSED`，综合分保持 `NOT_VALIDATED`。无轨迹输入回归也已通过：不带任何 trajectory-specific 字段的标准 Case 直接进入现有 IDA 并通过报告契约验证。已新增 `tests/test_trajectory_era_integration.py`，针对现有 Runtime Record → ERA 报告链增加合成契约回归：检查新 clean-run 的 dataset SHA / case_id / trace_ref 绑定，防止历史 source trace 被当成新运行 trace，并确认无 Gold/Judge 时维持 NOT_RUN / NOT_VALIDATED。该测试已在 Run #2152 的全量离线测试中通过；它不执行 Agent，也不代表真实 clean-run。本轮新增 `scripts/build_era_run_plan.py`：从既有 Manifest + Case JSONL 生成非执行式 ERA Run Plan 草稿，冻结 Runtime Record 所需的目标/模型/Harness/环境/工具身份，逐 Case 携带 `execution_requirements` 与历史来源引用，并使用与既有 DSH importer 一致的数据集 SHA 算法。计划只接受 `READY_TO_RUN` Case，不分配 `run_id`、不创建 Runtime Record，也不把历史 source trace 当作新运行 trace。`tests/test_build_era_run_plan.py` 覆盖数据集哈希一致性、Case 选择、就绪门禁和来源隔离；专项验证已在 Run #2164 step 14 通过，全量离线测试 step 16 通过；Manifest 级 READY_TO_RUN 门禁和 CLI 文件输出也已纳入测试。下一步是由具体 Harness 消费该计划并产出独立的新 Trace / Result。当前已增加 `schemas/v0.0.3/era-harness-envelope.schema.json` 和 `scripts/import_era_harness_executions.py`：它先校验外层 envelope Schema，再将 Harness 执行 envelope 严格映射到既有 v0.0.2 Runtime Record JSONL，校验 Plan / Dataset / Case / 冻结配置绑定、run_id 唯一、每 Case 新 session、历史来源 Trace 不复用和 trace SHA；没有独立 Oracle 附件时强制 Gold=UNKNOWN。该适配器不执行 Agent。仓库现有 DSH Pilot 路径经核对与 WebApp Testing 专用基准强绑定，不作为通用 Harness 使用。Harness 产物导入契约专项 CI 已在 Run #2170 step 15 通过，全量离线测试 step 17 通过；这仍然是合成工程契约验证，不是 Agent clean-run。


真实执行由用户自行选择 Harness 和环境完成。仓库提供的准备工作、逐 Case fresh-session 协议、产物格式、导入命令、执行后人工复核与自动化边界已整理在 [Harness 执行手册](harness-execution-guide.md)。本仓库不会自动发起模型调用或访问用户环境。
