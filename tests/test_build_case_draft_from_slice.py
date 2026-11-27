import copy
import json
import unittest
from pathlib import Path

from scripts.build_case_draft_from_slice import build_case_draft

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "v0.0.3"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def case_fields():
    return {
        "case_id": "case-synthetic-trajectory-001",
        "dataset_id": "dataset-synthetic-001",
        "title": "SYNTHETIC reviewed task slice",
        "evaluation_target": "illustrative agent",
        "objective": "Produce the requested structured summary from supplied input.",
        "user_input": "SYNTHETIC: summarize fixture input.json using only supplied data.",
        "expected_behavior": "Return a valid JSON summary with the required fields.",
        "grading": {
            "method": "hybrid",
            "evaluation_subject": "illustrative agent",
            "criteria": [{
                "criterion_id": "criterion-001",
                "description": "Output is valid JSON with required fields.",
                "pass_condition": "JSON parses and all required fields are present.",
                "fail_condition": "JSON is invalid or required fields are missing.",
                "evidence_required": ["summary.json"],
            }],
            "pass_conditions": ["Output parses and satisfies the required structure."],
            "fail_conditions": ["Output is invalid JSON or omits required fields."],
            "evidence_required": ["summary.json"],
            "uncertainty_policy": "UNKNOWN if the supplied fixture is unavailable.",
        },
        "quality_status": "candidate",
        "scenario_bucket": ["tool_interaction"],
        "coverage_tags": [{
            "dimension": "capability",
            "value": "constraint following",
            "coverage_item_id": "cap-constraint-following",
        }],
        "execution_requirements": {"status": "DESIGN_ONLY"},
    }


class BuildCaseDraftFromSliceTests(unittest.TestCase):
    def setUp(self):
        self.source = load("trajectory-source.synthetic.json")
        self.candidate = load("task-candidate.synthetic.json")
        self.qualification = load("failure-qualification.synthetic.json")
        self.task_slice = load("task-slice.synthetic.json")

    def test_builds_existing_case_with_trace_provenance(self):
        case = build_case_draft(
            self.source, self.candidate, self.qualification, self.task_slice,
            case_fields(), "Synthetic trace source", "Synthetic test fixture authority",
        )
        self.assertEqual(case["case_origin"], "execution_trace")
        self.assertEqual(case["source_refs"][0]["source_id"], self.source["source_id"])
        self.assertEqual(case["source_refs"][0]["source_type"], "trace_log")
        self.assertIn(self.task_slice["trace_boundary"]["start_event_ref"], case["source_refs"][0]["locator"])
        self.assertEqual(case["quality_status"], "candidate")

    def test_missing_expected_behavior_is_rejected_not_invented(self):
        fields = case_fields()
        del fields["expected_behavior"]
        with self.assertRaisesRegex(ValueError, "expected_behavior"):
            build_case_draft(
                self.source, self.candidate, self.qualification, self.task_slice,
                fields, "Synthetic trace source", "Synthetic test fixture authority",
            )

    def test_incomplete_context_slice_is_rejected(self):
        sliced = copy.deepcopy(self.task_slice)
        sliced["initial_context"]["closure_review"] = "incomplete"
        with self.assertRaisesRegex(ValueError, "context closure"):
            build_case_draft(
                self.source, self.candidate, self.qualification, sliced,
                case_fields(), "Synthetic trace source", "Synthetic test fixture authority",
            )

    def test_case_cannot_override_provenance_fields(self):
        fields = case_fields()
        fields["case_origin"] = "business_document"
        with self.assertRaisesRegex(ValueError, "must not override provenance"):
            build_case_draft(
                self.source, self.candidate, self.qualification, self.task_slice,
                fields, "Synthetic trace source", "Synthetic test fixture authority",
            )


if __name__ == "__main__":
    unittest.main()
