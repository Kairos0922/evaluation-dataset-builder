# Round 4 Builder validation and pilot feasibility review (2026-11-22)

## Decision

Round 4 formal Builder output has passed the official independent validator against the exact Round 4 artifact. The deterministic selector has resolved three distinct Builder-authored candidates. No Skill Pilot was started in this review. The next action is a controlled feasibility decision for the three selected cases; this report does not authorize additional retries or alter the immutable Builder output.

## Exact artifact identity

- Builder production workflow: [44959366258](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44959366258)
- Builder artifact ID: `14729741906`
- Artifact ZIP SHA-256: `df1b4916aa31bdd46af8700c5d4c036a39aa6b35cf84bc8e3311fe3f44848a2c`
- Builder DSH exit: 0
- Actual Builder Skill calls: 1
- DSH trace: PASS, 530 events
- Formal output: 1 dataset, 15 cases
- Frozen input: 18 files, all 18 SHA-256 verified; six pinned upstream Skill files
- Frozen package manifest SHA-256: `b87a14a0b60d992eeeaacba431e8cab1679d2d1212d1174acbd1cbed12700d97`

## Independent validation

- Correctly bound archived validation workflow: [44968128127](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127)
- Validator code and selector head at validation: `adbbc64af4dba5bd6291ce72e06c31222c11bfd7`
- Independent validation artifact: `14732232796`
- Official status: PASS
- Schema errors: 0
- Source evidence references verified: 61
- Dataset count: 1
- Case count: 15
- Manifest quality status: `needs_info`
- Execution status: `NOT_RUN`
- Trace verification: PASS, 530 events, one actual Builder Skill call
- Frozen input verification: PASS, 18/18 files

### Validation binding correction

An earlier validation workflow run [44967917539](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44967917539) used a stale default Builder run ID `44910360571` and therefore validated Round 3, not Round 4. Its PASS must not be attributed to Round 4. The workflow default and all artifact-download references were corrected to `44959366258`. The official Round 4 PASS above is from the subsequent correctly bound run [44968128127](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44968128127).

## Validator correction

- Round 4 initially exposed false positives caused by Chinese subject omission in coordinated phrases such as “Skill 遗漏某项，或报告另一项”.
- Updated the clause parser to preserve the inherited Skill-failure subject across coordinated Chinese object/predicate lists while continuing to split independent clauses.
- Added positive regression cases for WB-03/WB-04/WB-14-style phrases and a negative regression ensuring an independent raw application outcome after a semicolon remains rejected.
- The first parser revision still mishandled adjacent separators; the follow-up fix tracks the previous non-empty delimiter. The final Round 4 official validation passed after that correction.
- The selector also initially missed the Builder-authored delete-confirmation candidate because the visible control was Markdown-backtick quoted. The selector now normalizes inline backticks and has a matching regression test.

## Pilot matrix prepared, not executed

The correctly bound selector run resolved these three unique candidates from the Round 4 Builder output:

| Case | Role | Fixture |
|---|---|---|
| WB-02 | search_mutation | mutant: search-case-sensitive |
| WB-10 | state_cycle | clean |
| WB-12 | delete_confirmation | clean |

No candidate was fabricated or hand-authored. The matrix is archived in artifact `14732232796`. No pilot execution or adjudication is claimed.

## Execution resource contract audit

All 15 Round 4 cases were checked against the Runner hard limits. No mismatch was found.

- Model steps: 32 per case
- Input tokens: 60,000
- Output tokens: 55,000
- Cache-read tokens: 1,600,000
- Total tokens: 1,750,000
- Hard wall-clock cap: 600 seconds
- Retries: 0
- Per-case DSH wall-clock budget equals the declared case timeout

Timeout distribution: 10 cases at 240 seconds, four at 300 seconds, and one at 480 seconds. The three selected candidates have timeouts of 240 seconds (WB-02), 480 seconds (WB-10), and 300 seconds (WB-12).

## Feasibility risk and next gate

The static budget contract passes, but it is not proof that the target Skill can execute within those limits. Round 3 provides direct warning evidence:

- Search pilot C02 consumed 23,448 output tokens and timed out before completing its query assertions because it could not locate the task row.
- State-cycle pilot C06 exceeded the Runner's 55,000 output-token hard cap by 1,145 tokens; the generated script did not execute.
- Delete pilot C08 performed a real deletion against the wrong task, so business behavior failed.

Round 4 narrows the search task and gives the state-cycle case a 480-second timeout, but it retains the 55,000 output-token cap. WB-10 remains the highest resource-risk candidate because it asks for three sequential state transitions and per-step summary verification. WB-12 remains the highest side-effect-risk candidate because a wrong row selection can delete the wrong task. These risks cannot be ruled out by schema validation or static budget-field checks.

Therefore, no Pilot was launched as part of this feasibility review. Before any paid execution, retain the exact three-case matrix, ensure the Runner records output-token consumption and action target identity, and use the already-declared stop conditions. Do not reduce assertions, evidence requirements, or safety constraints to make a case fit.

## Repository status

- PR #38 remains Draft/Open and unmerged.
- No new paid Builder call was made.
- No Skill Pilot was started in this review.
- Round 4 Builder output remains immutable.
