"""Contract tests for v0.0.3 trajectory-driven assets."""
from __future__ import annotations

import copy
import unittest

from scripts.validate_trajectory_assets import validate_assets


def valid_chain():
    source = {
        "schema_version": "0.0.3", "source_id": "src-001",
        "source_kind": "synthetic_fixture",
        "authorization": {"status": "synthetic_only", "scope": "CI-only illustrative fixture"},
        "redaction_status": "no_sensitive_content_attested",
        "artifact": {"uri": "fixture://trace-001", "sha256": "a" * 64},
        "created_at": "2026-11-28T12:00:00Z",
    }
    candidate = {
        "schema_version": "0.0.3", "candidate_id": "cand-001", "source_id": "src-001",
        "discovery_signals": ["user_correction", "rework_or_revision"],
        "evidence_refs": [{"event_start": "evt-01", "event_end": "evt-08", "description": "Illustrative correction sequence"}],
        "status": "under_review", "created_at": "2026-11-28T12:01:00Z",
    }
    qualification = {
        "schema_version": "0.0.3", "qualification_id": "qual-001", "candidate_id": "cand-001",
        "attribution": "agent_decision",
        "decision_context": {
            "critical_event_ref": "evt-04", "available_information_refs": ["evt-01", "evt-02"],
            "could_reasonably_avoid_error": "yes", "post_hoc_requirement_added": False,
            "rationale": "Illustrative evidence only",
        },
        "task_contract": {"input_identifiable": True, "deliverable_identifiable": True, "quality_criteria_identifiable": True},
        "environment_health": "healthy", "evidence_sufficiency": "sufficient_for_candidate",
        "review_status": "qualified",
    }
    task_slice = {
        "schema_version": "0.0.3", "slice_id": "slice-001", "candidate_id": "cand-001",
        "qualification_id": "qual-001", "source_id": "src-001",
        "trace_boundary": {"start_event_ref": "evt-02", "end_event_ref": "evt-06", "boundary_rationale": "Isolate the decision and its immediate outcome"},
        "initial_context": {"context_refs": ["evt-01"], "closure_review": "complete", "omitted_context_rationale": "No omitted task-critical context"},
        "task": {"instruction": "Complete the illustrative task.", "inputs": ["fixture input"], "deliverables": ["output.json"], "constraints": ["Do not access external services"], "prohibited_side_effects": ["No external writes"]},
        "capability_hypotheses": ["constraint reasoning"],
        "evaluation_contract": {"grading_mode": "hybrid", "criteria_refs": ["criterion-01"], "acceptable_variants": ["Equivalent valid output"], "unknown_conditions": ["Missing evidence"]},
        "leakage_review": "passed", "status": "ready_for_reconstruction",
    }
    reconstruction = {
        "schema_version": "0.0.3", "reconstruction_id": "recon-001", "slice_id": "slice-001",
        "initial_state": [{"artifact_ref": "fixture://input", "sha256": "b" * 64, "purpose": "Initial task state"}],
        "dependencies": [{"name": "python", "version": "3.12"}],
        "tools": [{"name": "local-runner", "version": "1", "contract_ref": "fixture://tool-contract"}],
        "permissions": ["read fixture workspace"],
        "resource_limits": {"timeout_seconds": 60, "action_budget": 10, "network_policy": "disabled"},
        "reset_and_cleanup": {"reset_strategy": "Fresh temporary workspace", "cleanup_strategy": "Delete temporary workspace", "side_effects_reviewed": True},
        "reconstruction_diff": [], "readiness": "ready_for_review",
    }
    return source, candidate, qualification, task_slice, reconstruction


class TrajectoryAssetValidationTests(unittest.TestCase):
    def validate(self, chain):
        return validate_assets(*chain)

    def test_complete_synthetic_chain_is_contract_valid(self):
        self.assertEqual(self.validate(valid_chain()), [])

    def test_unauthorized_source_is_rejected(self):
        chain = list(valid_chain())
        chain[0]["authorization"]["status"] = "not_authorized"
        self.assertTrue(any("authorization" in e for e in self.validate(chain)))

    def test_pending_redaction_blocks_qualification(self):
        chain = list(valid_chain())
        chain[0]["redaction_status"] = "pending_review"
        self.assertTrue(any("sensitive-content review" in e for e in self.validate(chain)))

    def test_synthetic_source_requires_synthetic_authorization(self):
        chain = list(valid_chain())
        chain[0]["authorization"]["status"] = "user_provided"
        self.assertTrue(any("synthetic_fixture requires" in e for e in self.validate(chain)))

    def test_source_identity_mismatch_is_rejected(self):
        chain = list(valid_chain())
        chain[1]["source_id"] = "different-source"
        self.assertTrue(any("source_id does not match" in e for e in self.validate(chain)))

    def test_qualified_failure_cannot_rely_on_post_hoc_requirement(self):
        chain = list(valid_chain())
        chain[2]["decision_context"]["post_hoc_requirement_added"] = True
        self.assertTrue(any("post-hoc requirement" in e for e in self.validate(chain)))

    def test_qualified_failure_requires_healthy_environment(self):
        chain = list(valid_chain())
        chain[2]["environment_health"] = "failed"
        self.assertTrue(any("healthy observed environment" in e for e in self.validate(chain)))

    def test_ready_slice_requires_context_closure(self):
        chain = list(valid_chain())
        chain[3]["initial_context"]["closure_review"] = "incomplete"
        self.assertTrue(any("complete context closure" in e for e in self.validate(chain)))

    def test_ready_slice_requires_leakage_review(self):
        chain = list(valid_chain())
        chain[3]["leakage_review"] = "pending"
        self.assertTrue(any("passed leakage review" in e for e in self.validate(chain)))

    def test_reconstruction_cannot_be_ready_with_unrestricted_network(self):
        chain = list(valid_chain())
        chain[4]["resource_limits"]["network_policy"] = "unrestricted_not_recommended"
        self.assertTrue(any("unrestricted network policy" in e for e in self.validate(chain)))

    def test_reconstruction_requires_side_effect_review(self):
        chain = list(valid_chain())
        chain[4]["reset_and_cleanup"]["side_effects_reviewed"] = False
        self.assertTrue(any("side-effect and cleanup plan" in e for e in self.validate(chain)))

    def test_reconstruction_slice_identity_mismatch_is_rejected(self):
        chain = list(valid_chain())
        chain[4]["slice_id"] = "other-slice"
        self.assertTrue(any("slice_id does not match" in e for e in self.validate(chain)))

    def test_schema_rejects_unknown_fields(self):
        chain = list(valid_chain())
        chain[1]["unreviewed_score"] = 99
        self.assertTrue(any("Additional properties" in e for e in self.validate(chain)))

    def test_non_object_root_fails_without_exception(self):
        errors = validate_assets(source=[])
        self.assertTrue(any("root must be an object" in error for error in errors))

    def test_non_finite_number_is_rejected(self):
        chain = list(valid_chain())
        chain[4]["resource_limits"]["cpu"] = float("inf")
        self.assertTrue(any("non-finite number" in e for e in self.validate(chain)))


if __name__ == "__main__":
    unittest.main()
