# Builder expansion: marginal-value review

**Date:** 2026-11-21  
**Scope:** The 11 unexecuted cases in the immutable Evaluation Dataset Builder output from workflow run [44726278657](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44726278657), artifact `14624897819`.  
**Question:** Which additional real executions would produce useful evidence about the quality of Evaluation Dataset Builder, and are they worth their incremental cost?  
**Non-goal:** This review does not optimize or score the target `webapp-testing` Skill. Its behavior is only an observation channel for assessing the Builder-authored cases.

## 1. Decision summary

**Do not execute all 11 cases by default.** The 11 cases are not 11 equally valuable independent experiments. They contain overlap, and several mostly repeat behaviors already exercised by the three-case Pilot.

The recommended next tranche is six cases:

1. `WB-CORE-03` — description-field search
2. `WB-CORE-05` — single status filter and restore All
3. `WB-CORE-07` — accessible names across controls and dialog
4. `WB-CORE-13` — delete Cancel branch
5. `WB-CORE-10` — whitespace-only create rejection
6. `WB-CORE-09` — successful create, title trimming and default priority

This is a **candidate tranche, not an execution authorization**. It is recommended because it samples six materially different Builder-authored specification problems: a distinct search clause, a new business rule, semantic accessibility requirements, a non-destructive branch, rejected-write behavior, and successful creation. The order above is a value grouping; actual execution order must keep successful writes last: 03, 05, 07, 13, 10, 09.

The six case timeout ceilings sum to **1,200 seconds (20 minutes)**, versus **2,220 seconds (37 minutes)** for all 11. These are declared maximum case timeouts, not expected DSH wall-clock, token consumption, or USD costs. No reliable USD estimate is available from the archived traces.

## 2. What evidence already exists about Builder quality?

The formal Builder output already has substantial static evidence:

- One Builder-produced dataset with 14 unique cases.
- 57 coverage items: 45 applicable, 11 not applicable, and 1 needs_info.
- All 45 applicable items are tagged by candidate cases.
- 47 case-level source evidence references independently verified against the frozen source corpus.
- 18 source files with matching SHA-256 records.
- 28 unique quotations checked as exact source substrings.
- 14/14 cases have the required execution assertions, structured grading criteria, evidence requirements, and PASS/FAIL/UNKNOWN policy.
- The official independent Validator passed against this immutable output.

This proves structural validity, source traceability, and declared coverage consistency for this particular output. It does **not** prove that all cases are operationally executable, that their grading contracts are sufficient when consumed, or that the coverage is behaviorally discriminative.

The three real Pilot cases are `WB-CORE-02`, `WB-CORE-12`, and `WB-CORE-14`. They cover title case-insensitive search, a three-step status cycle, and confirmed deletion. The remaining 11 cases are all still `NOT_RUN`.

The Builder-authored `QUALITY-REVIEW.md` is a Builder self-review, not an independent semantic review. Its own unresolved `BR-09-RF` gap remains correctly marked `needs_info`; executing the 11 candidates cannot close that missing failure-injection contract.

## 3. What counts as a Builder benefit?

A real case execution contributes to Builder quality evidence only when it answers one or more of these questions:

1. **Specification sufficiency:** Can the case be executed from its generated instructions and declared public inputs without an operator inventing missing steps, targets, or expected values?
2. **Operational executability:** Do the preconditions, actions, allowed/forbidden behavior, and budgets form a coherent, executable contract?
3. **Grading sufficiency:** Does the generated grading contract identify the correct evidence and distinguish PASS, FAIL, and UNKNOWN without relying on the target Skill's self-report?
4. **Coverage value:** Does the case test a behavior or rule not already established by the completed Pilot, rather than merely repeating a familiar workflow?
5. **Evidence determinacy:** Can the required artifacts actually establish the generated assertions and final verdict?
6. **Cost proportionality:** Is the case's incremental Builder-quality evidence worth its observed DSH usage and elapsed time?

The following are **not** Builder benefits by themselves:

- The target Skill passes or fails.
- More target Skill defects are discovered.
- Runner or Oracle code gets more test coverage.
- More cases are executed or a higher case count is reported.

A target Skill failure can still provide Builder evidence if it reveals that a case is ambiguous, under-specified, impossible to grade, or otherwise poorly generated. Conversely, a target Skill PASS does not establish that the case is a good or discriminative evaluation item.

## 4. Case-by-case marginal-value matrix

The novelty column compares each case with the three completed Pilot cases. Coverage tags are a navigation aid, **not a quality score**: broad tags can hide meaningful differences between individual clauses, and tag counts must not be interpreted as weighted value.

| Case | Builder-specific question the run can answer | Marginal value beyond Pilot | Overlap / reason to defer | Declared timeout | Side-effect class | Priority |
|---|---|---|---|---:|---|---|
| WB-CORE-01 | Are initial-state instructions, source facts, and summary assertions sufficient and unambiguous? | Low–medium. Adds a dedicated baseline case and WF-INITIAL tag. | Initial state and summary are already observed as preconditions/evidence in the status-cycle and delete Pilots. Mostly a baseline repeat. | 180s | Read-only | Defer |
| WB-CORE-03 | Does the generated case isolate description-field matching, rather than merely repeat title matching? | Medium–high. Same BR-02 tag as WB-CORE-02, but a distinct clause and query that exists only in task description. | Shares search setup and summary checks with WB-CORE-02. Keep only because it tests a separate field-matching obligation. | 180s | Read-only | **Select** |
| WB-CORE-04 | Does the generated contract distinguish a genuine empty result from stale rows/loading state and preserve global summary? | Medium. Adds an explicit empty-state assertion. | WB-CORE-06 also includes an empty result in a combined search/filter sequence. Prefer the combined case only if composition is the priority; otherwise this is the cleaner atomic test. | 180s | Read-only | Defer |
| WB-CORE-05 | Are the status-filter branches and restoration to All specified and gradeable? | High. Introduces BR-03 / WF-FILTER, not exercised by the Pilot. | Some interaction mechanics overlap with search/filter cases, but the business rule is new. | 180s | Read-only | **Select** |
| WB-CORE-06 | Does the Builder specify composition of search and status filter, including empty and restored states? | Medium–high. Tests interaction composition beyond atomic search/filter behavior. | Depends on BR-02 and BR-03, so it is more informative after WB-CORE-03 and 05. It is a compound case and may be harder to attribute if it fails. | 240s | Read-only | Defer to follow-up |
| WB-CORE-07 | Are accessible roles/names specified concretely enough to execute and independently grade across controls and a dialog? | High. Adds BR-10 and semantic locator requirements. | WB-CORE-13 also checks dialog button names, but does not inventory the search, filter, create, delete, and status controls. | 180s | Open dialog, then Cancel; no intended mutation | **Select** |
| WB-CORE-08 | Does the case specify the visible-title-to-data-ID mapping and pre-action reconnaissance? | Low–medium. Adds a dedicated read-only reconnaissance case. | WB-CORE-12 already performed the same visible-title mapping before state changes. Limited marginal evidence after that Pilot. | 180s | Read-only | Defer |
| WB-CORE-09 | Are successful-create instructions and grading sufficient for trim, default Medium, initial Open, unique ID, and summary update? | High. First real successful-create case in the current Pilot set; tests several generated business-rule assertions in one bounded action. | Shares the create form with WB-CORE-11, but tests different defaults/normalization rules. Prefer one successful-create case first. | 240s | One successful create | **Select** |
| WB-CORE-10 | Does the generated negative case distinguish rejected invalid input from false success or hidden mutation? | High. Adds whitespace-only rejection and BR-09-IN, with an explicit no-new-task/no-summary-change contract. | Some input-validation overlap with WB-CORE-11's boundary behavior, but rejection and successful boundary acceptance are complementary outcomes. | 240s | One rejected create attempt; no intended state mutation | **Select** |
| WB-CORE-11 | Are 80-character boundary and explicit High-priority assertions sufficiently specified? | Medium–high. Adds a positive boundary case and explicit priority selection. | Shares successful-create setup with WB-CORE-09 and repeats BR-04/05/06. Defer until the simpler successful-create contract is shown to work. | 240s | One successful create | Defer |
| WB-CORE-13 | Does the generated Cancel branch prove dialog closure and absence of DELETE/state mutation, independently of the confirmed-delete path? | High. Adds WF-DELETE-CANCEL, the complementary branch to the already executed confirmed-delete case. | Same dialog family as WB-CORE-14, but the expected side effect is the opposite. This is meaningful branch coverage, not duplicate deletion. | 180s | Open dialog, then Cancel; zero DELETE allowed | **Select** |

### Interpretation

- `WB-CORE-03` is not redundant merely because its coverage tags match `WB-CORE-02`: the two cases test different clauses of BR-02. Tag novelty alone would incorrectly discard it.
- `WB-CORE-13` is not redundant with `WB-CORE-14`: Cancel and confirm-delete are mutually distinct side-effect contracts.
- `WB-CORE-06` has value, but should follow atomic search and filter cases. Otherwise a failure can be harder to attribute to the Builder's task decomposition, the target Skill, or the application.
- `WB-CORE-09` and `WB-CORE-11` should not both be first-line create trials. One validates normalization/default behavior; the other validates a length boundary and explicit priority. Run the second only if its extra boundary evidence is needed.
- `WB-CORE-01` and `WB-CORE-08` are valid cases, but the completed Pilot already contains much of their initial-state/reconnaissance evidence.

## 5. Recommended tranche and sequencing

### Recommended six

| Order | Case | Why it earns a place | Timeout ceiling |
|---:|---|---|---:|
| 1 | WB-CORE-03 | Distinct BR-02 description-match clause | 180s |
| 2 | WB-CORE-05 | New BR-03 filter behavior | 180s |
| 3 | WB-CORE-07 | New BR-10 accessible-name contract | 180s |
| 4 | WB-CORE-13 | Cancel/no-DELETE branch complementary to confirmed delete | 180s |
| 5 | WB-CORE-10 | Negative create validation and no-mutation evidence | 240s |
| 6 | WB-CORE-09 | First successful-create contract, including trim/defaults | 240s |
| | **Total ceiling** | | **1,200s / 20min** |

This sequence intentionally puts read-only cases first, dialog/cancel cases next, rejected writes next, and the successful create last. Execute one case at a time, inspect its trace and artifacts, and decide whether to continue only after the Builder-specific quality adjudication is complete.

### Why not all 11?

The remaining five cases are not worthless. They are deferred because their marginal evidence is less urgent after the selected tranche:

- WB-CORE-01: initial state is already present in completed Pilot evidence.
- WB-CORE-04: empty-state behavior is partly represented in WB-CORE-06; choose it instead if atomic empty-state diagnosis is more important than combined-filter composition.
- WB-CORE-06: useful composition test after WB-CORE-03 and 05.
- WB-CORE-08: reconnaissance overlaps the already executed WB-CORE-12 pre-action mapping.
- WB-CORE-11: a second successful-create case, adding boundary/High evidence after WB-CORE-09.

After the six-case tranche, decide whether WB-CORE-06, 04, or 11 addresses a concrete remaining Builder-quality question. Do not run deferred cases merely to reach 14/14.

## 6. Cost and return: what can and cannot be claimed

Archived Pilot aggregate Trace totals were:

- WB-CORE-02: 634,679
- WB-CORE-12: 680,321
- WB-CORE-14: 2,625,818

The median is 680,321, but the spread is large: WB-CORE-14 used about 3.9–4.1 times the other two. The previous 11-case rough scale of about 7.48 million aggregate Trace tokens is only a median multiplication, not a forecast. The 1.75-million per-case aggregate-token ceiling implies a 19.25-million theoretical ceiling for 11 cases, not an expected usage value. Neither figure is USD billing.

For the recommended six cases:

- Declared timeout ceilings sum to 20 minutes.
- Per-case aggregate-token ceiling is still 1.75 million; the theoretical six-case sum is 10.5 million, not a forecast.
- No reliable per-case token or USD estimate exists. The archived cases are not calibrated enough to convert timeout or aggregate Trace tokens into provider cost.
- Actual USD cost must be taken from the DeepSeek billing/export record and associated with each run.

**Return assessment:** The six-case tranche has a better qualitative evidence-to-cost profile than all 11 because it prioritizes previously untested Builder contract types and defers baseline repeats, compound cases, and a second create variant. This is a reasoned prioritization, not a measured ROI ratio. A numeric return-per-dollar claim would be fabricated without actual billing and case-level Builder-quality findings.

## 7. Mandatory Builder-specific adjudication after each run

Do not treat the target Skill's PASS/FAIL as the Builder verdict. For every executed case, add a separate adjudication with these fields:

| Field | Question |
|---|---|
| Input-to-case traceability | Does the case accurately represent its cited source rule/capability? |
| Instruction sufficiency | Could the task be executed without inventing a target, step, or expected value? |
| Contract consistency | Are allowed actions, forbidden side effects, action budget, steps, and expected behavior consistent? |
| Grading determinacy | Can the required evidence distinguish PASS, FAIL, and UNKNOWN? |
| Evidence attainability | Did the specified evidence exist and suffice, without relying solely on target self-report? |
| Incremental coverage | What distinct behavior does this case add beyond the completed Pilot and already-run tranche? |
| Execution overhead | Actual DSH wall-clock, steps, token categories, and provider USD charge. |
| Attribution | Is any issue caused by Builder output, target Skill behavior, fixture/application behavior, Runner, or Oracle? |

Allowed Builder-quality conclusions per case:

- `ADEQUATE_FOR_THIS_CASE`: no material case-generation defect observed for this execution.
- `BUILDER_DEFECT_FOUND`: a concrete case specification, evidence, coverage, or grading defect is attributable to Builder output.
- `INCONCLUSIVE`: execution or evidence limitations prevent a Builder-quality conclusion.

Do not call `ADEQUATE_FOR_THIS_CASE` proof of general Builder quality. A single execution per case does not establish repeatability or cross-domain generalization.

## 8. Stop and continuation rules

Stop before the next case if:

- the case is FAIL, BLOCKED, or UNKNOWN because its specification/evidence contract is defective or insufficient;
- required evidence is missing or inconsistent;
- any step/token/time budget is exceeded;
- a side effect occurs outside the case contract;
- actual cost is anomalous or billing cannot be reconciled;
- an issue is attributable to Runner/Oracle and could contaminate later Builder judgments.

If a target Skill behavior defect occurs but the case remains clear and independently gradable, record that as target-Skill evidence, not a Builder defect; continue only if the Builder-specific adjudication and cost check are satisfactory.

No automatic retry or model repair. Preserve the original Builder artifact and cases unchanged. If a Builder defect is found, report it against the relevant input/rule and Builder instruction. Do not hand-edit the formal case. Any corrected case must come from a separately authorized Builder production after the underlying input or instruction is corrected.

## 9. Current authorization and experiment boundary

- The 11 cases remain `NOT_RUN`.
- This review is a static analysis of the immutable Builder output; it made no DSH or model calls.
- The recommended six are not authorized for paid execution by this document.
- Do not rerun Builder production: the current immutable output already passed the independent Validator.
- PR #38 must remain Draft/Open and unmerged; do not add `run-builder-production`.
