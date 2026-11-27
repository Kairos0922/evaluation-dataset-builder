import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
DOC_SCHEMA = ROOT / "docs/quality-assessment-v0.0.2/schemas/expert-review-record.schema.json"
SKILL_SCHEMA = ROOT / "skills/evaluation-dataset-builder/references/expert-review-record.schema.json"


def load_schema():
    return json.loads(DOC_SCHEMA.read_text(encoding="utf-8"))


def valid_record(**overrides):
    record = {
        "review_id": "ER-001",
        "dataset_id": "wb-core",
        "dataset_version": "1.0.0",
        "dataset_sha256": "a" * 64,
        "item_id": "WB-01",
        "item_sha256": "b" * 64,
        "reviewer_id": "R-01",
        "reviewer_profile": {
            "role": "domain_expert",
            "expertise_domains": ["browser automation"],
            "experience_band": "gt_10_years",
            "conflict_of_interest": "none_declared",
        },
        "review_round": 1,
        "review_stage": "blind_review",
        "rating_dimension": "relevance",
        "rating_scale": "four_point",
        "rating": 4,
        "rationale": "The item directly measures the declared construct.",
        "blind_status": True,
        "adjudication_status": "not_applicable",
        "protocol_version": "0.1.0",
        "protocol_sha256": "c" * 64,
        "reviewed_at": "2026-11-25T00:00:00Z",
    }
    record.update(overrides)
    return record


class ExpertReviewSchemaTests(unittest.TestCase):
    def setUp(self):
        self.validator = Draft202012Validator(
            load_schema(), format_checker=FormatChecker()
        )

    def test_expert_review_schema_is_valid_and_mirrored(self):
        schema_text = DOC_SCHEMA.read_text(encoding="utf-8")
        self.assertEqual(SKILL_SCHEMA.read_text(encoding="utf-8"), schema_text)
        Draft202012Validator.check_schema(json.loads(schema_text))

    def test_valid_blind_four_point_review_record(self):
        self.assertTrue(self.validator.is_valid(valid_record()))

    def test_valid_necessity_record_uses_distinct_three_level_scale(self):
        record = valid_record(
            rating_dimension="necessity",
            rating_scale="necessity_three_level",
            rating="essential",
        )
        self.assertTrue(self.validator.is_valid(record))

    def test_valid_adjudication_record_preserves_stage_and_decision(self):
        record = valid_record(
            review_stage="adjudication",
            blind_status=False,
            adjudication_status="needs_more_evidence",
        )
        self.assertTrue(self.validator.is_valid(record))

    def test_invalid_expert_review_records_are_rejected(self):
        invalid_overrides = [
            {"rating_dimension": "relevance", "rating_scale": "necessity_three_level", "rating": "essential"},
            {"rating_dimension": "necessity", "rating_scale": "four_point", "rating": 4},
            {"blind_status": False},
            {"reviewer_email": "reviewer@example.com"},
            {"dataset_sha256": "not-a-sha256"},
        ]
        for overrides in invalid_overrides:
            with self.subTest(overrides=overrides):
                self.assertFalse(self.validator.is_valid(valid_record(**overrides)))


if __name__ == "__main__":
    unittest.main()
