# Next Builder trial decision: WB-CORE-03

**Date:** 2026-11-21  
**Decision status:** Recommended next candidate; execution not authorized.  
**Evaluation target:** Evaluation Dataset Builder output quality, not target Skill quality.

## Preconditions verified

- Formal Builder artifact: workflow run 44726278657, artifact 14624897819; frozen case JSONL SHA-256 `0a1f549af5adbb790b134e7b740750b58b86845583acb7bea4e21131753271c1`.
- Independent validation of formal Builder output: PASS (previously recorded).
- Static baseline review for six selected cases: no material Builder defect identified; WB-CORE-03 has source-backed, concrete query and expected result, and is distinct from title-search Pilot WB-CORE-02.
- Exact source quotation cross-check for selected tranche: 19/19 PASS.
- Latest PR #38 CI at HEAD `3a3c23baed52314be81bc8c5717666c3e3e479ce`: PASS, run 44887663749. Paid jobs skipped.
- PR #38 remains Draft/Open/unmerged.

## Why WB-CORE-03 is the best next probe

1. **Incremental Builder evidence:** It tests a generated contract for matching the search term in the task description, distinct from the already executed title-search case. This gives information about Builder case decomposition and specification fidelity, not merely a new target Skill behavior.
2. **Low operational side-effect risk:** The case is read-only; it should not create, update, or delete data.
3. **Focused evidence question:** Can the generated case's requirements and evidence contract discriminate a correct description-only match from title-only or irrelevant matches, while demonstrating no mutations and preserving summary counts?
4. **Static review already done:** A paid run would not merely reveal an obvious static omission. Remaining uncertainty concerns real executability, evidence attainability, trace/evidence alignment, and adjudicability.

## What a single execution could and could not establish

**Could add Builder-quality evidence:** whether the generated steps/criteria are sufficiently precise and executable; whether the evidence contract supports all important assertions; whether PASS/FAIL/UNKNOWN can be adjudicated without relying on target self-report; whether the case is appropriately discriminative and proportionate.

**Cannot establish:** general Builder quality, reliability, coverage of all source rules, or target Skill quality from a single case. A target Skill PASS is not a Builder-quality finding by itself.

## Decision rule after the run

Do not automatically proceed to WB-CORE-05. First record the actual Runner verdict and independent Oracle verdict; review required evidence and source provenance; adjudicate Builder-specific dimensions; record wall time, step and token telemetry, and provider billing if available. Provider cost remains UNKNOWN without billing evidence.

Continue only if the run produces complete, attributable evidence and useful information about Builder quality, and the marginal expected information from the next case remains worth its incremental cost. Stop on BLOCKED/FAIL/UNKNOWN, evidence integrity or attribution problems, budget limit, unexpected side effect, or lack of Builder-specific information. No case repairs, retries, or substitutions.

## Authorization boundary

WB-CORE-03 remains NOT_RUN. This memo is a recommendation, not authorization. No DSH/model call is initiated by this commit. User approval is required before the paid single-case execution.
