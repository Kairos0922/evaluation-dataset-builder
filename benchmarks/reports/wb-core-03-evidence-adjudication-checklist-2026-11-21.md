# WB-CORE-03 execution evidence and adjudication checklist

**Status:** preparation only; NOT_RUN; no execution authorization.  
**Source:** immutable Builder output artifact 14624897819, case WB-CORE-03.  
**Builder-quality objective:** assess the generated case's precision, evidence sufficiency, and adjudicability. Do not use target Skill success/failure alone as a Builder-quality finding.

## Case contract summary

Search query: `token expiry`. Expected sole result: `Reset password flow`, because the query is present only in its description. Expected summary remains All=5, Open=2, In progress=2, Done=1. The Skill must perform a real visible UI search, run one script only, make zero mutations, and not call reset. Case timeout: 180 seconds. Any missing/inconsistent critical evidence or execution failure results in stopping, without retry; verdict UNKNOWN if the evidence cannot resolve the contract.

## Evidence-to-criterion mapping

| Criterion | Required observation | Evidence source | Adjudication caution |
|---|---|---|---|
| C03-EXEC | Visible search field receives query via real input event; request completes; one script execution | Runner invocation log, script stdout/stderr/exit code, browser interaction trace, request record | Agent-produced narrative alone is not proof; a script path is not proof of execution count unless Runner metadata corroborates |
| C03-OBS | Exactly one rendered result, title Reset password flow; its description contains query; no other row | Post-query DOM/snapshot and screenshot | Screenshot/DOM are Skill-collected, not independent browser instrumentation; compare against independent fixture/audit data where available |
| C03-SUMMARY | Summary stays 5/2/2/1 | Post-query DOM/card text and screenshot; fixture state/audit corroboration | Server-side state may corroborate summary invariance, but UI summary must be observed |
| C03-VERDICT | Final PASS/FAIL matches observations | Skill final report, linked evidence | Check conclusion against raw evidence; do not accept unsupported self-assertion |
| C03-EVID | Required pre/post screenshots, DOM, request evidence, console/pageerror, script path and exit code are present | Evidence manifest, files, Runner logs, fixture-server audit | Evidence integrity/hash and provenance; distinguish target-produced artifacts from runner/server evidence |

## Builder-specific questions

1. **Source fidelity:** Does the generated case correctly ground description search in BR-02 and avoid unsupported assertions?
2. **Specification sufficiency:** Does it identify the query, expected result, initial state, and action sequence without hidden assumptions?
3. **Contract coherence:** Is a read-only case correctly constrained to zero mutations, one script execution, no reset, and one isolated initial state?
4. **Grading sufficiency:** Can the criteria distinguish correct description matching from title-only matching, stale results, wrong rows, or false PASS?
5. **Evidence determinacy:** Does the evidence bundle actually prove the description-only nature of the match, result set, summary invariance, and execution count?
6. **Coverage contribution:** Does it provide nonredundant Builder-quality information beyond WB-CORE-02 title search?
7. **Discriminative intent:** Is the test able to detect a plausible implementation that searches titles but not descriptions?
8. **Cost proportionality:** Did this single read-only run yield a concrete Builder-quality finding commensurate with measured wall time, steps, tokens, and provider billing (if available)?

## Attribution rules

- Skill PASS is not evidence that Builder output is high quality by itself.
- Skill FAIL is not automatically a Builder defect. A failure may be target behavior, environmental issue, or a generated-contract issue; classify with evidence.
- A Runner/fixture/Oracle issue is infrastructure evidence, not Builder-quality evidence.
- If independent server audit does not record search request/query/result details, mark the corresponding independent evidence unavailable. Do not substitute Skill-generated DOM/screenshot for independent instrumentation.
- Provider USD cost is UNKNOWN without billing evidence. Trace token usage is not a billed-cost figure.
- Do not repair the case, repeat the script, reset the app, or substitute a different case.

## Outcome record template

- Runner verdict:
- Independent Oracle verdict:
- Builder-specific adjudication: ADEQUATE_FOR_THIS_CASE / BUILDER_DEFECT_FOUND / INCONCLUSIVE
- Findings and exact evidence references:
- Source-fidelity issue:
- Specification/contract issue:
- Grading issue:
- Evidence-determinacy issue:
- Coverage/discrimination contribution:
- Measured elapsed time:
- Model step count:
- Token telemetry:
- Provider billing evidence:
- Builder benefit/cost judgment:
- Decision on WB-CORE-05 (continue / stop / defer) and rationale:
