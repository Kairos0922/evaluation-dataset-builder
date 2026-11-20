# Remaining Builder cases: conservative sequential execution plan

**Date:** 2026-11-21  
**Input:** The immutable Builder artifact from run [44726278657](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44726278657), artifact 14624897819, plus the offline role selector.  
**Status:** DRY RUN PLAN ONLY. This document and generated plan do not authorize or start DSH/model calls.

## Purpose

Convert the eleven Builder-authored cases into a conservative execution order. The plan does not edit the original case JSONL, choose replacement cases, adjudicate outcomes, or execute any Skill.

## Order and side-effect exposure

| Order | Role | Case | Class | Timeout |
|---:|---|---|---|---:|
| 1 | initial_board | WB-CORE-01 | Read-only | 180s |
| 2 | search_description | WB-CORE-03 | Read-only | 180s |
| 3 | search_empty | WB-CORE-04 | Read-only | 180s |
| 4 | status_filter | WB-CORE-05 | Read-only | 180s |
| 5 | search_filter_combo | WB-CORE-06 | Read-only | 240s |
| 6 | visible_title_mapping | WB-CORE-08 | Read-only | 180s |
| 7 | accessible_names | WB-CORE-07 | Dialog then Cancel | 180s |
| 8 | delete_cancel | WB-CORE-13 | Dialog then Cancel | 180s |
| 9 | create_rejected | WB-CORE-10 | Rejected write | 240s |
| 10 | create_success | WB-CORE-09 | Successful write | 240s |
| 11 | create_boundary_80 | WB-CORE-11 | Successful write | 240s |

Read-only cases run first, then dialog/cancel cases, then rejected-write behavior, and successful writes last.

## Budget arithmetic

- Sum of per-case timeout ceilings: **2,220 seconds (37 minutes)**.
- This is only the sum of maximum case durations. It is not a token estimate, a provider-billing estimate, or a predicted runtime.
- Actual run policy must be sequential: execute one case, inspect its trace/evidence and measured cost, then decide whether to continue.
- The Runner's provisional per-case step/token/DSH-time budgets remain enforced. A timeout or budget violation stops the sequence; no automatic model repair/retry.
- Each case is isolated in a fresh fixture. Evidence must be saved before moving on.

## Stop conditions

Stop and do not proceed to the next case if any case is BLOCKED, FAIL, UNKNOWN, or if:

1. independent evidence is incomplete or inconsistent;
2. case-level DSH/token/step budget is exceeded;
3. a secret/credential is found in output or artifacts;
4. the Builder source/provenance or artifact integrity is not verified;
5. a write occurs outside the declared side-effect class.

For create cases, check audit, pre/post state, summary, DOM and the exact expected title/priority. For dialog cases, preserve open-dialog and post-Cancel DOM snapshots, verify the dialog closed, the target row remains, and no DELETE occurred.

## Authorization

**No additional paid execution is authorized by this plan.** The three-case Pilot acceptance gate remains complete and unchanged. The eleven cases remain NOT_RUN. To proceed to real execution, the user must explicitly authorize the additional paid DSH/model calls and confirm the budget policy. After authorization, the safest starting point is one read-only case (WB-CORE-01), not the whole matrix.
