# Round 4 evidence reuse audit for release candidate 0.0.1

Date: 2026-11-24

## Scope

Compare the Skill package used by the frozen Round 4 Builder evidence with the current Skill package synced from PR #38. This audit determines which prior evidence can be reused and which gates require targeted follow-up. It does not trigger model calls.

Round 4 formal Builder run candidate SHA: `eb1fa5c21e7b2320e0904bb1cb72a38854b9cbd8` (run `44959366258`, artifact `14729741906`).  
Current source Skill branch: `experiment/webapp-testing-contract`  
Builder-run Skill file blob SHA: `1743b5b133e83d7f9a3332d9bae5912b0300dccb`  
Current Skill file blob SHA: `1743b5b133e83d7f9a3332d9bae5912b0300dccb`

Builder-run schema blob SHA: `b1314c3d7811dfd0c1e61ddad245927add92affa`  
Current schema blob SHA: `b1314c3d7811dfd0c1e61ddad245927add92affa`

The two Skill package files are byte-identical to the current source branch. GitHub commit comparison also found no changes under `skills/evaluation-dataset-builder/` between the Builder candidate commit and PR #38's current branch.

## Exact changes

At the historical formal Builder run, the current Skill already included the two requirements being audited. The current package has no further changes relative to that Builder package. For context, the two requirements are:

1. **Source-reference identity consistency:** source-map/source registry identity fields (`source_id`, `title`, `source_type`, `path`) must match each case's `source_refs`; copy canonical values, put section/topic notes in `locator`, and check identity before generation.
2. **Explicit evaluation subject:** each grading contract must distinguish the application/API from the testing/auditing/diagnostic Agent or Skill. Application defects are facts for a testing Agent to discover, not automatically Agent failures. Criteria must assess one subject consistently; split criteria when evaluating both subjects; case-level verdicts must align with criteria.

The schema requires `grading.evaluation_subject`, and the formal Builder output populated it in all 15 cases.

## Evidence disposition

| Evidence | Decision | Reason / follow-up |
|---|---|---|
| WB-02, WB-10, WB-12 real execution traces | **Reuse: exact case match verified** | The frozen Builder output used by Round 4 has the same case IDs/titles and contracts. WB-02 tests case-insensitive search reporting; WB-10 tests exactly three status transitions; WB-12 tests exactly one confirmation delete. Each explicitly sets `grading.evaluation_subject` to the webapp-testing Skill. |
| WB-12 DeepSeek execution | **Reuse** | Actual DSH execution completed; 30/30 assertions, exactly one guarded DELETE, no retries or unrelated mutations. The artifact is tied to the same frozen Builder output. |
| Gold Oracle 3/3 adjudication | **Reuse as historical execution adjudication; re-check binding** | The adjudication of the frozen historical cases remains valid. Do not label it as adjudication of a newly generated dataset unless case identity and semantics are verified. |
| Formal Builder production | **PASS; reuse** | Run `44959366258` produced 15 cases from the current Skill package; the recorded candidate commit's Skill/schema blobs match the current package exactly. |
| Independent Builder-output validation | **PASS; reuse** | Run `44968128127` validated the archived output: 15 cases, 0 schema errors, 61 source references verified, and source identity/path/title/type checks passed. All 15 cases include `grading.evaluation_subject`; all 61 source refs match their source registry identity fields. |
| Three-case trial gate | **PASS; reuse all three** | The Round 4 immutable Builder output is already package-matched. The exact WB-02/WB-10/WB-12 case definitions are the ones consumed by the pilots; Gold Oracle adjudication is 3/3 PASS. No case rerun is justified. |
| Current-candidate behavior evaluation | **Not automatically required by SHA drift** | Determine whether the release evaluation compares Skill behavior rather than generation-time output. If it consumes a new dataset, ensure the dataset's relevant cases and grading contract are validated first. Avoid rerunning completed behavior cases merely to attach a new commit SHA. |

## Release gate recommendation

1. Reuse the Round 4 formal Builder output and independent validation. The package tree matches the current candidate exactly.
2. Reuse all three real pilot traces and Gold Oracle PASS 3/3. The selected case contracts were checked against the archived Builder output.
3. Do not re-run Builder, validator, pilots, or Oracle solely to rebind a new commit SHA.
4. Keep the separate diagnostic `builder-validation-summary.json` finding under review: its heuristic flags WB-03-C3, WB-04-C2, and WB-14-C2. Manual review shows these criteria assess the Skill's detection/reporting accuracy (including correctly reporting app deviations), not raw application outcomes, so the flags appear false-positive. The formal quality review also records 15/15 schema checks, source integrity checks, and a non-approved `needs_info` status due to the BR-09/error-recovery evidence gap. This does not invalidate the three selected pilot cases, but should remain visible as a quality limitation.
5. The remaining release work is separate: candidate-specific behavior evaluation, reconcile any true quality findings, exact-head CI, release review, and approval.

## Evidence links

- Round 4 formal Builder production: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258 (artifact 14729741906)
- Independent output validation: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127 (artifact 14732232796)
- Round 4 final acceptance report: `benchmarks/reports/round4-final-acceptance-decision-2026-11-22.md`
- WB-12 actual DeepSeek evaluation and Gold Oracle 3/3: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45189512695
- Historical exact-head CI: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45221565463

This is an evidence reuse audit, not a new execution or release approval. No model calls were made during this audit.
