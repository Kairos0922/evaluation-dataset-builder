# Pilot Runner safety audit (2026-11-22)

## Decision

The Round 4 pilot remains **NOT RUN**. This pass performed static code review and repository safety cleanup only. No DSH/model request was made and no Builder output was changed.

## Findings

- The source Runner enforces cumulative model-step, input-token, output-token, cache-read-token and total-token ceilings while DSH is running. Missing or incomplete usage telemetry blocks `INVOCATION_OK` at finalization.
- The DSH process timeout is clamped to the Builder-declared case timeout. Each case gets a fresh fixture process and audit log; the Runner records pre/post application state, DSH trace digest/event count, run UUID, and whether the fixture port closed.
- The fixture server records the exact task object associated with a successful DELETE. The independent Oracle derives the expected target from the Builder-authored case and checks the deleted object, remaining tasks, and final summary. For Round 4, the resolved delete-confirmation case targets `WB-104`; `WB-102` in earlier notes belongs to historical evidence and is not the Round 4 target. This is **post-action detection**, not a pre-action interlock: the Runner and fixture currently do not prevent a mis-targeted delete by the target Skill. The Oracle must therefore remain a hard fail gate and the pilot must remain isolated to the disposable fixture.
- Round 3 evidence confirms the need for these controls: state-cycle output exceeded the 55,000-token cap and the delete pilot removed the wrong task.

## Safety remediation

Removed the obsolete Round 3 pilot dispatch workflow and its trigger file:

- `.github/workflows/resume-builder-pilot.yml`
- `.github/dispatch/resume-pilot-from-round3-44910360571`

The workflow was pinned to Round 3 Builder run `44910360571` and validator run `44914032444`, and its trigger text still claimed the three trials were authorized. Leaving this active could accidentally execute pilots against stale evidence. The deletion preserves the historical commits and artifacts.

## Verification

- Runner preflight on the workflow-deletion commit `3d0257383dceaff188176cc321ec35410f03b004`: PASS, run [44969107900](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44969107900).
- Runner preflight on final head `1ceefd5d2aa1ff7885ac5b8ed3eb99bb16939ea7`: PASS, run [44969110134](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44969110134). This includes actionlint across workflows, duplicate-key YAML validation, Runner/selector/Oracle self-tests, and pilot command-contract checks.
- Exact-head PR CI: PASS, run [44969112202](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44969112202). Offline suite: 208 tests passed; upstream asset audit and main-target check passed. Paid Builder, runtime, pilot, and adjudication jobs were skipped.
- The stale workflow and trigger are absent from the final branch tree.

## Remaining limits and next gate

- Static review does not prove live DSH telemetry behavior or target Skill safety.
- The delete case remains inherently side-effecting within its disposable fixture. The Oracle detects a wrong deletion after the fact; it does not prevent it.
- The 55,000-token output cap remains unchanged. The state-cycle case remains the highest resource-risk candidate.
- Do not launch the three Round 4 pilots until the execution decision explicitly accepts these residual risks and the exact Round 4 matrix. Do not lower assertions, evidence requirements, or safety controls.
- PR #38 remains Draft/Open and unmerged.
