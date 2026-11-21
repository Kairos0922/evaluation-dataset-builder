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


## CI and workflow hardening (2026-11-21)

- Fixed the manual artifact Dry Run workflow to download a prior-run artifact by ID through the authenticated GitHub REST API; `actions/download-artifact` is scoped to artifacts in the current workflow run and was unsuitable for this cross-run use case.
- Added artifact metadata checks (numeric ID, not expired, exact ID), authenticated ZIP download, and normalized the archived hash-manifest paths for the ZIP's actual directory layout before SHA-256 verification.
- Independently exercised the normalization against the previously downloaded original ZIP: all nine source files verified.
- Added the remaining-plan generator compile and focused unittest discovery to normal PR validation.
- Exact-head PR validation run [#44840616963](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44840616963) completed PASS: formal package validation, Benchmark validation, offline tests, Gold Oracle/validator checks, Selector self-tests, and upstream asset audit all passed. Runtime preflight and paid/experiment jobs were skipped as intended.
- The cross-run artifact Dry Run workflow itself was not dispatched in this environment, so its end-to-end GitHub download step remains unverified. No DSH/model call was made.

## Automated exact-artifact dry run (2026-11-21)

- Removed the prior verification boundary: the committed selector and plan generator were executed by GitHub Actions against the exact original Builder artifact, without a manual dispatch. Workflow run [#44849835465](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44849835465) was triggered by the push event on commit `48755cf841113cc4ea0fd26f1205c452665c803f`; its `artifact-dry-run` job and all seven substantive steps completed successfully.
- The workflow downloaded Builder artifact `14624897819`, verified its original SHA-256 manifest, resolved all eleven roles, built the non-executing plan, and archived artifact `14683758954` (`remaining-pilot-artifact-dry-run`). The resulting ZIP was downloaded and independently inspected: it contains `remaining-pilot-matrix.json` and `remaining-pilot-plan.json`; matrix SHA-256 `94e3c5d8af9d4d85cbf16b8b199d2a697f2a8479ba874d71ddbb694f995bb34f`; plan SHA-256 `e9354f2c038e3efbddb87e2cb0c8080c4af0bba24e18313d9034edf41a3bcb3e`.
- The archived plan independently confirms 11 unique Builder case IDs, exact required-role coverage, sequence 1–11, 2,220 seconds cumulative case-timeout ceiling, `DRY_RUN_PLAN_ONLY`, `execution_authorized=false`, `execution_started=false`, and all 11 steps `NOT_AUTHORIZED`.
- Exact-head Runner Preflight [#44849835358](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44849835358) completed PASS, including actionlint, duplicate YAML-key checks, runner compile/self-test and pilot command contract. Exact-head PR validation [#44849842362](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44849842362) completed PASS for package/benchmark validation, offline tests, Gold Oracle/validator checks, selector checks, upstream asset audit and main-target check. The runtime-preflight and paid execution jobs were skipped, as intended.
- The committed execution workflow explicitly passes the provisional per-case hard limits: 32 model steps, 60,000 input tokens, 55,000 output tokens, 1,600,000 cache-read tokens, 1,750,000 total tokens and a 600-second DSH ceiling, further capped by each Builder case timeout. These are operational stop limits, not quality thresholds or USD estimates.
- No DSH/model invocation, browser execution, fixture mutation, or paid work occurred. All eleven candidates remain `NOT_RUN`. PR #38 remains Draft/Open and unmerged.
