# Offline IDA Controlled-Mutation Validation

**Status:** Engineering sensitivity experiment passed; semantic validation remains externally blocked.  
**Run:** GitHub Actions #2011, commit 9cb0e46cd78193a9419929f90c73817a0ac511c3.  
**Evidence level:** SYNTHETIC_CONTROLLED_MUTATION.

## Protocol

The runner creates a frozen two-case synthetic dataset and applies the eight deterministic operators in defect-mutation-catalog.yaml. For each mutation it:
1. writes a fresh manifest, JSONL and source registry;
2. executes the production offline IDA assessor;
3. validates the resulting IDA report against the IDA report schema and cross-field validator;
4. checks the catalog's expected signal and stores dataset/report SHA-256 plus observed gate, metric and finding signals.

Four negative controls check formatting-only changes, consistent Case ID renaming, case order reversal and an unused source-registry entry. Four nondeterministic classes (M09–M12) are explicitly reported NOT_ASSESSED.

## Results

- Deterministic mutations detected: 8/8 (100%); Wilson 95% CI 0.676–1.000.
- Negative controls with false-positive critical failure: 0/4 (0%); Wilson 95% CI 0–0.490.
- M01–M05 produce the expected FAIL states; M06–M08 produce the expected PARTIAL/warning states.
- M09–M12 remain NOT_ASSESSED.

Artifact #15108859637, ZIP SHA-256: bb45162be43dd87e2b0587e8d35ae80c2b4328870bc2689debf23a594d323a1e.

## Interpretation limits

This result tests deterministic implementation sensitivity to the exact synthetic mutation operators. It is not a blind experiment and the 4 negative controls are too few to estimate a general false-positive rate. It does not test semantic ambiguity, construct alignment, independent Gold correctness, source claim support, or answer leakage. Those require independent expert review, independent Oracle evidence and contamination audits.

The real Round 4 IDA result remains PARTIAL: G01 PASS, G02–G04 NOT_ASSESSED, G05/G07 UNKNOWN and composite NOT_VALIDATED. Do not upgrade QA-02 until independent review evidence is imported and audited.


## Metamorphic invariance check (2026-11-27)

Negative controls now have a stronger deterministic contract. For each control, the runner compares a SHA-256 signature of the baseline and transformed report projection:

- overall status;
- all gate results;
- all metric results.

The byte-level dataset digest is deliberately excluded because harmless serialization or identity transformations can change raw bytes. A control is counted as a false positive if it triggers a hard FAIL **or** changes the invariant metric projection. The report records both signatures and the boolean comparison, and the JSON Schema enforces those fields.

This improves the test from “no hard FAIL” to “no hard FAIL and no change in measured gate/metric outputs” for the four authored controls. It does not enlarge the control sample, estimate a general false-positive rate, validate semantic equivalence for arbitrary transformations, or replace independent semantic review. The statistical result remains 0/4 with a wide Wilson interval.
