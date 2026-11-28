# 用户执行手册：ERA Run Plan → Harness → Runtime Record（v0.0.3）

## 目的与边界

本手册用于在用户明确选择的 Agent / Harness / 隔离环境中执行已审查的 Case。仓库负责生成冻结计划、校验 Harness 产物并将记录交给既有 ERA；**实际执行由用户控制**。

- 本仓库不会自动启动 Agent、调用模型 API、访问用户业务系统或导入用户本地轨迹。
- 不要把历史发现轨迹当成 clean-run Trace。
- 不要把 Harness 的退出码、Agent 自报成功或工具返回成功当成独立 Gold。
- 没有独立 Oracle 时，Runtime Record 的 `gold_outcome` 必须是 `unknown`，`gold_source` 必须是 `not_available`。
- 任何真实执行都应在获授权、隔离、最小权限的环境进行；默认不重放会产生外部副作用的原始操作。

## A. 执行前准备

1. 选定要测的 Case，并确认其输入、交付物、判定标准和 `execution_requirements` 已审查完成。
2. 确认数据集 Manifest 的 `execution_status=READY_TO_RUN`，所选 Case 的 `execution_requirements.status=READY_TO_RUN`。
3. 明确本次允许执行的模型/Agent 版本、Harness、工具版本、环境、权限、网络策略、预算、超时、资源限制、重置和清理方式。
4. 确认不会把个人信息、凭据、客户数据或未授权业务内容写入 Trace / Result。日志按最小必要原则采集。
5. 若任务有副作用，使用可丢弃的测试账号/数据和隔离环境；明确禁止动作及停止条件。
6. 若无法保证环境健康、上下文完整或独立性，暂停执行并记录原因，不要把该次结果归因于 Agent。

## B. 生成冻结 Run Plan

在仓库根目录运行：

```bash
python scripts/build_era_run_plan.py \
  --manifest path/to/dataset-manifest.json \
  --cases path/to/cases.jsonl \
  --configuration path/to/frozen-runtime-configuration.json \
  --output artifacts/era-run-plan.json
```

可用重复的 `--case-id CASE_ID` 只选择部分 Case。配置文件只包含现有 Runtime Record 身份字段：`configuration_id`、`target_revision`、`target_type`、`model`、`harness`、`environment`、`tool_versions`，以及可选 `seed`。冻结后不要在执行中途更改这些身份；若有变更，应生成新计划。

生成成功只代表计划通过结构和 READY_TO_RUN 门禁，不代表 Agent 已执行。

## C. Harness 必须遵守的执行协议

对 Run Plan 中每个 Case：

1. 建立全新、可审计的 `session_id`；不同 Case 不得复用会话、隐藏状态、对话历史、缓存的 Agent 工作区或前一 Case 产物。确有共享只读基础镜像时，须保证每个 Case 的可变状态独立。
2. 只向 Agent 提供该 Case 在真实使用场景中应当可见的输入和上下文。不得注入事后用户纠偏、参考答案、Oracle、预期判定或历史轨迹中的解题步骤。
3. 由 Harness 在执行开始时创建唯一 `run_id`。保留开始/结束时间、执行状态、Agent / 工具调用轨迹、结果工件及必要的成本数据。
4. 产出本次执行新生成的 `trace_ref`、`result_ref`；工件不可变保存，并计算 Trace 文件原始字节的 SHA-256。不能只填写一个未经计算的哈希字符串。
5. 记录工具、环境、网络、超时、权限或资源异常。若执行未完成或基础设施故障，按 Runtime Record 的现有语义记录，不得伪装成 Agent 失败。
6. 一个 Case 的执行结束后销毁或重置其可变状态，再开始下一个 Case。
7. 不要在 Runtime Record 中写入不存在的 Judge / Gold 结果。独立 Oracle 应在 Agent 执行结束后，按预先确定的标准独立判定，并另行保留来源与审查记录。

## D. 输出 envelope

每个 Case 产生一条 JSONL 记录。外层 envelope 的 Schema 是 `schemas/v0.0.3/era-harness-envelope.schema.json`：

```json
{
  "plan_id": "<exact plan_id>",
  "case_id": "<exact Case ID>",
  "session_id": "<new unique Harness session identifier>",
  "runtime_record": {
    "...": "one complete v0.0.2 Runtime Record object"
  }
}
```

`runtime_record` 必须完整符合现有 v0.0.2 Runtime Record Schema，并将以下值绑定到 Run Plan：

- `dataset_id`、`dataset_sha256`、`case_id`
- `configuration_id`、`target_revision`、`target_type`、`model`、`harness`、`environment`、`tool_versions`、可选 `seed`
- `run_id`：真实执行产生且全批次唯一
- `trace_ref`、`trace_sha256`、`result_ref)：本次真实执行的新工件
- `outcomes.gold_outcome=unknown` 和 `outcomes.gold_source=not_available`，除非另有符合现有 Oracle 证据流程的独立判定；当前导入适配器只接受 unknown 状态

不要把以下内容放进 envelope：提示词秘密、API Key、访问令牌、完整用户隐私数据、未经脱敏的业务数据。它们不属于导入接口所需身份字段。

## E. 校验并导入

将所有 Case 的 envelope 写入一个 JSONL 文件后运行：

```bash
python scripts/import_era_harness_executions.py \
  --plan artifacts/era-run-plan.json \
  --executions artifacts/harness-executions.jsonl \
  --output artifacts/runtime-records.jsonl
```

导入器会检查 envelope Schema、Runtime Record Schema、计划/数据集/Case/配置绑定、每 Case 唯一执行、session 不复用、run_id 唯一、新 Trace / Result 不复用历史来源引用、Trace SHA 格式，以及 Oracle 缺失时 Gold=UNKNOWN。

注意：导入器当前验证 Trace SHA 字段格式和身份约束，但**不会下载或读取远端 Trace 工件来重新计算哈希**，也无法证明 Harness 真的使用了全新上下文。执行方必须保留工件并让审查者可独立核验。

导入成功后，`runtime-records.jsonl` 是既有 v0.0.2 Runtime Record 格式，可按现有 ERA CLI / 流程分析。不要把“导入器 PASS”解释成 Agent 正确、任务有效或 Benchmark 有效。

## F. 执行后人工复核

- Trace / Result 是否存在、哈希是否与实际工件一致、工件是否完整且可访问？
- 每个 Case 是否真正使用新 session，是否发生隐藏状态泄漏？
- Agent 当时是否获得了任务所需的全部上下文？是否出现提示/答案泄漏？
- 失败是否由 Agent 决策导致，还是工具、环境、权限、资源或任务歧义导致？
- 独立 Oracle 是否在不知晓 Agent 结果的条件下判定？是否记录了合理可接受变体与 UNKNOWN？
- 是否需要重跑？重跑必须产生新的 run_id、session_id、Trace 和 Result，不覆盖旧工件。
- 是否有任何未授权数据或副作用？如有，停止后续运行并按组织流程处置。

## G. 当前未自动化的责任

以下事项有意保留给具体 Harness / 用户，而不是由本仓库伪造：

- 创建 Agent 会话、执行模型和工具调用；
- 隔离文件系统、网络、凭据、测试账号和外部副作用；
- 生成并持久化真实 run_id、Trace、Result；
- 从工件内容重新计算并核对哈希；
- 验证实际 fresh-context 行为及环境健康；
- 独立 Oracle 判定与人工争议处理。

这些责任完成并有可复核证据后，V03-08 / V03-11 才能进入下一阶段。
