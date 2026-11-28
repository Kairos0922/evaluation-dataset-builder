# Evaluation Dataset Quality & Execution Effectiveness Research

**Status:** Research support for the v0.0.2 evaluation methodology; proposed instruments are not empirically validated.
**Target:** Evaluation datasets produced by the Builder, and their ability to measure real Agent/Skill execution.
**Scope rule:** Every artifact in this branch must improve either (1) our ability to judge evaluation-dataset quality or (2) our ability to judge the effectiveness of those datasets in real execution. Work that does neither is out of scope.

## 1. Research questions

1. **Dataset quality:** Can the quality-assessment method identify meaningful defects in generated evaluation datasets, distinguish their severity, and avoid false alarms on harmless changes?
2. **Evaluation effectiveness:** Do datasets judged to be higher quality produce more valid, discriminative, and stable assessments of real Agent/Skill execution?

The two questions must remain separate. A structurally valid dataset is not necessarily semantically valid; a semantically plausible dataset is not necessarily effective when used in real runs.

## 2. Reuse the existing v0.0.2 foundation

Do not create a parallel quality model or duplicate metric system. The authoritative starting points are:

- `docs/quality-assessment-v0.0.2/metric-catalog.md`: candidate IDA/ERA metrics, definitions, denominators, and evidence requirements.
- `docs/quality-assessment-v0.0.2/experimental-design.md`: content review, controlled defect injection, real-run criterion validation, and frozen validation.
- `docs/quality-assessment-v0.0.2/expert-review-protocol.md`: independent review, raw ratings, disagreement, and adjudication.
- `tests/benchmark/`: offline structural/referential validation and controlled empirical benchmark contracts.
- `tests/run_eval.py` and the existing self-evaluation suite: a reusable execution-comparison harness, subject to the limitations below.

Reuse these assets before adding anything. A new metric, schema, runner, or abstraction requires a demonstrated gap in answering one of the two research questions.

## 3. What this branch contributes

- An assertion-level rubric for the existing Skill behavior cases, with stable IDs, severity, and explicit PASS/FAIL/UNKNOWN evidence anchors.
- Runner integration that checks rubric/case parity, attaches assertion metadata, and reports critical-rule outcomes separately without creating a compensatory score or automatic release decision.
- A narrowly targeted subject-attribution case (SE13), separating the application outcome from the test Agent's performance when the suite is used to assess execution behavior.

These are supporting instruments for assessing the Builder Skill's execution on dataset-building tasks. They are not a substitute for the independent quality assessment of the datasets it generates.

## 4. Evidence boundaries

- Offline schema and contract tests establish only that the implementation obeys encoded contracts.
- Synthetic mutation tests establish sensitivity only to the exact mutation operators and fixtures tested.
- Simulation / Monte Carlo parameter-recovery tests establish behavior under their specified simulated assumptions.
- None of the above alone establishes semantic validity, real-world predictive validity, or effectiveness in actual Agent/Skill runs.
- A same-model generator/Judge arrangement is not an independent semantic evaluator. Claims about semantic output quality require independent blind review or a genuinely distinct evaluator.
- No paid model evaluation or real execution-effectiveness experiment is claimed unless its raw run evidence, frozen versions, and protocol are present.

## 5. Deferred / out of scope

The following work is explicitly paused because it is not currently necessary to answer the two research questions:

- Host-specific adapter development and cross-host certification.
- Claude Code, Codex, or other host hook comparisons.
- Per-file reference-read telemetry and navigation scoring.
- Generic Skill engineering quality or package optimization unrelated to measured evaluation outcomes.

Do not revive these items without identifying the specific validity question they answer and demonstrating that existing execution evidence cannot answer it.

## 6. Immediate empirical priorities

1. **Metric sensitivity:** apply controlled, independently checked defects to representative evaluation datasets; predefine expected metric changes and harmless negative controls.
2. **Criterion validity:** compare dataset quality assessments with independent expert judgments and, where feasible, known defect / real execution outcomes.
3. **Execution effectiveness:** run matched Agent/Skill tasks using datasets with meaningfully different quality profiles; compare defect detection, false alarms, discrimination, and evaluability.
4. **Stability:** repeat the same frozen runs and independent judgments to quantify run-to-run and reviewer variation.

Report raw counts, denominators, uncertainty, exclusions, and failure examples. Do not collapse these results into a single score without independent validation.

## 7. Current status

| Evidence | Status |
|---|---|
| Rubric / case contract | Offline contract tests only |
| Deterministic IDA mutation sensitivity | Synthetic controlled fixtures only |
| IDA ambiguous / incorrect Gold / construct mismatch / leakage | NOT_ASSESSED without independent review or Oracle |
| Expert content-validity evidence | NOT_RUN unless raw independent ratings are archived |
| Real Agent/Skill execution-effectiveness experiment | NOT_RUN |
| Cross-host compatibility | Out of scope for this research branch |

## 8. References

- Repository-local v0.0.2 metric catalog, experimental design, expert-review protocol, and benchmark validation assets.
- [Agent Skills specification](https://agentskills.io/specification) only where package behavior is directly relevant to a measured execution outcome.
