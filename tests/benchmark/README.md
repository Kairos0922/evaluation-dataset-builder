# Benchmark 验证设施

本目录属于开发与验收工具，不属于正式 Skill 运行包。本设施不调用模型，也不访问外部服务。

## 数据包结构

输入 JSON 包含 task、ground_truth、dataset_manifest、cases、defect_specs、defect_instances、runs 和 coverage_validations。评测用例继续复用正式 Skill 的 dataset-schema.json，不建立平行用例 Schema。

## 验证职责

1. L1 Schema Validation：字段、类型、必需属性和枚举。
2. L2 Referential Integrity：跨对象引用、ID 唯一性、数据集归属和状态约束。
3. L3 Semantic Validity：由独立专家审查或明确的语义判定记录确认。静态代码不能仅凭文本字段证明语义相关性。
4. L4 Empirical Validity：由隔离的真实执行和正常对照实验确认。静态验证器不模拟 Agent，也不声称实验已经发生。

## 运行

    python tests/benchmark/validate_benchmark.py tests/benchmark/fixtures/refund-valid.json --strict
    python -m unittest tests.benchmark.test_validate_benchmark -v

依赖沿用仓库 CI 已安装的 jsonschema。不需要模型密钥。

## 统计约束

- 缺陷检出率按唯一 defect_instance_id 统计。
- 同一缺陷实例的重复运行用于稳定性分析，不增加独立缺陷样本数。
- 注入状态不是 VALID 的实例不进入检出率分母。
- 对照状态不是 PASS 的实验不得作为有效检出证据。
- 注入失败但标记为检测成功属于矛盾记录，验证器会拒绝。
- 有效注入样本数为零时，检出率返回 null，而不是 0%。

## 退款贯通样例

fixtures/refund-valid.json 提供规则、能力、风险、覆盖要求、用例断言、缺陷定义、注入实例和运行记录的闭环示例。它是结构与引用测试夹具，不是真实业务证据，也不构成 Agent 能力测试结果。
