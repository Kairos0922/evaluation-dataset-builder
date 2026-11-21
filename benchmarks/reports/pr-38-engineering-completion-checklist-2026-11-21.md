# PR #38 Engineering Completion Checklist

**Scope:** `experiment/webapp-testing-contract`  
**Policy:** Keep PR #38 Draft/Open and unmerged. Do not start paid DSH/model execution without explicit user authorization. Do not convert offline/synthetic tests into real Skill-run evidence.

## Work queue and acceptance criteria

| ID | Task | Acceptance criteria | Status |
|---|---|---|---|
| T01 | Reconcile PR, release-gate history, and current head | Current branch/head, required checks, existing artifacts, and execution gates verified from live GitHub state | DONE |
| T02 | Harden evidence-manifest path handling | Reject traversal, absolute/non-canonical paths, symlinks, and resolved paths outside the pilot root; fail closed | DONE |
| T03 | Expand manifest security regression tests | Tests cover traversal, absolute paths, symlink files/directories, duplicate paths, tampering, missing files, and unlisted files | DONE |
| T04 | Harden run-identity correlation | Oracle validates Runner ID, all server audit IDs, trace sidecar ID, trace SHA-256, and trace event count; missing evidence is UNKNOWN, mismatch is FAIL | DONE |
| T05 | Expand run-identity regression tests | Tests cover missing IDs, mixed IDs, malformed sidecars, trace digest mismatch, event-count mismatch, and valid matching evidence | DONE |
| T06 | Audit Runner evidence finalization | Confirm evidence files are finalized before manifest; runner-result excluded intentionally; no overwrite or stale case directory reuse | DONE |
| T07 | Audit fixture isolation and server audit provenance | Each run gets a fresh fixture/log, audit events carry Runner ID, server shuts down, port closes, cleanup is deterministic | DONE (code review; runtime not re-exercised) |
| T08 | Audit workflow safety and paid gates | Ordinary PR CI cannot invoke paid Builder/Skill runs; only explicit opt-in gates can; no automatic retry; main runs are not canceled | DONE |
| T09 | Reconcile experiment docs and execution plan | Documents agree on the accepted three-case pilot, eleven remaining NOT_RUN cases, cost unknowns, and authorization boundary | IN_PROGRESS |
| T10 | Run final exact-head CI and inspect logs | Required jobs pass; test count and Oracle self-test verified from logs; paid jobs remain skipped | TODO |
| T11 | Verify final PR state and evidence | PR remains Draft/Open/unmerged; latest SHA, checks, and artifact status recorded | TODO |
| T12 | Final self-review | No unsupported PASS claims; list completed, blocked/NOT_RUN, and unverified items separately | TODO |

## Explicitly blocked pending user authorization

- Execute any of the eleven remaining real Skill trials. They remain `NOT_RUN`.
- Start another paid Builder production run. The existing Builder artifact already has an official independent-validator PASS; do not regenerate without a material reason and authorization.
- Run any paid DSH/model call, automatic retry, or model-based repair.
- Merge or close PR #38.

## Completion rule

The engineering checklist is complete when all safe repository/code/documentation tasks above are DONE, the exact-head CI passes, and the remaining items are explicitly documented as authorization-blocked or evidence-unverified. This does **not** mean the eleven real trials have passed or the experiment is fully complete.
