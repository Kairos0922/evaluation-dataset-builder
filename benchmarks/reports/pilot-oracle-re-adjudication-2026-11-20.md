# Webapp-testing Pilot Oracle re-adjudication

**Date:** 2026-11-20  
**Scope:** Re-adjudicate the three archived real Skill pilot runs using the corrected independent Gold Oracle.  
**Model execution:** None during this replay. The Builder output and all three Pilot evidence packages were reused unchanged.

## Evidence lineage

| Stage | Workflow run / artifact | Result |
|---|---|---|
| Formal Builder production | Run [44726278657](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44726278657), artifact `14624897819` | Builder job succeeded; actual DSH Builder Skill invocation and trace were verified |
| Independent Builder validation | Same run, artifact `14624652990` | PASS against the actual Builder-produced suite |
| Search mutation Pilot | Same run, artifact `14625780995` | Real Skill execution completed |
| State-cycle Pilot | Same run, artifact `14625492287` | Real Skill execution completed |
| Delete-confirmation Pilot | Same run, artifact `14625534646` | Real Skill execution completed |
| Corrected offline Oracle replay | Run [44733891829](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44733891829), artifact `14627572220` | PASS, 3/3 |

The original Builder output, frozen input, three Pilot packages and their SHA-256 artifact digests were downloaded from the original run by the offline replay job. No Pilot was repeated and no Builder generation was started.

## Original Oracle failure and correction

The first adjudication in run `44726278657` returned FAIL 3/3. Evidence review showed that the report checks imposed literal business-rule identifiers (`BR-02`, `BR-07`, `BR-08`) that were not required as literal report text by the Builder-authored grading contracts. The delete Pilot also contained both a raw diagnostic report and a final post-processed report; concatenating both made the report check inspect diagnostic output as if it were the final report.

The Oracle was corrected to:
- judge the report against the case-declared observable outcome rather than requiring literal rule-ID strings;
- check the expected task/query and violation finding for search mutation;
- check the target and state-cycle result for state-cycle cases;
- check the target, confirmation dialog and delete action for delete-confirmation cases;
- prefer canonical final reports and use raw/original/diagnostic reports only as a fallback when no canonical report exists.

The business-behavior checks were not weakened: search result counts, state transitions, target identity, writes/deletes, pre/post state, summary, DSH invocation evidence, and evidence-package requirements remain independently checked.

Regression tests were added in `tests/test_gold_oracle_reporting.py`. The exact-head PR validation run reported 163 unit tests passing and the Gold Oracle self-test passing.

## Corrected adjudication

Run `44733891829` re-downloaded the original Builder artifact and the three original Pilot artifacts, then ran the corrected Gold Oracle without invoking DSH or a model.

| Case | Pilot role | Contract verdict | Oracle verdict | Business behavior |
|---|---|---:|---:|---|
| `WB-CORE-02` | search_mutation | PASS | PASS | EXPECTED_VIOLATION_DETECTED | PASS (runner 137.3s; case budget 180s) |
| `WB-CORE-12` | state_cycle | PASS | PASS | PASS | PASS (runner 167.9s; case budget 300s) |
| `WB-CORE-14` | delete_confirmation | PASS | PASS | PASS | UNKNOWN (runner 362.6s; case budget 240s; actual DSH elapsed not recorded) |

**Business-behavior adjudication:** `status=PASS`, `case_count=3`, `passed_cases=3`, `failed_cases=0`, `verdict_counts={"PASS": 3}`.

**Execution-budget evidence:** 2 cases are demonstrably within their declared budgets because total runner wall time is below the budget. WB-CORE-14 is UNKNOWN: its total runner wall time exceeded the 240-second case budget, but includes fixture setup/teardown and the old runner did not record the DSH process's own elapsed time. Its exact budget compliance cannot be reconstructed from the archived trace.

The search-mutation case is a controlled synthetic defect. Its expected outcome is that the Skill detects and reports the defect, not that the mutated application passes the business rule. The three business-behavior PASS verdicts must not be presented as proof that every operational execution constraint passed.

## Gate status and limitations

- The formal Builder production and independent Builder validation gates passed in the original run.
- The three real Skill Pilot executions completed and the corrected independent Oracle adjudicated all three business-behavior outcomes PASS.
- Operational case-budget compliance is PASS for WB-CORE-02 and WB-CORE-12; WB-CORE-14 remains UNKNOWN because the old runner did not record DSH elapsed time separately.
- The replay establishes the result for these three selected cases only. It does not establish that every generated case has been executed or that the full generated suite meets all release gates.
- PR #38 remains Draft/Open and unmerged.
- The `run-builder-production` opt-in label was removed after the original production run to prevent accidental paid Builder executions. No new Builder or Pilot model execution is authorized by this report.
