# Builder output offline review and execution-cost audit

**Date:** 2026-11-20  
**Source:** Formal Builder artifact `14624897819` from workflow run [44726278657](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44726278657).  
**Method:** Deterministic inspection of the immutable Builder output and archived DSH traces. No Builder or Pilot was rerun for this review.

## 1. Formal output and independent validation

The actual Builder-produced suite contains:

- 1 dataset, `wb-core`.
- 14 unique cases, all marked `candidate`.
- Suite and dataset quality status: `needs_info`.
- Suite, dataset and all 14 case execution statuses: `NOT_RUN` at Builder-production time.
- 57 coverage items: 45 `applicable`, 11 `not_applicable`, and 1 `needs_info`.
- All 45 applicable items are covered by candidate cases across the five reported dimensions.
- 18 source files are registered in the source map.

The official independent Builder validator passed in the same original workflow run: `schema_errors=0`, 14 cases, and 47 case-level source evidence references independently verified against the exact frozen input and its source-file hashes.

The 100% applicable coverage figures do not mean the suite is fully resolved. The suite correctly remains `needs_info` because `BR-09-RF` is unresolved.

## 2. Offline structural checks

The following checks were independently recomputed from the archived JSONL and manifests:

| Check | Result |
|---|---:|
| Case count agrees across JSONL and both manifests | 14 / 14 |
| Unique case IDs | 14 / 14 |
| Single user-message input shape | 14 / 14 |
| Non-empty runtime `execution_requirements.observable_assertions` string arrays | 14 / 14 |
| Non-empty top-level structured observable assertions | 14 / 14 |
| Non-empty grading criteria | 14 / 14 |
| Non-empty source references | 14 / 14 |
| App URL and timeout contract valid | 14 / 14 |
| Single-script execution budget declared | 14 / 14 |
| Execution status remains `NOT_RUN` | 14 / 14 |

No multi-turn cases were generated. This is consistent with the input contract: each case has one user message, and none depends on context carried from a prior user message. No heldout split was declared; the Builder documents this as a fixed regression suite rather than a tuning benchmark.

## 3. Scope and documentation finding

The actual case distribution is **8 read-only cases** (`WB-CORE-01` through `WB-CORE-08`) and **6 write-oriented cases** (`WB-CORE-09` through `WB-CORE-14`).

The Builder-generated `README.md` currently describes the split as 7 read-only and 7 write/evidence cases, placing `WB-CORE-08` in the latter group. However, `WB-CORE-08` is titled “WB-101 可见标题侦察与只读状态确认” and performs read-only inspection. This is a documentation classification inconsistency. The formal Builder artifact was not manually edited; the discrepancy is recorded for a future Builder instruction/output correction.

The three selected real Pilots cover `WB-CORE-02`, `WB-CORE-12`, and `WB-CORE-14`. The other 11 cases have not been executed. The three-case PASS must not be generalized to the entire dataset.

## 4. Unresolved quality gap

`BR-09-RF` remains `needs_info`: the public fixture has no controlled, repeatable request-failure injection contract. A failure case must not be fabricated by changing application code or introducing an undeclared network interception method. The appropriate next step is for the fixture/runner owner to define a controlled failure-injection contract; only then should the Builder generate a corresponding case.

The other recorded boundaries remain explicit: no production authentication/authorization, external integrations, concurrency, persistence, or full WCAG audit is claimed.

## 5. DSH trace usage audit

Token counts below are sums of the per-turn `usage` records in the archived DSH traces. They are cumulative trace usage, not unique prompt size and not an invoice. Cache reads may be priced differently. Exact monetary charges cannot be derived from these artifacts.

| Execution | Usage records | Input tokens | Output tokens | Cache-read tokens | Aggregate trace tokens |
|---|---:|---:|---:|---:|---:|
| Builder production | 82 | 124,014 | 199,890 | 16,296,704 | 16,620,608 |
| Connectivity probe | 1 | 229 | 5 | 5,376 | 5,610 |
| Pilot `WB-CORE-02` | 24 | 17,869 | 20,330 | 596,480 | 634,679 |
| Pilot `WB-CORE-12` | 22 | 22,815 | 28,642 | 628,864 | 680,321 |
| Pilot `WB-CORE-14` | 40 | 35,762 | 65,256 | 2,524,800 | 2,625,818 |
| **Combined** | **169** | **200,689** | **314,123** | **20,052,224** | **20,567,036** |

The Builder trace contains 101 tool calls: 46 bash, 29 read, 16 edit, 9 write and 1 Skill invocation. The delete-confirmation Pilot is the largest cost centre. **Correction to the earlier wording:** its 40 usage records are 40 model steps inside one DSH user turn, not 40 separate turns or 40 independent sessions. The trace has 214 events, 44 tool calls (30 bash, 5 read, 3 edit, 3 read_image, 2 write, 1 Skill call), 123,656 characters of recorded thinking text, 65,256 output tokens and 2,524,800 cache-read tokens.

Across the three Pilots, WB-CORE-14 accounts for 66.6% of aggregate trace tokens, 57.1% of output tokens and 67.3% of cache reads. Compared with WB-CORE-02 it used 4.14x aggregate tokens; compared with WB-CORE-12 it used 3.86x.

### WB-CORE-14 step-level attribution

| Phase | Steps | Input | Output | Cache reads | Aggregate |
|---|---:|---:|---:|---:|---:|
| Initial planning, script authoring and pre-run checks | 1–17 | 19,054 | 41,428 | 586,880 | 647,362 |
| Single Playwright test execution step | 18 | 134 | 673 | 64,256 | 65,063 |
| Evidence inspection | 19–26 | 7,082 | 6,110 | 565,760 | 578,952 |
| Post-processing and report correction | 27–40 | 9,492 | 17,045 | 1,307,904 | 1,334,441 |
| **Total** | **40** | **35,762** | **65,256** | **2,524,800** | **2,625,818** |

The Playwright test itself ran once for approximately 3.18 seconds. The DSH runner envelope lasted 362.596 seconds from runner start to finish. The Builder-generated task carried a 240-second execution budget, but the old runner only passed that value in the prompt; its configured DSH process timeout was 1,500 seconds and it did not enforce or separately record actual DSH elapsed time. Since runner wall time includes fixture setup and teardown, this does not prove the DSH process itself exceeded 240 seconds. It does mean compliance with that case budget is **UNKNOWN**, not proven PASS. This is a runner control/evidence gap.

The major avoidable cost is not the browser test. It is the repeated model reasoning, iterative script edits and post-run evidence/report correction. In particular, steps 27–40 alone consumed 1,334,441 aggregate trace tokens. The initial script's dialog-title extractor selected the Delete button text instead of the dialog heading; the agent then wrote a separate postprocessor and spent 14 further model steps correcting and re-verifying the report.

The offline Gold Oracle replay in run `44733891829` used archived Builder/Pilot artifacts and deterministic Python adjudication only. It did not invoke DSH or a model. Its PASS verdicts describe business behavior; they do not retroactively prove DSH time-budget compliance.

### Operational budget controls added

The runner now records usage totals, usage-record count, model-step count, model-turn count and tool-call counts. It monitors the trace while DSH is running and stops the process when a ceiling is crossed. It also enforces the effective DSH wall-clock timeout as the smaller of the configured DSH timeout and the Builder-declared case timeout, and records actual DSH start/end timestamps and elapsed time.

The provisional per-case stop ceilings for future authorized Pilot runs are:
- 32 model steps;
- 60,000 uncached input tokens;
- 55,000 output tokens;
- 1,600,000 cache-read tokens;
- 1,750,000 aggregate `totalTokens`;
- DSH process timeout 600 seconds, additionally bounded by the case's own declared timeout.

These are operational cost/safety controls, not evaluation-quality thresholds. They are calibrated to allow the observed pre/post-browser core of WB-CORE-14 (26 steps, 48,211 output tokens, 1,216,896 cache reads) with limited headroom, while stopping the observed 14-step post-processing tail before it can repeat. If a ceiling is crossed, the case is BLOCKED and its partial evidence is preserved; no automatic model repair or retry is allowed. No future run is authorized by adding these controls.

The old runner result did not record actual DSH elapsed time or usage summaries. The updated runner will do so on future executions.

## 6. Cost-control decision

No further paid Builder production or model-backed Pilot run should be started until the execution traces have been reviewed and an explicit cost budget has been agreed.

Before any future model run:
1. Identify why the delete-confirmation Pilot required 40 usage-bearing turns and whether repeated image/report/tool work can be eliminated without weakening evidence.
2. Keep deterministic schema checks, manifest generation, coverage counts, hashes and file checks outside the model.
3. Limit the model context to the exact Skill, task contract and necessary source material; avoid repeated whole-workspace reads.
4. Define explicit per-run and per-case ceilings for model turns, uncached input and output. Stop on the first ceiling; do not use automatic model repair loops.
5. Capture the provider's actual billing/export data alongside DSH trace usage. Do not infer money from aggregate token counts.

The `run-builder-production` opt-in label was removed from PR #38 after the original run. It remains removed. The PR remains Draft/Open and unmerged.
