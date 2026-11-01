# Evaluation Dataset Builder test protocol

## Local deterministic checks

Run:

```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py" -v
```

The structural validator checks packaging and schema consistency. The DeepSeek preflight unit tests use mocked metadata responses and make no network or generation calls.

## Provider preflight

When DeepSeek credentials are available, run:

```bash
python scripts/deepseek_model_preflight.py
python scripts/deepseek_model_preflight.py --input-tokens 250000 --estimated-output-tokens 120000
```

This makes an authenticated metadata GET request to `/models`, not a model-generation request. It confirms the current API model ID and live context/output limits. A planned budget check requires token estimates supplied by the caller or a tokenizer/estimator in the calling runtime.

## Behavioral evaluation

Run each prompt from `self-eval-cases.json` in a fresh context with the Skill loaded. Grade expected properties, not wording. Include trigger-positive, paraphrase, and negative-trigger cases. Repeat stochastic cases when measuring consistency. Report per-case results, aggregate pass rate, critical failures, model/version, and run configuration.

For large-context and recovery cases, record:
- actual model ID and protocol;
- estimated and provider-reported input/output/reasoning tokens;
- planned output ceiling and context margin;
- response status/finish reason and request ID;
- completed case IDs, retry count, and resume cursor.

For capability uplift, compare with a matched baseline without the Skill. Keep a held-out subset for regression and avoid tuning indefinitely against all cases.

The repository provides fixtures, deterministic validation, and a metadata preflight helper. It does not include a general model-execution harness and does not claim DeepSeek generation behavior has been benchmarked unless a compatible runtime actually ran these cases.
