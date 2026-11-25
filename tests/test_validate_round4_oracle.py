import json
import unittest
from pathlib import Path

from scripts.validate_round4_oracle import EXPECTED_CASE_IDS, validate_records


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "docs/quality-assessment-v0.0.2/schemas/round4-oracle-record.schema.json")
    .read_text(encoding="utf-8")
)


def record():
    return {
        "schema_version": "0.1.0",
        "record_id": "OR-R4-WB-01",
        "dataset_id": "wb-core",
        "dataset_version": "1.0.0",
        "dataset_sha256": "a" * 64,
        "case_id": "WB-01",
        "case_sha256": "b" * 64,
        "oracle_plan_sha256": "c" * 64,
        "blind_execution": True,
        "sources": [{
            "source_id": "business-rules",
            "sha256": "d" * 64,
            "authority_role": "normative_rule",
            "locator": "BR-01",
        }],
        "environment": {
            "runner_image": "ubuntu-26.04",
            "python_version": "3.12.16",
            "playwright_version": "1.64.1",
            "chromium_version": "156.0.8078.4",
            "fixture_sha256": {
                "server_py": "e" * 64,
                "app_js": "f" * 64,
                "index_html": "1" * 64,
            },
        },
        "run": {
            "run_id": "run-001",
            "started_at": "2026-11-25T00:00:00Z",
            "execution_status": "completed",
            "attempt_count": 1,
            "reset_verified": True,
        },
        "observations": [{
            "observation_id": "OBS-01",
            "assertion_id": "BR-01-summary",
            "normative_ref": "business-rules.md#BR-01",
            "method": "api_state",
            "expected_summary": "All=5/Open=2/In progress=2/Done=1",
            "observed_summary": "All=5/Open=2/In progress=2/Done=1",
            "outcome": "PASS",
            "evidence_refs": ["api-before.json"],
        }],
        "action_budget": {
            "max_script_runs": 1,
            "observed_script_runs": 1,
            "max_write_actions": 0,
            "observed_write_actions": 0,
            "budget_exceeded": False,
        },
        "application_outcome": "PASS",
        "skill_outcome": "PASS",
        "adjudication": {
            "reviewer_ids": ["R-01", "R-02"],
            "independent_decisions": [
                {
                    "reviewer_id": "R-01",
                    "application_outcome": "PASS",
                    "skill_outcome": "PASS",
                    "rationale": "The independent API and DOM evidence agree.",
                    "evidence_refs": ["api-before.json"],
                },
                {
                    "reviewer_id": "R-02",
                    "application_outcome": "PASS",
                    "skill_outcome": "PASS",
                    "rationale": "The trace confirms the read-only process and report.",
                    "evidence_refs": ["trace.json"],
                },
            ],
            "consensus_status": "agreed",
            "final_application_outcome": "PASS",
            "final_skill_outcome": "PASS",
        },
        "record_status": "accepted",
    }


class Round4OracleValidatorTests(unittest.TestCase):
    def setUp(self):
        self.case_hashes = {case_id: "b" * 64 for case_id in EXPECTED_CASE_IDS}
        self.kwargs = {
            "dataset_sha256": "a" * 64,
            "case_hashes": self.case_hashes,
            "plan_sha256": "c" * 64,
            "schema": SCHEMA,
        }

    def test_accepts_hash_bound_independently_reviewed_record(self):
        self.assertEqual(validate_records([record()], **self.kwargs), [])

    def test_rejects_dataset_case_and_plan_hash_mismatch(self):
        item = record()
        item["dataset_sha256"] = "9" * 64
        item["case_sha256"] = "8" * 64
        item["oracle_plan_sha256"] = "7" * 64
        errors = validate_records([item], **self.kwargs)
        self.assertTrue(any("dataset_sha256" in error for error in errors))
        self.assertTrue(any("case_sha256" in error for error in errors))
        self.assertTrue(any("oracle_plan_sha256" in error for error in errors))

    def test_rejects_duplicate_case_records(self):
        first = record()
        second = record()
        second["record_id"] = "OR-R4-WB-01-duplicate"
        errors = validate_records([first, second], **self.kwargs)
        self.assertTrue(any("duplicate Oracle record" in error for error in errors))

    def test_require_complete_reports_missing_cases(self):
        errors = validate_records([record()], require_complete=True, **self.kwargs)
        self.assertTrue(any("missing Oracle records" in error for error in errors))

    def test_rejects_accepted_record_without_two_matching_reviewers(self):
        item = record()
        item["adjudication"]["independent_decisions"].pop()
        errors = validate_records([item], **self.kwargs)
        self.assertTrue(any("reviewer_ids must exactly match" in error for error in errors))

    def test_rejects_accepted_record_without_verified_reset(self):
        item = record()
        item["run"]["reset_verified"] = False
        errors = validate_records([item], **self.kwargs)
        self.assertTrue(any("verified clean reset" in error for error in errors))

    def test_rejects_top_level_outcomes_that_disagree_with_adjudication(self):
        item = record()
        item["skill_outcome"] = "FAIL"
        errors = validate_records([item], **self.kwargs)
        self.assertTrue(any("skill_outcome differs" in error for error in errors))

    def test_action_budget_flag_must_match_observed_counts(self):
        item = record()
        item["action_budget"]["observed_write_actions"] = 1
        errors = validate_records([item], **self.kwargs)
        self.assertTrue(any("budget_exceeded does not match" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
