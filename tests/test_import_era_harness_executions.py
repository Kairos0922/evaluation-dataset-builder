import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.build_era_run_plan import build_era_run_plan
from scripts.import_era_harness_executions import import_harness_executions, main
from tests.test_build_era_run_plan import make_case, make_configuration, make_manifest


def make_plan():
    case = make_case()
    manifest = make_manifest(1)
    manifest_bytes = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    cases_bytes = (json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n").encode()
    return build_era_run_plan(manifest, manifest_bytes, [case], cases_bytes, make_configuration())


def make_record(plan):
    config = plan["configuration"]
    return {
        "record_version": "0.0.2",
        "run_id": "synthetic-run-001",
        "dataset_id": plan["dataset"]["dataset_id"],
        "dataset_sha256": plan["dataset"]["dataset_sha256"],
        "case_id": plan["planned_cases"][0]["case_id"],
        "configuration_id": config["configuration_id"],
        "target_revision": config["target_revision"],
        "target_type": config["target_type"],
        "model": config["model"],
        "harness": config["harness"],
        "environment": config["environment"],
        "tool_versions": config["tool_versions"],
        "status": "unknown",
        "seed": config["seed"],
        "pair_id": None,
        "repeat_group_id": None,
        "started_at": "2026-11-28T10:00:00Z",
        "trace_ref": "synthetic://fresh-run/trace.jsonl",
        "trace_sha256": "a" * 64,
        "result_ref": "synthetic://fresh-run/result.json",
        "outcomes": {
            "agent_outcome": "unknown",
            "process_outcome": "unknown",
            "grader_outcome": "unknown",
            "gold_outcome": "unknown",
            "grader_id": None,
            "grader_revision": None,
            "gold_source": "not_available"
        },
        "fault": {"kind": "none", "fault_id": None, "injected": False, "detected": None, "failure_exposed": None},
        "cost": {"duration_seconds": None, "input_tokens": None, "output_tokens": None,
                 "cache_read_tokens": None, "cache_write_tokens": None, "total_tokens": None,
                 "model_steps": None, "tool_calls": None, "cost_usd": None}
    }


def make_envelope(plan):
    return {
        "plan_id": plan["plan_id"],
        "case_id": plan["planned_cases"][0]["case_id"],
        "session_id": "synthetic-fresh-session-001",
        "runtime_record": make_record(plan)
    }


class ImportEraHarnessExecutionsTests(unittest.TestCase):
    def test_imports_fresh_harness_record_without_changing_runtime_schema(self):
        plan = make_plan()
        records = import_harness_executions(plan, [make_envelope(plan)])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_version"], "0.0.2")
        self.assertEqual(records[0]["gold_outcome"] if "gold_outcome" in records[0] else records[0]["outcomes"]["gold_outcome"], "unknown")

    def test_rejects_historical_source_trace_reuse(self):
        plan = make_plan()
        envelope = make_envelope(plan)
        envelope["runtime_record"]["trace_ref"] = plan["planned_cases"][0]["historical_source_refs"][0]["locator"]
        with self.assertRaisesRegex(ValueError, "historical source"):
            import_harness_executions(plan, [envelope])

    def test_rejects_reused_session(self):
        plan = make_plan()
        second_case = make_case("CASE-SYNTHETIC-002")
        manifest = make_manifest(2)
        manifest_bytes = (json.dumps(manifest, sort_keys=True) + "\n").encode()
        cases_bytes = "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in [make_case(), second_case]).encode()
        plan = build_era_run_plan(manifest, manifest_bytes, [make_case(), second_case], cases_bytes, make_configuration())
        first = make_envelope(plan)
        second = copy.deepcopy(first)
        second["case_id"] = "CASE-SYNTHETIC-002"
        second["runtime_record"]["case_id"] = second["case_id"]
        second["runtime_record"]["run_id"] = "synthetic-run-002"
        with self.assertRaisesRegex(ValueError, "session_id reused"):
            import_harness_executions(plan, [first, second])

    def test_rejects_wrong_dataset_digest_or_frozen_configuration(self):
        plan = make_plan()
        envelope = make_envelope(plan)
        envelope["runtime_record"]["dataset_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "dataset_sha256"):
            import_harness_executions(plan, [envelope])

    def test_missing_oracle_must_remain_unknown(self):
        plan = make_plan()
        envelope = make_envelope(plan)
        envelope["runtime_record"]["outcomes"]["gold_outcome"] = "pass"
        envelope["runtime_record"]["outcomes"]["gold_source"] = "independent_oracle"
        with self.assertRaisesRegex(ValueError, "no independent Oracle"):
            import_harness_executions(plan, [envelope])

    def test_requires_new_trace_hash_and_result_reference(self):
        plan = make_plan()
        envelope = make_envelope(plan)
        envelope["runtime_record"]["trace_sha256"] = None
        with self.assertRaisesRegex(ValueError, "trace_sha256"):
            import_harness_executions(plan, [envelope])

    def test_rejects_envelope_with_unrecognized_fields(self):
        plan = make_plan()
        envelope = make_envelope(plan)
        envelope["agent_prompt"] = "should not be embedded in the transport envelope"
        with self.assertRaisesRegex(ValueError, "envelope schema validation failed"):
            import_harness_executions(plan, [envelope])

    def test_rejects_missing_session_id_at_schema_boundary(self):
        plan = make_plan()
        envelope = make_envelope(plan)
        del envelope["session_id"]
        with self.assertRaisesRegex(ValueError, "envelope schema validation failed"):
            import_harness_executions(plan, [envelope])

    def test_cli_writes_existing_runtime_record_jsonl(self):
        plan = make_plan()
        envelope = make_envelope(plan)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path, executions_path, output_path = root / "plan.json", root / "executions.jsonl", root / "records.jsonl"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            executions_path.write_text(json.dumps(envelope) + "\n", encoding="utf-8")
            with patch("sys.argv", ["import_era_harness_executions.py", "--plan", str(plan_path),
                                    "--executions", str(executions_path), "--output", str(output_path)]):
                self.assertEqual(main(), 0)
            rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["case_id"], envelope["case_id"])


if __name__ == "__main__":
    unittest.main()
