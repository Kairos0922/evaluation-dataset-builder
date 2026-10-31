# Evaluation Dataset Builder

A general-purpose Skill for planning, generating, validating, repairing, and packaging evaluation datasets for agents, skills, models, APIs, workflows, and other systems.

## Features
- Parses materials and distinguishes evidence, assumptions, and conflicts.
- Plans multiple purpose-specific datasets and coverage matrices.
- Generates structured cases with graders.
- Applies case-level and dataset-level quality gates.
- Repairs defects and reports gaps.
- Produces traceable, versioned assets.

## Validate
Run: python scripts/validate_skill.py

Structural validation does not prove semantic quality. Run tests/self-eval-cases.json with a model-based harness for behavioral evaluation.
