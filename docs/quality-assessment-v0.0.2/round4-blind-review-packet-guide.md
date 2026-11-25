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

## 7. 当前门禁

- [x] 冻结数据集 SHA 校验。
- [x] 两份审查包匿名化和分离。
- [x] Builder 评分/Gold 字段排除测试。
- [x] 协调者 crosswalk 独立存放。
- [ ] 两名独立审查者完成盲审。
- [ ] 分歧仲裁并冻结 Oracle plan 新版本与 SHA。
- [ ] Runner/adjudicator 接通并通过执行前 Gate。
- [ ] 用户确认后启动剩余 12 条用例运行。

WB-15 继续保持 UNKNOWN；未提供受控请求失败注入契约前，不对应用 BR-09 请求失败分支作 PASS/FAIL 判定。
