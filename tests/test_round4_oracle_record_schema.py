import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs/quality-assessment-v0.0.2/schemas/round4-oracle-record.schema.json"


def valid_record(**overrides):
    record = {
        "schema_version": "0.1.0",
        "record_id": "OR-R4-WB-01",
        "dataset_id": "wb-core",
        "dataset_version": "1.0.0",
        "dataset_sha256": "a" * 64,
        "case_id": "WB-01",
        "case_sha256": "b" * 64,
        "oracle_plan_sha256": "c" * 64,
        "blind_execution": True,
        "sources": [
            {
                "source_id": "business-rules",
                "sha256": "d" * 64,
                "authority_role": "normative_rule",
                "locator": "BR-01",
            }
        ],
        "environment": {
            "runner_image": "ubuntu-26.04/20261116.202",
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
            "initial_snapshot_sha256": "2" * 64,
            "final_snapshot_sha256": "3" * 64,
        },
        "observations": [
            {
                "observation_id": "OBS-01",
                "assertion_id": "BR-01-summary",
                "normative_ref": "business-rules.md#BR-01",
                "method": "api_state",
                "expected_summary": "All=5/Open=2/In progress=2/Done=1",
                "observed_summary": "All=5/Open=2/In progress=2/Done=1",
                "outcome": "PASS",
                "evidence_refs": ["api-before.json", "dom-summary.json"],
            }
        ],
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
                    "evidence_refs": ["api-before.json", "dom-summary.json"],
                },
                {
                    "reviewer_id": "R-02",
                    "application_outcome": "PASS",
                    "skill_outcome": "PASS",
                    "rationale": "The trace confirms the read-only process and report.",
                    "evidence_refs": ["trace.json", "dom-summary.json"],
                },
            ],
            "consensus_status": "agreed",
            "final_application_outcome": "PASS",
            "final_skill_outcome": "PASS",
        },
        "record_status": "accepted",
    }
    record.update(overrides)
    return record


class Round4OracleRecordSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(
            cls.schema, format_checker=FormatChecker()
        )

    def test_schema_is_valid_and_defines_only_the_unrun_case_set(self):
        case_ids = self.schema["properties"]["case_id"]["enum"]
        self.assertEqual(
            set(case_ids),
            {"WB-01", "WB-03", "WB-04", "WB-05", "WB-06", "WB-07",
             "WB-08", "WB-09", "WB-11", "WB-13", "WB-14", "WB-15"},
        )

    def test_valid_record_keeps_application_and_skill_outcomes_separate(self):
        self.assertTrue(self.validator.is_valid(valid_record()))

    def test_wb15_cannot_claim_application_pass_or_fail_without_injection(self):
        record = valid_record(case_id="WB-15", application_outcome="FAIL")
        self.assertFalse(self.validator.is_valid(record))
        record["application_outcome"] = "UNKNOWN"
        self.assertTrue(self.validator.is_valid(record))

    def test_requires_two_independent_reviewers_and_evidence(self):
        record = valid_record()
        record["adjudication"]["reviewer_ids"] = ["R-01"]
        self.assertFalse(self.validator.is_valid(record))
        record = valid_record()
        record["observations"][0]["evidence_refs"] = []
        self.assertFalse(self.validator.is_valid(record))

    def test_budget_violation_cannot_be_recorded_as_skill_pass(self):
        record = valid_record()
        record["action_budget"]["budget_exceeded"] = True
        self.assertFalse(self.validator.is_valid(record))
        record["skill_outcome"] = "FAIL"
        record["adjudication"]["final_skill_outcome"] = "FAIL"
        for decision in record["adjudication"]["independent_decisions"]:
            decision["skill_outcome"] = "FAIL"
        self.assertTrue(self.validator.is_valid(record))


if __name__ == "__main__":
    unittest.main()
