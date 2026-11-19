# Historical UNKNOWN evidence audit

Date: 2026-11-19

## Scope

Offline inspection of the original evaluation artifact from workflow run `44180925415` (candidate SHA `6c0c1942d2d83c6157b5a5debd33940b3cb7c55`). No model calls were made.

Files inspected:
- `eval-report.json`
- `eval-checkpoint.json`

## Findings

The report has four UNKNOWN criteria across three case instances:

| Run | Case | Criterion | Audit finding |
|---|---|---|---|
| 1 | SE12 | Records old/new SLA versions, P1 change, unchanged P3, source ID, effective date | Cached repair evidence contains exact matching candidate-output excerpts |
| 1 | SE12 | Identifies impacted and unchanged cases | Cached repair evidence contains exact matching candidate-output excerpts |
| 2 | SE04 | Records both source IDs, versions, and conflicting clauses | Cached repair evidence contains exact matching candidate-output excerpts |
| 2 | SE05 | Defines observable evidence, pass/fail, variants, and UNKNOWN handling | Cached repair evidence contains exact matching candidate-output excerpts |

For each criterion, one or more cached repair responses contain quotes that exactly match the candidate output. This supports the conclusion that the current evidence-repair implementation can salvage valid exact quotations even when the response over-returns.

## Non-upgradable failures

- Run 2 SE01 remains a genuine FAIL: source rule IDs/provenance for expected outcomes are reported absent.
- Run 1 SE10 remains a genuine FAIL: unsupported cases are not adequately labeled as needs_info/synthetic rather than approved.

Neither failure is eligible for evidence-only upgrade.

## Provenance limitation

The checkpoint stores responses keyed by request hash, but this artifact does not store the original request payloads alongside each cached response. Therefore this audit cannot conclusively bind every repair response to a specific case/check criterion. The exact quote matches are diagnostic evidence only; they are not official PASS results or a formal replay.

## Recommendation

Do not spend API budget on a new full evaluation until this offline audit is documented and the candidate CI is green. After that, a fresh exact-SHA evaluation remains necessary for release evidence because the historical report is bound to an older SHA and has genuine FAILs, incomplete evaluability, and incomplete baseline evidence.
