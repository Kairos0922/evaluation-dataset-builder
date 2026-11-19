# WB-C10 Trial Readiness Note

**Date:** 2026-11-19  
**Source:** Builder run #1039 archived case WB-C10 (immutable)  
**Status:** Ready for controlled execution, subject to explicit authorization for model/Skill trial. No execution performed.

## Scope

WB-C10 tests request failure feedback and recovery (BR-09):
- Inject one failure for browser-originated `POST /api/tasks`.
- Submit `Failure Path Check`.
- Verify visible error, no success message, no new task, and unchanged task count/summary.
- Remove interception and submit the same title again.
- Verify successful creation, new task ID, Open state, and summary `6/3/2/1`.

The source case is candidate and NOT_RUN. This note does not alter it.

## Execution protocol clarification

The case's primary user instruction specifies a controlled HTTP 500 JSON response with:
`error: Simulated save failure`.

Its acceptable-variants section also permits `route.abort()`, which is a network-failure path and is not equivalent to a server HTTP 500 response.

For a reproducible trial:
1. Use the specified HTTP 500 JSON response as the primary route.
2. Record the intercepted method, URL, response status, response body, and whether the route was triggered exactly once.
3. Submit through the real page form, not an API-only shortcut.
4. Capture visible error text and verify no success message.
5. Verify task rows, task data, and summary remain unchanged after the failure. Record initial and post-failure snapshots.
6. Remove the route before retry; record that it is no longer active.
7. Submit the same title through the page form and verify the task ID, title, Open status, and summary.
8. Preserve failure/recovery screenshots and trace. Include console/page errors, but distinguish expected injected error from unrelated errors.

If HTTP 500 injection is unavailable, do not silently substitute `route.abort()`. Report an environment limitation or obtain approval for a separately identified network-failure variant.

## Evidence checklist

- [ ] Initial task count, task list, and summary (5/2/2/1)
- [ ] Route definition and intercepted request evidence
- [ ] HTTP 500 response and JSON error body
- [ ] Failure submission screenshot
- [ ] Visible error message
- [ ] No success message
- [ ] Post-failure task list/count and summary unchanged
- [ ] Interceptor removed evidence
- [ ] Recovery submission screenshot
- [ ] Created task ID/title/status
- [ ] Post-recovery summary (6/3/2/1)
- [ ] Final VERDICT consistent with observations
- [ ] Trace and runner completion artifacts

## Boundaries

Do not call reset from the target Skill. Do not start, stop, or restart the app. Do not edit the application, bypass validation, or access external systems. The runner's initial reset is part of environment preparation, not a Skill action.

## Decision

The case has a clear, observable failure/recovery contract and is a strong next trial candidate. It is not yet executed. No model call was made in this readiness review. Dataset status remains candidate; this note does not approve a quality gate or introduce thresholds.
