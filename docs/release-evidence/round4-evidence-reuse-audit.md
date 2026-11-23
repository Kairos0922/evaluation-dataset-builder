# Round 4 evidence reuse audit for release candidate 0.0.1

Date: 2026-11-24

## Scope

Compare the Skill package used by the frozen Round 4 Builder evidence with the current Skill package synced from PR #38. This audit determines which prior evidence can be reused and which gates require targeted follow-up. It does not trigger model calls.

Historical Builder evidence SHA: `93f4ce7464d48009aaf0a341cdb15da509a9f868`  
Current source Skill branch: `experiment/webapp-testing-contract`  
Current Skill file blob SHA: `1743b5b133e83d7f9a3332d9bae5912b0300dccb`  
Historical Skill file blob SHA: `945d9f837b7b7af711886ce496a423384981cb78`

Historical schema blob SHA: `e9473927c0b99f0e18c28ca5968413711e663317`  
Current schema blob SHA: `b1314c3d7811dfd0c1e61ddad245927add92affa`

## Exact changes

The current Skill adds two requirements (no previous lines were removed):

1. **Source-reference identity consistency:** source-map/source registry identity fields (`source_id`, `title`, `source_type`, `path`) must match each case's `source_refs`; copy canonical values, put section/topic notes in `locator`, and check identity before generation.
2. **Explicit evaluation subject:** each grading contract must distinguish the application/API from the testing/auditing/diagnostic Agent or Skill. Application defects are facts for a testing Agent to discover, not automatically Agent failures. Criteria must assess one subject consistently; split criteria when evaluating both subjects; case-level verdicts must align with criteria.

The schema adds required `grading.evaluation_subject` with a description identifying the actual subject being scored.

## Evidence disposition

| Evidence | Decision | Reason / follow-up |
|---|---|---|
| WB-02, WB-10, WB-12 real execution traces | **Reuse, subject to case identity check** | These additions concern dataset authoring and grading-contract clarity. They do not change browser/runtime instructions, tool usage, or the tested application interactions. Verify the corresponding case IDs and scenario/action/assertion semantics remain equivalent in the refreshed Builder output before binding the traces to it. |
| WB-12 DeepSeek execution | **Reuse** | Actual DSH execution completed; 30/30 assertions, exactly one guarded DELETE, no retries or unrelated mutations. No changed requirement modifies the delete-confirmation interaction itself. |
| Gold Oracle 3/3 adjudication | **Reuse as historical execution adjudication; re-check binding** | The adjudication of the frozen historical cases remains valid. Do not label it as adjudication of a newly generated dataset unless case identity and semantics are verified. |
| Formal Builder production | **Must run against current Skill** | The new source-identity and evaluation-subject requirements are generation-time contract changes not covered by the historical Builder invocation. |
| Independent Builder-output validation | **Must run against current schema/output** | Historical output predates required `grading.evaluation_subject`; it cannot establish conformance to the current schema. Validate the new formal output. |
| Three-case trial gate | **No blanket rerun** | Reuse prior trials if the refreshed dataset preserves the same selected cases and materially equivalent instructions, preconditions, assertions, and allowed actions. If any selected case changes in behaviorally relevant ways, rerun only that affected trial. |
| Current-candidate behavior evaluation | **Not automatically required by SHA drift** | Determine whether the release evaluation compares Skill behavior rather than generation-time output. If it consumes a new dataset, ensure the dataset's relevant cases and grading contract are validated first. Avoid rerunning completed behavior cases merely to attach a new commit SHA. |

## Release gate recommendation

1. Run formal Builder production using the current Skill only because the dataset-generation contract changed.
2. Run the independent validator on that exact output/current schema.
3. Compare the new Builder output to the frozen Round 4 dataset for the three pilot case IDs, their source references, grading subject, criteria, preconditions, allowed actions, and observable assertions.
4. Reuse the three historical pilot traces and Gold Oracle adjudication for unchanged cases. If any case's behavior contract changes materially, run only that case.
5. Record exact artifact IDs, case-level comparison, and reused evidence references. Do not require a new full behavior evaluation solely because the Git SHA changed.

## Evidence links

- Round 4 final acceptance report: `benchmarks/reports/round4-final-acceptance-decision-2026-11-22.md`
- WB-12 actual DeepSeek evaluation: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45189512695
- Historical exact-head CI: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45221565463

This is an evidence reuse audit, not a new execution or release approval.
