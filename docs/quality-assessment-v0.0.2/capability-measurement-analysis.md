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


## 8. G-Theory Monte Carlo 参数恢复（模拟证据）

新增 `scripts/run_g_theory_parameter_recovery.py`，以 Bernoulli(logit(intercept + person + item)) 的 crossed random-effects DGP 评估当前双 facet ANOVA method-of-moments 估计器。真值不由待测估计器自身生成：脚本使用独立的高规模 Monte Carlo 积分，计算 observed binary-score scale 上 Person / Item 协方差分量及剩余分量，再与有限样本估计比较。

预注册默认设计：4 个情景（balanced moderate、low prevalence、low person variance、high item variance），每个情景 100 次重复、40 persons × 25 items，reference integration 1,000 × 1,000 draws，seed=9100。报告 raw Person/Item variance component 的 bias、RMSE、采样分布分位数、负方差分量发生率，以及 relative G / absolute Phi 系数恢复情况。

**解释边界：** 真值是 observed binary-score scale 的方差分量，不是 logistic latent scale 参数；Person×Item 与 Bernoulli residual 仍混合。模拟只覆盖当前 additive logistic random-effects DGP 和平衡双 facet，不验证模型拟合、DIF、测量不变性或真实 Agent/Skill 外部效度。模拟重复分布分位数不是现实置信区间。证据等级固定为 SIMULATION_ONLY。

运行：`python scripts/run_g_theory_parameter_recovery.py --output artifacts/g-theory-parameter-recovery.json`。


## 9. G-Theory 参数恢复与样本设计敏感性（Run #2002）

Run #2002（[45804426404](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45804426404)，精确代码 head `61fd978f496a3eb2db00eeb89a4bf696b84ddbf5`）以固定 seed 9100、每场景 100 次重复、1,000×1,000 reference integration，对四种 Bernoulli logistic crossed-random-effects 情景分别比较 20×10、40×25、80×50 的 Person×Item 设计。G-Theory JSON Schema validation 和 CI artifact 上传均成功；artifact #15107584570，ZIP SHA-256 `c9e7f8f7788439932e88658318c1cd9fbf39a415ac141ad7fce115618a3db90b`。

| 设计 | 场景 | Relative G bias / RMSE | Absolute Phi bias / RMSE | raw Person/Item 负分量率 |
|---|---|---:|---:|---:|
| 20×10 | balanced moderate | -0.0410 / 0.1827 | -0.0381 / 0.1794 | 2% / 10% |
| 20×10 | low prevalence | -0.1102 / 0.2292 | -0.1088 / 0.2246 | 8% / 16% |
| 20×10 | low person variance | +0.0501 / 0.1697 | +0.0487 / 0.1638 | 41% / 10% |
| 20×10 | high item variance | -0.0240 / 0.1794 | -0.0167 / 0.1723 | 4% / 1% |
| 40×25 | balanced moderate | -0.0011 / 0.0602 | -0.0003 / 0.0611 | 0% / 0% |
| 40×25 | low prevalence | -0.0403 / 0.0966 | -0.0398 / 0.0972 | 0% / 2% |
| 40×25 | low person variance | -0.0101 / 0.1490 | -0.0088 / 0.1433 | 23% / 0% |
| 40×25 | high item variance | -0.0178 / 0.0835 | -0.0154 / 0.0883 | 0% / 0% |
| 80×50 | balanced moderate | +0.0038 / 0.0283 | +0.0044 / 0.0294 | 0% / 0% |
| 80×50 | low prevalence | -0.0257 / 0.0452 | -0.0259 / 0.0458 | 0% / 0% |
| 80×50 | low person variance | -0.0112 / 0.1103 | -0.0097 / 0.1072 | 2% / 0% |
| 80×50 | high item variance | -0.0039 / 0.0292 | -0.0033 / 0.0322 | 0% / 0% |

**Interpretation:** small 20×10 designs show large coefficient RMSE and frequent negative raw variance components. 40×25 improves typical scenarios but remains unstable when the Person component is small. 80×50 substantially improves recovery in balanced/moderate, low-prevalence and high-item-variance conditions, yet low-person-variance RMSE remains around 0.11. This supports design-specific simulation rather than a universal minimum sample-size rule.

The empirical reference components are approximated by an independent Monte Carlo integral on the observed binary-score scale. They are not latent logistic-scale parameters. Replication quantiles are sampling-distribution summaries, not confidence intervals. The model still conflates Person×Item interaction with Bernoulli residual and does not model Seed, Environment or Judge facets.

## 10. Capability analysis of the available Round 4 real Pilot evidence

Run #2002 also passed the Capability measurement report contract against the actual three imported Runtime Records. The observed design is **1 configuration × 3 cases**. Rasch 1PL is NOT_ASSESSED (requires at least 3 persons and 3 items in this exploratory implementation); G-Theory is NOT_ASSESSED (requires at least 2 persons and 2 items). DIF and measurement invariance are NOT_ASSESSED because no preregistered group variable or multi-group held-out matrix exists. This is an explicit data sufficiency result, not a zero score.

The real-evidence artifact is #15108548510, ZIP SHA-256 `d02e9557b071febdac9bc93e53b4306727033e35a0394492ad498e36c9615e1b`.
