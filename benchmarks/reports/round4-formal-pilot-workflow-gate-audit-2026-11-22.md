# Round 4 formal pilot workflow gate audit (2026-11-22)

## Scope and decision

This review covers the formal replay workflow, semantic pilot matrix, Runner invocation, independent Gold Oracle, and archived-evidence re-adjudication path at the current branch head. It is a static contract audit plus existing CI/self-test evidence. **No DSH/model invocation or pilot was started.**

Decision: the three-case Round 4 workflow is structurally aligned and can proceed to an explicit execution decision, but it is not yet a live-execution guarantee. Keep the pilots NOT RUN until the residual risks below are consciously accepted.

## Verified alignment

1. `.github/workflows/replay-webapp-testing.yml` revalidates the downloaded original Builder output before resolving the matrix. It verifies Builder DSH trace completion, at least one actual Builder Skill call, a clean credential scan, the input bundle, and the Builder output.
2. The workflow requires exactly three distinct cases and the semantic roles `search_mutation`, `state_cycle`, and `delete_confirmation`. It requires the search case to use the `search-case-sensitive` mutant and the other two cases to use the clean fixture.
3. The Runner receives the exact case and dataset identifiers from the matrix. Its DSH timeout is capped by the Builder-declared case timeout. Model-step and token ceilings remain 32 / 60,000 input / 55,000 output / 1,600,000 cache-read / 1,750,000 total.
4. `benchmarks/webapp-testing/scripts/gold_oracle.py` accepts the same three roles, loads the Builder-authored case by case ID and dataset ID, and derives expected behavior from that case. It verifies evidence manifests, DSH trace/session evidence, server audit, state snapshots and target Skill reports.
5. The Oracle report explicitly limits its conclusion to the three selected cases; it does not claim full-suite quality or release approval.
6. The archived re-adjudication workflow downloads the original Builder artifact and exact case-specific pilot artifacts, then re-runs the independent Oracle without repeating target calls. Oracle FAIL/UNKNOWN remains visible in the JSON verdict; workflow success only means adjudication completed.

## Residual risks

- The workflow's matrix and output-token ceilings are static configuration. They do not establish that a live run will finish within the cap. Round 3 already demonstrated an output-token overrun.
- The delete test is a real side effect within a disposable fixture. The Oracle can detect an incorrect target after the action, but cannot prevent the target Skill from clicking the wrong delete button. Preserve fixture isolation and treat any unexpected DELETE as a hard failure.
- The replay workflow can be manually dispatched with a Builder run ID. Operators must supply the verified Round 4 Builder run `44959366258`, not a stale run, and retain the Round 4 official validator evidence `44968128127`. The workflow revalidates the output itself, but the operator must still preserve exact artifact provenance in the final report.
- A passing workflow is not a passing pilot. The independent Oracle's JSON status and each case verdict are authoritative.
- Screenshot presence is machine-checked; semantic screenshot review remains a human review item.
- The audit does not establish live DSH token telemetry completeness, actual target-Skill behavior, or the absence of runtime-specific failures.

## Execution decision checklist

Before any paid pilot:
- [ ] Confirm source Builder run `44959366258` and immutable artifact `14729741906`.
- [ ] Confirm official Round 4 independent validation run `44968128127` remains PASS and is bound to that artifact.
- [ ] Use only the three resolved Round 4 case IDs and fixture profiles; do not hand-author or alter cases.
- [ ] Execute sequentially with no retries and stop immediately on missing usage telemetry, budget overrun, unexpected write, wrong deletion target, or incomplete trace.
- [ ] Archive all three case artifacts and run the independent Oracle on the exact archived output.
- [ ] Review screenshots and adjudication evidence manually before drawing conclusions.

No Builder output, formal case, assertion, budget, or safety requirement was modified. PR #38 must remain Draft/Open and unmerged.
