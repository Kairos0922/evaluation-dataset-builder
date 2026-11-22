# OpenRouter Free-Model Qualification Record

Date: 2026-11-22
Repository: `Kairos0922/evaluation-dataset-builder`
Branch: `experiment/webapp-testing-contract`
Scope: provider/model smoke tests only. No Builder production, independent validation, or target-Skill pilot was run.

## Findings

- `OPENROUTER_API_KEY` was present in GitHub Actions. The secret value was never printed.
- The first `openrouter/free` request returned HTTP 200 and routed to `nvidia/nemotron-3.5-super-vl:free`, but `message.content` was null. The initial probe misclassified the parsing exception as `BLOCKED`; the parser was corrected.
- The live model catalog exposed 11 models meeting the probe's zero prompt/completion price and text input/output filters. Five were screened with an exact-instruction and JSON-output check.
- `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` passed both checks and then passed two repeated structured-output trials (2/2).
- `nvidia/nemotron-3-ultra-550b-a55b:free` passed one initial instruction/JSON screen, but a subsequent structured response was truncated (`finish_reason=length`).
- `google/gemma-4-31b-it:free` had one exact-instruction pass, but structured output was rate-limited or invalid in later attempts.
- `google/gemma-4-26b-a4b-it:free` and `nvidia/nemotron-3.5-lightning:free` did not pass the two-part screen in the observed runs.

## Rate-limit incident and correction

The test matrix was triggered by both push and pull-request events while the PR branch was being updated. This created duplicate runs and a burst of generation requests. The logs show 429 responses on subsequent attempts. OpenRouter's published free-model limits are 20 requests/minute and 50 requests/day for `:free` variants; failed attempts count toward the daily limit. Therefore, the burst itself may have exhausted the per-minute and/or daily allowance. The available logs from the affected runs did not preserve the provider error metadata or rate-limit headers, so the exact 429 source cannot be distinguished retrospectively.

The workflow was changed to:
- use a push-only explicit marker trigger, preventing duplicate push/PR generation runs;
- check `GET /api/v1/key` and the remaining free-model daily quota before generation;
- make at most one generation request per run;
- record `Retry-After`, `X-RateLimit-*`, and sanitized provider error metadata on a 429;
- avoid automatic retries because failed free-model attempts can consume the daily allowance.

No further model calls should be made until the quota check reports remaining capacity.

## Evidence

- Initial single-router probe: [run 45018554016](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45018554016)
- Five-model matrix and repeated trials: [run 45018682074](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45018682074)
- Later matrix run with 429 responses: [run 45018747794](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45018747794)
- Pinned-model task probe with three 429 responses: [run 45018790432](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45018790432)

## Acceptance status

This is preliminary provider qualification only. The Nano Omni model is the best candidate observed so far, but its realistic rule-based dataset-generation task has not passed. It is not yet qualified for Builder production. The Builder workflow still uses its existing DeepSeek-specific production configuration; OpenRouter has not been wired into the Builder production path.

PR #38 remains Draft, Open, and Unmerged. The existing gates remain unchanged: actual Builder production PASS, independent validator PASS, and real Skill pilots WB-02, WB-10, and WB-12 must all be supported by their own evidence.
