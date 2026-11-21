# Evaluation Dataset Builder formal output: quality adjudication

Date: 2026-11-21  
Scope: **quality and cost of the Builder-generated evaluation datasets only**. Target-Skill performance, Runner/CI quality, and infrastructure work are not counted as Builder benefits.

## 1. Immutable production evidence

| Item | Evidence |
|---|---|
| Formal Builder run | `44889956698` |
| Builder artifact | `14702092011` |
| Artifact SHA-256 | `11b10519fdc87ac35fcd2493c57f84600954374e3a5a490b935f27512773d1c9` |
| Frozen input artifact | `14701272903` |
| Frozen input SHA-256 | `1a801304a29b5c2b883f35426a2c3a5e39e61dae95f1c1f7f8e801fd29f11f6` |
| Independent validation artifact | `14702560789` |
| Independent validation artifact SHA-256 | `5802192a6923da574a2adf91a667393707a052ba9eeab78fa585441fa89f7277` |
| Builder invocation | One actual Evaluation Dataset Builder Skill tool call; DSH exit 0; final reason `completed`; 783 trace events |
| Output files | 13 formal files: 2 JSONL datasets, 2 dataset manifests, suite manifest, coverage matrix, source map, README, build plan, assumptions/gaps, quality review, report template, changelog |

The Builder output is immutable. No generated case was edited, substituted, or repaired.

## 2. Independent validator result

<badge>PASS</badge> Independent validation passed on the exact artifact above.

- Frozen input integrity: 18/18 files SHA-256 verified; 6 pinned upstream Skill files; no formal evaluation cases or Gold Oracle in the input bundle.
- Output: 2 datasets, 15 cases, 10 in `wb-core` and 5 in `wb-advanced`.
- Schema errors: 0.
- Source evidence references: 57/57 verified against the exact archived input, including source identity, locator, path, source hash, and normalized exact quote.
- Coverage universe: 46 items, comprising 42 applicable, 1 `needs_info` (`BR-09-RF`), and 3 `not_applicable`.
- Applicable coverage: business rules 10/10, capabilities 9/9, risks 10/10, scenarios 13/13.
- Quality roll-up: suite `needs_info`; `wb-core` `candidate`; `wb-advanced` `needs_info`.
- Execution status at generation: `NOT_RUN`.

Important limitation: this validator establishes structural, schema, manifest, provenance, and exact-source integrity. It does not prove that every grading contract is semantically coherent or that every case is executable within its selected time budget.

## 3. Builder production cost

The final cumulative DSH usage record for the formal Builder production was:

| Metric | Usage |
|---|---:|
| Input tokens | 229 |
| Output tokens | 1,316 |
| Cache-read tokens | 251,904 |
| Cache-write tokens | 0 |
| Total tokens | **253,449** |

A separate minimal connectivity probe used 5,610 tokens and is not included in the Builder production total. USD billing is **unknown** because no provider billing record was captured. Token telemetry is not a USD price.

The three target-Skill pilot calls consumed additional tokens. They are downstream experiment cost, not Builder production cost, and are excluded from the Builder cost figure.

## 4. Static Builder-quality adjudication

### 4.1 Direct Builder defect found: grading contract contradiction

<badge color="danger">BUILDER_DEFECT_FOUND</badge> Case `WBT-CORE-02-SEARCH-MATCH`.

The case is assigned to the controlled mutant fixture with `search-case-sensitive`. The fixture returns no results for uppercase `PASSWORD` and for `screenshots` because the mutant searches case-sensitively in titles only. The case-level `pass_conditions` correctly say that the Skill should report FAIL with evidence when the observed results violate BR-02.

However, the criterion `WBT-CORE-02-G2` is internally contradictory:

- Its `pass_condition` requires `PASSWORD` to show `Reset password flow` and `screenshots` to show `Update onboarding guide`.
- Its `fail_condition` treats either query returning empty as a failure.
- The case's overall `pass_conditions` require the Skill to report FAIL accurately when the mutant violates BR-02.

Therefore, a generic grader applying the criterion literally can fail a correct defect-detection report. The criterion-level contract and case-level contract do not agree. This is a Builder output defect in grading sufficiency and contract coherence.

The Builder's own `QUALITY-REVIEW.md` finding F-03 says pass conditions were corrected so that accurate defect reporting is accepted, but the criterion-level G2 pass/fail conditions remain contradictory. The review did not catch this residual defect.

The independent Gold Oracle uses fixture-branch logic and can separately recognize the expected violation. That does not repair the Builder artifact's own grading contract.

### 4.2 Timeout calibration risk: inconclusive

<badge color="warning">INCONCLUSIVE</badge> Case `WBT-CORE-06-STATUS-CYCLE`.

- Builder-authored case timeout: 240 seconds.
- Observed DSH elapsed time: 239.119 seconds.
- DSH exited with timeout code 124; no final event or turn-end event.
- No status PATCH occurred; no final report, evidence index, or screenshot was produced.
- The Runner closed the fixture server and preserved the trace and audit evidence.

The timeout is part of the Builder-generated case contract, so the near-zero margin is a legitimate quality risk. But one execution cannot distinguish an under-calibrated Builder timeout from target-Skill/DSH runtime variability. No retry is permitted by the case's zero-retry budget. Do not classify this as a proven Builder defect or as a target-Skill business failure.

### 4.3 Case-specific adequate result

<badge color="success">ADEQUATE_FOR_THIS_CASE</badge> Case `WBT-CORE-08-DELETE-CONFIRM`.

- Builder-authored timeout: 180 seconds; observed DSH elapsed time: 100.658 seconds.
- Runner status: `INVOCATION_OK`; case budget PASS; 16 model steps.
- One confirmation click and one `DELETE /api/tasks/WB-104` request, HTTP 200.
- Only the declared task was removed; four other tasks remained unchanged.
- Summary correctly changed from 5/2/2/1 to 4/1/2/1.
- Target report: 22/22 checks PASS.
- Independent Gold Oracle: PASS.

This supports the adequacy of this case's specification, action budget, evidence requirements, and grading for this one synthetic fixture execution. It does not validate the other generated cases or the full suite.

## 5. Real pilot evidence and independent Oracle

The three Builder-generated cases were selected from the immutable output by the corrected semantic selector. The original independent Builder validator PASS was rechecked before the pilot-only workflow reused the archived artifact. No new Builder production occurred.

| Builder case | Runner result | Independent business-behavior result | Interpretation |
|---|---|---|---|
| `WBT-CORE-02-SEARCH-MATCH` | BLOCKED: 33 model steps exceeded the Runner cap of 32; DSH itself completed in 170.134 seconds | `EXPECTED_VIOLATION_DETECTED` | Target report accurately identified the two search defects and preserved all read-only invariants. Overall contract remains FAIL because the Runner step budget was exceeded. |
| `WBT-CORE-06-STATUS-CYCLE` | BLOCKED: case timeout after 239.119 of 240 seconds; no final DSH response | `UNKNOWN` | Incomplete execution. No business-behavior verdict is justified. |
| `WBT-CORE-08-DELETE-CONFIRM` | `INVOCATION_OK` | PASS | Complete evidence and correct single deletion. |

Corrected offline Gold Oracle run: `44894303807`; adjudication artifact `14702569034`.

- Oracle contract verdicts: 1 PASS, 2 FAIL.
- Business-behavior verdicts: 1 PASS, 1 `EXPECTED_VIOLATION_DETECTED`, 1 `UNKNOWN`.
- The two contract FAIL results are attributable to the Runner model-step cap and the case timeout, not proof of Builder semantic failure or target-Skill business failure.
- The Oracle parser itself required correction: it previously over-extracted search probes from task titles, failed to parse three Chinese ordinal clauses inside one Builder list item, and classified incomplete state-cycle execution as business FAIL. These Oracle fixes are separate from Builder output changes and are covered by self-tests.

The pilot tranche is **not 3/3 PASS**. No retries or substitutions were performed.

## 6. Attribution and decision

### Benefits attributable to the Builder output

- 15 structured cases across two useful datasets.
- 42/42 applicable coverage items represented.
- 57 exact source references verified against a frozen input.
- Explicitly retained `needs_info` for the unsupported BR-09 request-failure branch rather than inventing a test or evidence.
- Three semantically distinct candidate cases could be selected from the Builder output without hand-authoring replacement cases.

### Costs and risks attributable to the Builder output

- Formal generation consumed 253,449 DSH tokens; USD billing is unknown.
- One confirmed grading-contract contradiction exists in `WBT-CORE-02-G2`.
- The suite remains `needs_info` due the BR-09-RF evidence gap.
- The 240-second state-cycle timeout has inadequate observed margin in this one run, but attribution remains inconclusive.

### Decision

The formal output has **strong structural and source-provenance quality, but is not yet fully quality-approved**. The independent validator PASS must not be interpreted as a semantic quality PASS. At least one direct Builder defect is confirmed. The suite-level `needs_info` is correctly preserved.

Do not repair the archived output in place or replace its cases. Any Builder repair experiment must be a separately authorized production run with a new immutable artifact and a fresh independent validation. The current evidence is sufficient to record the defect and cost, but not to claim a completed 3/3 pilot or a full-suite quality PASS.

## 7. Evidence links

- Builder production: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44889956698
- Corrected pilot resume: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44892669832
- Corrected offline Oracle adjudication: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44894303807
- PR #38: https://github.com/Kairos0922/evaluation-dataset-builder/pull/38
