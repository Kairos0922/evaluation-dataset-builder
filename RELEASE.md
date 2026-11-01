# Release 0.0.1

<badge>Release status: BLOCKED — do not publish</badge>

## Scope

General-purpose Agent Skill for evaluation dataset planning, generation, quality review, repair, and packaging. The 0.0.1 release candidate includes model-aware request budgeting and a DeepSeek V4.1 Flash metadata-only preflight helper.

The agreed target version for this release remains **0.0.1**. A change in capability or implementation does not by itself authorize changing the version. Do not create a Git tag or GitHub Release until all required gates pass and release approval is explicit.

## Install

For internal testing, copy the complete repository Skill contents into a directory named `evaluation-dataset-builder` in the target Skill environment. Keep `SKILL.md` and the `references/` directory together. Internal testing is not a public release.

## Validate

```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py" -v
```

## Release gates

| Gate | Required evidence | Current status |
|---|---|---|
| Package and entrypoint integrity | Skill, references, schema, manifest, and required files validate | PASS |
| Deterministic validation | Structural and policy validator passes | PASS |
| CI and offline tests | GitHub Actions validator and unit-test job pass | PASS |
| DeepSeek live preflight | Authenticated `GET /models` confirms live model ID and limits in GitHub Actions runner | PASS — run `41362696533`, commit `c4162aa`; secret injected, `deepseek-flash` metadata returned, no generation request sent |
| Model behavior benchmark | Run the self-evaluation suite with the target Skill/model; report per-case outcomes and critical failures | NOT RUN |
| Independent quality review | Human review of representative generated outputs, graders, coverage, and evidence traceability | NOT RUN |
| Target-system execution validation | Execute applicable tool/action cases in a controlled harness; verify end state, side effects, reset, and cleanup | NOT RUN |

**Release decision: BLOCKED.** The live DeepSeek metadata preflight is now verified in GitHub Actions (run `41362696533`): the runner received the configured secret, authenticated `GET /models`, and returned the `deepseek-flash` model metadata. No generation request was sent. Model behavior benchmarking, independent human quality review, and target-system execution validation remain incomplete. Passing CI and metadata preflight do not satisfy those gates.

## DeepSeek preflight

Set `DEEPSEEK_API_KEY` in the target runtime and run:

```bash
python scripts/deepseek_model_preflight.py
python scripts/deepseek_model_preflight.py --input-tokens 250000 --estimated-output-tokens 120000
```

This reads live model metadata through `GET /models`; it does not send a generation prompt. Supply estimated input/output tokens to validate a specific planned request. A successful preflight is necessary operational evidence, but it does not replace model behavior benchmarking.

## Publication rule

Do not mark this version publishable, create a version tag, or create a GitHub Release until every required gate above has recorded evidence and the release owner approves the result. A green CI run is necessary but not sufficient.
