# Capability 测量分析器（探索性实现）

**状态：** 已实现的工程估计器；尚未完成统计模型适配、参数恢复、测量不变性和外部效度验证。输出不得标记为 VALIDATED。

## 1. 用途与输入

`scripts/analyze_capability_measurement.py` 从 Runtime Record JSONL 构建平衡的 Configuration × Case 响应矩阵，并输出：

- Rasch 1PL（联合最大似然）探索性估计：配置能力位置、题目难度、局部 Fisher 信息近似标准误、题目信息和测试信息曲线；
- 双 facet（Person × Item）G-study：方法矩估计的 Person、Item、Person×Item+Residual 方差分量，相对 G 系数、绝对 Phi 系数和按题目数变化的 D-study 画像。

只纳入 `status=valid`、`agent_outcome` 为 pass/fail，且 Gold 来源为 `independent_oracle` 或 `expert_adjudication` 的记录。合成标签、未知 Gold、无效运行和缺失 Agent outcome 均不进入测量矩阵，并在排除列表中记录。

运行示例：

```bash
python scripts/analyze_capability_measurement.py \
  --records artifacts/runtime-records.jsonl \
  --output artifacts/capability-measurement-report.json
```

报告契约：`schemas/capability-measurement-report.schema.json`。

## 2. 设计门禁与失败安全

- 要求单一 dataset_id 与 dataset_sha256。
- 每个 Configuration × Case 只能有一个观测；重复运行必须先明确设计 Seed facet，当前实现拒绝重复单元格，不把它们伪装成独立样本。
- 只接受完整平衡的 Person × Item 设计；缺格时停止分析并给出缺失单元格。
- 无独立 Gold 记录时，IRT 与 G-Theory 均返回 `NOT_ASSESSED`，不输出 0。
- Rasch 需要至少 3 个配置和 3 个用例；全通过/全失败的 Person 或 Item 导致完全分离时拒绝拟合。
- Rasch 不收敛时返回 `NOT_ASSESSED`，不输出参数。
- G-study 对负方差分量保留 raw 值并将展示用分量截断到 0，同时给出警告。
- 小样本只输出探索性画像，不自动触发通过/失败门槛。

## 3. 模型范围

### Rasch 1PL

\[ P(X_{pi}=1)=\frac{1}{1+\exp[-(\theta_p-b_i)]} \]

其中配置为 Person，Case 为 Item，`theta` 为配置能力位置，`b` 为题目难度。使用交替 Newton 更新与识别约束（题目难度均值中心化）。当前不实现 2PL 区分度、多维 IRT、DIF、正式拟合诊断或聚类稳健区间。

### G-Theory

采用平衡双 facet 随机效应近似：

\[ Y_{pi}=\mu+p_p+i_i+(pi,e)_{pi} \]

用双因素 ANOVA 方法矩估计方差分量。当前 Person×Item 交互与残差混合，不支持独立 Seed、Environment、Judge facet，也不支持嵌套/非平衡设计。D-study 只对当前 Item facet 作题目数量规划。

## 4. 解释限制

- 成功拟合只表示算法在给定矩阵上返回了数值，不表示单维性、局部独立、单调性、模型拟合或测量不变性成立。
- Person 集合是输入中的 Agent/Skill 配置，不代表一个已定义且具有代表性的 Agent 总体。
- G 系数和 Phi 系数依赖随机 facet 假设和题目总体定义；不能脱离使用场景解释。
- 参数与系数不用于综合评分、发布门槛或跨域排名。
- 正式使用前必须预注册构念、设计和模型，完成 Monte Carlo 参数恢复、模型拟合/残差检查、DIF/测量不变性、精度分析和独立外部验证。

## 5. 后续工作

- 扩展多 facet G-study：Agent × Task × Seed × Environment × Judge，并区分交叉/嵌套设计；
- 增加 2PL/多维模型时先建立参数恢复模拟和模型诊断；
- 增加 DIF 分组设计和不变性检验；
- 将估计结果与外部能力效标、专家蓝图和历史故障样本进行独立验证。


## 6. Rasch 1PL Monte Carlo 参数恢复（模拟证据）

新增可复现脚本 `scripts/run_capability_measurement_monte_carlo.py`，默认固定 seed=8000、30 次独立重复、每次 80 个配置 × 25 个用例。数据由已知的 Rasch 1PL 生成：能力位置服从 Normal(0, 0.8)，题目难度服从 Normal(0, 0.9)，响应服从 Bernoulli(logit(theta - difficulty))。每次重复均调用生产估计函数；完全分离或无法估计的重复单独计数，不从失败重复中伪造参数。

固定设计的基线模拟结果：
- 有效重复：26/30；失败 4/30（完全分离时 fail-closed）。
- 有效重复上的平均能力位置相关：约 0.867；平均题目难度相关：约 0.961。
- 平均能力 RMSE：约 0.492 logits；平均题目难度 RMSE：约 0.268 logits。
- 报告同时输出重复间 p2.5 / median / p97.5 分位数；这些是模拟重复分布分位数，不是现实总体置信区间。

运行：`python scripts/run_capability_measurement_monte_carlo.py --output artifacts/rasch-recovery.json`。

**解释边界：** 该模拟只验证在正确指定的单维 Rasch 1PL 数据生成模型下的参数恢复行为；它不是对真实 Agent/Skill 能力构念、单维性、局部独立、DIF、测量不变性或 G-Theory 模型的验证。G-Theory 的二元观测方差分解尚无独立参数恢复实验。IM-05 继续 IN_PROGRESS。


## 7. G-Theory 数值性质与失败安全测试

离线测试另以固定 seed 的 crossed Configuration×Case 二元矩阵检查 D-study 的相对 G 与绝对 Phi 系数处于 [0,1] 且随题目数增加单调不减；另用小型退化矩阵检查负 raw 方差分量被保留、展示分量截断并发出警告。该测试验证实现的数值边界和失败可见性，不是已知总体方差参数下的 G-Theory 参数恢复实验。二元结果的潜在尺度方差分解仍需更合适的 GLMM/多 facet 模型及 Monte Carlo 研究。
