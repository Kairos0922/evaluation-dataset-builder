# v0.0.3 轨迹驱动评测任务生产

**开发分支：** `feat/trajectory-driven-v0.0.3`  
**基线：** v0.0.2（保持不变）  
**跟踪 Issue：** [#51](https://github.com/Kairos0922/evaluation-dataset-builder/issues/51)

## 目标

在现有通用 Agent / Skill Evaluation Dataset Builder 上，增加从经授权的真实 Agent 轨迹发现候选能力缺口、进行失败资格审查、切片、环境重建描述和独立复测的能力。

这不是 Terminal-Bench 格式移植，也不是自动把失败轨迹判成能力缺陷。轨迹只提供可审计的观察证据；能力归因和任务有效性必须经过独立证据验证。

## 方法论原则

1. 真实工作需求优先；候选发现不等于质量结论。
2. 区分 Agent 决策失败、上下文缺失、任务歧义、工具故障、环境故障、随机波动和未知原因。
3. 切片边界围绕独立任务契约，而不是轨迹长度。
4. 仅记录必要证据引用和哈希；不默认收集本地轨迹或复制敏感内容。
5. 重建环境时显式记录上下文闭包、依赖、初始状态、权限、副作用和重置策略。
6. Clean-run、Verifier、Oracle 和多模型实验遵循 v0.0.2 ERA 的冻结、独立性和授权要求。
7. 无真实样本或独立效标时明确 NOT_RUN / UNKNOWN / NOT_VALIDATED；不新增未经验证的综合分或权重。

## 交付阶段

详见 [TASKS.md](TASKS.md) 与 [architecture.md](architecture.md)。

## 与 v0.0.2 的关系

v0.0.2 的 IDA / ERA、既有报告、实验结论和发布资产均作为稳定基线。v0.0.3 将新证据作为独立、版本化的数据契约接入，不回写或重新解释历史结果。
