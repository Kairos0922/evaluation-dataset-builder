# Evaluation test harness

## Provider and models

The evaluator uses DeepSeek's OpenAI-compatible Chat Completions API:

- Base URL: https://api.deepseek.com
- Generator: `deepseek-flash` (DeepSeek-V4.1-Flash-1017)
- Judge and Trigger classifier: Groq `openai/gpt-oss-120b` by default (independent of the DeepSeek Generator), or a separately configured OpenAI-compatible endpoint/model
- Generator secret: `DEEPSEEK_API_KEY`
- Independent Judge secret: `GROQ_API_KEY` (fallback) or `EVAL_JUDGE_API_KEY`; endpoint/model/pricing can be overridden with repository Actions variables

Generation uses non-thinking mode and an 16,384-token output ceiling for both Skill and matched-baseline responses. Trigger classification uses 180 tokens; Judge rubric scoring uses 1,200 tokens. The local estimated total-request guard is 950,000 tokens, below DeepSeek Flash's documented 1M context window; the model's maximum output capacity is not used as the per-call budget. The runner records both endpoints, model IDs, token usage, conservative peak-price cost estimates, and checkpoint cache hits.

**Important model-routing constraint (2026-11-02):** DeepSeek announced that requests using `deepseek-v4-pro` are routed to V4.1 Flash from 2026-09-14 until V4.1-Pro is launched. Therefore `deepseek-v4-pro` is not an independent Judge for `deepseek-flash`. The harness detects and rejects this same-backend configuration before making a paid request. The default independent Judge is Groq `openai/gpt-oss-120b` at `https://api.groq.com/openai/v1`, using `GROQ_API_KEY`, and conservative published prices of $0.15/M input and $0.60/M output. Override with `EVAL_JUDGE_BASE_URL`, `EVAL_JUDGE_MODEL`, `EVAL_JUDGE_API_KEY`, `EVAL_JUDGE_INPUT_PRICE_USD_PER_MILLION`, and `EVAL_JUDGE_OUTPUT_PRICE_USD_PER_MILLION` when using another provider.

Each evaluation is protected by a USD 1.50 estimated-spend ceiling and a 220-request ceiling. The request count and peak-price cost reservation are persisted before each network call, including requests that fail or are truncated. Cost estimates reserve each request at peak-hour cache-miss prices before sending it. The runner stops immediately on insufficient balance/quota, authentication failure, or budget exhaustion. Successful API responses are checkpointed after each call; rerunning with the same commit, models, suite, and run count reuses completed responses. Each repeated run has a distinct cache namespace so stability testing still generates independent samples.

The runner retries transient rate-limit/server failures only a bounded number of times. It never converts an account/budget stop into an ordinary score of zero and continues spending.

## Automated gates

- Behavior expected-property pass rate: >= 90% on every complete run.
- Trigger Precision: >= 95% on every run.
- Trigger Recall: >= 95% on every run.
- Behavior suite: 12 scenario-grounded cases with 57 expected properties, including explicit synthetic policies, missing evidence, conflicting source versions, semantic duplicates, side effects, and a rule-version change.
- Trigger suite: 40 balanced queries (20 positive and 20 negative).
- Repeated-run stability: at least 2 complete runs on the same commit; spread for behavior, Precision, and Recall must each be <= 5 percentage points.
- Matched baseline: mandatory; same Generator model, prompts, suite, and Judge criteria without the Skill. The report records per-run and mean uplift for human review.

The runner has no skip flags for baseline or trigger evaluation and rejects a single-run shortcut.

## Run locally

Python 3.10+; no third-party packages required.

    export DEEPSEEK_API_KEY="..."
    export DEEPSEEK_GENERATOR_MODEL="deepseek-flash"
    export EVAL_JUDGE_BASE_URL="https://your-independent-provider.example/v1"
    export EVAL_JUDGE_MODEL="your-independent-model"
    export EVAL_JUDGE_API_KEY="..."
    export EVAL_JUDGE_INPUT_PRICE_USD_PER_MILLION="..."
    export EVAL_JUDGE_OUTPUT_PRICE_USD_PER_MILLION="..."
    python scripts/deepseek_model_preflight.py  # metadata GET only; no generation
    python scripts/validate_skill.py
    python -m unittest discover -s tests -p "test_*.py"
    python tests/run_eval.py --runs 2 --output artifacts/eval-report.json

Optional controls:

- `DEEPSEEK_MAX_ESTIMATED_COST_USD` (default: 1.50)
- `DEEPSEEK_MAX_API_REQUESTS` (default: 220)
- `DEEPSEEK_MAX_TOKENS` (default: 16384)
- `DEEPSEEK_MAX_ESTIMATED_REQUEST_TOKENS` (default: 950000)
- `EVAL_JUDGE_BASE_URL`, `EVAL_JUDGE_MODEL`, `EVAL_JUDGE_API_KEY`, `EVAL_JUDGE_INPUT_PRICE_USD_PER_MILLION`, and `EVAL_JUDGE_OUTPUT_PRICE_USD_PER_MILLION` (required for an independent Judge endpoint)
- `--checkpoint` (default: `artifacts/eval-checkpoint.json`); successful responses and conservative provider token reservations are stored after each call. Groq Judge calls are locally paced to 30 RPM / 8K TPM and capped at 180K reserved tokens per evaluation; the provider's account-specific limits remain authoritative.
- GitHub Actions manual fallback accepts `resume_run_id` to restore a prior workflow artifact checkpoint. Use the same branch/SHA, models, suite, and run count so the signature matches.

Never commit API keys or reports containing sensitive business prompts/data.

## Read the report

- Behavior pass rate is property-level: passed expected properties divided by all expected-property checks in the suite.
- Every run must independently meet the behavior and Trigger Precision/Recall thresholds.
- Trigger results include the confusion matrix and each query's expected/predicted label.
- Baseline results use the same Generator, prompts, and criteria. Review absolute scores and uplift; a delta is evidence for interpretation, not a substitute for examining outputs.
- Stability is the max-minus-min spread across repeated runs. The threshold is 0.05 (five percentage points).
- The report records provider, model IDs, candidate SHA, suite ID, workflow run ID, all outputs, Judge rationale/evidence, baseline deltas, and token usage. A passing Judge result must contain a verbatim evidence quote of at least 6 non-whitespace characters found in the exact candidate output; missing, duplicate, malformed, or unverifiable results fail closed. Any trigger-classifier JSON parse error is also a hard failure. On DeepSeek's specific JSON-mode validation error, the client retries once without the provider's JSON response constraint; the result is still parsed and validated locally. API errors or invalid/missing Judge results are preserved in the report and fail closed.

## Human review is mandatory

An independent reviewer must inspect the report, all failures, Judge evidence, generated samples, the baseline comparison, and critical cases SE03, SE04, SE05, SE08, SE09, SE11, SE12. The reviewer must record an APPROVED GitHub PR review that links the exact workflow run/report and summarizes findings. A successful automated run is not release approval.

This evaluator runs the self-contained SKILL.md entrypoint as the system instruction. The reference files remain packaged for the target Skill runtime but are not duplicated into the evaluation prompt; core operating contracts are summarized in the entrypoint to keep requests within the configured paid-provider budget. This is a portable behavioral proxy, not a full target Skills runtime; validate in the target runtime before broad deployment. LLM-as-judge is not a substitute for critical-case review.


## GitHub Actions candidate run

Use **Actions → Behavioral Skill Evaluation** and supply the full current PR #2 head SHA. The workflow verifies the exact SHA before running candidate code, performs metadata-only DeepSeek preflight, and requires the independent Judge endpoint/model/key and explicit input/output prices. It runs two complete rounds under the existing USD 1.50 / 220-request limits and uploads `candidate-evaluation-report-<run_id>`. Use the same SHA and `resume_run_id` to restore a checkpoint; do not resume against a changed candidate.
