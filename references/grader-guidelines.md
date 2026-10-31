# Grader Design Guidelines

Choose the grader based on the measured outcome:
- Deterministic/rule-based for exact labels, schemas, numeric values, and constraints.
- Reference-based when a trustworthy expected result exists.
- Rubric/LLM judge for open-ended outputs with multiple acceptable forms.
- State/end-result checks for agents that change files, call APIs, or alter environments.
- Trace/tool-call checks for process constraints and prohibited actions.
- Hybrid when outcomes have multiple facets.

Every grader defines criterion, observable evidence, pass/fail conditions, acceptable variants, partial-credit policy, UNKNOWN behavior, reference authority, and calibration method.

Prefer end-state checks over transcript claims for acting agents. Do not exact-match free-form text unless exactness is the target. Validate graders against positive, negative, borderline, and adversarial examples. For high-impact use, compare judge decisions with human-reviewed samples. Never treat unverified model-generated gold as authoritative.
