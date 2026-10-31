# Changelog

## 0.0.1 — 2026-11-01
- Initial general-purpose Evaluation Dataset Builder Skill.
- Added quality standard, case schema, grader and coverage guidance.
- Added evidence/source governance and quality gates.
- Added self-evaluation and trigger-evaluation fixtures.
- Added structural validator and CI workflow.

### Known limitations
- Behavioral self-evaluation requires a compatible model runtime/harness and is not executed by structural CI.
- Dataset quality scores are rubric-based reviewer outputs unless a calibrated grader and evidence are supplied.
- Execution verification requires an external target-system harness.
