# Remaining Builder case readiness review

**Date:** 2026-11-20  
**Source:** Immutable Builder output from run [44726278657](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44726278657), artifact `14624897819`.  
**Scope:** Offline classification of the 11 generated cases not included in the three completed Pilot roles. No DSH, Skill or model execution was performed.

## 1. Why these cases are not being launched yet

The current acceptance gate required three real Skill trials after formal Builder production and independent Builder validation. That three-case gate has been completed: WB-CORE-02, WB-CORE-12 and WB-CORE-14 have real execution evidence and corrected independent business-behavior Oracle verdicts.

The remaining 11 cases are an optional expansion from a three-case Pilot to broader execution coverage. They are not needed to claim the three-case Pilot gate. The selector and independent Gold Oracle now have offline implementations for all eleven semantic roles, with synthetic regression fixtures. This closes the previous code-coverage prerequisite, but it does not constitute execution evidence for the real Builder cases. All eleven remain NOT_RUN; no paid DSH/Skill run was started in this phase.

## 2. Remaining-case inventory

| Case | Scenario | Interaction / side-effect class | Builder case timeout | Independent Oracle readiness |
|---|---|---|---:|---|
| WB-CORE-01 | Initial board and summary consistency | Read-only | 180s | Implemented offline; selector + state/DOM Oracle tests pass; real case NOT_RUN |
| WB-CORE-03 | Search by task description | Read-only search | 180s | Implemented offline; query audit + exact result-DOM checks; real case NOT_RUN |
| WB-CORE-04 | Empty search and empty-state message | Read-only search | 180s | Implemented offline; zero-result audit + visible empty-state DOM check; real case NOT_RUN |
| WB-CORE-05 | Single status filter and restore All | Read-only filter | 180s | Implemented offline; selected/restored query audit + separate DOM states; real case NOT_RUN |
| WB-CORE-06 | Combined search and status filter | Read-only combined filter | 240s | Implemented offline; all declared query/filter states checked; real case NOT_RUN |
| WB-CORE-07 | Accessible names for controls and dialog | Opens dialog, then Cancel; no intended mutation | 180s | Implemented offline; role/name pairs and target title parsed from rendered DOM; real case NOT_RUN |
| WB-CORE-08 | Visible-title mapping and read-only status check | Read-only | 180s | Implemented offline; exact visible row/status/action and no data-ID leakage; real case NOT_RUN |
| WB-CORE-09 | Create trimmed title with default Medium priority | One real create | 240s | Implemented offline; one audited create, trimmed title, priority, description, state and DOM; real case NOT_RUN |
| WB-CORE-10 | Reject whitespace-only title | One invalid create attempt; no intended mutation | 240s | Implemented offline; one HTTP 400 rejection, error DOM and unchanged state; real case NOT_RUN |
| WB-CORE-11 | Create 80-character title with explicit High priority | One real create | 240s | Implemented offline; exact 80-char input, one create, preserved baseline and updated summary; real case NOT_RUN |
| WB-CORE-13 | Delete dialog Cancel path | Opens dialog, then Cancel; zero delete requests allowed | 180s | Implemented offline; zero writes, visible dialog/actions, closed dialog and target retention; real case NOT_RUN |

All 11 cases are Builder-marked `candidate` and have no OPEN/IN_PROGRESS information gaps. That establishes eligibility for future review, not execution success.

### Offline implementation status

- `resolve_pilot_matrix.py` now supports eleven additional semantic roles, but only behind `--include-remaining-candidates`. The default path remains the accepted three-case Pilot.
- Each role requires a structured `execution_requirements.test_data[].kind` plus corroborating business-rule and workflow references. The selector self-test resolves an isolated eleven-role matrix and verifies all source cases remain `NOT_RUN`.
- `gold_oracle.py` independently checks server audit, pre/post state, and rendered HTML DOM snapshots. It does not use the target Skill's own verdict as the sole evidence source. Missing DOM, audit or state evidence is `UNKNOWN`, not an assumed pass or fail.
- Synthetic regression fixtures exercise the eleven role branches, including separate query/filter DOM states, accessible names, create/reject/boundary behavior, and the open/closed delete dialog lifecycle. These fixtures are tests of the validator, not Builder output and not real Skill executions.
- The latest PR validation run [44756938809](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44756938809) and runner preflight [44756928738](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44756928738) passed. Paid Builder/Validator/Pilot jobs were skipped.

## 3. Safe execution ordering if full-suite coverage is requested

1. **Read-only baseline and query/filter cases:** WB-CORE-01, 03, 04, 05, 06, 08.
2. **Dialog and cancellation cases:** WB-CORE-07, 13. Verify no DELETE or other mutation.
3. **Rejected write attempt:** WB-CORE-10. Verify a single invalid submission, an observable error, no 201 response and unchanged state.
4. **Successful writes last:** WB-CORE-09 and 11. Each case must run in its own reset fixture, create exactly one task and verify the server-side audit, returned ID, resulting row and summary.

This ordering reduces the chance of spending time on write scenarios before the independent read-only and cancellation checks are stable. The runner resets the isolated fixture before each case; the Skill itself remains forbidden from calling reset.

## 4. Remaining gates before any of these cases can run

The selector and Oracle implementation work described in the initial readiness review is complete and has passed the offline CI gate. The remaining prerequisites concern real execution, not missing code:

- The eleven formal Builder-authored JSONL cases must remain unchanged; no hand-authored replacement cases may be used.
- Before optional expansion is run, obtain explicit authorization for the additional DSH/model cost. The three-case Pilot gate does not imply authorization to execute the other eleven.
- Use the new per-case DSH timeout/token/step monitor. Run sequentially, one case at a time, inspect its artifacts and usage before proceeding, and stop on any budget violation.
- A real case can only receive PASS/FAIL when the required independent evidence exists. Missing DOM snapshots, audit logs or state must remain UNKNOWN.
- For WB-CORE-07 and WB-CORE-13, capture rendered DOM evidence for the dialog-open state and post-Cancel state. Screenshots and the Skill's report alone are not substitutes for semantic DOM evidence.
- The new budget monitor has only offline test evidence. Its behavior under paid DSH execution is still unverified, and no such validation was started in this phase.

## 5. Cost exposure

The three observed Pilot aggregate trace totals were 634,679, 680,321 and 2,625,818. The median was 680,321; multiplying that by 11 gives a rough scale indicator of approximately 7.48 million aggregate trace tokens. This is not a forecast: case complexity varies, and WB-CORE-14 was a substantial outlier. The current per-case hard ceiling of 1.75 million would allow up to 19.25 million aggregate trace tokens across 11 cases if every case reached its ceiling.

These figures are cumulative trace usage, not unique prompt size and not provider billing. Actual USD cost still requires DeepSeek billing/export data. For that reason, a full 11-case run should not be started as one parallel batch. If authorized, run sequentially, inspect each artifact and usage summary, and stop before the next case if cost or quality evidence is abnormal.

## 6. Decision boundary

- **Three-case Pilot acceptance:** complete for the business-behavior gate, with the historical WB-CORE-14 execution-budget status explicitly UNKNOWN.
- **Full 14-case execution:** not started; not required by the current three-case Pilot gate.
- **Offline technical prerequisite for full coverage:** selector and independent Oracle expansion for the 11 remaining cases is implemented and passes synthetic regression tests.
- **Real 11-case execution:** not started; all eleven cases remain NOT_RUN. Offline self-tests do not count as case execution.
- **Paid execution:** none authorized or started by this phase.
