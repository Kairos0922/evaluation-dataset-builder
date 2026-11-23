# 0.0.1 Candidate Behavior Evaluation Report

Date: 2026-11-24

## Evaluated code candidate binding

- Release PR: #42, release/0.0.1-candidate
- Evaluated code candidate SHA: 6868d38efd8a29b9b153dd5e70040382e296f8d9
- CI run: [45287379185](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45287379185) — PASS
- Behavioral evaluation run: [45287365898](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45287365898) — completed successfully
- Artifact: candidate-evaluation-report-45287365898, ID 14872207908
- Artifact ZIP SHA-256: 6dc98ffc5c9d6b83e9d065236e8eac706972d073f506a001f460cc8e2a54b054
- Report git_sha: exact match to the evaluated code candidate SHA
- release_approved: false

This report records the completed evaluation of the code candidate before the final documentation and release-evidence-index refresh. The final documentation commit is a new candidate SHA and must have its own exact-head Actions report. The report artifact produced on that final head is the release authority; this historical report must not be substituted for it.

## Results

| Metric | Run 1 | Run 2 | Mean / final |
|---|---:|---:|---:|
| Skill behavior checks passed | 57/57 | 57/57 | 57/57 per run |
| Skill behavior pass rate | 100.00% | 100.00% | 100.00% |
| Matched baseline checks passed | 57/57 | 56/57 | 56.5/57 |
| Matched baseline pass rate | 100.00% | 98.25% | 99.12% |
| Uplift over matched baseline | 0.00 pp | +1.75 pp | +0.88 pp |
| Trigger TP / FP / FN / TN | 20/0/0/20 | 20/0/0/20 | 40/40 correct |
| Trigger precision | 100% | 100% | 100% |
| Trigger recall | 100% | 100% | 100% |
| Skill / baseline UNKNOWN | 0 / 0 | 0 / 0 | 0 |

- Behavior pass threshold: 90% per complete run — **PASS both runs**.
- Trigger precision and recall thresholds: 95% — **PASS both runs**.
- Trigger suite: 40 cases (20 positive, 20 negative), no parse errors — **PASS**.
- Baseline comparison: complete on both runs; every baseline check has an explicit PASS or FAIL disposition — **PASS**.
- Stability: behavior, trigger precision and trigger recall spreads are all 0 percentage points — **PASS**.
- Automated evaluation gates — **PASS**.

## Explicit case-level baseline miss

Run 2 has one baseline FAIL in **SE07 semantic deduplication**. The baseline output reported 4 unique cases but omitted the original case count of 6 and did not explain why semantic deduplication did not inflate the count. This is a genuine baseline miss and remains FAIL in the report. It is not an UNKNOWN, not hidden, and not upgraded to PASS.

The candidate Skill passed all 57/57 behavior checks in both runs. The SE07 baseline failure contributes to the matched baseline comparison and the reported uplift; it does not invalidate the predeclared per-run 90% behavior threshold.

## Model configuration, usage and scope

- Generator, Judge and Trigger Classifier: DeepSeek V4.1 Flash, API model ID deepseek-flash.
- Same model identity across separate roles. No cross-model independent Judge claim is made.
- Two complete runs, 199 distinct API responses recorded by the report; 390,834 total tokens.
- Estimated actual peak-price cost: USD 0.222123; configured protection ceiling: USD 10.
- Checkpoint reuse: 176 responses were resumed from the prior failed-evaluation checkpoint after the evidence-repair change; no pending or uncertain request remains.
- Evaluation scope: SKILL_ENTRYPOINT_TEXT_PROXY; loaded SKILL.md only, not references/*.
- This does not verify host-specific Skill discovery, reference loading, tool invocation or runtime compatibility.

## Evidence repair

The prior exact-head evaluation was blocked because baseline SE03 and SE08 received unsupported Judge PASS claims without locally verifiable quotes. Review of the archived output showed that the evidence-repair prompt was not explicit enough about preserving Markdown delimiters. The repair prompt was changed to require character-for-character quotation, including **, __, backticks, table pipes, list markers and punctuation; it now also provides the prior Judge rationale as context, never as evidence. A new offline regression test covers a quote containing Markdown formatting. The runner still verifies every quote locally and still fails closed when a quote cannot be verified.

## Final-head binding and release disposition

The final release-evidence refresh also synchronized `references/grader-guidelines.md` byte-for-byte with the Builder-run package. This changes one installable reference file, but the behavior evaluator's declared scope loads `SKILL.md` only and does not load `references/*`; the evaluated input therefore remains unchanged. The behavior workflow uses an explicit compatible checkpoint, and the final-head run must still report the exact PR head SHA.

The release verifier enforces both report.git_sha == PR #42 head SHA and report.workflow_run_id == Actions run ID, validates the complete report, and rejects stale artifacts. A historical report or a successful run on an earlier SHA is not sufficient.

**Evaluated code candidate behavior gate: PASS. Overall release: NOT APPROVED.** The final documentation-head exact-SHA result is the attached Actions artifact for the final PR head. No merge, Tag or GitHub Release is created by this report.
