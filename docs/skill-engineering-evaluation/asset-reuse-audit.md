# Skill Evaluation Asset Reuse Audit

**Audit date:** 2026-11-28  
**Branch baseline:** `main` at `3552e5be429e347ae675896c3c095b36ea498363`  
**Scope:** repository assets relevant to evaluating the Evaluation Dataset Builder Skill.

## 1. Summary

The repository already contains a static Skill validator, a balanced trigger suite, a 12-case behavior suite, a model-based baseline comparison runner, and a host compatibility matrix/report schema. The research should extend and clarify these assets rather than duplicate them.

The most important uncovered capability is **observable progressive-disclosure evaluation**: the current behavior runner loads only `SKILL.md` and does not record whether an Agent/host actually opens the appropriate reference files.

## 2. Asset inventory and findings

### 2.1 Package conformance

- `scripts/validate_skill.py`
- `tests/test_*.py`
- Skill package under `skills/evaluation-dataset-builder/`

The validator already checks:
- semantic version and Skill directory;
- frontmatter required/allowed fields, name format and directory match;
- package file allowlist;
- SKILL.md line limit;
- direct references from SKILL.md and existence of all referenced files;
- absence of second-level reference paths;
- provider-neutral Skill content;
- JSON Schema validity and selected cross-field constraints;
- machine-readable quality standard constraints;
- minimum shape/uniqueness of self-evaluation and trigger suites.

**Decision:** reuse unchanged as the package-conformance gate. Its PASS must not be represented as behavioral or scientific validity.

### 2.2 Trigger evaluation

- `tests/trigger-evals.json`
- 40 unique prompts: 20 positive and 20 negative.
- Positive prompts cover dataset creation, planning, audit, repair, coverage, grading, regression, and trace-derived test cases.
- Negative prompts cover general explanation, software implementation, summarization, translation, data processing, unrelated writing, and general advice.

**Decision:** retain as the initial discovery suite. Before using it for a high-confidence claim, independently review labels, near-duplicate intent clusters, ambiguity, and domain coverage. Add examples only for demonstrated gaps.

### 2.3 Behavior evaluation

- `tests/self-eval-cases.json`
- Suite ID: `edb-self-eval-v3-evidence-grounded`.
- 12 cases, SE01–SE12, with 58 expected assertions in total.

| Case | Category | Main behavior |
|---|---|---|
| SE01 | grounded_generation | evidence-grounded generation from explicitly synthetic rules |
| SE02 | multi_dataset_planning | multiple dataset purposes, boundaries, risk prioritization, overlap |
| SE03 | missing_evidence | continue supported work without inventing refund gold |
| SE04 | conflicting_sources | preserve conflict and avoid choosing by version number alone |
| SE05 | case_decidability | choose appropriate case-level grading contracts |
| SE06 | coverage | define coverage universe and critical non-compensatory gates |
| SE07 | semantic_deduplication | distinguish paraphrases from risk/intent variants |
| SE08 | critical_quality_gate | reject unsupported gold despite a high aggregate score |
| SE09 | execution_readiness | define preconditions, authorization, sandbox, assertions and cleanup without claiming execution |
| SE10 | packaging | package JSONL, manifest, source map and quality report |
| SE11 | negative_trigger | do not invoke the Skill for an unrelated poetry request |
| SE12 | incremental_update | update only cases affected by a rule change and preserve unaffected IDs |

**Decision:** keep these cases as the initial behavior suite. Review assertion granularity and criticality labels before relying on the current aggregate behavior pass rate.

**Coverage gap:** there is no clearly isolated, adversarial case whose primary purpose is to distinguish an application's actual defect from a test Agent/Skill's correct detection/reporting behavior. Add a narrowly scoped subject-attribution case rather than rewriting existing broad cases.

### 2.4 Existing behavior runner

- `tests/run_eval.py`
- Loads `SKILL.md` via `load_skill()`.
- Evaluates the same task suite with Skill text and a generic no-Skill baseline.
- Uses model-generated criterion judgments with verbatim evidence checks.
- Computes behavior pass/evaluability, baseline pass/evaluability, uplift, trigger precision/recall, repeated-run stability, and automated gates.
- Includes checkpointing and API request/cost protections.

Limitations requiring explicit treatment:
1. It loads only the Skill entrypoint. It does not perform actual on-demand reference loading and has no reference-read event telemetry.
2. The current generator and Judge model settings are both constrained to `deepseek-flash`; separate credentials do not make the model identities independent. The automated Judge can be a screening layer, but semantic outcome claims need an independent blind review or genuinely distinct evaluator.
3. Trigger classification in this runner is a model-based proxy, not proof of host-native Skill discovery.
4. Existing repeated-run and release thresholds are legacy operational gates. They must not be treated as universal validity thresholds for this new research.
5. The runner is a paid external-model workflow. Running it requires explicit authorization and a frozen candidate SHA, budget, credentials, and stop conditions.

**Decision:** reuse its paired baseline concept, evidence validation, checkpointing, and cost controls. Do not claim it already measures progressive disclosure or host-native discovery.

### 2.5 Cross-runtime compatibility

- `tests/target-runtime-matrix.md`
- `tests/target-runtime-report.schema.json`
- `tests/target-runtime-report.template.json`
- `scripts/validate_target_runtime_report.py`

The matrix distinguishes model/Skill behavior from host integration and defines per-host discovery, trigger, reference loading, task execution, side-effect, and cleanup checks. Its prose identifies several hosts as documented but not verified.

**Decision:** reuse the matrix and report contract. Review version references and ensure the schema can represent every required check (including side-effect and cleanup) before certification. Never convert DOCUMENTED_NOT_VERIFIED or NOT_RUN into PASS.

### 2.6 Existing methodology and evidence governance

Reuse:
- `docs/quality-assessment-v0.0.2/metric-catalog.md`: metric denominators, evidence types, uncertainty, non-applicability, and no unjustified aggregation.
- `docs/quality-assessment-v0.0.2/expert-review-protocol.md`: blind review, raw rating preservation, adjudication, reviewer agreement, and conflict disclosure.
- `docs/quality-assessment-v0.0.2/experimental-design.md`: pilot, defect injection, frozen validation, independent data, and replication.
- `docs/quality-assessment-v0.0.2/runtime-assessment-protocol.md`: exact version binding, failure attribution, trace evidence, and run governance.
- `scripts/validate_skill.py`: package structure and static test data integrity.

**Decision:** reuse these governance principles. Do not reuse IDA/ERA labels as if Skill package conformance and Skill-use behavior were the same construct.

## 3. New work justified by the audit

| Gap | Minimum addition | Why existing assets are insufficient |
|---|---|---|
| Evaluation-subject attribution | One targeted adversarial behavior case with separate application and test-Agent outcomes | Current cases contain adjacent principles but do not isolate this failure mode |
| Progressive disclosure | A task-to-reference dependency manifest and actual file-read event capture | Current runner injects only SKILL.md and cannot observe reference reads |
| Judge independence | Blind human review or distinct evaluator identity for semantic outcome claims | Current generator/Judge model identity is the same configured model |
| Trigger label validity | Independent review of existing positive/negative labels and ambiguity | Counts and uniqueness checks do not prove labels are correct |
| Host certification scope | Align target-runtime report schema with the matrix's full check list | A schema must be able to represent all checks being claimed |

## 4. Explicit non-goals

- Do not add empty `scripts/` or `assets/` folders to the Skill package.
- Do not move development tools or research protocols into the installable Skill directory.
- Do not duplicate the 12 behavior cases or 40 trigger prompts.
- Do not add a composite Skill-quality score or copy legacy thresholds without validation.
- Do not run paid model evaluation or claim cross-host certification as part of this audit.
