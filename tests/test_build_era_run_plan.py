import copy
import hashlib
import json
import unittest

from scripts.build_era_run_plan import build_era_run_plan
from scripts.import_dsh_pilot_records import dataset_digest as importer_dataset_digest


def make_manifest(case_count=1):
    return {
        "dataset_id": "dataset-synthetic-era-plan",
        "version": "0.0.3-synthetic",
        "evaluation_target": "synthetic agent",
        "purpose": "SYNTHETIC / ILLUSTRATIVE_ONLY contract test",
        "scope": {"included": ["one synthetic task"], "excluded": []},
        "coverage": {
            "universe_definition": "one illustrative task",
            "dimensions": []
        },
        "case_count": case_count,
        "quality_status": "candidate",
        "execution_status": "READY_TO_RUN"
    }


def make_case(case_id="CASE-SYNTHETIC-001"):
    return {
        "case_id": case_id,
        "dataset_id": "dataset-synthetic-era-plan",
        "title": "SYNTHETIC clean-run planning case",
        "evaluation_target": "synthetic agent",
        "objective": "Return the requested structured output.",
        "user_input": "SYNTHETIC: process the supplied fixture.",
        "expected_behavior": "Return a valid JSON object with a result field.",
        "grading": {
            "method": "rule_based",
            "evaluation_subject": "synthetic agent",
            "criteria": [{
                "criterion_id": "JSON-VALID",
                "description": "Output is valid JSON.",
                "pass_condition": "Output parses as JSON.",
                "fail_condition": "Output is not valid JSON.",
                "evidence_required": ["result.json"]
            }],
            "pass_conditions": ["Output parses as JSON."],
            "fail_conditions": ["Output is not valid JSON."],
            "evidence_required": ["result.json"]
        },
        "source_refs": [{
            "source_id": "synthetic-source-001",
            "source_type": "trace_log",
            "title": "SYNTHETIC historical source trace",
            "version": "synthetic-agent-rev",
            "effective_date": None,
            "authority": "Synthetic fixture only",
            "locator": "synthetic://historical-trace#events=1..3",
            "quoted_evidence": ""
        }],
        "quality_status": "candidate",
        "scenario_bucket": ["tool_interaction"],
        "case_origin": "execution_trace",
        "coverage_tags": [{
            "dimension": "capability",
            "value": "constraint following",
            "coverage_item_id": "synthetic-constraint-following"
        }],
        "execution_requirements": {
            "status": "READY_TO_RUN",
            "initial_state": {"fixture": "clean"},
            "required_permissions": ["no external permissions"],
            "environment": {"isolation": "ephemeral synthetic workspace"},
            "test_data": [],
            "allowed_actions": ["read fixture", "write result.json"],
            "steps": ["read fixture", "produce result.json"],
            "expected_end_state": {"result_exists": True},
            "observable_assertions": ["result.json exists and parses"],
            "forbidden_side_effects": ["no network access"],
            "reset_plan": "discard synthetic workspace",
            "cleanup_plan": "remove synthetic workspace",
            "failure_cleanup": "remove synthetic workspace even on failure"
        }
    }


def make_configuration():
    return {
        "configuration_id": "synthetic-agent-config-v1",
        "target_revision": "synthetic-agent-revision",
        "target_type": "agent",
        "model": {"provider": "synthetic", "model_id": "illustrative-model", "revision": None},
        "harness": {"name": "synthetic-harness", "version": "1.0"},
        "environment": {"name": "isolated-synthetic", "version": "1.0", "digest": None, "region": None},
        "tool_versions": {"synthetic-tool": "1.0"},
        "seed": 17
    }


class BuildEraRunPlanTests(unittest.TestCase):
    def build(self, cases=None, manifest=None, selected=None):
        cases = cases or [make_case()]
        manifest = manifest or make_manifest(len(cases))
        manifest_bytes = (json.dumps(manifest, sort_keys=True) + "\n").encode()
        cases_bytes = b"".join(
            (json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n").encode()
            for case in cases
        )
        return build_era_run_plan(
            manifest, manifest_bytes, cases, cases_bytes, make_configuration(), selected
        ), manifest_bytes, cases_bytes

    def test_builds_non_executing_plan_and_reuses_existing_dataset_digest(self):
        plan, manifest_bytes, cases_bytes = self.build()
        self.assertEqual(plan["status"], "DRAFT_NOT_EXECUTED")
        self.assertEqual(plan["dataset"]["dataset_sha256"], importer_dataset_digest(manifest_bytes, cases_bytes))
        self.assertEqual(plan["planned_cases"][0]["case_id"], "CASE-SYNTHETIC-001")
        self.assertTrue(plan["planned_cases"][0]["historical_source_refs_are_not_runtime_trace_refs"])
        self.assertEqual(plan["planned_cases"][0]["historical_source_refs"][0]["source_type"], "trace_log")
        self.assertNotIn("run_id", plan)
        self.assertNotIn("trace_ref", plan["planned_cases"][0])
        self.assertEqual(plan["execution_protocol"]["session_policy"], "fresh_session_per_case")

    def test_selects_cases_in_requested_order(self):
        first = make_case("CASE-SYNTHETIC-001")
        second = make_case("CASE-SYNTHETIC-002")
        plan, _, _ = self.build([first, second], make_manifest(2), ["CASE-SYNTHETIC-002"])
        self.assertEqual([item["case_id"] for item in plan["planned_cases"]], ["CASE-SYNTHETIC-002"])

    def test_rejects_case_not_ready_to_run(self):
        case = make_case()
        case["execution_requirements"]["status"] = "DESIGN_ONLY"
        with self.assertRaisesRegex(ValueError, "not READY_TO_RUN"):
            self.build([case], make_manifest(1))

    def test_rejects_dataset_identity_mismatch(self):
        case = make_case()
        case["dataset_id"] = "different-dataset"
        with self.assertRaisesRegex(ValueError, "does not match Manifest"):
            self.build([case], make_manifest(1))

    def test_rejects_unknown_or_duplicate_selection(self):
        with self.assertRaisesRegex(ValueError, "not found"):
            self.build(selected=["DOES-NOT-EXIST"])
        with self.assertRaisesRegex(ValueError, "unique"):
            self.build(selected=["CASE-SYNTHETIC-001", "CASE-SYNTHETIC-001"])


if __name__ == "__main__":
    unittest.main()
