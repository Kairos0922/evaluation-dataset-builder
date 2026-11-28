# Skill Engineering Best Practices & Quality Evaluation

**Status:** Research design baseline; no new behavioral experiment has been run.  
**Target:** `skills/evaluation-dataset-builder/` at the v0.0.2 baseline.  
**Scope:** Skill package engineering quality, Agent behavior when using the Skill, task outcome effectiveness, and host integration compatibility.

## 1. Purpose

This research evaluates whether the Evaluation Dataset Builder Skill is discoverable, navigable, followed correctly, and measurably useful. It does not treat Markdown conformance or a high self-evaluation score as proof of effectiveness.

The central question is:

> Under controlled and explicitly bounded conditions, does providing this Skill improve the correctness, evidence quality, and practical usefulness of evaluation-dataset work compared with a matched no-Skill baseline?

## 2. Evaluation layers

Keep these layers separate:

1. **Package conformance:** metadata, naming, package contents, references, schemas, and static integrity. Deterministic checks are appropriate.
2. **Skill-use behavior:** discovery, reference selection/loading, instruction following, and handling of critical rules.
3. **Outcome effectiveness:** quality of the resulting work compared with a matched baseline, assessed independently.
4. **Host integration:** whether a specific host discovers, loads, executes, and safely handles the Skill package.

A pass at one layer does not imply a pass at another. In particular, package validation does not prove correct Agent behavior; model behavior evaluation does not prove every host integration; and successful execution does not by itself prove outcome validity.

## 3. Existing project assets to reuse

The repository already contains a meaningful first-generation evaluation foundation:

| Asset | Existing role | Reuse decision |
|---|---|---|
| `tests/trigger-evals.json` | 40 trigger examples, balanced 20 positive / 20 negative | Retain as discovery baseline; review label quality before expanding |
| `tests/self-eval-cases.json` | 12 behavior cases (SE01–SE12) | Retain as behavior baseline; map coverage and add only missing critical scenarios |
| `tests/run_eval.py` | External-model Skill vs generic-baseline evaluation, repeated runs, trigger classification, evidence-checked judging | Reuse concepts and report data; audit limitations before relying on results |
| `scripts/validate_skill.py` | Static package, metadata, reference, schema, and test-suite checks | Keep as package-conformance gate |
| `tests/target-runtime-matrix.md` | Host integration plan and platform-specific evidence requirements | Reuse and align its version/status with v0.0.2 |
| `tests/target-runtime-report.schema.json` | Host compatibility report contract | Reuse where its required checks match the actual certification scope |
| `docs/quality-assessment-v0.0.2/metric-catalog.md` | Metric governance and IDA/ERA metric definitions | Reuse denominator, evidence, missingness, and non-aggregation principles |
| `docs/quality-assessment-v0.0.2/expert-review-protocol.md` | Blind review, raw ratings, adjudication, and agreement | Reuse for independent output-quality review |
| `docs/quality-assessment-v0.0.2/experimental-design.md` | Baseline, defect injection, frozen validation, replication | Reuse experimental controls and evidence governance |

The asset audit and limitations are documented in [asset-reuse-audit.md](asset-reuse-audit.md).

## 4. Evaluation dimensions

The proposed model has five dimensions:

- **Discovery:** correct activation on relevant requests and non-activation on irrelevant requests.
- **Progressive disclosure:** selection and loading of the references needed for a task, without critical omissions or unnecessary reads.
- **Instruction following:** compliance with ordinary, important, and critical Skill rules, with critical violations reported non-compensatorily.
- **Outcome effectiveness:** independently assessed quality difference between Skill-assisted and matched no-Skill outputs.
- **Cross-runtime compatibility:** host-specific discovery, loading, task execution, and safety/cleanup behavior.

Package conformance remains a prerequisite gate rather than a sixth behavioral score.

Definitions, denominators, evidence requirements, and limitations are specified in [quality-model.md](quality-model.md).

## 5. Pilot design

The first Pilot should reuse the existing SE01–SE12 cases and 40 trigger examples. The six proposed Pilot task groups are specified in [pilot-design.md](pilot-design.md). Two important gaps require new coverage before claiming full evaluation:

1. A direct adversarial test of evaluation-subject attribution (application defect vs. test Agent/Skill performance).
2. Instrumented reference-navigation tests that record which reference files were actually opened/read and why.

Do not create a duplicate second copy of existing scenarios. Keep new cases narrowly targeted at these uncovered behaviors.

## 6. Experimental principles

- Freeze the Skill tree, test suite, prompts, model, host, tools, and evaluation protocol for each batch.
- Compare Skill and no-Skill conditions on the same tasks and as closely matched as possible.
- Keep raw outputs, reference-read events, tool traces, judge records, and reviewer records.
- Use deterministic validators for structural facts; use independent blind review for semantic judgments.
- Report unknown, not-run, and not-assessed separately from pass/fail.
- Report per-dimension results. Do not create a composite Skill-quality score or universal pass threshold without independent validation.
- Treat the existing 12-case suite as a Pilot instrument, not as a statistically representative benchmark.
- Do not run paid model evaluations without explicit batch authorization, candidate SHA, budget, credentials, and stop conditions.

## 7. Current status

| Work item | Status |
|---|---|
| Repository asset inventory | Completed by source inspection |
| Five-dimension model | Design baseline drafted |
| Existing case coverage mapping | Drafted |
| Critical subject-attribution gap | Identified |
| Reference-navigation instrumentation gap | Identified |
| New experiments | NOT_RUN |
| Cross-host certification | NOT_RUN / platform-specific status must be evidenced |
| Skill package changes | Not in scope for this research branch |

## 8. References

- [Agent Skills specification](https://agentskills.io/specification)
- [Anthropic Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic: Equipping agents for the real world with Agent Skills](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills)
- Repository-local metric, experimental, expert-review, runtime, and package-validation assets listed above.
