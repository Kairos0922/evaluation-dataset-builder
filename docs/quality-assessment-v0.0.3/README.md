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

具体字段映射与不自动推断边界见 [integration-contract-map.md](integration-contract-map.md)；整体模块边界见 [architecture.md](architecture.md)。

## 方法论原则

1. 真实工作轨迹是候选来源，不是自动判失败的依据。
2. 区分 Agent 决策问题、上下文缺失、任务歧义、工具/环境故障、随机波动和未知原因。
3. 任务切片围绕最小完整任务契约，而不是轨迹长度。
4. 只记录必要证据引用和哈希；原始轨迹遵循授权、脱敏和最小化原则。
5. 只有需要复现的任务才补充环境细节；不另建强制 Runner 或第二套 Manifest。
6. 新上下文复测和独立 Verifier / Oracle 复用现有 ERA 证据体系。
7. 没有真实样本或独立效标时明确 NOT_RUN / UNKNOWN / NOT_VALIDATED；不新增未经验证的评分指标或综合分。

## 当前验证边界

最新 Run #2145（commit `de21c723dc0c50a2116a1f31b58951558d8b1a96`）已通过 actionlint、正式 Skill 包、Benchmark、轨迹候选发现、v0.0.3 证据链、Case adapter、轨迹 Case→IDA、无轨迹 Case→IDA、IDA 报告契约、全量离线测试、G-Theory 模拟和 IDA controlled-mutation。轨迹 Case draft、轨迹 JSONL、两种路径的 IDA report 已归档为 GitHub Actions artifact `trajectory-to-ida-integration`（90 天）。

本次 PR CI 中 Builder production、independent validation 和 Pilot 等受保护任务按条件 SKIPPED；没有真实轨迹导入或真实 Agent Pilot。合成样例只证明工程链路，不构成真实轨迹方法的有效性证据。

## 交付阶段

详见 [TASKS.md](TASKS.md)。已实现 Candidate / Qualification / Slice 到现有 Case Schema 的草稿转换器（`scripts/build_case_draft_from_slice.py`），并在 CI 中完成现有 IDA CLI 端到端验证。IDA 能解析轨迹来源身份，同时明确将构念对齐、任务可解性保留为 `NOT_ASSESSED`，综合分保持 `NOT_VALIDATED`。无轨迹输入回归也已通过：不带任何 trajectory-specific 字段的标准 Case 直接进入现有 IDA 并通过报告契约验证。下一步是评估如何把轨迹来源用例复用到 ERA clean-run / Runtime Record 路径，并明确真实运行的授权与独立 Oracle 条件；不是继续扩张独立 trajectory 模块。
