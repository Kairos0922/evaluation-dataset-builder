# Evaluation Dataset Builder

**Version:** 0.0.1 · **Type:** General-purpose Agent Skill

A Skill for planning, generating, validating, repairing, and packaging high-quality evaluation datasets for agents, skills, models, APIs, workflows, and other systems.

## What it does
- Parses source materials and separates evidence, assumptions, conflicts, and unknowns.
- Plans multiple purpose-specific datasets and coverage matrices before generating cases.
- Generates structured cases with expected behavior, forbidden behavior, graders, evidence requirements, and provenance.
- Applies case-level and dataset-level quality gates; critical failures cannot be averaged away.
- Repairs defects and reports coverage gaps, limitations, and quality scores.
- Supports incremental updates and versioned evaluation assets.

## Quick start
1. Install the complete Skill directory in your compatible Skill runtime.
2. Provide the target system, evaluation goals, source materials, constraints, dataset splits/counts, and desired output format.
3. Review the generated manifest, cases, graders, coverage matrix, quality report, assumptions, and unresolved issues.
4. Execute cases in a controlled harness if execution verification is required.

## Repository layout
- `SKILL.md`: Skill instructions and workflow
- `references/`: quality standard, schema, grader, coverage, and evidence policies
- `tests/self-eval-cases.json`: behavioral self-evaluation prompts
- `tests/trigger-evals.json`: trigger-positive and trigger-negative queries
- `scripts/validate_skill.py`: structural validation
- `RELEASE.md`: release/install notes
- `VERSION`: release version

## Validate
```bash
python scripts/validate_skill.py
```

Structural validation checks packaging and schema consistency. It does **not** establish semantic quality or model behavior. Run the self-evaluation fixtures in a compatible model harness; see `tests/README.md`.

## Quality standard
The Skill uses the versioned High-Quality Evaluation Dataset Standard in `references/quality-standard.md` and its machine-readable counterpart. Scores are evidence-backed rubric judgments. Critical gate failures block approval regardless of aggregate score.

## Safety and limitations
- Do not upload secrets or unnecessary personal data.
- Treat traces as observed behavior, not ground truth.
- Label synthetic/inferred cases and do not fabricate source references.
- For side-effecting agents, define sandboxing, reset, cleanup, permissions, and cost limits.
- Behavioral evaluation and execution verification require external runtimes/harnesses.

## License
MIT. See `LICENSE`.
