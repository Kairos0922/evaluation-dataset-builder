# Changelog

## 0.0.1 — release candidate; publication pending

- Initial general-purpose Evaluation Dataset Builder Skill with quality standard, case schema, grader and coverage guidance, and evidence governance.
- Added model-aware request planning using live provider metadata, combined input/output budgeting, configurable headroom, and no arbitrary small fixed caps.
- Added DeepSeek V4.1 Flash profile and metadata-only preflight helper.
- Added bounded API error handling, ambiguous-timeout guidance, and cursor-based recovery for partial output.
- Expanded self-evaluation fixtures and added offline preflight/budget unit tests.

### Release boundary

The package version remains **0.0.1**. These changes improve the 0.0.1 release candidate; they do not authorize a major-version increase or waive the release gates.

Structural CI and offline unit tests passed on the pull-request commit. Live model behavior, independent human review, and target-system execution validation have not been completed. See `RELEASE.md`.

## Historical baseline

The initial 0.0.1 repository baseline introduced the general-purpose Skill, quality standard, schema, graders, self-evaluation fixtures, validator, and release documentation.
