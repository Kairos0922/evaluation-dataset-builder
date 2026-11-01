# Evaluation Dataset Builder

**Version:** 0.0.1 · **Release status:** BLOCKED — release gates outstanding · **Type:** General-purpose Agent Skill

A Skill for planning, generating, validating, repairing, and packaging high-quality evaluation datasets for agents, skills, models, APIs, workflows, and other systems.

## What it does
- Parses source materials and separates evidence, assumptions, conflicts, and unknowns.
- Plans multiple purpose-specific datasets and coverage matrices before generating cases.
- Generates structured cases with expected behavior, forbidden behavior, graders, evidence requirements, and provenance.
- Applies case-level and dataset-level quality gates; critical failures cannot be averaged away.
- Repairs defects and reports coverage gaps, limitations, and quality scores.
- Supports incremental updates and versioned evaluation assets.
- Plans model requests from live capacity metadata instead of arbitrary small fixed limits.
- Provides DeepSeek V4.1 Flash metadata preflight and token-budget checks without spending a generation call.

## Quick start
1. Install the complete Skill directory in your compatible Skill runtime.
2. Provide the target system, evaluation goals, source materials, constraints, dataset splits/counts, and desired output format.
3. Review the generated manifest, cases, graders, coverage matrix, quality report, assumptions, and unresolved issues.
4. Execute cases in a controlled harness if execution verification is required.

## DeepSeek V4.1 Flash request preflight

The current official API model ID is `deepseek-flash` (display/version name: DeepSeek-V4.1-Flash-1017). Official limits are a 1,048,576-token combined context window and a 393,216-token maximum output. These are ceilings, not targets. The Skill calculates a task-specific budget and only splits work when the full request cannot fit.

With `DEEPSEEK_API_KEY` set:

```bash
python scripts/deepseek_model_preflight.py
python scripts/deepseek_model_preflight.py --input-tokens 250000 --estimated-output-tokens 120000
```

This calls the metadata endpoint `GET /models`, not a generation endpoint. It verifies the live model ID and limits and optionally checks a supplied token estimate. It does not guarantee generation success or replace a real behavioral run. See `references/deepseek-v4.1-flash.md` and `references/request-planning-and-recovery.md`.

## Repository layout
- `SKILL.md`: Skill instructions and workflow
- `references/`: quality standard, schema, graders, coverage, evidence, request planning, and provider profile
- `tests/self-eval-cases.json`: behavioral self-evaluation prompts
- `tests/trigger-evals.json`: trigger-positive and trigger-negative queries
- `tests/test_deepseek_model_preflight.py`: offline unit tests for budget and metadata logic
- `scripts/validate_skill.py`: structural and policy validation
- `scripts/deepseek_model_preflight.py`: metadata-only model and budget preflight
- `RELEASE.md`: release/install notes and release gates
- `VERSION`: intended package version

## Validate
```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py" -v
```

Structural validation and offline unit tests do **not** establish semantic quality or prove live generation success. Run the self-evaluation fixtures in a compatible model harness; see `tests/README.md`.

## Release discipline

The package remains at v0.0.1 until the release gates in `RELEASE.md` are met. Passing CI alone is not release approval. No formal GitHub Release or tag should be created while the release status is BLOCKED.

## Safety and limitations
- Do not upload secrets or unnecessary personal data.
- Treat traces as observed behavior, not ground truth.
- Label synthetic/inferred cases and do not fabricate source references.
- For side-effecting agents, define sandboxing, reset, cleanup, permissions, and cost limits.
- Preflight and bounded recovery reduce avoidable request failures but cannot control provider outages, account state, or network conditions.
- Behavioral evaluation and execution verification require external runtimes/harnesses.

## License
MIT. See `LICENSE`.
