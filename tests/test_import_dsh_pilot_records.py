import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.import_dsh_pilot_records import (
    build_runtime_record, dataset_digest, runner_is_valid, verify_pilot_evidence, load_jsonl
)


def runner_result(case_id="WB-02", mutations=None):
    return {
        "case_id": case_id,
        "run_id": f"run-{case_id}",
        "runner_status": "INVOCATION_OK",
        "started_at_utc": "2026-11-23T14:00:45.933166+00:00",
        "webapp_testing_skill_commit": "2c5958ecac7cee2b583967a2c4981d0f4a75c579",
        "fixture_mutations": mutations or [],
        "dsh_exit_code": 0,
        "case_budget_status": "PASS",
        "runner_error": None,
        "server_health": {"status": "ok"},
        "server_port_closed": True,
        "dsh_elapsed_seconds": 89.4,
        "required_skill_evidence": {
            "markdown_report": True,
            "json_evidence_index": True,
            "screenshot": True
        },
        "trace": {
            "final_reason": "completed",
            "webapp_testing_skill_calls": 1,
            "completed_skill_calls": 1,
            "usage": {
                "usage_totals": {
                    "inputTokens": 100,
                    "outputTokens": 50,
                    "cacheReadTokens": 200,
                    "cacheWriteTokens": 0,
                    "totalTokens": 350
                },
                "model_step_count": 4,
                "tool_call_count": 3
            }
        }
    }


def oracle_case(case_id="WB-02", mutation_detected=True):
    return {
        "case_id": case_id,
        "execution_valid": True,
        "adjudication_status": "PASS",
        "contract_verdict": "PASS",
        "oracle_verdict": "PASS",
        "business_behavior_verdict": "EXPECTED_VIOLATION_DETECTED" if mutation_detected else "PASS",
        "checks": [
            {"status": "PASS", "check": "Target report correctly identifies and supports the BR-02 violation"}
        ]
    }


class ImportDshPilotRecordsTests(unittest.TestCase):
    def test_trace_must_be_hash_bound_and_valid_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            pilot_dir = Path(directory)
            trace = pilot_dir / "dsh-events.jsonl"
            trace.write_text(json.dumps({
                "run_id": "run-WB-02", "case_id": "WB-02", "event": "completed"
            }) + "\n", encoding="utf-8")
            digest = hashlib.sha256(trace.read_bytes()).hexdigest()
            runner = runner_result()
            runner["evidence_files"] = [{"path": "dsh-events.jsonl", "sha256": digest}]
            self.assertEqual(verify_pilot_evidence(pilot_dir, runner)["dsh-events.jsonl"], digest)

    def test_trace_without_manifest_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            pilot_dir = Path(directory)
            (pilot_dir / "dsh-events.jsonl").write_text('{"event":"done"}\n', encoding="utf-8")
            runner = runner_result()
            runner["evidence_files"] = []
            with self.assertRaisesRegex(ValueError, "missing evidence_files manifest"):
                verify_pilot_evidence(pilot_dir, runner)

    def test_trace_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            pilot_dir = Path(directory)
            (pilot_dir / "dsh-events.jsonl").write_text('{"event":"done"}\n', encoding="utf-8")
            runner = runner_result()
            runner["evidence_files"] = [{"path": "dsh-events.jsonl", "sha256": "0" * 64}]
            with self.assertRaisesRegex(ValueError, "evidence hash mismatch"):
                verify_pilot_evidence(pilot_dir, runner)

    def test_trace_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            pilot_dir = Path(directory)
            runner = runner_result()
            runner["evidence_files"] = [{"path": "../outside.jsonl", "sha256": "0" * 64}]
            with self.assertRaisesRegex(ValueError, "unsafe evidence path"):
                verify_pilot_evidence(pilot_dir, runner)

    def test_dataset_digest_is_versioned_and_deterministic(self):
        first = dataset_digest(b'{"dataset_id":"d"}', b'{"case_id":"c"}\n')
        second = dataset_digest(b'{"dataset_id":"d"}', b'{"case_id":"c"}\n')
        changed = dataset_digest(b'{"dataset_id":"d"}', b'{"case_id":"changed"}\n')
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertEqual(len(first), 64)

    def test_mutated_fixture_maps_to_detection_and_exposure_without_claiming_judge(self):
        runner = runner_result(mutations=["search-case-sensitive"])
        oracle = oracle_case()
        self.assertTrue(runner_is_valid(runner, oracle))
        record = build_runtime_record("WB-02", runner, oracle, "wb-core", "a" * 64)
        self.assertEqual(record["target_type"], "skill")
        self.assertEqual(record["outcomes"]["agent_outcome"], "pass")
        self.assertEqual(record["outcomes"]["gold_outcome"], "pass")
        self.assertEqual(record["outcomes"]["gold_source"], "independent_oracle")
        self.assertEqual(record["outcomes"]["grader_outcome"], "unknown")
        self.assertIsNone(record["outcomes"]["grader_id"])
        self.assertEqual(record["fault"]["kind"], "mutation")
        self.assertTrue(record["fault"]["injected"])
        self.assertTrue(record["fault"]["detected"])
        self.assertTrue(record["fault"]["failure_exposed"])
        self.assertEqual(record["cost"]["cache_read_tokens"], 200)
        self.assertEqual(record["cost"]["total_tokens"], 350)
        self.assertEqual(record["cost"]["model_steps"], 4)
        self.assertIsNone(record["cost"]["cost_usd"])
        record_with_trace = build_runtime_record(
            "WB-02", runner, oracle, "wb-core", "a" * 64, trace_sha256="b" * 64
        )
        self.assertEqual(record_with_trace["trace_sha256"], "b" * 64)

    def test_clean_fixture_has_no_injected_fault(self):
        record = build_runtime_record(
            "WB-10",
            runner_result("WB-10"),
            oracle_case("WB-10", mutation_detected=False),
            "wb-core",
            "b" * 64
        )
        self.assertEqual(record["fault"]["kind"], "none")
        self.assertFalse(record["fault"]["injected"])
        self.assertIsNone(record["fault"]["detected"])
        self.assertIsNone(record["fault"]["failure_exposed"])

    def test_oracle_failure_invalidates_execution_record(self):
        oracle = oracle_case()
        oracle["checks"][0]["status"] = "FAIL"
        self.assertFalse(runner_is_valid(runner_result(), oracle))


    def test_uppercase_trace_digest_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            pilot_dir = Path(directory)
            trace = pilot_dir / "dsh-events.jsonl"
            trace.write_text(json.dumps({
                "run_id": "run-WB-02", "case_id": "WB-02", "event": "completed"
            }) + "\n", encoding="utf-8")
            digest = hashlib.sha256(trace.read_bytes()).hexdigest().upper()
            runner = runner_result()
            runner["evidence_files"] = [{"path": "dsh-events.jsonl", "sha256": digest}]
            self.assertEqual(verify_pilot_evidence(pilot_dir, runner)["dsh-events.jsonl"], digest.lower())

class StrictJsonInputTests(unittest.TestCase):
    def test_cases_jsonl_rejects_nan(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.jsonl"
            path.write_text('{"case_id":"WB-01","score":NaN}\\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid JSON numeric constant"):
                load_jsonl(path)


if __name__ == "__main__":
    unittest.main()
