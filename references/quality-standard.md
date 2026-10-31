# High-Quality Evaluation Dataset Standard

Version: 1.0.0 (initial operational baseline)

## Purpose
A high-quality dataset is fit for a stated evaluation purpose, grounded in credible evidence, representative of important scenarios, measurable with reliable graders, and maintainable. Case count alone is not quality.

## Dimensions (1–5, evidence-backed)
1. business_fidelity: grounded in real objectives, authoritative rules, or explicitly labeled synthetic scenarios.
2. capability_alignment: measures the intended capability, not incidental knowledge.
3. scenario_coverage: covers important workflows, variants, boundaries, and task types.
4. risk_coverage: covers relevant failures, safety, privacy, permissions, abuse, and high-impact cases.
5. case_validity: coherent, complete, feasible, and sufficiently unambiguous.
6. grader_reliability: explicit, evidence-based, stable pass/fail criteria.
7. diagnostic_power: identifies capability/requirement failures and distinguishes performance levels.
8. case_uniqueness: avoids semantic duplicates and template-only variations.
9. traceability_maintainability: sources, assumptions, versions, and update rationale are recorded.

Score anchors: 1 invalid; 2 weak; 3 adequate with caveats; 4 good; 5 excellent. Use not_assessed when evidence is insufficient.

## Case-level critical gates
G1 Evidence/fidelity: no unsupported or conflicting expected behavior.
G2 Objective alignment: measures declared objective.
G3 Expected behavior: explicit and judgeable.
G4 Grader validity: defensible criteria and observable evidence.
G5 Safety/compliance: no policy/privacy/compliance violation.
G6 Feasibility: required state, tools, data, permissions, and environment are available or specified.
G7 Integrity: no severe duplication, fabricated provenance, or misleading labels.

## Dataset-level critical gates
- Objectives and required capabilities have planned coverage.
- Required critical risks are covered.
- Dataset is not dominated by near-duplicates.
- Graders are validated for intended use.
- Coverage claims map to a declared coverage universe.
- Intended use is compatible with evidence and independence.

## Scoring and disposition
quality_score = sum((dimension_score / 5) * dimension_weight). Weights sum to 100 and are reported.
A/Approved: all critical gates pass, score >= 4.5, required coverage thresholds met.
B/Usable: all critical gates pass, score >= 3.8, caveats documented.
C/Needs Improvement: no disqualifying integrity/safety issue, but score or coverage is insufficient.
Rejected: unresolved critical gate failure or materially invalid dataset.
Composite scores never override critical gates.

## Grader quality
Define criterion, evidence, pass/fail conditions, acceptable variants, UNKNOWN handling, reference source, and calibration. Prefer deterministic checks for constrained outputs; state/end-result checks for acting agents; rubric judging for open-ended outputs. Validate graders against positive, negative, borderline, and adversarial cases. Model-generated gold must be labeled and independently checked.

## Dataset-level review
Check objective/capability/scenario/risk coverage, complexity distribution, source distribution, semantic duplicates, grader calibration, execution readiness, held-out independence, provenance, and maintenance plan.

## Governance
- Remove secrets and unnecessary personal data; label synthetic vs real-derived data.
- Separate development/tuning and held-out evaluation data where decisions depend on results.
- For side-effecting tasks define sandbox, reset, cleanup, allowed actions, and cost limits.
- Record standard, schema, builder, source, target, and dataset versions.
- Use independent review, repair, and revalidation. Unresolved cases are needs_info or rejected.
- Report dimension scores, gates, coverage numerator/denominator, duplicate analysis, grader validation, provenance, assumptions, limitations, and intended-use restrictions.
