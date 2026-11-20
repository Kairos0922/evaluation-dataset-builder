# Remaining Builder case readiness review

**Date:** 2026-11-20  
**Source:** Immutable Builder output from run [44726278657](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44726278657), artifact `14624897819`.  
**Scope:** Offline classification of the 11 generated cases not included in the three completed Pilot roles. No DSH, Skill or model execution was performed.

## 1. Why these cases are not being launched yet

The current acceptance gate required three real Skill trials after formal Builder production and independent Builder validation. That three-case gate has been completed: WB-CORE-02, WB-CORE-12 and WB-CORE-14 have real execution evidence and corrected independent business-behavior Oracle verdicts.

The remaining 11 cases are an optional expansion from a three-case Pilot to broader execution coverage. They are not needed to claim the three-case Pilot gate. They must not be run merely because the Builder generated them: the current semantic selector and Gold Oracle only implement three roles. Running unsupported cases first and trying to invent adjudication afterward would weaken the independence of the evaluation.

## 2. Remaining-case inventory

| Case | Scenario | Interaction / side-effect class | Builder case timeout | Independent Oracle readiness |
|---|---|---|---:|---|
| WB-CORE-01 | Initial board and summary consistency | Read-only | 180s | Not implemented |
| WB-CORE-03 | Search by task description | Read-only search | 180s | Not implemented; server audit exposes query/result count |
| WB-CORE-04 | Empty search and empty-state message | Read-only search | 180s | Not implemented; server audit exposes query/result count |
| WB-CORE-05 | Single status filter and restore All | Read-only filter | 180s | Not implemented; server audit exposes status query/result count |
| WB-CORE-06 | Combined search and status filter | Read-only combined filter | 240s | Not implemented; server audit exposes query/status/result count |
| WB-CORE-07 | Accessible names for controls and dialog | Opens dialog, then Cancel; no intended mutation | 180s | Not implemented; requires independent rendered-DOM accessible-name checks |
| WB-CORE-08 | Visible-title mapping and read-only status check | Read-only | 180s | Not implemented |
| WB-CORE-09 | Create trimmed title with default Medium priority | One real create | 240s | Not implemented; server audit and post-state can independently verify |
| WB-CORE-10 | Reject whitespace-only title | One invalid create attempt; no intended mutation | 240s | Not implemented; fixture records rejected POST /api/tasks with HTTP 400 |
| WB-CORE-11 | Create 80-character title with explicit High priority | One real create | 240s | Not implemented; server audit and post-state can independently verify |
| WB-CORE-13 | Delete dialog Cancel path | Opens dialog, then Cancel; zero delete requests allowed | 180s | Partial: Gold Oracle already contains a cancel-scenario branch, but selector/role wiring and regression coverage are missing |

All 11 cases are Builder-marked `candidate` and have no OPEN/IN_PROGRESS information gaps. That establishes eligibility for future review, not Oracle readiness or execution success.

## 3. Safe execution ordering if full-suite coverage is requested

1. **Read-only baseline and query/filter cases:** WB-CORE-01, 03, 04, 05, 06, 08.
2. **Dialog and cancellation cases:** WB-CORE-07, 13. Verify no DELETE or other mutation.
3. **Rejected write attempt:** WB-CORE-10. Verify a single invalid submission, an observable error, no 201 response and unchanged state.
4. **Successful writes last:** WB-CORE-09 and 11. Each case must run in its own reset fixture, create exactly one task and verify the server-side audit, returned ID, resulting row and summary.

This ordering reduces the chance of spending time on write scenarios before the independent read-only and cancellation checks are stable. The runner resets the isolated fixture before each case; the Skill itself remains forbidden from calling reset.

## 4. Oracle work required before any of these cases can run

- Add semantic role resolution for all 11 scenarios without hard-coding a replacement case or editing Builder JSONL.
- Add independent Oracle branches for initial-state verification, description search, empty search, status filtering, combined filters, accessible names, visible-title mapping, successful creation, rejected creation and 80-character boundary creation.
- Wire WB-CORE-13 to the existing delete-cancel branch and add explicit regression tests proving that Cancel means zero DELETE requests and an unchanged task set.
- For WB-CORE-07, parse captured rendered DOM independently; do not treat the Skill's own accessibility-name report as the sole source of truth.
- Add self-tests with synthetic audit records and pre/post states for each role. Unknown or missing evidence must produce UNKNOWN, not a guessed PASS.
- Only after selector and Oracle tests pass should a selected case be run under the new per-case DSH budget monitor.

## 5. Cost exposure

The three observed Pilot aggregate trace totals were 634,679, 680,321 and 2,625,818. The median was 680,321; multiplying that by 11 gives a rough scale indicator of approximately 7.48 million aggregate trace tokens. This is not a forecast: case complexity varies, and WB-CORE-14 was a substantial outlier. The current per-case hard ceiling of 1.75 million would allow up to 19.25 million aggregate trace tokens across 11 cases if every case reached its ceiling.

These figures are cumulative trace usage, not unique prompt size and not provider billing. Actual USD cost still requires DeepSeek billing/export data. For that reason, a full 11-case run should not be started as one parallel batch. If authorized, run sequentially, inspect each artifact and usage summary, and stop before the next case if cost or quality evidence is abnormal.

## 6. Decision boundary

- **Three-case Pilot acceptance:** complete for the business-behavior gate, with the historical WB-CORE-14 execution-budget status explicitly UNKNOWN.
- **Full 14-case execution:** not started; not required by the current three-case Pilot gate.
- **Next technical prerequisite for full coverage:** independent Oracle and selector expansion for the 11 remaining cases.
- **Paid execution:** none authorized or started by this readiness review.
