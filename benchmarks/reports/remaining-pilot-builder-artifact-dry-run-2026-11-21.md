# Remaining Builder Cases: Artifact Dry-Run Resolution

Date: 2026-11-21

## Scope and safety

This is an offline dry-run against the original Builder-produced artifact (workflow artifact ID `14624897819`). No DSH invocation, model call, browser execution, fixture mutation, or paid work was started. All 11 cases remain `NOT_RUN`; this report does not claim execution or evaluation results.

## Artifact integrity

The original ZIP was inspected. The archived `builder-output-sha256.txt` contains nine hashes for the Builder output files. All nine were recomputed and matched, including `wb-core.jsonl` SHA-256:

`0a1f549af5adbb790b134e7b740750b58b86845583acb7bea4e21131753271c1`

The JSONL contains 14 cases with unique case IDs. Each selected case is from the original Builder JSONL; no case was authored or edited for this plan.

## Semantic role resolution

Each role was resolved using the structured `execution_requirements.test_data[].kind`, corroborating business-rule references, and workflow references. Every role had exactly one match:

| Order | Role | Builder case | Test-data kind | Side-effect class | Timeout |
|---:|---|---|---|---|---:|
| 1 | initial_board | WB-CORE-01 | initial_board | read_only | 180s |
| 2 | search_description | WB-CORE-03 | search_description | read_only | 180s |
| 3 | search_empty | WB-CORE-04 | search_empty | read_only | 180s |
| 4 | status_filter | WB-CORE-05 | status_filter | read_only | 180s |
| 5 | search_filter_combo | WB-CORE-06 | search_filter_combo | read_only | 240s |
| 6 | visible_title_mapping | WB-CORE-08 | recon_only | read_only | 180s |
| 7 | accessible_names | WB-CORE-07 | accessible_names | dialog_cancel | 180s |
| 8 | delete_cancel | WB-CORE-13 | delete_cancel | dialog_cancel | 180s |
| 9 | create_rejected | WB-CORE-10 | invalid_create | rejected_write | 240s |
| 10 | create_success | WB-CORE-09 | create_task | successful_write | 240s |
| 11 | create_boundary_80 | WB-CORE-11 | boundary_create | successful_write | 240s |

The role set and case IDs are unique and complete. The execution order moves from read-only checks to dialog-cancel checks, rejected write, then successful writes.

## Plan summary

- Cases: 11
- Sum of per-case timeout ceilings: 2,220 seconds (37 minutes)
- Policy: strictly sequential; inspect trace, evidence, elapsed time, and usage after each case before deciding whether to continue.
- Authorization: false
- Execution started: false
- All steps: `NOT_AUTHORIZED`

The 37-minute sum is a timeout ceiling, not a runtime estimate or token/cost estimate.

## Stop conditions

Stop the sequence if any case is BLOCKED, FAIL, UNKNOWN, or has evidence-integrity problems; if any DSH usage/time budget is exceeded; if credentials/secrets appear in evidence; or if provenance/artifact integrity cannot be verified.

## Verification boundary

The artifact hashes and semantic role-to-case mapping were independently inspected and checked in an offline dry-run. The repository's committed selector and plan scripts were reviewed, but they were **not executed in this local environment against this artifact**. This report therefore records the direct artifact resolution, not a claim that the scripts' end-to-end artifact command was run. The next engineering step is to wire this exact-artifact dry-run into CI or run the scripts in a checkout, then verify the generated JSON matches this mapping before any paid execution.
