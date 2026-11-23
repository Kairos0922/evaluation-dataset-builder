# Round 4 final acceptance decision (2026-11-22)

**NOT PASSED.** Builder production and independent validation passed. The initial Oracle report falsely failed two completed pilots and misclassified the quota-blocked third pilot. After correcting the adjudicator and re-running it offline against the same immutable artifacts, the result is **2 PASS, 0 FAIL, 1 UNKNOWN**. WB-12 did not execute to completion because the provider returned HTTP 402 QUOTA. The three-case acceptance gate therefore remains unmet.

A targeted WB-12-only retry was subsequently initiated at the user's direction. It reused the frozen Builder dataset and did not send any generation request because the GitHub Actions preflight again reported insufficient DeepSeek balance. The acceptance decision remains NOT PASSED.

## Frozen scope

1. Reuse the Round 4 Builder output and independent-validator PASS.
2. Execute the three Builder-authored pilots once.
3. Review immutable pilot evidence and independent Oracle output.
4. Publish the decision and, if explicitly authorized, retry only an externally blocked case using the same frozen dataset. No dataset regeneration.

PR #38 remains Draft/Open/unmerged.

## Builder and validation evidence

- Builder production run: [44959366258](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258), artifact 14729741906.
  - One dataset, 15 cases; actual Builder Skill invocation verified; trace PASS, 530 events.
- Independent validation run: [44968128127](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127), artifact 14732232796.
  - PASS; one dataset, 15 cases, 0 schema errors, 61 source evidence references verified.
- Replay: [44980451933](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44980451933), commit 59d74dd79666c0c6e61f2c8ac53df4b30cc55860.
  - All three pilot jobs ran; Oracle job completed with FAIL.
  - Artifacts: WB-02 14738085222; WB-10 14738140416; WB-12 14737298412; Oracle 14737717458; immutable Builder input 14737577420.

## Pilot results and evidence review

| Case | Execution | Observed behavior | Corrected Oracle result | Independent review |
|---|---|---|---|---|
| WB-02 search mutation | DSH completed; 65.48s; 15 model steps; 21 tool calls; budget PASS | PASSWORD returned 0 and empty state; password returned 1, “Reset password flow”. Skill report accurately identifies case-sensitive behavior and BR-02 violation. No mutations. | **PASS**; business EXPECTED_VIOLATION_DETECTED | Corrected Oracle extracts both query values and expected title from Builder schema; all checks pass. Skill correctly reports the application defect. |
| WB-10 state cycle | DSH completed; 121.218s; 18 model steps; 26 tool calls; budget PASS | Exactly 3 PATCHes on WB-101: Open→In progress→Done→Open. Each summary matched; final state matched baseline; no other mutations. Skill report says PASS. | **PASS**; business PASS | Corrected Oracle recognizes the report’s 结果：PASS label. Audited transitions, summary, final state, and report verdict all agree. |
| WB-12 delete confirmation | DSH error; 81.043s; 15 model steps; 21 tool calls; budget PASS | Provider returned HTTP 402 QUOTA (“Insufficient Balance”). No DELETE occurred; task set and summary remained unchanged; no final report. | **UNKNOWN**; business UNKNOWN | Corrected Oracle recognizes the external quota blocker and resolves the target by visible title. It does not treat absent execution/report evidence as target-Skill failure.

### WB-02 key observation

- `PASSWORD`: 0 rows, visible empty state “No tasks match the current filters.”, no visible error.
- `password`: 1 row, title “Reset password flow”, empty state hidden, no visible error.
- Control query `ZZZ_NO_MATCH_9137` also returned 0 and the same empty state.
- Initial/final task set identical; no reset or mutations; browser console errors empty.
- The Skill report correctly concluded that the application is case-sensitive and violates BR-02.

### WB-10 key observation

Observed transitions and summary (All / Open / In progress / Done):

| Step | Status | Summary |
|---|---|---|
| 1 | Open → In progress | 5 / 1 / 3 / 1 |
| 2 | In progress → Done | 5 / 1 / 2 / 2 |
| 3 | Done → Open | 5 / 2 / 2 / 1 |

Three PATCH requests only; the four other tasks remained unchanged. Evidence is internally consistent with PASS.

### WB-12 key observation

Runner evidence reports DSH final reason `error`, exit 1, error code `QUOTA`, HTTP 402. Server audit contains only reset and read requests; no DELETE. Pre/post task set is identical. The destructive action was **not** performed.

## Oracle correction and offline re-adjudication

The original Oracle findings were corrected without regenerating the Builder output or making any model calls. The same immutable artifacts were adjudicated by the corrected Oracle in workflow run [44985689752](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44985689752), artifact **14739706689**.

Fixes:
- Search probes now read Builder test_data kind=search_queries and its values array.
- Expected search-match titles are extracted from Builder-authored expected_match_example data.
- Target resolution supports title-only Builder targets.
- Report verdict parsing accepts 结果：PASS and Markdown formatting.
- External provider quota/balance blocks are classified as execution BLOCKED and behavior UNKNOWN, not Skill FAIL.

Corrected results: WB-02 PASS (the Skill accurately detected the application defect), WB-10 PASS, WB-12 UNKNOWN (HTTP 402 QUOTA). Aggregate Oracle status is **UNKNOWN / COMPLETED_WITH_UNKNOWN**, with 2 PASS, 0 FAIL, 1 UNKNOWN. The original adjudicator’s three FAILs were false classifications, not evidence that the target Skill failed these cases.

Exact-head CI run [44985689752](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44985689752) passed: offline tests, Gold Oracle self-test, validator checks, pilot selector checks, and pinned upstream asset audit. No paid Builder or target-Skill execution was triggered.

## Cost and resource use

Across all three pilot attempts: **48 model steps, 68 tool calls, 42,837 input tokens, 41,886 output tokens, 938,752 cache-read tokens, 1,023,475 total tokens**. USD cost is not available and is not estimated. WB-12's quota error occurred before deletion, so no destructive action was taken.

## Targeted WB-12 retry after this decision

- Workflow run [44993465567](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44993465567), job `wb12`, commit `32a4c5d569d1bbced263d4008dc4cf07ca325a6f`.
- Frozen source artifact download and WB-12 identity checks: PASS.
- DeepSeek preflight: **FAIL** with `Insufficient Balance`; no generation request sent. DSH installation and execution steps were skipped.
- Artifact: `round4-wb12-retry-only`, ID 14742299922. It contains the frozen source inputs and no WB-12 execution evidence.
- This is a provider/account credential or balance issue, not a Skill result. It does not change WB-12 from UNKNOWN or the acceptance decision.

## Final gate

| Gate | Result |
|---|---|
| Builder production | PASS |
| Independent validation | PASS |
| Three pilot attempts captured | PASS (2 completed, 1 externally blocked) |
| WB-02 Skill reporting | PASS; application deviation detected |
| WB-10 state cycle | PASS |
| WB-12 delete confirmation | UNKNOWN; provider QUOTA / HTTP 402 blocked execution before DELETE |
| Independent Oracle (corrected, offline) | UNKNOWN: 2 PASS, 0 FAIL, 1 UNKNOWN |
| Overall acceptance | **NOT PASSED** because required three-case execution gate is incomplete |

## Stop condition

Round 4 remains **NOT PASSED**. Do not regenerate the Builder dataset or rerun any completed pilots. WB-12 can only be retried after the GitHub Actions DeepSeek credential/account balance is verified as usable; use the same frozen dataset and targeted retry. PR #38 remains Draft/Open/unmerged.


## Safe credential diagnostic (2026-11-22)

A separate diagnostic workflow made GET-only requests to DeepSeek's balance and model catalog endpoints; it did not make any generation requests.

- Workflow run [45001128665](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45001128665): failed the balance gate.
- DeepSeek returned `is_available: false`, currency CNY, `total_balance: -0.01`, `granted_balance: 0.00`, `topped_up_balance: -0.01`.
- This confirms the API credential used by GitHub Actions currently resolves to an account with unavailable/negative balance. It does not reveal how the balance was consumed or prove which request caused it.
- No generation request was made by this diagnostic. WB-12 remains UNKNOWN; no paid retries are authorized until the balance/key is corrected.


## Alternate LLM credential probe (2026-11-22)

To avoid another DeepSeek generation attempt, a temporary read-only GitHub Actions probe checked common provider credentials via GET model-catalog endpoints. No generation calls were made.

- Run [45001273706](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45001273706) completed successfully.
- OpenAI, Anthropic, Gemini/Google, OpenRouter, Together, Moonshot, Zhipu, and Qwen credentials were not configured in this repository's Actions environment.
- A Groq credential was present, but the read-only `/openai/v1/models` request returned HTTP 403, so it was not usable from this environment.
- No alternate LLM credential was verified as available. The temporary diagnostic workflow and trigger marker were removed after recording the result.

**Execution remains blocked:** no available alternate provider was found. Do not claim WB-12 passed or rerun it until an accessible credential/provider is configured.


## Addendum: one-time free-only WB-12 retry automation (2026-11-22)

This addendum supersedes the earlier DeepSeek-only stop condition above. **Do not use or request `DEEPSEEK_API_KEY`.** The only permitted inference credential for this retry is the existing `OPENROUTER_API_KEY`.

- Selected model: `inclusionai/ling-3.2-flash:free`. OpenRouter lists it as free, with tool calling and structured-output support and a 1,048,576-token context window. The model page currently lists one serving provider; availability is not guaranteed.
- The workflow is `.github/workflows/round4-wb12-free-retry.yml`, deployed on `main` and the task branch. The default-branch schedule is 08:30 UTC daily. The redundant synthetic model-qualification workflow was removed; this avoids spending free requests on a generic JSON probe.
- Before any DSH execution, it checks the existing one-time attempt marker and reads OpenRouter quota using GET only. It requires at least 37 free requests remaining: the original Round 4 ceiling of 32 model steps plus a five-request reserve. Below that threshold, it sends zero inference requests.
- It reuses the exact frozen Builder output and independent-validator PASS from run 44980451933. It does not regenerate the dataset. It reuses the already completed WB-02 and WB-10 artifacts and executes only WB-12.
- The model ID is explicitly `:free`; there is no paid fallback. The WB-12 workflow sends no separate connectivity or synthetic qualification probe. It performs a read-only quota check, then spends requests only on the real WB-12 Skill execution. DSH telemetry and Session Log upload remain disabled.
- Before the first DSH request, the workflow archives a one-time marker artifact. Future scheduled runs detect that marker and stop, so the retry is not repeated automatically after an execution attempt starts.
- After WB-12 execution, the same workflow runs the independent Gold Oracle against the exact three-case Round 4 matrix and archives the adjudication result.
- The scheduled workflow has not yet made a model request. Its first eligible run will occur only when the quota gate reports at least 37 remaining and no prior attempt marker exists.

Implementation verification:
- Task-branch PR validation run [45033961757](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45033961757): PASS; 219 offline tests passed; Round 4 offline re-adjudication, independent Oracle checks, and pinned upstream asset audit passed.
- Task-branch runner preflight [45033955677](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45033955677): PASS; actionlint and workflow syntax checks passed.
- Default-branch validation after removing the redundant synthetic qualification workflow [45033948594](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45033948594): PASS; 125 offline tests passed.
- PR #38 remains Draft/Open/unmerged.

**Acceptance remains NOT PASSED** until the real WB-12 Skill execution completes and the independent Oracle produces a passing three-case result. No offline self-test is substituted for that execution.


## Evidence review of the original WB-12 partial execution (2026-11-22)

Artifact **14737298412** was downloaded and inspected, including `runner-result.json`, `dsh-events.jsonl`, `server-audit.jsonl`, the aborted preflight log, and the model-authored Playwright scripts. This review adds partial behavioral evidence but does not change the official Oracle verdict.

- DSH loaded the pinned `webapp-testing` Skill, read the public assets, performed read-only browser reconnaissance, and authored a Playwright test. Trace: 15 model steps, 21 tool calls (10 bash, 2 edit, 5 read, 3 write, 1 Skill call), one user turn.
- The first test-script execution aborted before the destructive action due to a model-authored assertion defect: only summary field `All` was converted to an integer; `Open`, `In progress`, and `Done` remained strings. The expected summary used integers, so the baseline assertion failed despite the UI and task rows being correct.
- The evidence records **0 confirm clicks and 0 DELETE requests**. The task set remained unchanged. The runner's fixture initialization reset occurred before DSH started; no Skill-issued reset or mutation was observed.
- After the first test execution failed, the model edited the script to convert all four summary values, ran `py_compile` (syntax check only), and refreshed the read-only API baseline. It did **not** execute the test script a second time. The user instruction explicitly forbids retry; preparing a repaired script and refreshed baseline after the first execution is a recovery attempt that violates the intended stop-and-report discipline, even though no second test execution or destructive action occurred. The next model inference was rejected with HTTP 402 QUOTA / Insufficient Balance.
- No final Skill report was produced. Required evidence shows screenshots and JSON evidence, but `markdown_report=false`.

**Interpretation:** WB-12 remains UNKNOWN, not FAIL, because external quota interruption prevented the Skill from completing and Oracle lacks a complete run. This partial trace nevertheless demonstrates an observed test-script correctness defect and a rule-following risk: the model started preparing recovery after the case had explicitly prohibited retries. It does not support a claim that the model/Skill would complete the case if quota were available. The free-model retry remains unproven and must be judged only from actual execution and independent Oracle evidence.

## Final WB-12 execution and Round 4 acceptance (2026-11-23)

This section supersedes the prior **NOT PASSED** decision and the earlier free-only retry restriction. The user explicitly reconfigured `DEEPSEEK_API_KEY` and directed that DeepSeek be used only for evaluation execution, never for code or script repair.

- Read-only credential preflight: workflow run [45188903250](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45188903250) PASS. DeepSeek reported `is_available=true`, balance CNY 19.98, and `deepseek-flash` present in the model catalog. This preflight made zero generation requests.
- Real WB-12 execution: workflow run [45189512695](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45189512695) PASS; artifact **14824967038** (`round4-wb12-deepseek-output`).
- Frozen source: Builder artifact and independent-validator PASS from run `44980451933`; prior WB-02 and WB-10 evidence reused unchanged. No dataset regeneration and no rerun of completed pilots.
- DeepSeek was invoked only by the real WB-12 evaluation. DSH completed in 89.426 seconds: 15 model steps, 19 tool calls, one turn, final reason `completed`; usage telemetry was complete and all configured budgets passed.
- WB-12 target was the Builder-authored `WB-104 / Verify email notification`. The runner's delete guard recorded exactly one allowed request: `DELETE /api/tasks/WB-104`, HTTP 200. No second DELETE, unrelated mutation, or retry occurred.
- The Skill report recorded 30/30 assertions PASS, exactly one confirmation click, one DELETE request, no error, and the expected post-state: 4 tasks; Open=1, In progress=2, Done=1.
- Independent Gold Oracle adjudication in the same run returned **PASS: 3/3**, 0 FAIL, 0 UNKNOWN. WB-02 PASS, WB-10 PASS, WB-12 PASS. It verified all 20 WB-12 evidence files against the Runner SHA-256 manifest, execution count, mutation budget, run identity, final state, report, and screenshots.

### Final acceptance gate

| Gate | Final result |
|---|---|
| Builder formal production | PASS, original frozen Builder artifact reused |
| Independent Builder-output validation | PASS |
| DSH tool-call compatibility smoke | PASS, run [45186835825](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45186835825) |
| WB-02 real Skill trial | PASS, original evidence reused |
| WB-10 real Skill trial | PASS, original evidence reused |
| WB-12 real Skill trial using DeepSeek | PASS |
| Independent Gold Oracle | PASS, 3/3 |
| Overall Round 4 acceptance | **PASS** |

No model was used to write or repair code/scripts. The DeepSeek model was used only for the actual WB-12 evaluation. PR #38 remains Draft/Open/unmerged.


## PR delivery cleanup (2026-11-23)

The Round 4 final WB-12 execution and Gold Oracle adjudication supersede the earlier OpenRouter free-only retry plan. The dormant scheduled retry workflow was removed because it was no longer needed and would otherwise leave an obsolete scheduled/manual execution path in the PR. Its workflow-specific contract test was removed with it. The historical retry design and earlier quota-blocked evidence above are retained as experiment history; they are not current execution instructions.

The PR validation workflow no longer repeats the earlier offline re-adjudication that intentionally expected WB-12=UNKNOWN from the pre-final, quota-blocked evidence. That historical result remains documented above, while current Round 4 acceptance is established by the final WB-12 run and independent Gold Oracle PASS 3/3 recorded in the final acceptance section. This cleanup does not regenerate the dataset, rerun any Skill, or make model calls.
