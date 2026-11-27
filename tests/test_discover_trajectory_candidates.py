"""Tests for heuristic candidate discovery from normalized trajectory events."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.discover_trajectory_candidates import discover_candidates, read_events


def event(event_id, sequence, actor, event_type, **extra):
    return {
        "event_id": event_id, "session_id": "session-1", "sequence": sequence,
        "actor": actor, "event_type": event_type,
        "timestamp": f"2026-11-28T12:00:{sequence:02d}Z", **extra,
    }


def correction_trace():
    return [
        event("e1", 1, "user", "user_message", task_marker="task_input", content_ref="fixture://msg/e1"),
        event("e2", 2, "assistant", "assistant_message"),
        event("e3", 3, "assistant", "artifact_created", artifact_ref="artifact://v1", artifact_sha256="a" * 64),
        event("e4", 4, "user", "user_feedback", feedback_kind="correction"),
        event("e5", 5, "assistant", "assistant_message"),
        event("e6", 6, "assistant", "artifact_created", artifact_ref="artifact://v2", artifact_sha256="b" * 64, revision_of="artifact://v1"),
    ]


class TrajectoryDiscoveryTests(unittest.TestCase):
    def test_discovers_correction_and_material_revision(self):
        candidates = discover_candidates(correction_trace(), "src-1", min_turns=4)
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertIn("user_correction", candidate["discovery_signals"])
        self.assertIn("rework_or_revision", candidate["discovery_signals"])
        self.assertIn("material_output_change", candidate["discovery_signals"])
        self.assertIn("multi_turn_interaction", candidate["discovery_signals"])
        self.assertEqual(candidate["evidence_refs"][0]["event_start"], "e1")
        self.assertEqual(candidate["evidence_refs"][0]["event_end"], "e6")
        self.assertEqual(candidate["status"], "discovered")

    def test_unsatisfied_feedback_is_candidate_without_revision(self):
        events = [
            event("e1", 1, "user", "user_message", task_marker="task_input"),
            event("e2", 2, "assistant", "artifact_created", artifact_ref="artifact://v1", artifact_sha256="a" * 64),
            event("e3", 3, "user", "user_feedback", feedback_kind="unsatisfied"),
        ]
        candidates = discover_candidates(events, "src-1")
        self.assertEqual(len(candidates), 1)
        self.assertIn("explicit_failure_feedback", candidates[0]["discovery_signals"])
        self.assertNotIn("rework_or_revision", candidates[0]["discovery_signals"])

    def test_approval_does_not_create_candidate(self):
        events = [event("e1", 1, "user", "user_feedback", feedback_kind="approval")]
        self.assertEqual(discover_candidates(events, "src-1"), [])

    def test_long_horizon_is_only_a_discovery_signal(self):
        events = correction_trace()
        events.extend([
            event("e7", 7, "tool", "tool_call"),
            event("e8", 8, "tool", "tool_result"),
            event("e9", 9, "assistant", "assistant_message"),
            event("e10", 10, "user", "user_message"),
            event("e11", 11, "assistant", "assistant_message"),
            event("e12", 12, "assistant", "assistant_message"),
        ])
        candidates = discover_candidates(events, "src-1", min_turns=4)
        self.assertIn("long_horizon_execution", candidates[0]["discovery_signals"])
        self.assertEqual(candidates[0]["status"], "discovered")

    def test_duplicate_sequence_is_rejected(self):
        events = correction_trace()
        events[1]["sequence"] = events[0]["sequence"]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            path.write_text("\n".join(json.dumps(item) for item in events), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate sequence"):
                read_events(path)

    def test_missing_feedback_kind_is_rejected_by_event_schema(self):
        events = [event("e1", 1, "user", "user_feedback")]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            path.write_text(json.dumps(events[0]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid trajectory event"):
                read_events(path)

    def test_raw_content_field_is_rejected(self):
        events = [event("e1", 1, "user", "user_message", raw_message="private text")]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            path.write_text(json.dumps(events[0]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Additional properties"):
                read_events(path)

    def test_candidate_prefix_is_validated_by_candidate_schema(self):
        with self.assertRaisesRegex(ValueError, "violates schema"):
            discover_candidates(correction_trace(), "src-1", candidate_prefix="bad prefix")


if __name__ == "__main__":
    unittest.main()
