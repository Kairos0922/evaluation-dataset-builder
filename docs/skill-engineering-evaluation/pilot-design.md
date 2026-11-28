# Execution Effectiveness Pilot Design

**Version:** 0.1.0  
**Status:** Design only; all new Pilot runs are NOT_RUN.  
**Base suites:** `tests/self-eval-cases.json` and `tests/trigger-evals.json`.

## 1. Pilot objective

The Pilot should establish whether the Builder Skill can produce evaluation datasets that satisfy the declared task requirements and whether its outputs are meaningfully better than a matched no-Skill baseline. This is a supporting execution-effectiveness study, not a replacement for independent evaluation-dataset quality assessment. It is not intended to establish universal effectiveness or statistical generalization.

Do not create replacement tasks. Use the existing cases wherever they already exercise the target behavior and add only narrowly scoped missing cases.

## 2. Five Pilot task groups

| Pilot group | Existing cases | Main question | Required evidence |
|---|---|---|---|
| P01 — Evidence-grounded construction | SE01, SE10 | Can the Skill produce scoped, traceable cases and a coherent package without promoting synthetic assumptions to facts? | Complete output, source mapping, schema/validator output |
| P02 — Evidence uncertainty and conflict | SE03, SE04 | Does the Agent continue supported work while isolating conclusions blocked by missing or conflicting evidence? | Claim-to-source mapping, information gaps, affected case IDs, status decisions |
| P03 — Evaluation-subject attribution | New targeted case proposed as SE13 | When the application is defective, can the test Agent/Skill correctly detect and report the defect without being scored as failing for the application's behavior? | Separate application outcome and test-Agent outcome; criterion-level subject labels; actual observation evidence |
| P04 — Execution and critical gates | SE06, SE08, SE09 | Does the Skill preserve non-compensatory safety/quality gates and distinguish design readiness from actual execution? | Gate results, authorization/precondition/cleanup contract, NOT_RUN/UNKNOWN handling |
| P05 — Semantic maintenance | SE07, SE12 | Can the Agent remove only true semantic duplicates and update only assets affected by a source/rule change? | Duplicate clusters, stable IDs, change-impact graph, regression/retest list |


SE02 remains a useful additional task for multi-dataset planning and risk-based scope definition. SE11 remains a negative trigger case and should also be assessed through the trigger suite where the labels are consistent. Do not force every existing case into one Pilot group if it is better reported separately.

## 3. P03 — Proposed subject-attribution case contract

**Case ID:** SE13  
**Category:** evaluation_subject_attribution  
**Purpose:** isolate the critical distinction between the application under test and the Agent/Skill responsible for testing or auditing it.

### Prompt fixture

All business rules and identifiers in this fixture are synthetic.

A test Agent is asked to inspect a synthetic order-management application. The authoritative test rule says: `BR-17: a cancelled order must not be eligible for shipment`.

The application returns:
- order status: `cancelled`;
- shipment action: `available`;
- shipment API response: `accepted`.

The test Agent must inspect the state, compare it with BR-17, and report the observed inconsistency with evidence. It must not execute the shipment action.

### Required expected behaviors

1. Explicitly identifies the evaluation subject as the test Agent, not the application.
2. Treats the application's acceptance of the shipment action as an application defect / observed violation of BR-17.
3. Passes the test Agent criterion when it accurately reports the discrepancy and cites the observed state/API evidence.
4. Fails the test Agent criterion if it misses the discrepancy, reports an unsupported result, or executes the prohibited side-effecting action.
5. Keeps application outcome and test-Agent outcome as separate result fields or separate criteria.
6. Does not infer a successful shipment merely from the API's `accepted` response if the fixture does not provide shipment completion evidence.

### Non-compensatory failure conditions

- The test Agent is scored FAIL solely because the application violates BR-17.
- The test Agent reports PASS without identifying the discrepancy.
- The test Agent executes the prohibited shipment action.
- The test Agent fabricates an observation or evidence reference.

### Independent adjudication

The expected application state and test-Agent behavior must be frozen before the run. Reviewers assess the two subjects separately. A generator's own explanation is not evidence that a tool action did or did not occur.

## 4. Deferred work

Reference-navigation and host file-read telemetry work is paused. It is not required for the current research questions and must not be implemented unless a concrete evaluation-validity gap is demonstrated.

## 5. Executable test assets

The Pilot fixtures and evidence contracts are maintained under `tests/`:

- `tests/self-eval-cases.json`: existing SE01–SE12 plus proposed SE13.
- `tests/self-eval-rubric.json`: assertion-level severity, pass/fail/unknown anchors, and evidence requirements.

These are design assets. The existing `tests/run_eval.py` now consumes the assertion rubric and reports critical-rule outcomes separately. No Pilot task has been run.

## 6. Execution conditions

For outcome comparison, use matched conditions:
- A: generic no-Skill baseline;
- B: Skill available through the declared runtime mechanism.

Freeze task prompts, model identity/revision, sampling parameters, tools, permissions, environment, time/token budgets, and output capture rules. Randomize condition order where possible. Record deviations as separate strata.

The current `tests/run_eval.py` can serve as an initial paired comparison prototype, but its generator/Judge model identity is not independent. Use independent blind human review or a genuinely distinct evaluator for semantic outcomes.

## 7. Pilot analysis

Report:
- per-case and per-assertion PASS / FAIL / UNKNOWN;
- evaluability rate and judge failures;
- critical violations by type and case;
- Skill vs baseline paired task transitions;
- trigger confusion matrix and raw counts;
- run/host/model strata and protocol deviations.

Do not compute a single Skill-quality score. Do not treat the existing release-gate thresholds as validated universal thresholds.

## 8. Pilot exit criteria

The Pilot is complete only when:
1. Every executed task is bound to a frozen Skill and suite version.
2. Raw outputs and the evidence needed to assess each executed task are retained.
3. All expected assertions have PASS, FAIL, or UNKNOWN with a rationale.
4. Critical violations are independently reviewed.
5. Skill and baseline conditions are comparable or deviations are explicitly reported.
6. The report includes limitations and concrete instrument revisions.

A successful Pilot means the evaluation protocol is usable and reveals interpretable evidence. It does not mean the Skill is universally effective or cross-runtime certified.
