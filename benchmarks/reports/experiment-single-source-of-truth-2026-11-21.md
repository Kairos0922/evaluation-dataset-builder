# Evaluation Dataset Builder experiment: single source of truth

Updated: 2026-11-21  
PR: [#38](https://github.com/Kairos0922/evaluation-dataset-builder/pull/38), Draft/Open. Do not merge or close.  
Branch: `experiment/webapp-testing-contract`  
Current scope: evaluate **Builder-generated evaluation dataset quality and generation cost**. Target-Skill performance, Runner/CI changes, and Oracle implementation work are separate evidence categories, not Builder benefits.

## 1. Current authoritative experiment state

The latest completed formal Builder round is **Round 2**, workflow [44901698634](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44901698634). This run supersedes Round 1 as the current production candidate. Round 1 remains historical evidence and must not be substituted for Round 2.

| Item | Current value |
|---|---|
| Formal Builder run | `44901698634` |
| Builder result artifact | `14706494963` |
| Independent structural validation artifact | `14706599576` |
| Frozen Builder input artifact | `14706331453` |
| Builder Skill calls | 1 actual DSH Skill call; exit 0; final reason `completed` |
| DSH trace | 988 events; 187 model usage records |
| Formal output | 1 dataset, 15 cases, 9 files |
| Case quality status | 14 candidate; 1 needs_info |
| Dataset/suite quality status | `needs_info` |
| Execution status at generation | `NOT_RUN` |

The Round 2 Builder output is immutable. Do not hand-edit, replace, or repair its generated JSONL, manifests, coverage matrix, source map, or quality report. Any subsequent Builder run must create a new immutable artifact.

## 2. Independent validation: structural PASS, not quality approval

Independent validator result: **PASS**.

- Schema errors: 0.
- Source evidence: 86/86 references verified.
- Frozen input integrity: 18/18 files SHA-256 verified, including 6 pinned upstream Skill files.
- Coverage universe: 64 items; 52 applicable, 11 not_applicable, 1 needs_info.
- Applicable coverage: 52/52 covered (capability 16/16; business rule 11/11; risk 15/15; scenario 10/10).
- The one unresolved gap is `BR-09-RF` / WC-15: the frozen inputs do not provide a supported request-failure injection contract. The Builder correctly preserved this as `needs_info`; do not invent an endpoint or mark it covered.

The validator establishes schema, manifest, provenance, evidence-source, and declared coverage integrity. It does **not** prove that every rubric is semantically optimal or every case is executable. The suite is not Approved.

## 3. Independent pilot adjudication on immutable Round 2 evidence

The three pilot cases were selected from the exact Round 2 Builder JSONL. No cases were hand-authored or substituted.

- Original production/pilot workflow: [44901698634](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44901698634)
- Corrected offline re-adjudication: [44908652144](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44908652144)
- Corrected adjudication artifact: `14709295258`
- Adjudication JSON SHA-256: `db4f6ecec37c159746c8bc9bdedaca75723f876cb8bcde8a90332e39a008969e`
- No Builder or target-Skill model calls were made during re-adjudication.

| Builder case | Target Skill/business behavior | Execution contract | Evidence-based interpretation |
|---|---|---|---|
| WC-03 search mutation | `EXPECTED_VIOLATION_DETECTED` | PASS | One test-script execution (1/1), zero mutations (0/0); the Skill correctly found the controlled case-sensitivity defect and truthfully reported FAIL. |
| WC-11 delete confirmation | PASS | FAIL | One correct deletion of WB-105; final state and summary correct. However, the test script was invoked twice against max 1 and `no_retry`; the first run aborted without writes and a second run succeeded. Correct business result does not erase the execution-contract violation. |
| WC-12 state cycle | FAIL | FAIL | One script execution (1/1) but only one of the three expected state transitions occurred. The target-generated test script stopped with `NameError: initial_info is not defined`. |

Aggregate: **1/3 contract PASS, 2/3 contract FAIL**. This is not 3/3 PASS and must not be generalized to the other 12 unexecuted cases.

A prior Oracle version misread the Builder's actual target fields and expected-cycle structure, and failed to count two kinds of script invocation. Those Oracle defects have been corrected and covered with tests:
- targets support Builder `data_id` and `visible_title`;
- state cycles support `expected_cycle.steps[].status`;
- direct script invocations with immediate shell separators are counted;
- truncated heredoc executions are counted only when the paired DSH tool result contains distinctive runtime output and exit evidence;
- static compilation and post-run imports are not counted as test runs;
- script-execution and mutation budgets are checked independently.

The archived re-adjudication workflow now distinguishes successful report generation from the verdict inside the report. A generated FAIL report is a completed adjudication, not a workflow implementation error.

## 4. Builder-specific grading quality

Round 1 found a material grading-contract contradiction in the earlier immutable artifact: a case-level rule accepted truthful detection of an application defect, while criterion G2 could fail the same Skill for observing the defect. That was a Builder output defect, not a target-Skill failure.

For Round 2, all 15 grading contracts were manually inspected for evaluation subject and consistency between case-level and criterion-level conditions. The prior direct contradiction was **not found** in the Round 2 JSONL. This is a documented manual review, not a validated semantic evaluator or guarantee against future defects.

The validator now has a generic, conservative Agent/Skill subject lint that rejects a bare application outcome used as the Agent/Skill failure condition, irrespective of case ID. This semantic lint is a targeted safeguard, not a complete natural-language understanding system.

## 5. Builder generation cost and production-efficiency evidence

Round 2 Builder DSH telemetry:

| Metric | Usage |
|---|---:|
| Input tokens | 120,724 |
| Output tokens | 297,681 |
| Cache-read tokens | 52,279,936 |
| Cache-write tokens | 0 |
| **Total tokens** | **52,698,341** |
| Model usage records/steps | 187 |
| Tool calls | 210 (114 bash, 54 edit, 32 read, 9 write, 1 skill) |

Separate connectivity probe: 5,610 tokens, excluded from the Builder-production total.

Downstream target-Skill pilots: WC-03 350,721 tokens; WC-11 631,600; WC-12 1,008,585; combined 1,990,906 tokens. These are downstream experiment costs, not Builder-generation costs or Builder benefits.

**USD billing is unknown.** No provider invoice/export was captured. Token telemetry is not a USD price, and cache-read tokens must not be assumed to have the same unit price as ordinary input tokens.

Trace inspection found avoidable production rework:
- 15 separate follow-up edits added `scenario_bucket` after the case records had been written.
- The source map was read 5 times and edited 5 times during the same production.
- The JSONL was edited 35 times; total edit tool calls were 54.
- There were 114 bash calls, including multiple separate deterministic checks that could be consolidated.

These are operation-count observations, not proof that every edit or command lacked value. Necessary source review and quality checks must remain. The goal is to avoid preventable schema omissions and repetitive validation, not to reduce quality.

## 6. Current offline improvements underway

After observing the actual Round 2 trace and adjudication:
1. `validate_evaluation_subject_contract` was generalized beyond the historical case ID. New regression tests use arbitrary case IDs to ensure a raw application failure cannot masquerade as an Agent/Skill failure.
2. `BUILDER-TASK.md` now requires a Schema field checklist before the first formal JSONL write, complete case objects (including `scenario_bucket` and `grading.evaluation_subject`) at initial insertion, and a frozen source registry instead of repetitive source-map repair.
3. Regression tests were added for the one-pass Schema/source planning contract.
4. Oracle changes and corrected archived adjudication are complete; no further paid calls or target-Skill pilots are currently justified.

Latest offline CI validation is running for the new generic subject lint and generation-efficiency constraints. Record its final result here after checking the exact PR head and workflow run. Do not infer pass from a previous commit's run.

## 7. Current decision and gates

- Current Round 2 output remains `needs_info`, not Approved.
- Independent structural Validator PASS remains necessary but is not sufficient for semantic quality approval.
- The three pilot verdicts remain 1 PASS / 2 FAIL, with WC-11 business behavior PASS but execution contract FAIL, and WC-12 business behavior FAIL.
- Do not rerun Builder production or the target Skill merely to seek a green aggregate. A new paid generation is only justified after offline rules are complete and the expected incremental Builder-quality benefit outweighs the measured ~52.7M-token production usage.
- Before any next production, preflight the Oracle against the generated field shapes and run offline structural/semantic lint.
- PR #38 must remain Draft/Open. Do not merge, close, apply the `run-builder-production` label, or bypass the independent validator.

## 8. Reports and evidence

- Current detailed Round 2 review: [builder-output-quality-cost-adjudication-round2-2026-11-21.md](builder-output-quality-cost-adjudication-round2-2026-11-21.md)
- Historical Round 1 review: [builder-output-quality-adjudication-2026-11-21.md](builder-output-quality-adjudication-2026-11-21.md)
- Adjudication protocol: [builder-output-quality-adjudication-protocol-2026-11-21.md](builder-output-quality-adjudication-protocol-2026-11-21.md)
- Round 2 Builder workflow: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44901698634
- Round 2 corrected re-adjudication: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44908652144
- PR #38: https://github.com/Kairos0922/evaluation-dataset-builder/pull/38
