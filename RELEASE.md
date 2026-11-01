# Release 1.0.0

## Scope
Stable first major version of the general-purpose Evaluation Dataset Builder Skill. It includes planning, generation guidance, quality review, repair, packaging, evidence governance, and model-aware request budgeting. DeepSeek V4.1 Flash receives a documented provider profile and metadata-only preflight helper.

## Install
Copy the complete repository Skill contents into a directory named `evaluation-dataset-builder` in the target Skill environment. Keep `SKILL.md` and the `references/` directory together. The scripts and tests are for preflight and development.

## Validate
```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py" -v
```

## DeepSeek preflight
Set `DEEPSEEK_API_KEY` in the target runtime and run:

```bash
python scripts/deepseek_model_preflight.py
```

This reads live model metadata through `GET /models`; it does not send an inference prompt. Supply estimated input/output tokens to validate a specific planned request. No request policy can guarantee provider availability or every paid call.

## Release gates
- [x] Skill entrypoint and progressive reference files
- [x] Version and changelog
- [x] Case schema and quality standard
- [x] Structural and request-policy validator
- [x] CI workflow
- [x] Self-evaluation and trigger fixtures
- [x] DeepSeek model metadata preflight helper
- [x] Offline unit tests for budget and preflight behavior
- [ ] Live model behavioral benchmark on a configured runtime
- [ ] Independent human review of generated benchmark outputs
- [ ] Execution harness validation for target systems

This is a packaged v1.0.0 Skill release, not a claim that model-specific behavioral benchmarks or target-system execution verification have been completed. Before using its outputs for high-impact release decisions, run the behavioral fixtures in the target model harness and review results independently.
