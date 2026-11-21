# Offline Diagnostic Audit of Builder Output

Date: 2026-11-19

## Scope and provenance

This is a diagnostic audit of the actual Builder output captured by the authorized production run. It is **not** the repository's official independent-validator PASS and does not replace that release gate.

- Workflow run: [44554258000](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44554258000)
- Candidate SHA at Builder execution: `74c6485900dd12bdbe2283964e2cd07d8c3270ea`
- Builder artifact: `webapp-testing-builder-result` (artifact ID `14544598567`)
- DSH exit code: 0
- Trace verification: PASS, 665 events, exactly 1 Builder Skill invocation
- Captured files: 9

The artifact was inspected after the locator-only source-map validator fix was committed at `2a5ff3a4332fe9515a81415310f5bfd52b6101c7`.

## Checks performed offline

| Check | Result |
|---|---|
| JSONL parse | PASS |
| Case count | 14 |
| Unique case IDs | 14 |
| Manifest declared count | 14 |
| Dataset manifest count | 14 |
| Required case fields | PASS, all cases |
| Source references | 61 |
| Source IDs resolve to registry | PASS, all references |
| Source type agrees with registry | PASS, all references |
| Source paths safe and mapped | PASS, all references |
| Quoted evidence length and exact source-file match | PASS, 61/61 |
| Source corpus SHA-256 entries | PASS, 18/18 |
| Source map locators | 22, locator-only records are present and expected |
| No malformed or missing evidence detected | PASS |

## Remaining release blockers

- Official independent validator PASS: archived validation workflow [#44564856202](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44564856202), bound to Builder artifact run #44554258000. Evidence artifact [#14551686466](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44564856202/artifacts/14551686466). The validator accepted 14 cases, 0 schema errors, and verified 61 source evidence references against the frozen input.
- The manifest declares `quality_status: needs_info` and `execution_status: NOT_RUN`. This is appropriate and must not be promoted to PASS.
- Three real target-Skill pilot trials and independent Gold Oracle adjudication 3/3 have not been performed.
- No new paid Builder invocation was started.

## Conclusion

This offline diagnostic provides strong evidence that the captured dataset's 14 cases and 61 evidence references are structurally sound and source-verifiable. It does **not** establish official independent-validator PASS, execution readiness, or release approval.


## Pilot matrix preparation (2026-11-19)

The deterministic pilot selector was run against the same Builder-produced 14-case artifact after official independent-validator PASS. It selected exactly three unique Builder-authored candidate cases:

| Case | Pilot role | Fixture profile | Mutation |
|---|---|---|---|
| WB-CORE-02 | search_mutation | mutant | search-case-sensitive |
| WB-CORE-08 | state_cycle | clean | none |
| WB-CORE-10 | delete_confirmation | clean | none |

Selector workflow: [#44565690374](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44565690374), archived evidence artifact [#14551882351](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44565690374/artifacts/14551882351). The selector and validator passed. **No real trials were executed**; the pilot matrix is preparation only and does not satisfy the three-trial gate.
