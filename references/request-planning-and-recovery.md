# Model-Aware Request Planning and Recovery

## Goal

Maximize the probability that each paid generation request completes correctly without wasting tokens on unnecessarily small fixed limits or repeating work that already succeeded. A provider's published maximum is a ceiling, not a recommended size for every request. Never promise a 100% success rate: network, provider, account, and service conditions remain outside the Skill's control.

## 1. Preflight before generation

Perform all checks that do not require a generation call first:

1. Resolve the exact provider model identifier and API protocol. Do not assume a display name is a valid API model ID.
2. When supported, read the provider's model metadata endpoint to obtain the live context window, maximum output, modalities, and supported parameters. Metadata discovery is not a model-generation call.
3. Validate the request body, required fields, schema, tool definitions, parameter names, credential presence, and destination configuration locally.
4. Estimate input tokens across the complete request: system/developer instructions, Skill references, user request, retained conversation, retrieved source excerpts, examples, JSON Schema, tool definitions, and multimodal payloads.
5. Estimate the complete response, including structured fields, graders, provenance, manifests, and reasoning-token allowance when the provider counts reasoning against the output limit.

Use a provider tokenizer or trustworthy provider-side estimate when available. Otherwise use a model-aware estimator and observed usage from prior successful requests. Character counts alone are not a reliable token estimate, especially for Chinese, code, JSON, and mixed-language material. Do not silently drop relevant evidence to make a request fit.

## 2. Allocate the actual available budget

Respect both constraints:

`estimated_input_tokens + requested_output_budget + safety_margin <= context_window`

`requested_output_budget <= max_output_tokens`

A useful planning calculation is:

- `available_output = min(max_output_tokens, context_window - estimated_input_tokens - safety_margin)`
- `requested_output_budget = ceil(estimated_complete_output * headroom_factor)`

Use a modest, configurable headroom factor based on estimate quality and observed variance (the included DeepSeek preflight helper defaults to 1.15). A small safety margin protects against tokenizer and payload-estimation error; it is not a reason to impose a small fixed input cap. Always use live model metadata where available. The included helper defaults to a 1% context margin with a 4,096-token floor and lets operators change the assumptions.

If the complete output fits, keep the task together. Do not split a request merely because it exceeds an arbitrary token count, character count, or fixed number of cases. If it does not fit, split only at meaningful dataset/case boundaries and preserve stable IDs, source references, shared definitions, and a resumable cursor. Never silently truncate source material or expected output.

Do not set the output ceiling to a small generic default. Allocate enough room for the complete expected response plus headroom, bounded by the provider's published/live maximum and the remaining context capacity. A configured ceiling is not a target to consume; actual billing follows actual usage under the provider's pricing rules.

## 3. Prefer one well-prepared generation call

- Default to one generation call per coherent dataset batch after local preflight.
- Do not spend a separate model call merely to ask whether the main request is understood, to estimate tokens, or to restate the input when those steps can be done locally.
- Do not request a second LLM self-review by default. Run deterministic schema, ID, required-field, reference, and duplicate checks locally; add a semantic judge call only when the evaluation purpose requires it.
- Keep system instructions, schemas, and stable reference material cache-friendly and avoid sending irrelevant history.
- Record the planned budget and actual provider usage so later requests can use observed token-per-case and reasoning overhead.

## 4. Classify failures; do not retry blindly

| Failure | Default handling |
|---|---|
| HTTP 400 / invalid format | Do not retry unchanged. Correct the request structure or unsupported content. |
| HTTP 401 / authentication | Stop. Verify the credential and account configuration; never print the key. |
| HTTP 402 / insufficient balance | Stop and surface the balance issue. |
| HTTP 422 / invalid parameters | Do not retry unchanged. Correct model, parameter, schema, or value errors. |
| HTTP 429 / rate limit | Respect `Retry-After` when present, reduce request concurrency/pace, then retry a confirmed rejected request once with exponential backoff and jitter. |
| HTTP 500 / 503 | Retry a confirmed failed request once after a brief backoff. Stop if the retry fails and report the provider error. |
| Connection failure before request transmission | A bounded retry is normally safe. |
| Timeout or connection loss after the request body may have reached the provider | Treat the outcome as unknown. Do not automatically resend a large generation request: it may have been processed already. Check provider request records/status if available; otherwise report the ambiguous outcome and resume only after establishing what completed. |

Do not retry fatal configuration, authorization, or balance errors. Do not run unlimited retries. A retry is a new request and may consume additional quota if the provider processed the original request.

## 5. Handle incomplete output without losing completed work

Inspect the provider's terminal response status, finish reason, and usage. For a structured dataset:

1. Parse and validate complete records already returned.
2. Persist valid records and their stable IDs before attempting recovery.
3. If the response stopped because of the output ceiling, continue from the first missing case/dataset cursor; do not regenerate the entire successful portion.
4. If JSON is incomplete, do not mark it valid. Resume from a deterministic boundary and validate the assembled result locally.
5. Distinguish `completed`, `incomplete`, and `failed`; never infer success from partial streamed text.

For multi-call generation, maintain a small manifest with planned chunks, completed IDs, failed IDs, request IDs, and the next cursor. A repair call must target a specific defect or missing range.

## 6. Observability and cost controls

Log non-secret operational metadata: provider, actual model ID/version when available, API protocol, request ID, estimated input/output budgets, actual input/output/reasoning token usage, status/error code, retry count, duration, and completed case IDs. Never log API keys or unnecessary personal data.

Report clearly when a result is structurally validated but has not been behaviorally run. An external provider's maximum context does not prove this particular request will succeed; only a real provider response and subsequent local validation can establish that.

## 7. DeepSeek-specific policy

When using DeepSeek V4.1 Flash, follow `references/deepseek-v4.1-flash.md` and run `python scripts/deepseek_model_preflight.py` before a costly generation run where credentials are available. The script performs a model-metadata GET request only; it never sends a generation prompt.
