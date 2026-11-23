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
5. Prior PR #39 behavioral evaluation is reusable as a historical baseline only: run `44572520813` completed 2 runs × 12 Skill cases, 40 trigger cases, 100% behavior pass, 100% trigger precision/recall, zero stability spread, complete baseline comparison, and automated gates PASS. It evaluated only `SKILL.md` (references were not loaded), on old Skill/schema blobs (`945d9f...` / `e94739...`), so it is not current-candidate evidence.
6. The self-evaluation case file and trigger-evaluation file are byte-identical between that old evaluation commit and current candidate. The current package adds source-reference identity and explicit grading-subject/schema requirements. Impact is primarily generation/contract scenarios (SE01, SE03–SE10, SE12); the creative-writing negative trigger SE11 and trigger suite are unaffected. Reuse historical results for unaffected portions, but current-candidate release behavior still needs evidence for the changed contract unless the release owner formally accepts a documented targeted-scope substitute.
7. Remaining release work: determine/execute the smallest justified current-package behavior-evaluation scope, verify CI for the latest documentation-only candidate commits, review release evidence, and obtain explicit release approval.

## Evidence links

- Round 4 formal Builder production: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258 (artifact 14729741906)
- Independent output validation: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127 (artifact 14732232796)
- Round 4 final acceptance report: `benchmarks/reports/round4-final-acceptance-decision-2026-11-22.md`
- WB-12 actual DeepSeek evaluation and Gold Oracle 3/3: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45189512695
- Historical exact-head CI: https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45221565463

This is an evidence reuse audit, not a new execution or release approval. No model calls were made during this audit.


## Final evidence disposition and exact-head status (2026-11-24)

This addendum supersedes the earlier open items in this audit that predated the exact evidence-reuse check and current-candidate behavior evaluation. It does not rewrite the historical run records above.

### Builder output, diagnostic and independent verification

- Formal Builder invocation: run [44959366258](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258), Artifact 14729741906, Builder-run source commit eb1fa5c21e7b2320e0904bb1cb72a38854b9cbd8.
- The DSH invocation trace is PASS: exit code 0, 530 trace events, exactly one Builder Skill tool call, and nine generated output files. The output is an actual Builder-produced artifact; it was not written or repaired by the validator or this audit.
- The enclosing builder-production job concluded **failure** because the Builder artifact's heuristic builder-validation-summary.json flagged WB-03-C3, WB-04-C2 and WB-14-C2. These flags remain visible and are not relabelled PASS. Manual semantic review found they score whether the testing Skill detects, reports and classifies application deviations, rather than scoring the raw application outcome. No formal case or Builder output was edited to suppress the flags.
- Official independent archived-output validation: run [44968128127](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127), Artifact 14732232796: PASS, 1 dataset, 15 cases, 0 schema errors, 61 source evidence references verified; 18/18 public Builder input files and hashes verified. The validator created or modified zero formal cases.
- A separate Builder-output validation performed in the replay preparation and preserved in the final WB-12 archive also passed with the same 1 dataset / 15 cases / 0 schema errors / 61 source references.
- The manifest quality state remains needs_info; execution status remains NOT_RUN. The known BR-09 request-failure / error-recovery evidence gap remains unresolved.

### Trial provenance and final Gold Oracle

- WB-02 and WB-10 completed successfully in replay run [44980451933](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44980451933), Artifacts 14738085222 and 14738140416. Their complete archived file trees are byte-identical to the copies included in the final WB-12 evidence archive.
- WB-12 in that replay was quota-blocked and did not complete. Its failed early attempt and the early Oracle failure are historical only; they are not presented as a successful execution.
- The one-time targeted WB-12 completion used the frozen Builder dataset, with DeepSeek solely for the actual Skill evaluation: run [45189512695](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45189512695), Artifact 14824967038. The execution completed, recorded exactly one allowed DELETE to the Builder-declared target (HTTP 200), and recorded no retries or unrelated mutations.
- The final artifact includes all three pilot evidence packages and the final independent Oracle adjudication. Gold Oracle result: **WB-02 PASS, WB-10 PASS, WB-12 PASS; aggregate 3/3 PASS, 0 FAIL, 0 UNKNOWN**. WB-02's business verdict is EXPECTED_VIOLATION_DETECTED, not an application PASS.
- The four key Builder output files (wb-core.jsonl, source-map.json, wb-core.manifest.json, SUITE-MANIFEST.json) have identical SHA-256 values in the original Builder artifact, replay preparation archive, and final pilot / Oracle archive. The exact digests and workflow / artifact IDs are recorded in [round4-evidence-index.json](round4-evidence-index.json).

### Skill package tree equivalence

The Builder-run package commit, PR #38 current head and PR #42 release candidate contain the same complete skills/evaluation-dataset-builder/ Git tree. The current release verifier independently compares all package paths, modes, object types and blob SHAs across those three commits. It no longer incorrectly requires historic Builder production, independent validation, pilots and final Oracle adjudication to share a single Actions workflow run or the newest documentation-only PR #38 SHA.

### Release-candidate behavior evaluation

- Evidence-repair prompt fix commit: 6868d38efd8a29b9b153dd5e70040382e296f8d9.
- Exact code-candidate behavior evaluation run [45287365898](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45287365898), Artifact 14872207908: two runs, 57/57 Skill checks PASS each, 40/40 Trigger classifications correct, baseline complete, 0 UNKNOWN, stability spread 0 pp, automated gates PASS.
- The matched baseline contains one genuine Run-2 FAIL in SE07 (6 original cases versus 4 after deduplication, without explaining the reduction); it remains FAIL and the mean uplift is +0.88 percentage points.
- The report records 390,834 total tokens and estimated actual cost USD 0.222123; 176 responses were resumed from the preceding checkpoint.
- The documentation/evidence-index refresh changes the PR head but not Skill text or evaluation inputs. An exact-head evaluation is required after that commit; the workflow is configured for explicit compatible checkpoint reuse. Only the resulting report Artifact whose git_sha matches the final PR head is current release evidence.

### Final gate boundary

No Builder regeneration, independent-validator rerun, WB-02/WB-10 rerun, WB-12 rerun beyond its completed targeted attempt, or Oracle rerun is justified by documentation-only SHA changes. PR #42 and PR #38 remain Draft/Open. No merge, Tag, Release or publication has occurred. Explicit user approval remains required before the post-review merge and publish steps.
