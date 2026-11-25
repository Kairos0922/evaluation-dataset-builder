import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.validate_round4_oracle_freeze import validate_freeze_manifest
from scripts.validate_round4_oracle import EXPECTED_CASE_IDS

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "docs/quality-assessment-v0.0.2/schemas/round4-oracle-freeze-manifest.schema.json")
    .read_text(encoding="utf-8")
)
DATASET_SHA = "000d38b110b60eae902f86737ea6bd1368f98c6632c42a47bb9470a4a08bfc45
PLAN_SHA = "b" * 64
CASE_HASHES = {case_id: f"{index:064x}" for index, case_id in enumerate(sorted(EXPECTED_CASE_IDS), 1)}


def reviewer(slot: str, reviewer_id: str) -> dict:
    return {
        "reviewer_slot": slot,
        "reviewer_id": reviewer_id,
    }


def case_record(case_id: str, *, decision: str = "FROZEN") -> dict:
    return {
        "case_id": case_id,
        "case_sha256": CASE_HASHES[case_id],
        "freeze_decision": decision,
        "application_assertions": [{
            "assertion_id": f"{case_id}-APP-01",
            "normative_ref": "business-rules.md#BR-01",
            "pass_condition": "The independently observed application state conforms to the cited rule.",
            "fail_condition": "The independently observed application state contradicts the cited rule.",
            "unknown_condition": "The required independent state evidence is unavailable.",
            "observation_methods": ["api_state", "dom"],
        }],
        "skill_assertions": [{
            "assertion_id": f"{case_id}-SKILL-01",
            "pass_condition": "The Skill gathers the required evidence and reports the application outcome accurately.",
            "fail_condition": "The Skill misreports the outcome or violates the authorized action budget.",
            "unknown_condition": "The Skill trace or required independent evidence is unavailable.",
            "observation_methods": ["playwright_trace", "server_audit"],
        }],
        "application_unknown_conditions": ["Initial state or independent application evidence cannot be verified."],
        "skill_unknown_conditions": ["The Skill execution trace is missing or incomplete."],
        "max_script_runs": 1,
        "max_write_actions": 0,
        "prohibited_side_effects": ["No unapproved task mutation."],
        "rationale": "The independent normative source and observable evidence support these case-specific assertions.",
        "evidence_refs": ["business-rules.md#BR-01", "runtime-and-tool-contracts.md#read-only"],
    }


def manifest() -> dict:
    return {
        "schema_version": "1.0.0",
        "freeze_id": "OR-FREEZE-R4-TEST",
        "dataset_id": "wb-core",
        "dataset_version": "1.0.0",
        "dataset_sha256": DATASET_SHA,
        "oracle_plan_sha256": PLAN_SHA,
        "review_inputs": {
            "reviewer_a_id": "RV-reviewer-a",
            "reviewer_b_id": "RV-reviewer-b",
            "reviewer_a_submission_sha256": "c" * 64,
            "reviewer_b_submission_sha256": "d" * 64,
            "comparison_report_sha256": "e" * 64,
            "crosswalk_sha256": "f" * 64,
        },
        "adjudication": {
            "adjudicator_id": "ADJ-third-party",
            "adjudicated_at": "2026-11-25T12:00:00Z",
            "method": "independent_third_reviewer",
            "decision_summary": "All twelve case rules were independently reviewed and adjudicated against the frozen public normative assets.",
            "evidence_refs": ["review-comparison.json", "adjudication-notes.md"],
        },
        "cases": [case_record(case_id) for case_id in sorted(EXPECTED_CASE_IDS)],
        "freeze_status": "FROZEN",
    }


class Round4OracleFreezeManifestTests(unittest.TestCase):
    def setUp(self):
        self.a = reviewer("A", "RV-reviewer-a")
        self.b = reviewer("B", "RV-reviewer-b")
        self.report = {
            "status": "REQUIRES_HUMAN_ADJUDICATION",
            "dataset_sha256": DATASET_SHA,
            "reviewers": {
                "A": {"reviewer_id": "RV-reviewer-a"},
                "B": {"reviewer_id": "RV-reviewer-b"},
            },
            "cases": [{"case_id": case_id} for case_id in sorted(EXPECTED_CASE_IDS)],
        }
        self.kwargs = {
            "schema": SCHEMA,
            "dataset_sha256": DATASET_SHA,
            "case_hashes": CASE_HASHES,
            "plan_sha256": PLAN_SHA,
            "reviewer_a": self.a,
            "reviewer_b": self.b,
            "reviewer_a_sha256": "c" * 64,
            "reviewer_b_sha256": "d" * 64,
            "comparison_report": self.report,
            "comparison_report_sha256": "e" * 64,
            "crosswalk_sha256": "f" * 64,
        }

    def test_accepts_complete_hash_bound_frozen_manifest(self):
        item = manifest()
        self.assertEqual(
            list(Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(item)),
            [],
        )
        self.assertEqual(validate_freeze_manifest(item, **self.kwargs), [])

    def test_rejects_same_reviewer_identity(self):
        self.b["reviewer_id"] = self.a["reviewer_id"]
        errors = validate_freeze_manifest(manifest(), **self.kwargs)
        self.assertTrue(any("reviewer IDs must be distinct" in error for error in errors))

    def test_rejects_adjudicator_who_is_one_of_the_reviewers(self):
        item = manifest()
        item["adjudication"]["adjudicator_id"] = "RV-reviewer-a"
        errors = validate_freeze_manifest(item, **self.kwargs)
        self.assertTrue(any("adjudicator must be independent" in error for error in errors))

    def test_rejects_duplicate_or_missing_cases(self):
        item = manifest()
        item["cases"][-1] = item["cases"][0]
        errors = validate_freeze_manifest(item, **self.kwargs)
        self.assertTrue(any("each of the 12 target cases exactly once" in error for error in errors))

    def test_rejects_case_hash_mismatch(self):
        item = manifest()
        item["cases"][0]["case_sha256"] = "0" * 64
        errors = validate_freeze_manifest(item, **self.kwargs)
        self.assertTrue(any("case_sha256 mismatch" in error for error in errors))

    def test_rejects_submission_comparison_and_crosswalk_hash_mismatch(self):
        item = manifest()
        item["review_inputs"]["reviewer_a_submission_sha256"] = "0" * 64
        item["review_inputs"]["comparison_report_sha256"] = "1" * 64
        item["review_inputs"]["crosswalk_sha256"] = "2" * 64
        errors = validate_freeze_manifest(item, **self.kwargs)
        self.assertTrue(any("Reviewer A submission SHA-256 mismatch" in error for error in errors))
        self.assertTrue(any("comparison report SHA-256 mismatch" in error for error in errors))
        self.assertTrue(any("coordinator crosswalk SHA-256 mismatch" in error for error in errors))

    def test_refuses_frozen_status_when_any_case_is_not_frozen(self):
        item = manifest()
        item["cases"][0]["freeze_decision"] = "NOT_FROZEN"
        errors = validate_freeze_manifest(item, **self.kwargs)
        self.assertTrue(any("freeze_status must be NOT_FROZEN" in error for error in errors))

    def test_malformed_nested_manifest_values_return_validation_errors(self):
        item = manifest()
        item["review_inputs"] = []
        item["adjudication"] = None
        item["cases"] = None
        self.report["reviewers"] = None
        self.report["cases"] = None
        errors = validate_freeze_manifest(item, **self.kwargs)
        self.assertTrue(any("review_inputs" in error for error in errors))
        self.assertTrue(any("adjudication" in error for error in errors))
        self.assertTrue(any("cases" in error for error in errors))

    def test_requires_review_comparison_report_to_remain_non_adjudicating(self):
        self.report["status"] = "FROZEN"
        errors = validate_freeze_manifest(manifest(), **self.kwargs)
        self.assertTrue(any("REQUIRES_HUMAN_ADJUDICATION" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
