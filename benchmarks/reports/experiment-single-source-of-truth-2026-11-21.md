# Evaluation Dataset Builder experiment: single source of truth

Updated: 2026-11-21  
PR: #38, Draft/Open. Do not merge or close.  
Branch: `experiment/webapp-testing-contract`  
HEAD when this update was prepared: `fba670ce37e18e3a21059fc46c41a81d88e0dfcd`

## 1. Evaluation object and attribution boundary

This experiment assesses the quality and cost of **Evaluation Dataset Builder-generated evaluation datasets**.

Do not count target-Skill performance, Runner/CI engineering, infrastructure checks, or downstream skill execution as Builder benefit. Those are separate evidence categories. A target-Skill PASS/FAIL is not itself a Builder quality score.

Per case, use exactly one Builder-quality outcome:
- `ADEQUATE_FOR_THIS_CASE`
- `BUILDER_DEFECT_FOUND`
- `INCONCLUSIVE`

Review source fidelity, specification sufficiency, contract coherence, grading sufficiency, evidence determinacy, coverage contribution, discriminative intent, and cost proportionality. Do not invent weights or thresholds.

## 2. Immutable formal Builder production

| Item | Value |
|---|---|
| Formal Builder workflow run | `44889956698` |
| Builder result artifact | `14702092011` |
| Artifact SHA-256 | `11b10519fdc87ac35fcd2493c57f84600954374e3a5a490b935f27512773d1c9` |
| Frozen input artifact | `14701272903` |
| Frozen input artifact SHA-256 | `1a801304a29b5c2b883f35426a2c3a5e39e61dae1bf95c1f7f8e801fd29f11f6` |
| Independent validation artifact | `14702560789` |
| Independent validation SHA-256 | `5802192a6923da574a2adf91a667393707a052ba9eeab78fa585441fa89f7277` |
| Builder Skill invocation | One actual DSH Skill tool call; exit 0; final reason completed; 783 trace events |
| Output | 13 formal files; 2 JSONL datasets; 15 cases total |

The Builder output is immutable. Do not hand-edit, replace, or repair its generated cases. No new paid Builder production has been run.

### Independent validator

<badge>PASS</badge> The independent validator passed on the exact archived Builder output.

- Frozen input: 18/18 files SHA-256 verified; 6 pinned upstream Skill files.
- Datasets: `wb-core` 10 cases, `wb-advanced` 5 cases.
- Schema errors: 0.
- Source evidence references: 57/57 exact references verified against the frozen input.
- Coverage: 42/42 applicable items represented across 4 dimensions: business rules 10/10, capabilities 9/9, risks 10/10, scenarios 13/13.
- Universe: 46 items total, comprising 42 applicable, 1 `needs_info` (`BR-09-RF`), 3 `not_applicable`.
- Suite quality status: `needs_info`; `wb-core` `candidate`; `wb-advanced` `needs_info`.
- Generation-time execution status: `NOT_RUN`.

The validator establishes structural, schema, manifest, provenance, and exact-source integrity. It does not establish semantic grading coherence or runtime executability.

## 3. Builder production cost

Formal Builder production DSH telemetry:

| Metric | Tokens |
|---|---:|
| Input | 229 |
| Output | 1,316 |
| Cache read | 251,904 |
| Cache write | 0 |
| Total | **253,449** |

The separate minimal connectivity probe used 5,610 tokens and is excluded from the Builder production total. USD billing is unknown because no provider billing record was captured. Token telemetry is not a USD price.

Target-Skill pilot tokens are downstream execution costs, not Builder generation cost or Builder benefit.

## 4. Builder-quality adjudication

| Case | Outcome | Finding |
|---|---|---|
| `WBT-CORE-02-SEARCH-MATCH` | `BUILDER_DEFECT_FOUND` | Criterion G2 conflicts with case-level pass conditions on the mutant fixture. A correct defect-detection report can be failed by a generic grader that follows G2 literally. |
| `WBT-CORE-06-STATUS-CYCLE` | `INCONCLUSIVE` | Builder-authored timeout is 240s; one run timed out after 239.119s without a final response. This is a timeout-calibration risk, but one run cannot attribute cause conclusively. |
| `WBT-CORE-08-DELETE-CONFIRM` | `ADEQUATE_FOR_THIS_CASE` | One confirmed deletion, correct remaining state and summary, 22/22 checks, independent Oracle PASS. |

### Confirmed Builder defect: WBT-CORE-02 grading contradiction

The case is assigned to the controlled `search-case-sensitive` mutant. Its overall `pass_conditions` correctly require the Skill to report FAIL with evidence when the mutant violates BR-02. But criterion `WBT-CORE-02-G2` requires the two expected results in its `pass_condition` and treats an empty result as a `fail_condition`.

On the assigned mutant fixture, the two queries return no results. A correct Skill report identifying that violation can therefore satisfy the case-level contract while failing G2. This is a Builder defect in grading sufficiency and contract coherence.

The Builder's own `QUALITY-REVIEW.md` finding F-03 claims pass-condition semantics were corrected, but this criterion-level contradiction remained.

### Timeout risk: WBT-CORE-06

The case sets 240 seconds. DSH was terminated after 239.119 seconds, before the final event; no PATCH requests, report, evidence index, or screenshot were produced. The case budget itself was not exceeded, and the fixture server closed correctly. This is recorded as `INCONCLUSIVE`, not as a proven Builder defect or target-Skill business failure.

## 5. Three real target-Skill pilots

The corrected selector resolved three cases directly from the immutable Builder output. The original independent Builder PASS was rechecked before the pilot-only workflow reused the artifact. No Builder production was repeated.

| Case | Runner outcome | Oracle business-behavior outcome | Notes |
|---|---|---|---|
| `WBT-CORE-02-SEARCH-MATCH` | BLOCKED: 33 model steps exceeded Runner cap 32; DSH completed in 170.134s | `EXPECTED_VIOLATION_DETECTED` | Target report identified the two search defects and preserved read-only invariants. Contract still fails the Runner step budget. |
| `WBT-CORE-06-STATUS-CYCLE` | BLOCKED: 239.119s of 240s case timeout; no final response | `UNKNOWN` | Incomplete execution; no business verdict justified. |
| `WBT-CORE-08-DELETE-CONFIRM` | `INVOCATION_OK` | PASS | 100.658s, 16 model steps, one DELETE, 22/22 report checks. |

All three were attempted once. No retries, case substitutions, or additional paid model calls were made.

### Corrected independent Oracle

The first offline Oracle report exposed Oracle parsing defects: it over-extracted search terms from task titles, misread three Chinese ordinal clauses contained in one Builder list item, and treated an incomplete state-cycle run as business FAIL. These were Oracle defects, not Builder case defects. The Oracle parser and uncertainty handling were corrected and self-tested.

Corrected offline adjudication:
- Workflow run: `44894303807`
- Artifact: `14702569034`
- Contract verdicts: 1 PASS, 2 FAIL.
- Business-behavior verdicts: 1 PASS, 1 `EXPECTED_VIOLATION_DETECTED`, 1 `UNKNOWN`.

The two contract FAIL outcomes are caused by the Runner's model-step cap and the case timeout. They are not evidence that the Builder's business expectations were false. The pilot tranche is not 3/3 PASS.

## 6. Current decision

The Builder output has strong structural and source-provenance quality, but is not fully quality-approved:
- One direct Builder grading-contract defect is confirmed.
- The suite remains `needs_info` because the BR-09 request-failure branch lacks a controlled, auditable injection contract.
- One case timeout has insufficient observed margin, but attribution remains inconclusive.
- Only three of fifteen cases were piloted; two executions were incomplete under Runner limits.

Do not describe the suite as fully validated or quality-PASS. Any Builder repair experiment requires separate explicit authorization, a new immutable Builder artifact, and a fresh independent validation.

## 7. Evidence links

- Formal Builder run: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44889956698
- Corrected pilot run: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44892669832
- Corrected offline Oracle: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44894303807
- Quality adjudication report: [builder-output-quality-adjudication-2026-11-21.md](builder-output-quality-adjudication-2026-11-21.md)
- PR #38: https://github.com/Kairos0922/evaluation-dataset-builder/pull/38

## 8. Authorization and release gate

- PR #38 must remain Draft/Open and must not be merged or closed.
- Do not apply the `run-builder-production` label.
- Do not rerun Builder production or any target-Skill pilot without explicit authorization.
- Do not bypass the independent validator.
- Do not modify or replace formal Builder-generated cases.
- Treat current pilot evidence as limited, case-specific evidence only.
