# Changelog

## 1.0.0 — 2026-11-02
- Promoted the general-purpose Evaluation Dataset Builder Skill to its first 1.0 release.
- Added model-aware request planning with live metadata discovery, combined input/output budgeting, configurable headroom, and no arbitrary small fixed caps.
- Added DeepSeek V4.1 Flash API profile with the verified `deepseek-flash` model ID, 1M context window, and 384K maximum output.
- Added a metadata-only DeepSeek preflight script that does not send generation requests.
- Added offline tests for metadata parsing, API preflight shape, large request budgets, output ceilings, and no-silent-truncation behavior.
- Added bounded error classification, ambiguous-timeout handling, and cursor-based recovery for partial structured output.
- Expanded self-evaluation fixtures to cover large-context requests, output budgeting, retries, partial output, and preflight.

### Release boundary
This release adds deterministic policy and preflight tooling. It does not claim that a live DeepSeek generation benchmark or independent expert review was executed in this repository environment.

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
