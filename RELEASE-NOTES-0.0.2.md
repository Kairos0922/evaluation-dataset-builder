# Evaluation Dataset Builder v0.0.2

## 版本定位

0.0.2 在 0.0.1 的评测数据集构建 Skill 基础上，增加可审计的质量评价工程能力，包括独立离线数据集检查（IDA）、运行证据分析（ERA）、机器可读报告契约、Capability/Regression 专属分析设计，以及相关证据导入、验证和安全测试工具。

## 主要变化

- 增加 IDA 确定性数据集质量检查与机器可读报告。
- 增加 ERA Runtime Record、运行统计分析和报告契约验证。
- 增加 Judge Calibration、Formula Validation、Capability Measurement 等证据契约与探索性分析工具。
- 增加严格 JSON/JSONL 输入解析、非有限数值拒绝、哈希/路径安全和畸形输入失败安全。
- 增加研究协议、方法矩阵、架构基线和可复现的工程验证流程。

## 重要限制

- Round 4 真实数据为 15 条用例中的 3 条 Pilot；12 条仍 NOT_RUN。
- IDA/ERA 结果为 PARTIAL；Judge 校准为 NOT_RUN；Regression 没有配对数据。
- 真实数据不足以支持 IRT、DIF、测量不变性或 G-Theory 实证结论。
- IDA 8/8 mutation 结果是合成确定性变异敏感性测试，不证明语义效度或污染抵抗。
- 综合分、权重和阈值保持 NOT_VALIDATED，不提供已验证的通用总分。
- Codex、Claude Code、claude.ai、Claude API 的逐平台兼容性均未认证。
- 本版本不承诺完成独立专家效度、外部 Gold/Oracle 扩展、完整 Judge 校准、真实 Capability/Regression 效度或综合公式效度。

本版本的发布范围、证据边界和验收标准以仓库中的 RELEASE-GATE-0.0.2.md 为准。