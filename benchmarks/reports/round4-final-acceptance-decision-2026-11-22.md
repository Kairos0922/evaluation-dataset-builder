# Round 4 final acceptance decision (2026-11-22)

## Decision

**NOT PASSED.** Builder production and independent validation passed. The three real pilot runs and Oracle completed, but the independent adjudication returned FAIL for all three cases. Review of the immutable artifacts reveals two apparent Oracle contract/schema false-failures and one pilot blocked by model-provider quota. Therefore the Builder-generated suite is **not accepted in this round**. The evidence is sufficient to close this attempt without additional runs.

This is a terminal decision for this attempt. No retries, regenerated Builder output, or new engineering work are authorized by this report.

## Frozen scope

1. Reuse the Round 4 Builder output and independent-validator PASS.
2. Execute the three Builder-authored pilots once.
3. Review immutable pilot evidence and independent Oracle output.
4. Publish a final PASS/FAIL decision. No retry to chase PASS.

PR #38 remains Draft/Open/unmerged.

## Builder and validation evidence

- Builder production run: [44959366258](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258), artifact 14729741906.
  - One dataset, 15 cases; actual Builder Skill invocation verified; trace PASS, 530 events.
- Independent validation run: [44968128127](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127), artifact 14732232796.
  - PASS; one dataset, 15 cases, 0 schema errors, 61 source evidence references verified.
- Replay: [44980451933](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44980451933), commit 59d74dd79666c0c6e61f2c8ac53df4b30cc55860.
  - All three pilot jobs ran; Oracle job completed with FAIL.
  - Artifacts: WB-02 14738085222; WB-10 14738140416; WB-12 14737298412; Oracle 14737717458; immutable Builder input 14737577420.

## Pilot results and evidence review

| Case | Execution | Observed behavior | Oracle result | Independent review |
|---|---|---|---|---|
| WB-02 search mutation | DSH completed; 65.48s; 15 model steps; 21 tool calls; budget PASS | `PASSWORD` returned 0 and empty state; `password` returned 1, “Reset password flow”. Skill report accurately identifies case-sensitive behavior and BR-02 violation. No mutations. | Contract FAIL; business UNKNOWN | **Skill observation/report is behaviorally correct.** Oracle checks required probes/titles as empty because it did not extract the Builder case's array-form `expected_behavior` / query schema. It therefore fails to adjudicate the case contract. |
| WB-10 state cycle | DSH completed; 121.218s; 18 model steps; 26 tool calls; budget PASS | Exactly 3 PATCHes on WB-101: Open→In progress→Done→Open. Each summary matched; final state matched baseline; no other mutations. Skill report says PASS. | Contract FAIL; business FAIL | **Observed behavior PASS. Oracle false-fail suspected/strongly indicated:** its sole failed check says target report verdict does not match expected PASS, while archived report explicitly says PASS and audit transitions match. |
| WB-12 delete confirmation | DSH error; 81.043s; 15 model steps; 21 tool calls; budget PASS | Provider returned HTTP 402 QUOTA (“Insufficient Balance”). No DELETE occurred; task set and summary remained unchanged; no final report. | Contract FAIL; business FAIL | **Execution blocked; business outcome UNKNOWN, not a business FAIL.** Oracle could not resolve target from Builder test_data schema (target title field), and classified absent execution/report evidence as FAIL rather than separating invocation block from behavior. |

### WB-02 key observation

- `PASSWORD`: 0 rows, visible empty state “No tasks match the current filters.”, no visible error.
- `password`: 1 row, title “Reset password flow”, empty state hidden, no visible error.
- Control query `ZZZ_NO_MATCH_9137` also returned 0 and the same empty state.
- Initial/final task set identical; no reset or mutations; browser console errors empty.
- The Skill report correctly concluded that the application is case-sensitive and violates BR-02.

### WB-10 key observation

Observed transitions and summary (All / Open / In progress / Done):

| Step | Status | Summary |
|---|---|---|
| 1 | Open → In progress | 5 / 1 / 3 / 1 |
| 2 | In progress → Done | 5 / 1 / 2 / 2 |
| 3 | Done → Open | 5 / 2 / 2 / 1 |

Three PATCH requests only; the four other tasks remained unchanged. Evidence is internally consistent with PASS.

### WB-12 key observation

Runner evidence reports DSH final reason `error`, exit 1, error code `QUOTA`, HTTP 402. Server audit contains only reset and read requests; no DELETE. Pre/post task set is identical. The destructive action was **not** performed.

## Oracle reliability findings

The Oracle's aggregate FAIL is not a reliable business-quality conclusion for this pilot set:

1. **WB-02 schema extraction mismatch:** Builder `expected_behavior` is an array of prose requirements, but Oracle's required-query extraction appears to expect a different shape. Oracle reports no required queries/expected titles despite actual report and trace documenting both queries. The behavior is corroborated; contract adjudication is unresolved.
2. **WB-10 verdict mismatch:** archived Skill report says BR-07 PASS, and the server audit records the exact expected transitions. Oracle's failed check contradicts the report and observations. Treat as likely adjudicator false-negative pending code-level fix.
3. **WB-12 execution-state classification:** the target was never executed to completion due to provider quota. This should be execution-blocked / business UNKNOWN. Oracle instead emits FAIL, and target resolution also appears incompatible with the Builder's target-task test_data schema.

These findings are recorded as evidence-based defects/limitations in the independent adjudicator, not repaired during this acceptance attempt.

## Cost and resource use

Across all three pilot attempts: **48 model steps, 68 tool calls, 42,837 input tokens, 41,886 output tokens, 938,752 cache-read tokens, 1,023,475 total tokens**. USD cost is not available and is not estimated. WB-12's quota error occurred before deletion, so no destructive action was taken.

## Final gate

| Gate | Result |
|---|---|
| Builder production | PASS |
| Independent validation | PASS |
| Three pilot attempts captured | PASS (2 completed, 1 blocked) |
| Pilot business outcomes | WB-02 accurate observation; WB-10 PASS behavior; WB-12 UNKNOWN/block |
| Independent Oracle | FAIL, but adjudication reliability compromised by identified mismatches |
| Overall acceptance | **NOT PASSED** |

## Stop condition

Round 4 is closed **NOT PASSED**. Do not regenerate the Builder dataset, rerun paid pilots, add engineering work, merge or close PR #38. PR #38 remains Draft/Open/unmerged. A future round requires an explicit new decision and should prioritize fixing Oracle case-schema alignment and blocked-vs-business-fail classification before any new paid run.
