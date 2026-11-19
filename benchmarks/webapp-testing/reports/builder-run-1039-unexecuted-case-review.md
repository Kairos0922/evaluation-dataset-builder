# Builder Run #1039: Static review of unexecuted cases

**Review date:** 2026-11-19  
**Source:** immutable Builder output from run [44335613629](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44335613629)  
**Reviewed scope:** all 12 cases without archived trial evidence. This is a static case-design review only. No case was executed, no Builder run was repeated, and no model call was made.

## 1. Purpose and limits

This review identifies distinct coverage value, execution risk, overlap, and possible ambiguity in the 12 unexecuted cases. It does not introduce a numeric score, weights, or pass thresholds. It does not estimate dataset quality or target-Skill performance.

All 12 cases remain `candidate` and `NOT_RUN`. A favorable static review is not execution evidence.

## 2. Case-by-case review

| Case | Focus | Distinct evidence value | Static concern / overlap | Execution complexity | Recommendation |
|---|---|---|---|---|---|
| WB-C01 | Read-only initial summary/task consistency | Baseline read-only verification; checks summary against task rows | Low overlap with C07/C09 but A02/A04 also assert summary consistency. | Low; read-only | Useful low-risk baseline, but not the highest marginal coverage after integration cases. |
| WB-C03 | All status filters | Complete branch coverage for Open/In progress/Done/All | A01 and A04 also exercise filter behavior. | Low | Good deterministic case; reserve if filter-specific coverage is desired. |
| WB-C04 | Trim, 80-char boundary, 81-char rejection | Boundary and form-validation behavior | A03 substantially overlaps; A03 also includes empty and whitespace-only inputs. The expected 81-char behavior allows either rejection or maxlength truncation, so evidence must establish which occurred. | Medium; multiple form submissions and boundary data | Strong atomic boundary case; preferable to A03 for focused boundary diagnosis. |
| WB-C05 | Priority choices/default | Options, default value, and explicit High selection | Limited overlap with create cases, but create-task workflows recur elsewhere. | Low | Low-cost, distinct rule coverage. |
| WB-C06 | Two creates, unique IDs, Open initial state, summary | Create semantics and uniqueness | A02/A04 also create tasks and inspect summary; C04/C05/C10 create tasks for their own objectives. | Low-medium | Important atomic create case; avoid duplicating create checks when running integration cases. |
| WB-C08 | Delete confirmation Cancel branch | Non-destructive cancellation and confirmation dialog | Complementary to C09; no direct duplication. | Low | High-value safety complement to already executed destructive confirmation C09. |
| WB-C10 | HTTP 500 create failure, error visibility, no mutation, retry recovery | Error handling, absence of false success, recovery after route unblocking | C11 also intercepts POST failure to test status messaging. Keep C10 focused on behavior/state recovery, not accessibility semantics. | Medium; route interception plus retry | High distinct coverage; a strong next candidate. |
| WB-C11 | Accessible roles/names and error status messaging | Semantic locators and accessible naming across controls | A4 includes filter/accessibility-adjacent interaction. Error-message part overlaps C10; its qualitative “understandable name” criterion could be subjective. | Medium; role/name inventory and intercepted request | Review/clarify observable name expectations before execution; retain separate from C10. |
| WB-A01 | Search mutation audit plus search/Open intersection | Cross-query discrepancy and combined-filter interaction | Significant overlap with executed C02. Adds the search/Open intersection. | Low-medium | Lower marginal value immediately after C02; run only if combined filter coverage is needed. |
| WB-A02 | Create, state transition, delete, reload, summary audit | Multi-step cross-feature consistency and reload behavior | Overlaps C06/C07/C09 and A04; stronger integration interaction than atomic cases. | High; multi-step mutation and reload | Valuable integration case after focused create/error cases; avoid redundant pilot selection. |
| WB-A03 | Whitespace/empty/81-char invalid-title audit | Invalid input and false-success detection | Significant overlap with C04; also overlaps C10's failure/error-message contract. | Medium | Prefer C04 for focused boundary testing, or A03 only if empty/whitespace cases are specifically needed. |
| WB-A04 | Create/status/delete/reload/filter/empty-state audit | Broad state, reload, filter and empty-state integration | Strong overlap with A02 and C03/C06/C07/C09; most broad and longest case. | High | Defer until atomic behaviors are understood; high value for later integration, not the next low-cost trial. |

## 3. Overlap map

- **Search:** C02 (already executed) ↔ A01. A01 adds the Open + review intersection, but repeats core case-insensitive and description search checks.
- **Summary/create/state/delete/reload integration:** A02 ↔ A04. A04 adds filter and empty-state checks; both repeat create, status, delete and reload consistency.
- **Title boundaries/invalid input:** C04 ↔ A03. A03 adds empty and whitespace-only input; C04 isolates trim and 80/81 boundary behavior.
- **Create semantics:** C06 overlaps with the setup/actions of C04/C05/C10 and integration cases, but uniquely checks two distinct IDs and initial Open state.
- **Request failure:** C10 ↔ C11. C10 focuses failure state and recovery; C11 focuses semantic names and status-region accessibility.
- **Delete confirmation:** C08 ↔ executed C09. These are complementary branches, not duplicates: Cancel must preserve state; confirmation must delete.

Overlap is not automatically a defect. It may support triangulation, but repeated checks should be justified by distinct expected evidence, not merely repeated action sequences.

## 4. Risk-led next-case candidates

Without numerical weighting, the following candidates offer distinct evidence beyond the three executed pilots:

1. **WB-C10 — request failure and recovery.** Tests error path, no false-success state, no data mutation on failure, and recovery on retry.
2. **WB-C04 — title trim and 80/81-character boundary.** Isolates boundary validation with clear observable outcomes.
3. **WB-C08 — Delete Cancel.** Complements C09 and tests destructive-action safety.
4. **WB-C11 — accessibility/semantic locators.** Before execution, make qualitative name criteria observable and separate the error-message requirement from C10.
5. **WB-C06 — create uniqueness/initial state.** Focused create semantics not covered by the existing pilots.

This is a qualitative sequence for consideration, not a statistically optimal sample and not approval to spend on model calls.

## 5. Execution design cautions

- Keep one isolated app process/session per case; the runner's reset occurs before the case. The Skill must never reset.
- Preserve immutable artifacts: trace, screenshots, report, event logs and runner outcome.
- For C10/C11, verify interception scope is exact (POST `/api/tasks`), remove interception before retry, and independently verify no task/summary mutation after the failed request.
- For C04, record whether 81 characters are rejected or truncated by browser maxlength. Do not use JavaScript to bypass the form.
- For C08, record dialog visibility and task/summary state both before and after Cancel.
- For C11, prefer role/name/label evidence and define the exact expected name strings already stated in the case. Avoid subjective judgments without evidence.
- Do not run A02 and A04 back-to-back as if they were independent coverage without accounting for overlap.
- Keep the dataset status `candidate`; no arbitrary pass rate or threshold is introduced.

## 6. Conclusion

The 12 unexecuted cases are generally differentiated by their declared objectives, but the set contains intentional and substantial overlap among search, create, boundary/error, and integration scenarios. The highest marginal next evidence appears to be error recovery (C10), focused boundary validation (C04), and the non-destructive delete branch (C08). Broad integration cases A02/A04 should follow focused case evidence rather than be treated as substitutes for it.

This review is static. It does not change case definitions, execution status, or quality status.
