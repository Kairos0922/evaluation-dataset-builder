# Webapp-testing / Evaluation Dataset Builder experiment: single source of truth

Updated: 2026-11-21  
PR: #38, Draft/Open; do not merge or close.  
Branch: `experiment/webapp-testing-contract`  
Current HEAD at document creation: `a2eb13af68df15301aa10650a434da426bb44e58`

## Goal and evaluation object

This experiment assesses **Evaluation Dataset Builder-generated dataset quality**. It does not assess target Skill quality, Runner/CI infrastructure quality, or overall webapp-testing skill behavior except insofar as actual execution reveals whether Builder-generated cases are executable, evidence-supported, discriminative, and independently adjudicable.

## Immutable formal Builder output

- Formal Builder run: `44726278657`
- Artifact ID: `14624897819`
- JSONL SHA-256: `0a1f549af5adbb790b134e7b740750b58b86845583acb7bea4e21131753271c1`
- Independent validator: **PASS** on this exact output.
- Source quote verification: selected six-case tranche **19/19 exact quote checks PASS** against frozen Builder input.
- Builder regeneration is not currently warranted; no authorization for a new paid production call.

## Execution status ledger

| Case | Status | Evidence / decision |
|---|---|---|
| WB-CORE-02 | REAL PILOT COMPLETE | Search mutation; Runner/Oracle artifacts previously reviewed |
| WB-CORE-12 | REAL PILOT COMPLETE | State cycle; Runner/Oracle artifacts previously reviewed |
| WB-CORE-14 | REAL PILOT COMPLETE | Delete confirmation; note elapsed-time compliance was not independently measured |
| WB-CORE-03 | NOT_RUN | Recommended next; read-only description search |
| WB-CORE-05 | NOT_RUN | Status filter and restore All |
| WB-CORE-07 | NOT_RUN | Accessible names and control inventory |
| WB-CORE-13 | NOT_RUN | Delete cancel / no side effect |
| WB-CORE-10 | NOT_RUN | Reject whitespace-only create |
| WB-CORE-09 | NOT_RUN | Successful create normalization/defaults |
| WB-CORE-01 | DEFERRED | Lower expected marginal Builder-quality value / overlap |
| WB-CORE-04 | DEFERRED | Lower expected marginal Builder-quality value / overlap |
| WB-CORE-06 | DEFERRED | Lower expected marginal Builder-quality value / overlap |
| WB-CORE-08 | DEFERRED | Lower expected marginal Builder-quality value / overlap |
| WB-CORE-11 | DEFERRED | Lower expected marginal Builder-quality value / overlap |

The accepted additional tranche is six cases, ordered sequentially: 03, 05, 07, 13, 10, 09. This is a purposive sample, not statistical coverage of all Builder output.

## Completed engineering and review

- Independent output validation against real formal Builder output.
- Source quote/path/hash checks.
- Static review of six candidate case contracts; no material Builder defect identified at static stage. Precision risks noted for WB-CORE-07 subjective accessible-name criterion and WB-CORE-10 error-state determinacy.
- Structured Builder-quality adjudication protocol; no invented score weights or thresholds.
- Sequential execution planning, dry-run and preflight.
- Execution budget/stop rules and cost limitations recorded.
- Runner/Oracle evidence-manifest path hardening, run correlation, trace integrity, symlink preservation, and offline regression tests.
- WB-CORE-03 focused execution checklist prepared; it remains preparation, not a run.
- Current CI exact-head PASS: workflow run `44887766089`; `validate`, `audit-upstream-assets`, `require-main-target` PASS. Runtime and paid Builder/pilot/Oracle jobs SKIPPED as designed.

## Builder-specific adjudication outcome framework

Per case, record one:
- `ADEQUATE_FOR_THIS_CASE`
- `BUILDER_DEFECT_FOUND`
- `INCONCLUSIVE`

Review source fidelity, specification sufficiency, contract coherence, grading sufficiency, evidence determinacy, coverage contribution, discriminative intent, and cost proportionality. Do not treat target Skill PASS/FAIL, successful run count, infrastructure tests, or tokens alone as Builder benefit.

## Cost accounting and continuation

- Aggregate trace-token figures are telemetry, not USD.
- Provider billing is **UNKNOWN** unless billing evidence is captured.
- Total proposed six-case ceiling: 1,200 seconds; this is time ceiling, not price estimate.
- Sequential case ceilings are operational stop limits; do not interpret as expected spend.
- After each single run, decide whether it yielded usable Builder-quality information and whether the next case's marginal information justifies cost. No automatic continuation.

## Blocking authorization

Paid DSH/model execution is not authorized. Do not initiate:
- WB-CORE-03 or any other real Skill trial;
- a new formal Builder production run;
- paid model-based repair/retry;
- provider switching.

No automatic retries, case edits, or case substitution. Partial outputs remain diagnostic only. An explicit user authorization for a named operation is required.

## Completion criteria

The **safe engineering phase** is complete when this status ledger is accurate, all documentation and static work is committed, exact-head required CI passes, and all unverified/blocked claims are clearly labeled.

The **experiment** is not complete until the six-case tranche is either:
1. run sequentially under explicit authorization, with per-case evidence reviewed and Builder-specific adjudication recorded, stopping as required; or
2. deliberately closed by the user as an authorization-blocked / limited-evidence study, with conclusions and limitations written.

Do not claim the experiment, Builder quality, or six-case tranche is complete merely because engineering/CI is complete.
