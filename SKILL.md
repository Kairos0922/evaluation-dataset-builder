---
name: evaluation-dataset-builder
description: Plan, generate, validate, repair, and package high-quality evaluation datasets for agents, skills, models, APIs, workflows, and other systems. Use when users need eval cases, benchmarks, graders, coverage plans, or quality audits.
---

# Evaluation Dataset Builder

Build evaluation assets that are business-grounded, capability-aligned, representative, measurable, executable when applicable, traceable, and maintainable. Do not optimize for case count alone.

## Rules
- Use user materials as evidence; never invent business rules, reference outcomes, or execution evidence.
- Separate facts, inferences, assumptions, conflicts, and unresolved questions.
- Support multiple purpose-specific datasets in one request.
- Read references/quality-standard.md and references/quality-standard.yaml before generation or audit.
- Use references/dataset-schema.json for the case contract and references/grader-guidelines.md for grader design.
- Read references/request-planning-and-recovery.md before any large or paid model-generation task.
- When using DeepSeek V4.1 Flash, also read references/deepseek-v4.1-flash.md and run scripts/deepseek_model_preflight.py when credentials are available.
- Validate case-level and dataset-level quality separately. Critical failures cannot be averaged away.
- If information is incomplete, proceed with safe defaults, record assumptions, and mark affected cases needs_info.
- Never claim execution verification unless a harness ran the case and recorded evidence.
- Never promise that an external model request is guaranteed to succeed; preflight, budget, and recovery reduce avoidable failures but cannot control provider availability.

## Workflow
1. Parse target, evaluation objectives, capabilities, rules, scenarios, historical cases, environment, constraints, and output requirements.
2. Build a knowledge model containing targets, capabilities, rules, scenarios, risks, constraints, source references, assumptions, and conflicts.
3. Plan datasets before cases. For each dataset define purpose, target capabilities, scope, exclusions, coverage dimensions, size/distribution, grader approach, execution needs, and relation to other datasets.
4. Create a coverage matrix. Prioritize business importance, risk, frequency, known failures, capability gaps, and diagnostic value. Do not blindly generate Cartesian products.
5. Before generation, preflight the complete request and allocate input/output budgets from live model metadata where available. Include instructions, history, schemas, tools, evidence, multimodal payloads, visible output, and reasoning tokens where applicable. Do not apply arbitrary fixed small caps; split only when the estimated complete request cannot fit the actual provider limits.
6. Generate cases with measurable objectives, credible or labeled synthetic scenarios, complete inputs/preconditions, explicit expected and forbidden behavior, observable grading evidence, and provenance. Allocate enough output budget for the complete requested artifact plus a configurable estimation margin.
7. Design graders alongside cases. Choose deterministic, reference, rubric/LLM, state/end-result, trace/tool-call, or hybrid grading based on the outcome measured.
8. Review cases and datasets against the quality standard. Prefer local deterministic validation for structure and avoid an unnecessary second model call; use a semantic judge call only when required by the evaluation purpose.
9. Repair defects and rerun affected checks. For partial generation, persist valid records and continue from the first missing stable ID/cursor instead of regenerating successful work. Classify API errors and retry only confirmed transient failures within a bounded policy.
10. Package datasets, manifest, coverage matrix, graders, quality reports, source map, assumptions/limitations, and version history.

## Evidence precedence
1. Authoritative policy, business rule, or safety requirement.
2. Current product/system/API documentation.
3. Confirmed process or expert-approved behavior.
4. Capability and interface specification.
5. Verified historical evaluation outcomes.
6. Incidents, tickets, and user feedback.
7. Traces/logs as evidence of observed behavior, not correctness.
8. Explicitly labeled inference or synthetic assumptions.

If authoritative sources conflict, preserve the conflict and do not assert a gold outcome for affected cases. A ticket shows a reported issue, not necessarily the correct resolution. A trace shows what happened, not what should happen.

## Grader requirements
Every grader defines criteria, evidence, pass/fail conditions, acceptable variants, uncertainty handling, reference source, and calibration method. Use UNKNOWN when evidence is insufficient. For agents that act, inspect end state and side effects, not transcript claims alone. Do not treat unverified model-generated answers as gold.

## Quality status
- candidate: generated, not validated
- validated: passed applicable checks
- approved: passed all required gates for intended use
- needs_info: authoritative information missing/conflicting
- rejected: invalid, unsafe, unmeasurable, or irreparable
- execution_verified: actually run with recorded evidence

Approved does not imply execution_verified.

## Output requirements
Report purpose, dataset plan, coverage choices/gaps, per-dimension quality, gate failures, provenance, assumptions, limitations, and versions. Distinguish measured results from reviewer judgments. Never claim execution, expert review, or statistical confidence without evidence.

## References
- references/quality-standard.md
- references/quality-standard.yaml
- references/dataset-schema.json
- references/grader-guidelines.md
- references/coverage-design-guideline.md
- references/source-and-evidence-policy.md
- references/request-planning-and-recovery.md
- references/deepseek-v4.1-flash.md
- scripts/deepseek_model_preflight.py
- tests/self-eval-cases.json
