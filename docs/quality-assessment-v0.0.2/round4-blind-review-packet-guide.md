# Round 4 独立 Oracle 盲审资料包生成与分发

**状态：** 已生成两个匿名审查包；尚未分发、尚无审查者评分或 Oracle 共识。  
**冻结数据集：** wb-core@1.0.0  
**原始 JSONL SHA-256：** 000d38b110b60eae902f86737ea6bd1368f98c6632c42a47bb9470a4a08bfc45

## 1. 目的

为剩余 12 条 Builder 原始用例准备两份相互独立的 Oracle 设计审查包。审查者仅查看原始 user_input 和公开输入资产，分别提出规范断言、证据方法、Application/Skill 双结果规则、动作预算及 UNKNOWN 条件。

## 2. 盲审隔离规则

生成器仅从每条原始 JSONL 记录读取 case_id、user_input 和该行哈希。审查者资料包不包含 Builder 自己生成的以下内容：

- title、objective；
- expected_behavior、forbidden_behavior；
- reference_outcome、grading；
- observable_assertions、trace_expectations；
- quality_status、coverage_tags、assumptions 和执行可行性标签。

每份资料包都使用独立随机顺序和匿名标签（RA-ITEM-xx / RB-ITEM-xx）。审查者包不含原始 case_id，也不含交叉映射表。两份审查包分别压缩，不能将协调者交叉表发给审查者。

## 3. 包含的公开来源

- business-rules.md：合成应用的规范性业务规则；
- application-overview.md：应用范围与初始数据；
- capability-description.md：被测 Skill 的公开能力范围；
- runtime-and-tool-contracts.md：运行环境、权限、动作预算和证据契约。

不包含 fixture 实现源码，也不包含任何 Pilot trace、Gold 标签或独立判定结果。应用实现不能替代业务规则作为规范真值。

## 4. 生成命令

从冻结 Pilot artifact 解压后，定位：

- source/webapp-testing-builder-output/wb-core.jsonl
- source/webapp-testing-builder-input/assets/public/

运行：

```bash
python scripts/build_round4_blind_review_packets.py \
  --dataset-jsonl /path/to/wb-core.jsonl \
  --assets-dir /path/to/assets/public \
  --output-dir /path/to/output
```

生成器默认强制校验冻结 JSONL SHA-256。只有隔离测试才允许将 expected dataset SHA 置空。生成两个审查者 ZIP 和一个单独的 coordinator-only crosswalk ZIP。

## 5. 本次生成结果

本次基于冻结 artifact 14824967038 的 15-case 原始 JSONL，选取 WB-01、WB-03 至 WB-09、WB-11、WB-13、WB-14、WB-15：

| 产物 | 条目数 | SHA-256 |
|---|---:|---|
| reviewer A | 12 | 0dff42e51bba9e85fc12df9f1ae170a6baec28793ad3ca3496e07a6abe94180f |
| reviewer B | 12 | 205bd9bda8579c19c127cb1279e3f8378518fcc02f0cf84abbe33a7a8f733d92 |
| coordinator-only crosswalk | 24 个标签映射 | ff761e9ad1dbdc9e61165d33b4b2c6f03356e0a0eb293e58d636fe93449d6d4b |

已检查两个审查者 ZIP：各含 12 个 task.md、12 个空白 review-sheet.md 和 4 个公开来源；未包含 crosswalk、原始 WB-01 等 case ID 或 Builder 评分/Gold 字段值。协调者交叉表单独存放。

## 6. 分发和回收要求

1. 只把 reviewer A ZIP 发给审查者 A，只把 reviewer B ZIP 发给审查者 B。
2. 不发送 coordinator-only crosswalk ZIP；协调者独立保管。
3. 两位审查者应在互不交流的情况下完成全部 12 条审查，并提交原始工作表和总体意见。
4. 在双方独立提交前，不向审查者透露另一方排序、标签或判断。
5. 收齐后先冻结两份原始意见和哈希，再生成分歧清单并执行独立仲裁。
6. 只有经审查者确认并仲裁后的 Oracle 规则才能冻结。资料包生成和 CI 通过都不等于 Oracle 已获批准。
7. 目前未招募审查者、未收到评分、未计算 CVI/CVR/Aiken's V 或一致性统计；剩余 12 条仍 NOT_RUN。

## 7. 评审提交格式与差异比较

新增提交契约：`schemas/round4-blind-review-submission.schema.json`。每位评审者在完成 12 份 Markdown 工作表后，另提交一份 JSON：

- `reviewer_slot` 必须为 A 或 B；`reviewer_id` 使用匿名 ID，且两人必须不同。
- `packet_sha256` 必须匹配其收到的 ZIP；`dataset_sha256` 必须匹配本节冻结 JSONL。
- `items` 必须恰好包含该审查包中的 12 个匿名标签，每个标签一次。
- 每个案例提交构念必要性、清晰度、可执行性、独立规范断言、证据方法、PASS/FAIL/UNKNOWN 条件、Application/Skill 分离规则、动作预算、冻结建议、理由和至少两个证据引用。
- JSON 是机器接收格式，不取代原始 Markdown 工作表；两者都应保留并计算 SHA-256。

完成回收后，协调者先核验两份 JSON 和 ZIP 哈希，再从 coordinator-only ZIP 提取 `crosswalk.csv`。比较命令：

```bash
python scripts/compare_round4_blind_reviews.py \\
  --reviewer-a /path/to/reviewer-a-submission.json \\
  --reviewer-b /path/to/reviewer-b-submission.json \\
  --crosswalk /path/to/coordinator-only/crosswalk.csv \\
  --output /path/to/round4-review-comparison.json
```

比较器会检查 Schema、资料包身份、冻结数据集 SHA、12 个标签完整性、交叉表映射、两位评审对同一 case 的 case SHA 一致性和评审者身份是否不同；然后按原始 case ID 对齐两位评审的判断，并列出构念/可执行性/冻结意见、动作预算、Application/Skill 分离、理由、证据引用和规范断言差异，同时比较总体意见。输出状态固定为 `REQUIRES_HUMAN_ADJUDICATION`。比较器不裁决分歧、不自动选择 PASS/FAIL/UNKNOWN、不冻结 Oracle，也不授权 Runner 启动。

比较报告、两份原始 JSON、12×2 Markdown 工作表、两份原始资料包及 coordinator crosswalk 应分别归档并记录 SHA。任何补充或更正都应作为新版本保留，不覆盖原始提交。

## 8. 仲裁结果与执行前 Oracle 冻结

两份独立评审提交并完成差异比较后，必须由独立仲裁者逐案形成冻结决定。新增契约：

- Schema：`schemas/round4-oracle-freeze-manifest.schema.json`
- 验证器：`scripts/validate_round4_oracle_freeze.py`
- 测试：`tests/test_validate_round4_oracle_freeze.py`

Freeze manifest 是执行前的 Oracle 规则冻结记录，不是 Skill 运行结果。它必须记录：

1. 冻结数据集、Oracle plan、两份原始评审提交、差异报告和 coordinator crosswalk 的 SHA-256。
2. 两位不同评审者的匿名 ID，以及与两位评审者不同的仲裁者 ID。
3. 12 条案例逐条的 case SHA、Application assertions、Skill assertions、PASS/FAIL/UNKNOWN 条件、观测方法、动作预算、禁止副作用和证据依据。
4. 每条案例的 `FROZEN` 或 `NOT_FROZEN` 决定。任何一条未冻结，整体状态必须为 `NOT_FROZEN`。

验证器会重新验证两份盲评提交，使用 coordinator crosswalk 重新计算比较报告并要求与归档报告逐字段完全一致；同时核对所有输入文件 SHA、数据集和逐条 case SHA、12 条案例集合、评审者与仲裁者身份。只有 12 条全部冻结且 `--require-frozen` 验证通过，才可将该 manifest 作为 Runner 的后续执行前输入。验证成功本身仍不会启动 Runner，当前实现固定输出 `execution_authorized: false`。

示例：

```bash
python scripts/validate_round4_oracle_freeze.py \
  --manifest /path/to/oracle-freeze-manifest.json \
  --dataset-jsonl /path/to/wb-core.jsonl \
  --oracle-plan docs/quality-assessment-v0.0.2/round4-independent-oracle-plan.md \
  --reviewer-a /path/to/reviewer-a-submission.json \
  --reviewer-b /path/to/reviewer-b-submission.json \
  --comparison-report /path/to/round4-review-comparison.json \
  --crosswalk /path/to/coordinator-only/crosswalk.csv \
  --require-frozen
```

仲裁者不得以 Builder 的 `expected_behavior`、`grading`、`reference_outcome` 或 trace expectations 作为 Gold 来源。若两位评审的分歧未解决、规范来源不足、观测方法不可执行或 UNKNOWN 边界不清晰，应将对应 case 标为 `NOT_FROZEN`，修订后重新独立审查。

## 9. 当前门禁

- [x] 冻结数据集 SHA 校验。
- [x] 两份审查包匿名化和分离。
- [x] Builder 评分/Gold 字段排除测试。
- [x] 协调者 crosswalk 独立存放。
- [ ] 两名独立审查者完成盲审。
- [ ] 分歧仲裁并冻结 Oracle plan 新版本与 SHA。
- [ ] Runner/adjudicator 接通并通过执行前 Gate。
- [ ] 用户确认后启动剩余 12 条用例运行。

WB-15 继续保持 UNKNOWN；未提供受控请求失败注入契约前，不对应用 BR-09 请求失败分支作 PASS/FAIL 判定。
