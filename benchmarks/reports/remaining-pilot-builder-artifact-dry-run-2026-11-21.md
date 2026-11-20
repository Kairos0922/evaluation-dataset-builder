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


## Reverification addendum (2026-11-21)

- Re-downloaded Builder artifact ID `14624897819` and independently recomputed all nine archived SHA-256 values. The ZIP stores files under `webapp-testing-builder-output/`, while the hash manifest prefixes paths with `artifacts/`; stripping that prefix for archive lookup yields nine/ nine matches.
- Parsed the original `wb-core.jsonl` directly: 14 cases, all IDs unique. For the 11 remaining roles, each match was checked against structured `test_data.kind`, required business-rule refs, and workflow refs as defined in the committed selector. Each role matched exactly one case; all selected cases were `candidate`, `NOT_RUN`, target the local fixture URL, and had no unresolved OPEN/IN_PROGRESS gaps.
- Generated the resolved matrix from those matches and executed a local copy of the committed plan generator's source logic. Output: 11 steps, 2,220 seconds cumulative timeout ceiling, `DRY_RUN_PLAN_ONLY`, `execution_authorized=false`, `execution_started=false`, and every step `NOT_AUTHORIZED`. Assertions on uniqueness, exact role coverage, sequence, and authorization state passed.
- Boundary: the committed selector script itself was **not executed** from a repository checkout in this environment. The role resolution was a direct artifact-based implementation of its current matching requirements; the plan generator source was copied for local execution. CI run [#44837433532](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44837433532) passed repository validation and selector self-tests, but the artifact-specific matrix dry-run was not part of that CI run.
- No model, DSH, browser, or paid execution was started.
