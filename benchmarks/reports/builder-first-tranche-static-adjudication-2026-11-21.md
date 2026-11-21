# First-tranche static Builder-quality adjudication

**Date:** 2026-11-21  
**Artifact reviewed:** Evaluation Dataset Builder output, workflow run `44726278657`, artifact `14624897819`  
**Cases reviewed:** `WB-CORE-03`, `WB-CORE-05`, `WB-CORE-07`  
**Review type:** Offline semantic/specification review only. No DSH, model, browser, or target-Skill execution was performed.  
**Evaluation object:** Evaluation Dataset Builder output quality. The target webapp-testing Skill is not being scored.

## 1. Decision

Do not automatically execute all first three cases as previously proposed.

- `WB-CORE-03`: **READY_FOR_TRIAL**, with one source-traceability check to retain in the adjudication.
- `WB-CORE-05`: **READY_FOR_TRIAL**.
- `WB-CORE-07`: **HOLD_FOR_COVERAGE_CONTRACT_REVIEW**. The case itself is a plausible accessibility-name test, but the Builder's coverage model compresses the source rule and does not explicitly represent all of its clauses.

This changes the first paid tranche from three cases to two until the coverage issue is resolved. The declared timeout ceiling for the two ready cases is 360 seconds (6 minutes), not a cost forecast. This is not an execution authorization.

## 2. Case-level findings

### WB-CORE-03 — Search description field

**Static assessment: READY_FOR_TRIAL**

Strengths:
- The case isolates a distinct BR-02 obligation: matching text in a task description when the query is absent from titles.
- The query, expected row, unchanged summary, one-script limit, zero-mutating-action budget, forbidden reset, and UNKNOWN conditions are explicit.
- Grading separates real interaction, result correctness, summary consistency, verdict consistency, and evidence completeness.
- The case is complementary to the completed title-search Pilot `WB-CORE-02`, rather than a simple duplicate.

Residual Builder-quality question:
- The claim that `token expiry` occurs only in the description of `Reset password flow` is a fixture-data premise. It appears in the generated `test_data.note` and user instruction, but the case's `source_refs` cite the business rule and general application overview, not a dedicated source locator for that exact fixture datum.
- Before judging the Builder, the adjudicator must confirm this premise against the runner-provided reset dataset and record that confirmation. Do not use target Skill success/failure to infer whether the premise was true.

Builder-specific value:
- Tests whether the Builder can turn one compound business rule into an atomic, discriminative case with a clear expected row and independently checkable evidence.

### WB-CORE-05 — Status filter and restore All

**Static assessment: READY_FOR_TRIAL**

Strengths:
- It tests BR-03, a business rule not exercised by the completed three-case Pilot.
- The expected In progress result is explicit: two named tasks, both with the expected status.
- The return to All statuses has a separately stated expected row count and initial title set.
- The case checks that global summary counts remain 5/2/2/1 across both filter states.
- It allows two filter changes within one script, defines a zero-mutation budget, prohibits retries/reset, and specifies UNKNOWN for missing or ambiguous evidence.
- The source rule and initial task-state table provide a clear basis for expected behavior.

Residual Builder-quality question:
- The grading contract should preserve the distinction between the filtered visible row set and the global summary. It already states this, so the adjudicator should verify both separately and not treat summary values as the filtered result count.

Builder-specific value:
- Tests whether the Builder generates a complete, multi-state read-only contract for a new business rule, including restoration to baseline and protection against stale/filtered summary confusion.

### WB-CORE-07 — Accessible names

**Static assessment: HOLD_FOR_COVERAGE_CONTRACT_REVIEW**

Strengths:
- It requires role/name-based inspection of search, filter, create, delete, and status controls.
- It explicitly opens the target row's delete dialog and cancels, with zero deletes and zero state changes.
- It requires a role/name inventory and evidence, rather than accepting the target Skill's self-report.
- It covers a behavior not directly exercised by the original three Pilot cases.

Builder-quality concern:
- Source rule BR-10 contains at least two distinct obligations:
  1. Interactive controls have understandable accessible names, and search/filter/create/delete operations can be located through labels or semantic roles.
  2. Status changes and operation results are presented through page text.
- The generated coverage matrix collapses BR-10 into one item, `BR-10: 可交互控件有可理解的可访问名称`, and says WB-CORE-07 covers it. That item omits the second source obligation.
- WB-CORE-07 itself is scoped to names and locators; it does not test whether status changes and operation results are presented through page text.
- Other cases may provide some relevant observations, but the coverage matrix does not decompose BR-10 into independently traceable obligations or explicitly map the page-text feedback obligation to the case(s) that verify it. Therefore the stated 100% business-rule coverage is not, by itself, sufficient evidence that the full BR-10 source rule is covered.

Additional specification weakness:
- The phrase “可理解的名称” is qualitative. The case gives exact expected names for Search tasks and Filter tasks by status, but for row-level Delete and Move to controls it relies on “non-empty/understandable” and “distinguish the operation” without defining how contextual row information is assessed. This may be acceptable if the adjudicator uses the accessible role/name plus row context, but that interpretation should be explicit before execution.

Required offline resolution:
- Split BR-10 into at least two coverage items, one for accessible names/semantic location and one for visible textual status/result feedback.
- Map the second item to a case that explicitly asserts the relevant feedback text, or add a separate Builder-generated case in a future authorized Builder production if existing cases do not cover it.
- Clarify the grading interpretation for row-level action names, without hand-editing the immutable formal case.

This is a **coverage-model defect/risk attributable to the Builder output**, not evidence that the target Skill has an accessibility defect. The formal output must remain unchanged; any correction requires a separately authorized Builder production after the source/Builder input is corrected.

## 3. Revised first-tranche decision

| Case | Static Builder-quality conclusion | Next action | Timeout ceiling |
|---|---|---|---:|
| WB-CORE-03 | READY_FOR_TRIAL | Verify the query phrase against reset fixture data, then consider one real run | 180s |
| WB-CORE-05 | READY_FOR_TRIAL | Consider one real run | 180s |
| WB-CORE-07 | HOLD_FOR_COVERAGE_CONTRACT_REVIEW | Resolve BR-10 coverage decomposition and name interpretation first | 180s |

The first two cases are the current preferred paid trial candidates. Their combined declared timeout ceiling is 6 minutes. This is not a token, wall-clock, or USD estimate.

## 4. Builder-specific adjudication protocol for these cases

For each actual run, record:

1. Source-to-case fidelity: does the generated case accurately encode the cited source obligation?
2. Specification sufficiency: are target, preconditions, steps, allowed actions, forbidden actions, and expected values explicit?
3. Contract consistency: do action budgets, timeout, steps, and end-state requirements agree?
4. Grading determinacy: can evidence distinguish PASS, FAIL, and UNKNOWN?
5. Evidence attainability: can the requested evidence be collected within the stated environment and permissions?
6. Incremental coverage: what new Builder-authored obligation does this case add beyond completed Pilots?
7. Actual cost: wall-clock, steps, token categories, and provider billing amount.

Use only these conclusions:
- `ADEQUATE_FOR_THIS_CASE`: no material Builder defect observed in this case execution.
- `BUILDER_DEFECT_FOUND`: a concrete case-generation or coverage defect is attributable to Builder output.
- `INCONCLUSIVE`: execution/evidence limitations prevent a Builder-quality conclusion.

The target Skill's PASS/FAIL is an observation, not the Builder verdict. A single run cannot prove general Builder quality, repeatability, or cross-domain generalization.

## 5. Authorization and experiment boundary

- All 11 additional cases remain `NOT_RUN`.
- This review used the downloaded immutable Builder artifact and repository source documents only.
- No paid DSH/model execution or real target-Skill trial was started.
- No new Builder production was started.
- Do not manually modify the formal Builder output.
- PR #38 remains Draft/Open and must not be merged or closed.
