# Manual / LLM Judge Calibration Evidence Protocol

**Status:** Import contract and workflow implemented; no independent empirical calibration has yet been conducted.  
**Scope:** Human/manual adjudicators and independent LLM Judges.

## 1. Separation of evidence

- The evaluated Agent/Skill and the Judge must be separate systems; record provider, endpoint origin, model or panel identifier, prompt SHA-256, implementation SHA-256, and the separation declaration.
- Gold labels must come from independent experts, an independent adjudicated Oracle, or independently documented historical incidents. Builder-authored expected outcomes and synthetic fixtures are not independent Gold.
- Every case must retain separate Gold and Judge evidence references, the candidate output SHA-256, and an evidence-validation flag.
- Reviewer and adjudicator identities are pseudonymous IDs only. Do not put names, email addresses, credentials, or other direct identifiers in the observation file.

## 2. Frozen suite and held-out protocol

Before scoring, freeze the exact suite bytes and case IDs. For independent empirical calibration, the observation set must declare a named held-out split, independent Gold, blinded scoring, independent review, and an explicit abstention policy. The importer checks suite SHA-256, exact case coverage, duplicate IDs, report Schema, and cross-field invariants.

## 3. Observation input

The machine-readable input contract is schemas/judge-calibration-observations.schema.json. Each observation contains case_id, gold_status, judge_status, evidence_validated, output_sha256, gold_evidence_ref, judge_evidence_ref, and optional anonymous reviewer_id, adjudicator_id, and repeat_index.

The Judge may be human or llm. For a human panel, use an offline endpoint label such as offline://manual-review and a non-identifying panel ID. For an LLM, record the provider, endpoint origin, model, prompt hash, and implementation hash.

## 4. Import

Use scripts/import_judge_calibration_evidence.py with:
- --suite: exact frozen suite JSON
- --observations: manual/LLM observation JSON
- --output: destination report
- --run-id and --commit-sha: optional execution identity

The importer recomputes exact matches, adjudicable denominator, False Pass, False Fail, abstentions, and accuracy. It binds the source observation file by SHA-256 and validates the generated report against the frozen suite.

## 5. Interpretation and safeguards

- Synthetic smoke imports remain NOT_VALIDATED.
- Independent empirical imports are always emitted as PARTIAL; the importer cannot authenticate external reviewer identities, prove the real blinding process, or independently verify evidence URLs.
- VALIDATED_FOR_SCOPE requires a separate external review decision and must not be inferred from successful import, schema validation, or a high accuracy value.
- Accuracy is accompanied by case-level results and error counts. Small or selected samples do not support broad generalization; report uncertainty and the scope of the held-out set.
- If evidence is missing, keep the affected status UNKNOWN; do not replace it with PASS or FAIL.
