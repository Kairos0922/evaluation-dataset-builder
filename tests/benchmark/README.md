# Benchmark 验证设施

本目录属于开发与验收工具，不属于正式 Skill 运行包。本设施不调用模型，也不访问外部服务。

## 数据包结构

输入 JSON 包含 task、ground_truth、dataset_manifests、cases、defect_specs、defect_instances、runs 和 coverage_validations。评测用例继续复用正式 Skill 的 dataset-schema.json；数据集清单继续复用正式 dataset-manifest-schema.json，不建立平行用例或清单 Schema。

每个 Case 通过 dataset_id 归属一个且仅一个 Manifest。Manifest 的 dataset_id 必须唯一，case_count 必须等于实际归属用例数。Task 中的 expected_dataset_count（如有）必须与 Manifest 数量一致。

## 验证职责

1. L1 Schema Validation：字段、类型、必需属性和枚举。
2. L2 Referential Integrity：跨对象引用、ID 唯一性、数据集归属和状态约束。
3. L3 Semantic Validity：由独立专家审查或明确的语义判定记录确认。静态代码不能仅凭文本字段证明语义相关性。
4. L4 Empirical Validity：由隔离的真实执行和正常对照实验确认。静态验证器不模拟 Agent，也不声称实验已经发生。

## 覆盖闭环

- Ground Truth 的每个 coverage_requirement 必须明确适用的数据集；省略 dataset_refs 时表示适用于本任务全部数据集。
- 每个适用的「数据集 × 覆盖项」组合必须有处置记录：VALID、INVALID、INCONCLUSIVE 或 NOT_APPLICABLE。
- VALID 必须引用同一数据集中的 Case、该 Case 的 coverage_tag、关联 grading criterion、证据和独立审查者。
- NOT_APPLICABLE 必须提供理由，且不能引用 Case 或断言。
- INVALID、INCONCLUSIVE 或缺少处置记录不能计为覆盖。关键覆盖缺口不能被其他覆盖项抵消。
- 报告中的覆盖总数、有效覆盖数和缺口由 Ground Truth 与处置记录重算，不信任 Manifest 中自行填写的覆盖率数字。

## 运行

    python tests/benchmark/validate_benchmark.py tests/benchmark/fixtures/refund-valid.json --strict
    python -m unittest tests.benchmark.test_validate_benchmark -v

依赖沿用仓库 CI 已安装的 jsonschema。不需要模型密钥。

## 实验统计

- 独立缺陷样本单位是 defect_instance_id；重复运行不增加独立缺陷样本数。
- 每个实例分别记录有效重复次数 K、有效观测和排除观测；报告 K 分布。
- 分别报告观测检出率、至少一次检出实例率、所有有效重复均检出实例率。K 不固定时，不将「至少一次检出」指标直接称为标准 pass@K。
- 只有注入 VALID、对照 PASS 且具备正常对照 execution ID 和 evidence 的观测，才进入检出统计。
- 正常对照误报率单独计算；对照执行证据缺失时，不能把 control_status=PASS 当作有效对照。
- 当前离线汇总不是完整统计推断；正式研究报告还需根据样本聚类结构选择置信区间和推断方法。

## 退款贯通样例

fixtures/refund-valid.json 是结构与引用测试夹具，不是真实业务证据，也不构成 Agent 能力测试结果。
