# 通用基准评测集覆盖矩阵 v1.0.0

## Safety（100 cases）

| 覆盖项 | 覆盖 ID | 用例数 | 风险设计 | 代表性检查 |
|---|---|---:|---|---|
| 有害行为与危险请求 | SAF-COV-harmful_requests | 10 | critical | 暴力、危险行为、犯罪协助、伤害优化 |
| 自伤及危机情境 | SAF-COV-crisis_support | 10 | critical | 即时风险、支持性响应、方法拒绝、危机转介 |
| 网络攻击与滥用 | SAF-COV-cyber_abuse | 10 | critical | 凭据窃取、恶意软件、未授权访问、防御辨别 |
| 隐私与敏感数据 | SAF-COV-privacy | 10 | high | 个人定位、凭证、重新识别、最小化 |
| Prompt Injection | SAF-COV-prompt_injection | 10 | high | 文档、网页、工具、图片、伪造角色 |
| 权限越界 | SAF-COV-authorization | 10 | critical | 身份冒充、跨租户、只读写入、撤权 |
| 高风险专业领域 | SAF-COV-high_stakes | 10 | high | 医疗、法律、金融、紧急情境、资质边界 |
| 欺骗与操纵 | SAF-COV-deception | 10 | high | 诈骗、勒索、虚假证据、透明倡议 |
| 工具副作用安全 | SAF-COV-tool_side_effects | 10 | critical | 发送、删除、支付、写入、幂等与回滚 |
| 良性请求辨别 | SAF-COV-benign_discrimination | 10 | medium | 防御、教育、公开信息、非操作性创作、过度拒绝 |

风险等级是设计时的后果/优先级标记，不是经验概率。Safety 覆盖标签还包括 risk_level，唯一值为 critical、high、medium。

## Robustness（100 cases）

| 覆盖项 | 覆盖 ID | 用例数 | 风险设计 | 代表性检查 |
|---|---|---:|---|---|
| 输入噪声与扰动 | ROB-COV-input_noise | 10 | medium | 错别字、语音转写、字符混淆、噪声 |
| 歧义与信息缺失 | ROB-COV-ambiguity | 10 | high | 缺失对象、单位、时间、目的地、必要材料 |
| 长上下文与干扰 | ROB-COV-long_context | 10 | high | 约束保持、注入过滤、事实冲突、局部更新 |
| 多轮约束保持 | ROB-COV-multi_turn | 10 | medium | 参数累积、纠正、格式变化、状态恢复 |
| 指令冲突 | ROB-COV-instruction_conflict | 10 | high | 角色伪造、权限层级、数据指令、同级冲突 |
| 结构化数据异常 | ROB-COV-structured_data | 10 | medium | 缺字段、类型、重复键、编码、部分损坏 |
| 极端边界输入 | ROB-COV-extreme_inputs | 10 | medium | 空值、超长、溢出、非法枚举、资源上限 |
| 多语言切换 | ROB-COV-multilingual | 10 | medium | 中英混合、地区格式、Unicode、低资源语言 |
| 工具失败恢复 | ROB-COV-tool_failure | 10 | high | 超时、部分结果、未知状态、重试和幂等 |
| 信息变化与纠错 | ROB-COV-change_recovery | 10 | medium | 新版本、范围变化、规则修订、回滚和重测 |

Robustness 覆盖标签还包括 risk_level，唯一值为 high、medium。

## 计数口径

- 数据集规模按唯一 case_id 计数；两个数据集之间不合并计数。
- 构念覆盖按唯一 coverage_item_id 计数；一个用例可以有多个标签，但不能因此增加用例总数。
- 当前每个构念维度的 10/10 只表示设计覆盖已分配，不代表构念全集已由外部专家确认完整。
- 语义重复审查尚未完成；自动精确重复检查不能替代语义去重。
