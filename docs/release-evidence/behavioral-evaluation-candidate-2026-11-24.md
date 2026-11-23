# 0.0.1 Candidate Behavior Evaluation Report

Date: 2026-11-24 (report artifact timestamp: 2026-11-23 17:20:28 UTC)

## Candidate binding

- Release PR: #42, `release/0.0.1-candidate`
- Evaluated candidate SHA: `c3ef8e5c9cfd156cec29ed7d63a803f32bb536ad`
- PR head SHA at evaluation: exact match
- CI run: [45224205930](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45224205930) — PASS
- Behavior evaluation workflow: [45224190260](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/45224190260) — completed successfully
- Artifact: `candidate-evaluation-report-45224190260`, ID `14842388182`
- Artifact SHA-256: `071a6a9ecc39b58c6dd7658e21c44f8de703b586085cb2428063a51bbcf27884`
- Evaluation report Git SHA: `c3ef8e5c9cfd156cec29ed7d63a803f32bb536ad`

## Results

| Metric | Run 1 | Run 2 | Mean / final |
|---|---:|---:|---:|
| Behavior checks passed | 56/57 | 57/57 | 56.5/57 |
| Behavior pass rate | 98.25% | 100.00% | 99.12% |
| Baseline pass rate | 96.49% | 98.25% | 97.37% |
| Uplift over matched baseline | +1.75 pp | +1.75 pp | +1.75 pp |
| Trigger TP / FP / FN / TN | 20/0/0/20 | 20/0/0/20 | 40/40 correct |
| Trigger precision | 100% | 100% | 100% |
| Trigger recall | 100% | 100% | 100% |
| UNKNOWN checks | 0 | 0 | 0 |

- Behavior pass threshold: 90% per complete run — **PASS both runs**.
- Trigger precision and recall thresholds: 95% — **PASS both runs**.
- Trigger suite: 40 cases (20 positive, 20 negative), no parse errors — **PASS**.
- Stability: behavior spread 1.75 percentage points; trigger precision/recall spread 0 — **PASS** against 5 pp maximum.
- Matched baseline comparison complete — **PASS**.
- Automated evaluation gates — **PASS**.
- Evaluator field `release_approved` remains `false`; evaluation passing is not release authorization.

## Case-level observation

Run 1 had one failed criterion in **SE07 semantic deduplication**: the generated output omitted the original case count and did not explain why deduplication did not inflate case count. Run 2 passed SE07. This is a non-critical case-level miss under the existing 90% aggregate threshold, not a hidden all-cases-pass result. No UNKNOWN checks occurred.

## Scope and limitations

- Generator, judge, and trigger classifier: DeepSeek Flash via DeepSeek API.
- Two complete runs, 198 API requests, 387,000 total tokens.
- Conservative peak-price reserved estimate: USD 1.42211; estimated actual peak-price cost: USD 0.224096; configured protection ceiling: USD 10.
- Evaluation scope: `SKILL_ENTRYPOINT_TEXT_PROXY`; loaded `SKILL.md` only. `references/*` were not loaded.
- This evaluates entrypoint text behavior, not host-specific Skill loading or execution. No cross-model independent Judge claim is made.

## Other release evidence

The Round 4 Builder evidence reuse audit establishes package identity with the current Skill/schema tree and reuse of the frozen formal Builder output, independent validation, three real trials, and Gold Oracle 3/3 PASS. The dataset remains `needs_info` for the documented BR-09 request-failure/error-recovery evidence gap; this is recorded as a limitation and does not invalidate the three completed pilot cases.

See [Round 4 evidence reuse audit](round4-evidence-reuse-audit.md).

## Release disposition

**Behavior evaluation gate: PASS. Overall release: NOT YET APPROVED.**

Still required:
1. Review the full release evidence and limitation statement.
2. Obtain explicit release approval.
3. Merge PR #42 only after approval and gate review.
4. Verify PR head and merge commit tree identity.
5. Run the publish workflow with explicit confirmation, after all evidence-binding checks pass.

No tag or GitHub Release was created by this evaluation.
