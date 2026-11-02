---
name: evaluation-dataset-builder
description: Plan, generate, validate, repair, and package evidence-grounded evaluation datasets for agents, skills, models, APIs, and workflows. Use for evaluation cases, benchmarks, graders, coverage plans, and quality audits.
---

# Evaluation Dataset Builder

Build business-grounded, capability-aligned, representative, measurable, executable (where applicable), traceable, maintainable datasets. More cases do not mean higher quality.

## Non-negotiable rules
- Before large or paid DeepSeek generation, read `references/request-planning-and-recovery.md` and `references/deepseek-v4.1-flash.md`; run `scripts/deepseek_model_preflight.py` when credentials are available. Metadata preflight uses `GET /models` and does not submit a generation request.
- Budget the complete request (system instructions, history, schemas, tools, sources, expected output, and reasoning where applicable) against live provider limits. Do not impose arbitrary small fixed caps or silently truncate.
- Never invent business rules, gold outcomes, source identities/versions, or execution evidence.
- Distinguish facts, inferences, assumptions, synthetic examples, reported conflicts, and unknowns.
- Check case and dataset quality separately. Critical failures cannot be averaged away.
- Missing evidence blocks only dependent outcomes; continue supported independent work.
- A plan is not an executed test; a draft is not validated or approved.

## Workflow
1. **Intake:** identify target, objectives, capabilities, rules, scenarios, risks, data, environment, permissions, constraints, and deliverable. List knowns and gaps.
2. **Knowledge model:** map capabilities, rules, scenarios, risks, source IDs/versions, assumptions, conflicts, and confidence.
3. **Plan:** define each dataset's purpose, scope/exclusions, audience, coverage universe, distribution, grader, execution needs, and overlap.
4. **Coverage:** build a matrix before cases; prioritize impact, risk, frequency, known failures, capability gaps, and diagnostic value. Avoid blind Cartesian products; report covered/total and gaps.
5. **Cases:** use stable IDs; include target, objective, scenario, preconditions, inputs, expected/forbidden behavior, grader/evidence, sources, assumptions, risk, and status.
6. **Graders:** choose deterministic, trusted-reference, rubric/LLM, state/end-result, trace/tool-call, human, or hybrid methods to match the outcome.
7. **Review/repair:** check case and dataset gates, duplicates, and execution readiness. Give actionable repairs, rerun affected checks, and package cases, manifest, graders, quality report, source map, limits, and versions.

## Missing evidence: continue safely
Split work into supported cases, blocked outcomes, and reusable scaffolding.
- Generate cases supported by supplied contracts, schemas, or authoritative rules.
- Mark only dependent outcomes `needs_info` or `UNKNOWN`; name the missing source, owner, and exact question.
- Label scaffolding `SYNTHETIC` with `ILLUSTRATIVE_ONLY` outcomes. It is not business gold and cannot be production-approved.
Never guess expected results. Continue unaffected work; do not stop the whole task because one source is missing.

## Conflict handling: record, do not hand-wave
For each conflict record ID; source title/ID, version/date, exact clause (or `NOT PROVIDED`); authority/scope; competing interpretations; affected cases/capabilities; resolution owner; status; downstream action.
- Without source artifacts, call it a **reported but unverified conflict** and set identity/version/clause to `NOT PROVIDED`; invent nothing.
- Do not choose by recency/version unless precedence is explicitly governed.
- Mark affected gold `needs_info` / `NOT APPROVED`; unaffected cases may proceed.

## Deduplication and coverage
Cluster by intent, capability, preconditions, action, and expected outcome—not wording alone. Report cluster, member IDs, representative, merge rationale, and retained boundary/risk variants. Keep distinct cases when permission, risk, state, tools, policy outcome, or failure mode differs. Without a candidate corpus, disclose that the real audit is pending; label demo clusters synthetic. Never inflate counts with paraphrases.

## Grader contract
Each grader defines criterion, method, required evidence, pass/fail, acceptable variants, failure conditions, `UNKNOWN` handling, reference authority/version, and calibration.
- Use deterministic checks for schemas/constraints/numbers; trusted references only when gold exists; rubric/LLM for open-ended answers; state checks for side effects; trace checks for tool/process constraints.
- For acting agents inspect actual end state and side effects—not transcript claims.
- Calibrate on positive, negative, borderline, and adversarial cases. Missing, malformed, ambiguous, or unverified evidence must fail closed or return `UNKNOWN`, never pass.

## Quality gates and repair plan
Case gates: evidence fidelity, objective alignment, expected behavior, grader validity, safety, feasibility, integrity. Dataset gates: objective/capability/scenario/risk coverage, duplicates, grader calibration, execution readiness, provenance, held-out independence.
For each failure give evidence, impact, exact repair, accountable role, affected IDs, retest scope/gates, required proof, and status (`BLOCKED`, `READY_FOR_RETEST`, `VERIFIED`). Only retest evidence permits `VERIFIED`. Aggregate scores never override critical failures.

## Execution readiness and side effects
For tool/API/agent cases specify initial state/preconditions; identity/permissions; data/dependencies; sandbox/tenant and allowed actions; ordered inputs/steps; expected end state/assertions; forbidden side effects; reset/rollback; cleanup/teardown; failure cleanup and cost limits.
Set `DESIGN_ONLY`, `READY_TO_RUN`, or `EXECUTION_VERIFIED`. Without a real environment state `NOT RUN`; never invent run IDs, traces, or success evidence.

## Incremental updates and version changes
Record old/new source version, effective date, exact change, impacted capabilities/scenarios/case IDs, and rationale. Preserve unaffected cases and stable IDs; update only impacted cases/gold supported by the new authority. List gates to rerun (provenance, validity, grader calibration, behavior/regression, risk, trigger, coverage). Record command/run ID, SHA, result, evidence. Anything not run is `RERUN_REQUIRED`, never passed.

## Evidence precedence
1. Authoritative policy/business/safety rule.
2. Current product/system/API documentation.
3. Confirmed expert-approved process.
4. Capability/interface specification.
5. Verified historical evaluation.
6. Incident tickets/user feedback (reports, not proof).
7. Traces/logs (observed behavior, not correctness).
8. Explicit inference/synthetic assumption.
Preserve unresolved authoritative conflicts. A trace shows what happened, not what should happen.

## Output contract
Report target/objective and gaps; plan/coverage (`coverage_universe`, covered/total counts by dimension, risk and gaps); cases/dedup (stable IDs, preconditions/input, expected/forbidden behavior, clusters/variants); graders (method, pass/fail conditions, evidence, UNKNOWN, calibration); repairs (defect, fix, owner, retest, proof); execution (state, permissions, steps, assertions, sandbox/reset/cleanup/status); changes/JSONL (versions, impacted/preserved IDs, manifest, source/quality maps); conflict register; provenance, limits, and change log.

## Output completeness
For JSONL emit one complete JSON object per line, schema-compliant; provide manifest and quality report separately. Manifest: purpose, target, version, case_count, coverage_universe, covered/total counts by dimension, gaps, grader/source refs, assumptions, status. Checklist every requested artifact: plan/coverage, cases/dedup, repairs, graders, execution, changes/JSONL. **Final completeness pass:** map every requested deliverable to a file/section; verify requested counts and schema; no placeholders or claims that unrun checks passed. Never invent facts or results; mark only blocked outcomes `needs_info`.

## Quality status
- `candidate`: generated, not validated
- `validated`: passed applicable checks
- `approved`: all required gates passed for intended use
- `needs_info`: authority missing/conflicting
- `rejected`: invalid, unsafe, unmeasurable, irreparable
- `execution_verified`: actually run with evidence
`approved` does not imply `execution_verified`.

## References
- `references/request-planning-and-recovery.md`
- `references/deepseek-v4.1-flash.md`
- `scripts/deepseek_model_preflight.py`
- `references/quality-standard.md`
- `references/quality-standard.yaml`
- `references/dataset-schema.json`
- `references/grader-guidelines.md`
- `references/coverage-design-guideline.md`
- `references/source-and-evidence-policy.md`
