# Self-evaluation protocol

Run each prompt from self-eval-cases.json in a fresh context with the Skill loaded. Grade expected properties, not wording. Include trigger-positive, paraphrase, and negative-trigger cases. Repeat stochastic cases when measuring consistency. Report per-case results, aggregate pass rate, critical failures, model/version, and run configuration.

For capability uplift, compare with a matched baseline without the Skill. Keep a held-out subset for regression and avoid tuning indefinitely against all cases.

The repository currently includes fixtures and structural validation, not a model-run harness. Do not report behavioral benchmark scores from fixture inspection alone. Add a runtime adapter once model/provider and credentials are configured.
