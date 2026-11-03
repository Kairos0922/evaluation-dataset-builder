# 0.0.1 Release Review Checklist

Use this checklist only after the repeated evaluation workflow has completed on the exact candidate commit.

## Evidence

- PR head SHA (review identity):
- PR merge commit SHA (evaluation candidate and release tag):
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


## Target-runtime execution gate
- [ ] Target runtime/build and isolated environment are identified.
- [ ] Critical executable cases have real run IDs, traces, initial/final state assertions, and side-effect checks.
- [ ] Permissions, test data, rollback/reset, cleanup, and failure cleanup are evidenced.
- [ ] Reviewer records `target-runtime: PASS` with a stable HTTPS evidence link; otherwise release remains BLOCKED.
