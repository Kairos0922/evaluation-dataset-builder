# Round 4 evidence reuse audit for release candidate 0.0.1

Date: 2026-11-24

## Scope

Compare the Skill package used by the frozen Round 4 Builder evidence with the current Skill package synced from PR #38. This audit determines which prior evidence can be reused and which gates require targeted follow-up. It does not trigger model calls.

Round 4 formal Builder run candidate SHA: `eb1fa5c21e7b2320e0904bb1cb72a38854b9cbd8` (run `44959366258`, artifact `14729741906`).  
Current source Skill branch: `experiment/webapp-testing-contract`  
Builder-run Skill file blob SHA: `1743b5b133e83d7f9a3332d9bae5912b0300dccb`  
Current Skill file blob SHA: `1743b5b133e83d7f9a3332d9bae5912b0300dccb`

Builder-run schema blob SHA: `b1314c3d7811dfd0c1e61ddad245927add92affa`  
Current schema blob SHA: `b1314c3d7811dfd0c1e61ddad245927add92affa`

The two Skill package files are byte-identical to the current source branch. GitHub commit comparison also found no changes under `skills/evaluation-dataset-builder/` between the Builder candidate commit and PR #38's current branch.

## Exact changes

At the historical formal Builder run, the current Skill already included the two requirements being audited. The current package has no further changes relative to that Builder package. For context, the two requirements are:

1. **Source-reference identity consistency:** source-map/source registry identity fields (`source_id`, `title`, `source_type`, `path`) must match each case's `source_refs`; copy canonical values, put section/topic notes in `locator`, and check identity before generation.
2. **Explicit evaluation subject:** each grading contract must distinguish the application/API from the testing/auditing/diagnostic Agent or Skill. Application defects are facts for a testing Agent to discover, not automatically Agent failures. Criteria must assess one subject consistently; split criteria when evaluating both subjects; case-level verdicts must align with criteria.

The schema requires `grading.evaluation_subject`, and the formal Builder output populated it in all 15 cases. Independent validation reported 0 schema errors and verified 61 source references. A separate byte comparison confirmed that the pilot archive and formal Builder archive contain identical `wb-core.jsonl`, `source-map.json`, and `wb-core.manifest.json` files (SHA-256: `000d38b110b60eae902f86737ea6bd1368f98c6632c42a47bb9470a4a08bfc45`, `ae7609b9a42dc37fe190660246c06d687d9cd6fdcca9b9ea1d2795b1b29dd780`, and `016b3fc6fba3a3e0d61efef58a265d1b82f696db19aee53aec44bf3bca950b0a`, respectively).

## Evidence disposition

| Evidence | Decision | Reason / follow-up |
|---|---|---|
| WB-02, WB-10, WB-12 real execution traces | **Reuse: exact case match verified** | The frozen Builder output used by Round 4 has the same case IDs/titles and contracts. WB-02 tests case-insensitive search reporting; WB-10 tests exactly three status transitions; WB-12 tests exactly one confirmation delete. Each explicitly sets `grading.evaluation_subject` to the webapp-testing Skill. |
| WB-12 DeepSeek execution | **Reuse** | Actual DSH execution completed; 30/30 assertions, exactly one guarded DELETE, no retries or unrelated mutations. The artifact is tied to the same frozen Builder output. |
| Gold Oracle 3/3 adjudication | **Reuse: exact artifact binding verified** | The pilot archive contains byte-identical Builder JSONL, source map, and dataset manifest. Gold Oracle adjudicated the same frozen cases: WB-02, WB-10, WB-12, 3/3 PASS. |
| Formal Builder production | **PASS; reuse** | Run `44959366258` produced 15 cases from the current Skill package; the recorded candidate commit's Skill/schema blobs match the current package exactly. |
| Independent Builder-output validation | **PASS; reuse** | Run `44968128127` validated the archived output: 15 cases, 0 schema errors, 61 source references verified, and source identity/path/title/type checks passed. All 15 cases include `grading.evaluation_subject`; all 61 source refs match their source registry identity fields. |
| Three-case trial gate | **PASS; reuse all three** | The Round 4 immutable Builder output is already package-matched. The exact WB-02/WB-10/WB-12 case definitions are the ones consumed by the pilots; Gold Oracle adjudication is 3/3 PASS. No case rerun is justified. |
| Current-candidate behavior evaluation | **Not automatically required by SHA drift** | Determine whether the release evaluation compares Skill behavior rather than generation-time output. If it consumes a new dataset, ensure the dataset's relevant cases and grading contract are validated first. Avoid rerunning completed behavior cases merely to attach a new commit SHA. |

## Release gate recommendation

1. Reuse the Round 4 formal Builder output and independent validation. The package tree matches the current candidate exactly.
2. Reuse all three real pilot traces and Gold Oracle PASS 3/3. The selected case contracts were checked against the archived Builder output.
3. Do not re-run Builder, validator, pilots, or Oracle solely to rebind a new commit SHA.
4. Resolve the diagnostic `builder-validation-summary.json` false-positive flags in the audit record. It flags WB-03-C3, WB-04-C2, and WB-14-C2. Manual review of the exact clauses shows they score whether the Skill correctly observes, reports, and classifies application deviations; they do not mark the raw application deviation as a Skill failure. The flags are false positives. The formal quality review still correctly records suite `needs_info` because BR-09 request-failure/error-recovery evidence is unavailable; this limitation is documented and does not invalidate WB-02/WB-10/WB-12 execution.
5. The remaining release work is separate: candidate-specific behavior evaluation, reconcile any true quality findings, exact-head CI, release review, and approval.

## Evidence links

- Round 4 formal Builder production: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258 (artifact 14729741906)
- Independent output validation: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127 (artifact 14732232796)
- Round 4 final acceptance report: `benchmarks/reports/round4-final-acceptance-decision-2026-11-22.md`
- WB-12 actual DeepSeek evaluation and Gold Oracle 3/3: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45189512695
- Historical exact-head CI: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45221565463

This is an evidence reuse audit, not a new execution or release approval. No model calls were made during this audit.
