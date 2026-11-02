# Release gate policy

A release is blocked unless every gate below has evidence tied to the exact candidate commit. The v0.0.1 tag and GitHub Release must not be created before approval. All pull requests must target `master`; CI rejects PRs targeting any other base. The repository default branch should also be set to `master` so new PRs default to the release trunk.

## Automated gates

1. Structural and offline harness tests pass on the candidate commit. The behavior suite must use concrete, scenario-grounded prompts and independently inspectable expected properties.
2. Behavior expected-property pass rate is at least 90%. The denominator is the total binary expected-property checks across the complete self-evaluation suite, not the number of whole test cases. Every repeated run must independently meet the threshold.
3. Trigger Precision and Recall are each at least 95% on every repeated run. The balanced trigger suite must contain at least 20 positive and 20 negative cases. Any classifier JSON parse error on any query is a separate hard failure; it must not be counted as a correct negative prediction.
4. A matched baseline is mandatory: same Generator model, prompts, cases, and Judge criteria without the Skill. The report must contain complete baseline results and per-run/mean absolute score delta. Any regression or surprising uplift must be examined and explicitly accepted by the human reviewer.
5. At least 2 complete runs are required on the same commit and model configuration. The max-minus-min spread for behavior pass rate, Trigger Precision, and Trigger Recall must each be <= 5 percentage points. Every run must independently pass gates 2 and 3.
6. DeepSeek API errors, unavailable models, empty responses, insufficient balance/quota, local budget exhaustion, missing reports, or incomplete baselines fail closed. Billing/quota/budget stop errors immediately halt further paid calls. Successful responses are checkpointed by exact commit/model/suite/run scope so an interrupted run can resume without paying twice for completed calls. No partial run is a passing run.

## Model configuration

The Groq Judge uses conservative local safeguards based on published baseline limits: 30 RPM, 8K TPM, and a 180K per-UTC-day token reservation ceiling (below the documented 200K TPD baseline; cumulative evaluation spend/request caps persist across daily checkpoint resumes). The model-specific 131,072-token context limit is enforced locally. The provider may impose lower account-specific limits; any 429/limit response is handled with bounded, paced retries and remasters charged against the request/cost ledger.

- Online provider: DeepSeek Chat Completions API at https://api.deepseek.com.
- Generator: `deepseek-flash` (DeepSeek-V4.1-Flash-1017), non-thinking mode, 16,384-token output ceiling. The estimated total-request guard defaults to 950,000 tokens (the provider documents a 1M context window and 384K maximum output).
- Judge: Groq `openai/gpt-oss-120b` by default, or another genuinely separate OpenAI-compatible provider/model; non-thinking mode, 2,400-token output ceiling. Trigger classification uses that Judge endpoint with a 180-token output ceiling. Groq GPT-OSS 120B has a 131,072-token context window and supports JSON Object Mode.
- Generator secret: `DEEPSEEK_API_KEY`. Independent Judge secret: `GROQ_API_KEY` (default) or `EVAL_JUDGE_API_KEY`; the default endpoint/model are `https://api.groq.com/openai/v1` / `openai/gpt-oss-120b`, with conservative prices $0.15/M input and $0.60/M output. Custom providers use the `EVAL_JUDGE_*` variables.
- **Current DeepSeek routing blocker:** DeepSeek announced that since 2026-09-14, `deepseek-v4-pro` requests are routed to V4.1 Flash until V4.1-Pro launches. As of 2026-11-02 this is not an independent model from `deepseek-flash`. The harness fails before paid calls if both roles resolve to that same deployed model. Do not label the Pro model ID as independent until DeepSeek officially changes the routing.
- Each full evaluation is capped at USD 1.50 estimated peak-price spend and 220 provider requests. The cost estimate and request count are persisted before each paid call, including failed or truncated calls; a compatible checkpoint restores prior reservations before any further API request.
- The exact generator and Judge endpoints/model IDs, token usage, estimated peak-price cost, paid generation/Judge POST attempt count (including retries); metadata-only GET /models preflights are separate and do not consume generation tokens, per-model context/rate limits, daily token reservations, and checkpoint cache hits must appear in the report. Every retry attempt is reserved against both the request and estimated-cost caps before the network call.

## Mandatory human gates

Target-system execution is a separate mandatory release gate, not satisfied by this portable text benchmark. The independent reviewer must verify the controlled target-runtime execution report (environment/build, test IDs, initial/final state, tool/API traces, permissions, side effects, reset/cleanup, and run timestamp). The APPROVED review must include `target-runtime: PASS` and a stable HTTPS evidence link. If the target runtime is unavailable or any side-effect/reset evidence is missing, the release remasters BLOCKED.

An independent reviewer must inspect the machine-readable report and record an APPROVED GitHub PR review. The review must explicitly confirm:

- Critical cases: SE03, SE04, SE05, SE08, SE09, SE11, SE12.
- All failed cases and Judge rationales/evidence; every passing Judge result must include a verbatim quote of at least 6 non-whitespace characters that the harness can locate in the exact candidate output; challenge any quote that does not support the stated rationale.
- Representative generated outputs, including provenance, assumptions, conflict handling, grader observability, side-effect/reset handling, and negative-trigger behavior.
- Baseline comparison and every negative or surprising uplift/regression.
- Model IDs, suite ID, candidate SHA, workflow run ID, and at least two repeated-run metrics.

A review that only says "looks good" is insufficient. The reviewer must cite the evaluation workflow run/report and summarize critical findings. Any unresolved critical safety, fabricated-gold, source-conflict, grader-validity, or side-effect issue blocks release regardless of aggregate score.

## Release procedure

1. Merge the release-gate/test-harness PR into master only after its code and structural checks are reviewed. This does not itself release v0.0.1.
2. Configure DEEPSEEK_API_KEY and the independent EVAL_JUDGE_* repository variables/secret, then use Actions → Behavioral Skill Evaluation with the exact PR #2 head SHA. The workflow checks the SHA, performs metadata-only preflight, and runs two complete rounds under the USD 1.50 / 220-request caps.
3. Confirm both complete runs pass all metric thresholds, baseline comparison is complete, and all stability gates pass.
4. Complete the mandatory independent human review. If code changes after evaluation, discard the report and rerun on the new SHA.
5. Only after steps 1-4 pass, create tag v0.0.1 at the reviewed commit and publish the GitHub Release with the evaluation report/run link attached.

No threshold override, skipped baseline, skipped trigger evaluation, single-run shortcut, or structural-CI-only release is allowed. Failed, missing, stale, or unverifiable evidence means NO RELEASE.
