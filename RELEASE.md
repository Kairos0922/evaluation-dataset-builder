# Release 0.0.1

## Scope
General-purpose Agent Skill for evaluation dataset planning, generation, quality review, repair, and packaging. No domain-specific assumptions are built in.

## Install
Copy the complete repository Skill contents into a directory named `evaluation-dataset-builder` in the target Skill environment. Keep `SKILL.md` and the `references/` directory together; optional tests/scripts are for validation and development.

## Validate
```bash
python scripts/validate_skill.py
```

## Use
Provide the evaluation target, objectives, capability/business documentation, rules/policies, historical cases/traces, environment constraints, desired dataset split/count, and output format in one request. The Skill will plan datasets, generate cases and graders, review quality, and report assumptions/gaps. Missing authoritative evidence must not be fabricated.

## Release gates
- [x] Skill entrypoint and progressive reference files
- [x] Version and changelog
- [x] Case schema and quality standard
- [x] Structural validator
- [x] CI workflow
- [x] Self-evaluation and trigger fixtures
- [ ] Claude/model behavioral benchmark executed
- [ ] Independent human review of generated benchmark outputs
- [ ] Execution harness validation for target systems

This is a first public baseline (0.0.1), not a claim of benchmark-proven production performance. Use controlled rollout and review outputs before high-impact release decisions.
