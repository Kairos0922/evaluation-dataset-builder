# Release 0.0.1 — Candidate (not yet published)

## Scope

General-purpose Agent Skill for evaluation dataset planning, generation, quality review, repair, and packaging. No domain-specific assumptions are built in.

## Install

Copy the complete repository Skill contents into a directory named evaluation-dataset-builder in the target Skill environment. Keep SKILL.md and the references/ directory together; optional tests/scripts are for validation and development.

## Validate

    python scripts/validate_skill.py
    python -m unittest discover -s tests -p "test_*.py"

## Use

Provide the evaluation target, objectives, capability/business documentation, rules/policies, historical cases/traces, environment constraints, desired dataset split/count, and output format in one request. The Skill will plan datasets, generate cases and graders, review quality, and report assumptions/gaps. Missing authoritative evidence must not be fabricated.

## Evaluation provider configuration

- Generator: `deepseek-flash` (DeepSeek-V4.1-Flash-1017), non-thinking mode.
- Independent Judge/Trigger: Groq `openai/gpt-oss-120b` by default, using `GROQ_API_KEY`; custom providers can use `EVAL_JUDGE_*`. Do not use `deepseek-v4-pro` as an independent Judge because DeepSeek currently routes it to V4.1 Flash.
- Per-evaluation budget: USD 1.50 estimated peak-price ceiling and 220-call ceiling.
- Secrets: `DEEPSEEK_API_KEY` (Generator) and `GROQ_API_KEY` (independent Judge; `EVAL_JUDGE_API_KEY` overrides). Default Judge pricing is conservatively reserved at $0.15/M input and $0.60/M output.

## Release gates

- [ ] Repository default branch changed from `main` to `master` by an administrator. The release verifier intentionally blocks publication until this setting is changed.


- [x] Trusted-event-only DeepSeek metadata preflight workflow; PR jobs do not receive the DeepSeek secret.
- [x] Exact-SHA manually dispatched behavior-evaluation workflow with independent Judge configuration and spend caps.


- [x] DeepSeek live metadata preflight: authenticated `GET /models` passed in GitHub Actions run `41362696533`; no generation request was sent.
- [ ] Independent Judge configuration and complete behavior benchmark.
- [ ] Independent human review and target-runtime execution evidence.


- [x] Skill entrypoint, reference files, case schema, and quality standards
- [x] Structural validator and offline release-gate unit tests
- [x] Behavior evaluation harness with mandatory matched baseline
- [x] Trigger fixture: 40 balanced queries (20 positive, 20 negative)
- [x] Repeated-run stability calculation (minimum two full runs)
- [x] Paid DeepSeek provider with peak-price spend cap and resumable API-response checkpointing
- [ ] Behavioral pass rate >= 90% on every run
- [ ] Trigger Precision >= 95% and Recall >= 95% on every run
- [ ] Baseline comparison reviewed and accepted
- [ ] Stability spread <= 5 percentage points for all three metrics
- [ ] Independent human review of critical cases and generated outputs
- [ ] Target-runtime validation

This is a release candidate only. Do not publish tag v0.0.1 until every automated and human gate in RELEASE-GATE.md has passed on the exact release commit.
