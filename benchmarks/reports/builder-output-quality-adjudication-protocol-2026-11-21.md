# Builder-output quality adjudication protocol

**Date:** 2026-11-21  
**Applies to:** the immutable Evaluation Dataset Builder output from workflow run [44726278657](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44726278657), artifact `14624897819`.  
**Purpose:** assess the quality of the cases produced by Evaluation Dataset Builder. This protocol does not score or improve the target `webapp-testing` Skill.  
**Execution status:** protocol only. It does not authorize or start DSH/model calls. The six-case tranche remains NOT_RUN unless a separately authorized run produces evidence.

## 1. Evaluation object and attribution boundary

The evaluation object is the Builder-authored evaluation case and its grading contract. The target Skill is only the consumer used to reveal whether the generated case is executable and gradeable.

Count a finding as Builder-quality evidence only when it is attributable to one or more generated artifacts or their source-to-case transformation:

- case intent, preconditions, task instructions, and permitted/forbidden actions;
- expected outcomes, assertions, and grading criteria;
- evidence requirements and PASS/FAIL/UNKNOWN policy;
- source references, rule mapping, and coverage claims;
- case decomposition, redundancy, or omission relative to the frozen input assets.

Do **not** count these as Builder benefits by themselves:

- target Skill PASS/FAIL rate or newly discovered target-Skill defects;
- Runner, fixture-server, CI, or Oracle implementation coverage;
- elapsed time, token usage, or number of completed runs without a quality finding;
- a successful execution where the generated case was too easy, redundant, or weakly discriminative.

A target Skill failure is not automatically a Builder defect. A target Skill PASS is not proof of Builder quality.

## 2. Unit of adjudication

Adjudicate each Builder-authored case individually, then produce a tranche-level synthesis.

For each case, preserve:
1. the exact immutable case ID and source artifact digest;
2. the generated case definition and grading contract as written, without repair;
3. the Runner result, Trace, audit log, pre/post state, and required snapshots;
4. the independent Gold Oracle result;
5. the adjudicator's Builder-specific findings and cited evidence;
6. measured DSH wall-clock, step count, token telemetry, and provider billing when available.

Never edit a generated case before adjudicating it. Any proposed repair must be recorded separately and must not be substituted into the tested artifact.

## 3. Builder-quality dimensions

Use the following dimensions as a structured review, not as a weighted score. Do not invent weights or pass-rate thresholds.

| Dimension | Adjudication question | Evidence to inspect | Builder-attributable defect examples |
|---|---|---|---|
| Source fidelity | Does the case accurately reflect the frozen input assets and cited business rules? | Source IDs, exact quotations, source hashes, rule references, case assertions | Unsupported requirement, misquoted rule, contradictory source interpretation |
| Specification sufficiency | Can an operator execute the case from the generated instructions and declared inputs without inventing missing details? | Preconditions, target selection, steps, input values, expected outcomes | Missing target, ambiguous action, unspecified expected value, hidden prerequisite |
| Contract coherence | Are allowed actions, forbidden actions, side-effect class, timeout, and budget mutually consistent? | Execution requirements, side-effect declarations, budget fields, task steps | Case requires a forbidden mutation, impossible sequence, incompatible timeout |
| Grading sufficiency | Does the generated rubric distinguish PASS, FAIL, and UNKNOWN using observable evidence rather than target self-report? | Assertions, grading criteria, evidence requirements, Oracle verdict and reason | PASS can be awarded without required evidence; failure condition is untestable; UNKNOWN conflated with PASS |
| Evidence determinacy | Can the declared evidence actually establish each important assertion? | DOM snapshots, server audit, pre/post state, trace metadata, manifest | Assertion has no evidence source; snapshot timing insufficient; evidence cannot distinguish competing outcomes |
| Coverage contribution | Does this case add a meaningful behavior/rule obligation not already adequately represented by the other cases and completed Pilot? | Frozen asset coverage map, case-to-rule mapping, Pilot evidence, case semantics | Duplicate case with no new clause or decision value; important source requirement omitted |
| Discriminative intent | Does the case test a meaningful distinction rather than merely a happy-path click sequence? | Positive/negative branches, boundary conditions, mutation/no-mutation assertions | Success can be claimed from superficial UI response; no observable distinction between correct and incorrect behavior |
| Cost proportionality | Is the incremental Builder-quality evidence justified by the measured execution cost? | Actual wall-clock, token telemetry, DeepSeek billing/export, findings above | High-cost case yields no new Builder-quality evidence and duplicates an already supported contract |

### Important evidence limitation

HTML/DOM snapshots in this experiment are artifacts produced by the target Skill and archived by Runner. They are not independently instrumented browser captures. Server-side audit and state evidence are independent of the Skill's self-report, but do not make the DOM snapshots independent. Do not claim stronger browser-evidence independence than the instrumentation provides.

## 4. Per-case adjudication outcome

Assign exactly one overall Builder-quality outcome per case:

- `ADEQUATE_FOR_THIS_CASE`: no material Builder-attributable defect was found in the dimensions that the case can meaningfully test, and the evidence is sufficient to support that limited conclusion.
- `BUILDER_DEFECT_FOUND`: at least one material defect is demonstrated in the generated case or grading contract. Record the exact defect, affected dimension, source/case evidence, and whether it invalidates execution or verdict.
- `INCONCLUSIVE`: available evidence cannot support either conclusion. This includes target/runtime failures that prevent examination of the generated contract, missing evidence, unresolved attribution, or insufficient instrumentation.

The target Skill's PASS/FAIL/UNKNOWN is recorded separately and must never be copied into the Builder-quality outcome.

For each dimension, use one of:
- `SUPPORTED`: evidence supports adequacy for this case;
- `DEFECT`: a concrete Builder-attributable defect is demonstrated;
- `NOT_EXERCISED`: this case does not test the dimension;
- `INCONCLUSIVE`: the evidence is insufficient.

Do not treat `NOT_EXERCISED` as a pass.

## 5. Attribution rules

Before recording a Builder defect, test these alternatives:

1. **Target behavior:** Did the generated contract remain clear and executable, with the target Skill simply failing to comply? If yes, this is target-Skill evidence, not a Builder defect.
2. **Environment or Runner:** Did infrastructure, fixture state, tool access, or orchestration prevent execution? If yes, record an execution limitation; do not attribute it to Builder without evidence that the generated contract caused it.
3. **Oracle defect:** Did the Oracle misinterpret an otherwise adequate generated contract? If yes, record an Oracle/benchmark defect separately.
4. **Builder contract defect:** Does the generated case omit, contradict, ambiguously state, or fail to require information necessary for execution or grading? Only then attribute the finding to Builder.
5. **Source limitation:** Is the relevant business rule absent or explicitly marked `needs_info` in the frozen inputs? Do not penalize Builder for inventing no unsupported requirement. Assess whether it correctly preserved the uncertainty.

A single observed failure may have multiple contributing causes. Record mixed attribution rather than forcing a single cause.

## 6. Case-specific adjudication focus for the recommended tranche

| Case | Builder-quality questions to answer | Required observations |
|---|---|---|
| WB-CORE-03 | Does the generated task isolate description-field matching from title matching? Are the query, target, and expected row set explicit? | Actual description-only match, non-match controls, rendered result, state unchanged |
| WB-CORE-05 | Are each status-filter branch and restoration to All specified and independently gradeable? | Filter values, expected visible rows, restoration, global summary/state invariants |
| WB-CORE-07 | Are roles and accessible names concrete enough to test without guessing? Does the case require adequate evidence for all listed controls? | Required open-dialog and post-Cancel snapshots, accessible names, dialog closure, target remains |
| WB-CORE-13 | Does the generated Cancel branch explicitly distinguish cancel from confirmation and prove zero deletion side effects? | Dialog open/closed evidence, target row retained, zero DELETE audit events, unchanged state |
| WB-CORE-10 | Does the generated negative case distinguish rejected whitespace-only input from hidden/false-success mutation? | Validation feedback, no created record, unchanged summary and server state, no create mutation |
| WB-CORE-09 | Are title trimming, default Medium priority, initial Open status, unique ID, and summary update all specified and gradeable? | Created record, exact normalized title, default priority/status, unique identity, summary consistency |

A case can be `ADEQUATE_FOR_THIS_CASE` even when the target Skill fails, provided the generated specification and grading contract are sound and the failure is reliably evidenced. Conversely, a target Skill PASS does not establish adequacy if the generated contract is ambiguous or weak.

## 7. Tranche-level synthesis

After each case, update a cumulative table with:

- case ID and target Skill result;
- Builder-quality outcome;
- dimensions supported, defective, not exercised, or inconclusive;
- material Builder defects and their evidence;
- new source obligations or behavior distinctions actually tested;
- overlap with completed Pilot and previously adjudicated tranche cases;
- measured elapsed time, model steps, input/output/cache/total tokens;
- provider-billed cost, or `UNKNOWN` if no billing record is available;
- continue/stop decision and rationale.

At tranche end, answer these Builder-specific questions:

1. Which generated requirements were actually executable as written?
2. Which generated grading contracts could be independently adjudicated with the available evidence?
3. Which material source requirements were omitted, misrepresented, or overclaimed?
4. Which cases added non-redundant coverage beyond the completed Pilot?
5. Which cases were too weak, ambiguous, redundant, or expensive relative to their Builder-quality evidence?
6. What specific changes to Builder generation rules or output schema are justified by observed defects?
7. What remains unknown because this is one Builder output, one application, one target Skill, and a small purposive case sample?

Do not aggregate the outcomes into a numeric Builder quality score or ROI ratio unless a validated measurement model and defensible weights/thresholds are established. Report counts by outcome and dimension, with denominators and limitations.

## 8. Cost and continuation policy

- No DSH/model execution is authorized by this protocol.
- If separately authorized, run one case at a time, in the selected order: WB-CORE-03, WB-CORE-05, WB-CORE-07, WB-CORE-13, WB-CORE-10, WB-CORE-09.
- After each case, inspect evidence and adjudicate Builder quality before starting the next.
- Stop on BLOCKED, target result FAIL/UNKNOWN, missing or inconsistent evidence, budget exceedance, secret exposure, provenance/integrity issue, or side effect outside the case contract. A stop does not itself imply a Builder defect.
- Do not automatically retry, repair the case, or continue to the next paid case after a stop condition.
- Capture actual provider billing/export data. Trace token totals and declared timeout ceilings are not USD cost estimates.
- Continue to the next case only if the current case yielded usable evidence and the expected marginal Builder-quality information remains worth the measured incremental cost.
- Deferred cases WB-CORE-01, 04, 06, 08, and 11 remain deferred unless the tranche review identifies a specific unresolved Builder-quality question they can answer.

## 9. Scope and claims

This protocol supports conclusions only about the inspected immutable Builder output and the cases actually adjudicated. It does not establish Builder generalization across domains, repeatability across independent Builder runs, or statistical representativeness of all Agent/Skill evaluation tasks.

A stronger Builder capability study would require additional independent Builder generations from materially different input assets, followed by the same independent validation and adjudication protocol. That is a separate experiment and requires its own cost/benefit decision.
