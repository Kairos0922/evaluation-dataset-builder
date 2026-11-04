# 0.0.1 Release Review Checklist

Use this checklist only after the repeated evaluation workflow has completed on the exact candidate commit.

## Evidence

- PR head SHA (evaluation and review identity):
- PR merge commit SHA (release tag target; its tree must match the evaluated head):
- Evaluation workflow run ID and URL:
- Model:
- Suite ID:
- Repeated run count (must be >= 2):
- Report artifact URL:

## Automated gate results

| Gate | Required | Run 1 | Run 2 | Pass |
|---|---:|---:|---:|---|
| Behavior expected-property pass rate | >= 90% | | | |
| Trigger Precision | >= 95% | | | |
| Trigger Recall | >= 95% | | | |
| Baseline complete and comparable | Required | | | |
| Behavior metric spread | <= 5 pp | | | |
| Trigger Precision spread | <= 5 pp | | | |
| Trigger Recall spread | <= 5 pp | | | |

## Mandatory critical-case review

For each case, record result and evidence/output location reviewed.

| Case | Risk area | Reviewer finding / evidence |
|---|---|---|
| SE03 | Missing authoritative expected outcomes; fabricated gold | |
| SE04 | Conflicting source versions and unresolved outcomes | |
| SE05 | Grader validity, observable evidence, end-state checks | |
| SE08 | Critical quality gate must not be overridden by aggregate score | |
| SE09 | Side effects, sandbox, reset, and cleanup | |
| SE11 | Negative trigger / unrelated request must not force dataset construction | |
| SE12 | Incremental update, impact analysis, and rerun of affected gates | |

Also inspect every failed case, judge rationale/evidence, representative generated outputs, and baseline comparison. Any unresolved critical defect blocks release.

## Business-model and dataset-construction review

- [ ] Business model links capabilities, rules, workflow/state, risks, and observable evidence to traceable sources.
- [ ] Coverage universe and applicability are explicit; gaps have reasons and priorities.
- [ ] Generated cases map to coverage gaps and state their incremental coverage value.
- [ ] Scenario buckets are selected by applicability; high-risk and known-defect areas are addressed.
- [ ] Real cases and synthetic gap-fill cases are clearly distinguished; synthetic cases are not treated as authoritative gold.
- [ ] Case schema includes observable assertions; applicable Agent/Skill/tool cases include trace constraints.
- [ ] Process constraints and outcome constraints are judged separately; missing traces are not treated as successful execution.
- [ ] Change-impact links identify affected rules, scenarios, cases, graders, and coverage reports; local repairs have evidence of retesting.
- [ ] Dataset manifest validates against `skills/evaluation-dataset-builder/references/dataset-manifest-schema.json`.

## Baseline review

- Mean Skill behavior pass rate:
- Mean baseline behavior pass rate:
- Mean uplift:
- Any negative or surprising delta and explanation:
- Reviewer conclusion:

## Decision

- Reviewer:
- Decision: APPROVED / REQUEST_CHANGES
- Critical cases all reviewed: YES / NO
- Generated samples and judge evidence reviewed: YES / NO
- Baseline comparison reviewed: YES / NO
- Unresolved critical findings: NONE / LIST
- Rationale:

The reviewer must submit an APPROVED GitHub PR review with this information and link the workflow run/report. Do not create tag v0.0.1 unless automated gates pass and independent review is approved.


## 目标宿主运行证据门禁

- 目标候选 PR head SHA：
- Skill 目录树 SHA：
- 证据报告文件路径：`tests/runtime-evidence/<candidate_sha>.json`
- 固定报告永久链接（必须使用证据提交的完整 SHA）：
- 证据报告提交 SHA：
- 报告 Schema 校验结果：
- 本地证据包 SHA-256 校验结果（如提供证据包）：

| 宿主 | 发现 | 正向触发 | 负向触发 | 参考资料读取 | 任务执行 | 副作用 | 清理 | 综合状态 |
|---|---|---|---|---|---|---|---|---|
| Codex | | | | | | | | |
| Claude Code | | | | | | | | |
| claude.ai | | | | | | | | |
| Claude API | | | | | | | | |

每项 PASS、FAIL 或 BLOCKED 必须填写 evidence_id；NOT_RUN 必须填写原因。确认四种宿主的运行版本、安装方式、包 SHA、Skill tree SHA 与候选一致。审核人必须实际检查证据原件，并确认未暴露密钥、令牌、客户数据或个人信息。

仅当机器校验报告的 `overall_status=PASS`、四种宿主所有检查均通过，且报告链接为同仓库固定提交 SHA 的永久链接时，才能在独立 PR 审查正文中记录：

`target-runtime: PASS https://github.com/<owner>/<repo>/blob/<evidence_commit_sha>/tests/runtime-evidence/<candidate_sha>.json`

否则发布状态必须为 BLOCKED。
