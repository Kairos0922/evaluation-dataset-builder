# DeepSeek V4.1 Flash API Profile

**Verification date:** 2026-11-02  
**Official API model ID:** `deepseek-flash`  
**Current display/version name in the official API pricing documentation:** `DeepSeek-V4.1-Flash-1017`

This page records the official DeepSeek API profile verified on 2026-11-02. Recheck live `GET /models` metadata before relying on the limits in a future release.

## Model identifier and limits

| Property | Official value |
|---|---:|
| API model ID | `deepseek-flash` |
| Context window | 1,048,576 tokens (1M) |
| Maximum output per response | 393,216 tokens (384K) |
| Input modalities | Text and image |
| Output modality | Text |
| OpenAI-compatible API base URL | `https://api.deepseek.com` |

Important interpretation:

- The model metadata defines `context_window` as the total capacity counting **both input and output** tokens.
- The metadata defines `max_output_tokens` as the maximum output accepted by the server for one response. It is a separate upper bound, not an additional 384K that can be added on top of the 1M context.
- Therefore, a request must fit both `input_tokens + output_tokens <= 1,048,576` and `output_tokens <= 393,216`, with a practical estimation margin.
- In the Responses API, `max_output_tokens` includes visible response tokens **and reasoning tokens**. Reserve output capacity for both when thinking mode is enabled.
- Do not hard-code a small input cap or a small output default. Use live metadata and estimate the actual request. Do not try to fill the entire context just because it is available.

The model's official API identifier is `deepseek-flash`; `DeepSeek-V4.1-Flash` / `DeepSeek-V4.1-Flash-1017` are display/version names, not the model ID to pass as `model`.

## API preflight

DeepSeek documents `GET https://api.deepseek.com/models` as the endpoint for current model IDs, context windows, output limits, modalities, and capabilities. Use the `DEEPSEEK_API_KEY` environment variable for authorization. This is a metadata request, not a generation request; it does not consume model output tokens.

Run:

```bash
python scripts/deepseek_model_preflight.py
```

To validate a planned request budget:

```bash
python scripts/deepseek_model_preflight.py \
  --input-tokens 250000 \
  --estimated-output-tokens 120000
```

The helper uses the live metadata returned by DeepSeek and prints a suggested output ceiling only if the estimate fits. It never silently lowers the requested output budget. Use `--headroom` and `--safety-margin-ratio` to change planning assumptions when you have better empirical estimates.

The helper only reads model metadata. It does not make a billable generation call, and passing preflight is not a guarantee against network failures, account limits, rate limits, or provider outages.

## Output and recovery

For the Responses API, use the protocol's `max_output_tokens` parameter. DeepSeek documents that this upper bound includes reasoning and visible output. Inspect the terminal response status and `incomplete_details.reason`; `max_output_tokens` is a documented incomplete reason. Never treat a partial streamed response as complete.

For Chat Completions, use the parameter name supported by that endpoint and the current API reference; do not copy a Responses API parameter into a different protocol. Validate the complete request shape before sending it.

Follow the generic retry and continuation policy in `references/request-planning-and-recovery.md`: do not retry 400/401/402/422 unchanged; pace 429; retry confirmed 500/503 failures only within a bounded policy; treat post-transmission timeouts as ambiguous; and resume only missing case IDs after partial output.

## Official sources

- [DeepSeek Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) — model version, 1M context, 384K maximum output, API model ID and billing basis.
- [DeepSeek Lists Models API](https://api-docs.deepseek.com/api/list-models/) — live model metadata; defines `context_window` as input plus output and `max_output_tokens` as the maximum accepted response size.
- [DeepSeek Responses API](https://api-docs.deepseek.com/api/create-response/) — `max_output_tokens` includes visible and reasoning tokens; terminal status and incomplete reasons.
- [DeepSeek Error Codes](https://api-docs.deepseek.com/quick_start/error_codes/) — documented 400, 401, 402, 422, 429, 500, and 503 handling.
- [DeepSeek Change Log](https://api-docs.deepseek.com/updates/) — 2026-10-17 update to V4.1-Flash-1017; API model ID and calling method unchanged.
