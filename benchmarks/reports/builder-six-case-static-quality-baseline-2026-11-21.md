# Static Builder-quality baseline: recommended six-case tranche

**Date:** 2026-11-21  
**Builder artifact:** workflow run [44726278657](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44726278657), artifact `14624897819`  
**Artifact inspected:** `webapp-testing-builder-output/wb-core.jsonl` extracted from the downloaded immutable ZIP.  
**SHA-256:** `0a1f549af5adbb790b134e7b740750b58b86845583acb7bea4e21131753271c1`  
**Scope:** static review of six selected Builder-authored cases only. No DSH/model calls or Skill execution.

## 1. Review approach

For each case, inspect source-rule references, objective, preconditions, user instructions, expected behavior, grading criteria, required evidence, uncertainty policy, execution budget, side-effect constraints, and observable assertions. Compare overlap against completed Pilot cases WB-CORE-02, WB-CORE-12, and WB-CORE-14.

The outcomes below are provisional static baseline labels, not final adjudication. Execution may reveal issues not visible in the artifacts.

## 2. Case baseline

| Case | Baseline outcome | Dimensions supported by static review | Not exercised / limitations | Findings |
|---|---|---|---|---|
| WB-CORE-03 | ADEQUATE_FOR_THIS_CASE (provisional) | Source fidelity; specification sufficiency; grading sufficiency; evidence requirements; incremental coverage | Evidence attainability and actual executability; snapshots are target-produced, not independent | Query `token expiry` is explicitly stated to occur only in WB-101's description; expected sole row, summary invariance, zero mutations and one script run are clear. Separate clause from title-search Pilot. |
| WB-CORE-05 | ADEQUATE_FOR_THIS_CASE (provisional) | Source fidelity; specification sufficiency; grading sufficiency; evidence requirements; incremental coverage | Actual filter semantics, request completion, evidence attainability | Explicit filter value, expected two rows, restore All=5 and summary invariance. Single-script sequence is coherent. |
| WB-CORE-07 | ADEQUATE_FOR_THIS_CASE (provisional, with a minor precision note) | Source fidelity; specification sufficiency; grading sufficiency; evidence requirements; incremental coverage | Actual accessibility tree and names; evidence attainability | Inventory of search, filter, Create, per-row Delete/status controls and dialog is explicit; opens dialog then Cancel. Clarify that row-scoped locators are needed for repeated Delete/Move buttons and that “non-empty understandable name” requires a defined review criterion. |
| WB-CORE-13 | ADEQUATE_FOR_THIS_CASE (provisional) | Source fidelity; specification sufficiency; contract coherence; grading sufficiency; evidence requirements; incremental coverage | Actual no-DELETE proof and evidence attainability | Cancel branch complements Pilot confirmation deletion; explicit zero DELETE, unchanged row count/summary, one Cancel, no retries. |
| WB-CORE-10 | ADEQUATE_FOR_THIS_CASE (provisional, with a contract precision note) | Source fidelity; specification sufficiency; contract coherence; grading sufficiency; evidence requirements; incremental coverage | Actual server rejection, UI error state and no mutation; evidence attainability | Whitespace-only input, one submission, no new task and summary unchanged are clear. It expects “understandable error” and error-state marker but does not operationally define the acceptable error text/marker; should be adjudicated for whether the generated evidence contract is sufficiently determinate. |
| WB-CORE-09 | ADEQUATE_FOR_THIS_CASE (provisional) | Source fidelity; specification sufficiency; contract coherence; grading sufficiency; evidence requirements; incremental coverage | Actual creation, generated ID, summary consistency and evidence attainability | Single successful create; trim, default Medium, Open, unique ID and summary update assertions are explicit; one attempt and no retries. |

**Important:** `ADEQUATE_FOR_THIS_CASE` at this stage means static inspection found no material defect that invalidates the case's intended contract. It is not an execution result and does not prove behavior, evidence attainability, reliability, or Builder generalization.

## 3. Static findings that matter for Builder

### No material defect identified in the six selected case definitions

All six include a source rule reference and quotation, task objective, independent initial-state precondition, bounded action/script budget, expected behavior, observable assertions, explicit forbidden actions, and a PASS/FAIL/UNKNOWN uncertainty policy. They contain concrete values and target identifiers rather than generic instructions.

This is useful evidence about the Builder output's specification structure. It remains limited to these six cases and their frozen source assets.

### Precision issues to examine during adjudication

1. **WB-CORE-07 — semantic-name criteria:** The case requires “non-empty, understandable” accessible names for repeated row-level controls. The contract provides examples and requires role/name enumeration, but a human semantic assessment of “understandable” is not fully operationalized. Record whether the generated criterion is still independently judgeable with its listed evidence.
2. **WB-CORE-10 — error quality:** The criterion requires an understandable error and error-state marker, but it does not prescribe a specific acceptable message or machine-observable error-state contract. This may be intentional flexibility; adjudication should decide whether it permits reliable independent judgment or creates ambiguity. Do not repair the generated case before evaluation.
3. **Evidence independence:** For all six cases, screenshots and DOM/snapshot artifacts produced by the target Skill are not independent browser instrumentation. Independent server audit and state evidence may corroborate relevant claims, but must not be treated as proving every UI assertion. This is an experiment evidence limitation, not automatically a Builder defect.

No finding above is classified as `BUILDER_DEFECT_FOUND` at static review. The precision notes are risks to investigate, not confirmed defects.

## 4. Baseline coverage beyond the completed Pilot

The selected six add distinct obligations beyond the three executed cases:

- description-field matching (WB-CORE-03) beyond title matching;
- status filter branches and restoration (WB-CORE-05);
- accessible names across control inventory (WB-CORE-07);
- cancel-delete branch with zero deletion side effects (WB-CORE-13);
- invalid whitespace-only create rejection (WB-CORE-10);
- successful create normalization/defaults (WB-CORE-09).

The static review therefore supports the selection rationale: the tranche is not six arbitrary extra runs. It tests six different generated contract types. Whether these contracts are operationally executable and whether evidence can support their verdicts remains untested.

## 5. Cost decision update

Static inspection found no obvious case-definition defect that makes a selected case unnecessary to execute. This increases the expected value of a first real run because it is less likely that execution spend merely reveals a defect already visible by reading the artifact.

It does **not** justify paying for all six automatically. Continue sequentially and reassess after each case:

- Record the target Skill outcome separately.
- Complete the Builder-specific adjudication using the protocol.
- Record measured time, step/Token telemetry and provider billing when available.
- Stop if the case is blocked, evidence is incomplete/inconsistent, attribution is contaminated, a budget limit is reached, or a side effect violates the contract.
- Continue only when the case yields usable Builder-quality evidence and the remaining expected information is still worth the marginal cost.


## 7. Source quote cross-check

The frozen Builder input artifact `14623409443` was downloaded and inspected. For the six selected cases, every source path resolved within that input artifact and every `quoted_evidence` string was found as an exact substring in its referenced source file: **19/19 source quote checks PASS**.

| Case | Referenced sources | Path resolution | Exact quote checks |
|---|---:|---|---:|
| WB-CORE-03 | 2 | PASS | 2/2 |
| WB-CORE-05 | 2 | PASS | 2/2 |
| WB-CORE-07 | 3 | PASS | 3/3 |
| WB-CORE-13 | 3 | PASS | 3/3 |
| WB-CORE-10 | 4 | PASS | 4/4 |
| WB-CORE-09 | 5 | PASS | 5/5 |
| **Total** | **19** | **PASS** | **19/19** |

This cross-check confirms the quoted source passages for these six cases are present in the frozen input files. It does not independently establish that Builder interpreted the passages correctly or that the cases' assertions are behaviorally complete.

## 8. Recommendation

Static baseline review supports the six-case tranche as a defensible candidate, with no confirmed Builder defect found in the generated definitions. It specifically flags WB-CORE-07's subjective accessibility-name criterion and WB-CORE-10's error-message determinacy for focused review during actual evidence adjudication.

This document is a baseline review only. The six cases remain `NOT_RUN`; no execution authorization is implied.


## 9. Repository verification refresh (2026-11-21)

- PR #38 head verified as `67c1ffd36f2cf73c90fdf985a80cc48073f8bfac`, Draft/Open, unmerged.
- Exact-head workflow run [#44885094352](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44885094352) completed successfully: `require-main-target`, `validate` (formal package validation, benchmark validation, offline tests, Gold Oracle/validator self-tests, source-evidence smoke checks, pilot selector tests), and `audit-upstream-assets` all PASS.
- Paid/runtime jobs (`runtime-preflight`, Builder production, independent validation, pilot execution, Oracle adjudication) were skipped as intended. This is CI evidence only, not new Builder or Skill execution evidence.
- Next action remains one real WB-CORE-03 run, contingent on explicit user authorization for the paid DSH/model execution. No such execution was started in this refresh.
