# Builder Run #1039: Post-production dataset quality review

**Review date:** 2026-11-19  
**Source Builder run:** [#1039 / Actions run 44335613629](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44335613629)  
**Dataset:** `wb-workboard`, suite `webapp-testing-workboard-lite-suite` v1.0.0  
**Review scope:** archived Builder output, independent Validator, three pilot artifacts and Oracle adjudication. No formal cases were modified.

## 1. Decision

**Quality status: candidate. Execution evidence: 3 of 15 cases.**

Suitable for continued controlled evaluation, but not enough evidence to mark `validated` or `approved`. No new Builder production or paid target-Skill call was performed for this review.

## 2. Source and integrity evidence

| Check | Result | Interpretation |
|---|---|---|
| Builder DSH invocation | PASS, exit 0; 847 events; 1 Builder Skill call | Production invocation evidenced |
| Dataset count | 1 | `wb-workboard` |
| Generated cases | 15 | All `candidate` |
| Independent Validator | PASS | Structural, provenance and coverage scope |
| Schema errors | 0 | Schema validation passed |
| Source evidence references | 75/75 verified | Source map, source hashes and exact normalized quotes checked |
| Coverage | 45/45 applicable items covered | Four other items marked not applicable |
| Manifest execution status | `NOT_RUN` | Original production-time state; later pilots are separate |
| Unresolved authority gaps / needs_info | 0 / 0 | Does not mean independent approval |

The Validator's `quality_status_gate: candidate/needs_info` is a permitted-state gate. The actual archived dataset status is `candidate`, with 0 `needs_info` cases.

## 3. Case inventory

| Case | Focus | Status |
|---|---|---|
| WB-C01 | Initial summary and task set | candidate, not executed |
| WB-C02 | Case-insensitive title/description search | candidate, **pilot executed** |
| WB-C03 | Status filters | candidate, not executed |
| WB-C04 | Whitespace and 80/81-character title boundaries | candidate, not executed |
| WB-C05 | Priority options/default | candidate, not executed |
| WB-C06 | Create IDs, initial state and summary | candidate, not executed |
| WB-C07 | Status cycle and summary sync | candidate, **pilot executed** |
| WB-C08 | Delete confirmation Cancel branch | candidate, not executed |
| WB-C09 | Confirmed deletion and summary sync | candidate, **pilot executed** |
| WB-C10 | Failed request, visible error and recovery | candidate, not executed |
| WB-C11 | Accessible names/roles and error message | candidate, not executed |
| WB-A01 | Search discrepancy audit and combined filter | candidate, not executed |
| WB-A02 | Summary across create/state/delete/reload | candidate, not executed |
| WB-A03 | Invalid-title acceptance audit | candidate, not executed |
| WB-A04 | Reload consistency, filter and empty state | candidate, not executed |

The three pilots were selected by semantic role (search mutation, state cycle, delete confirmation), not randomly or statistically.

## 4. Pilot evidence

| Case | Fixture | Observed | Case adjudication |
|---|---|---|---|
| WB-C02 | Mutant: case-sensitive search | `reset`, `RESET`, `CSV` returned empty results; Skill reported the BR-02 defect with evidence | PASS: expected violation detected |
| WB-C07 | Clean | WB-101 Open → In progress → Done → Open; summary synchronized | PASS |
| WB-C09 | Clean | Confirmation dialog; WB-103 removed; remaining 4 tasks and summary 4/2/2/0 correct | PASS |

All three runner artifacts show successful DSH invocation, completed session, browser evidence and runner completion. The archived Oracle adjudication reports 3/3 PASS, 0 FAIL, 0 UNKNOWN.

Application verdict and Skill-case verdict are distinct: C02's application behavior was defective, but the Skill correctly detected it, so the case adjudication was PASS.

## 5. Quality review observations

### Strengths evidenced

- Cases define observable actions, expected state, reporting requirements and prohibited side effects.
- Source evidence is traceable to archived Builder inputs and exact quotes.
- Case families include normal, boundary/negative, recovery and discrepancy audits.
- C02 tests defect detection on a mutant fixture.
- C07 and C09 have concrete state-transition and destructive-action evidence.

### Limits and risks

1. **Execution coverage:** 12/15 remain unexecuted. Static validity does not establish feasibility or target performance on those cases.
2. **Sampling:** three role-selected cases provide feasibility evidence, not a statistical estimate of dataset quality or model performance.
3. **Coverage interpretation:** 45/45 is coverage against Builder-defined applicable tags. It is not importance-weighted, empirically calibrated or proof of coverage depth.
4. **Synthetic environment:** Workboard Lite and its rules/fixtures are synthetic; transfer to production applications is unknown.
5. **Accessibility scope:** BR-10 checks accessible names/roles and error-message visibility. It is not a manual or standards-conformance audit.
6. **Not-applicable categories:** permission/security, multi-turn, adversarial and other are marked not applicable; this review does not claim these were tested.
7. **Oracle correction and replay:** C09's Oracle check was corrected so a report need not mention Cancel when the Builder case asks only for the confirmation/Delete path. The corrected Oracle was run against all three original, immutable pilot artifacts in GitHub Actions run [#44499350929](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44499350929). Result: **3/3 PASS, 0 FAIL, 0 UNKNOWN**. The replay did not run DSH, invoke the target Skill, or create/modify formal cases. The corrected report artifact is `14516781143`.

## 6. Recommendations

No score, weighting or threshold is introduced.

- Preserve the Builder output and trial artifacts as immutable evidence.
- Keep quality status `candidate`.
- If broader confidence is needed, choose the next cases based on risk and currently untested behavior rather than maximizing the run count. Consider search/filter, boundary validation, failed requests and accessibility, with explicit cost approval before model calls.
- Keep the corrected Oracle replay report as a separate immutable audit artifact.
- Do not merge PR #38 or mark the dataset approved based on this report.

## 7. Artifact references

- Builder result: `14442058992`
- Independent validation: `14441729812`
- Pilot C02: `14443662364`; C07: `14444955906`; C09: `14443239921`
- Historical Oracle replay: `14478179215` (original adjudication)
- Corrected Oracle replay run: [#44499350929](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/44499350929)
- Corrected Oracle replay artifact: `14516781143`
- Corrected Oracle code: [commit 6850010](https://github.com/Kairos0922/evaluation-dataset-builder/commit/6850010b669040649560c30329a0a5c6e9ec3d80)
