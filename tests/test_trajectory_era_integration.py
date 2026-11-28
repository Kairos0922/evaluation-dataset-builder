import json
import tempfile
import unittest
from pathlib import Path

from scripts.assess_runtime_quality import build_era_report, load_records
from scripts.validate_quality_assessment import validate_report


class TrajectoryEraIntegrationTests(unittest.TestCase):
    def test_new_clean_run_binds_existing_case_without_reusing_source_trace(self):
        # SYNTHETIC / ILLUSTRATIVE_ONLY: this verifies the existing Runtime Record
        # and ERA contracts, not an actual Agent execution or a real capability claim.
        historical_source_trace = "trace-source://authorized-history/events-10-18"
        clean_run_trace = "trace-runtime://synthetic-clean-run/run-001"
        record = {
            "record_version": "0.0.2",
            "run_id": "synthetic-clean-run-001",
            "dataset_id": "trajectory-derived-demo",
            "dataset_sha256": "d" * 64,
            "case_id": "TRACE-CASE-001",
            "configuration_id": "synthetic-agent-config-v1",
            "target_revision": "agent-revision-synthetic",
            "target_type": "agent",
            "model": {"provider": "synthetic", "model_id": "illustrative-model", "revision": None},
            "harness": {"name": "synthetic-harness", "version": "1.0"},
            "environment": {"name": "isolated-synthetic-env", "version": "1.0", "digest": None, "region": None},
            "tool_versions": {"synthetic-tool": "1.0"},
            "status": "valid",
            "seed": 17,
            "pair_id": None,
            "repeat_group_id": None,
            "started_at": "2026-11-28T00:00:00Z",
            "trace_ref": clean_run_trace,
            "result_ref": "result://synthetic-clean-run/run-001",
            "outcomes": {
                "agent_outcome": "unknown",
                "process_outcome": "pass",
                "grader_outcome": "unknown",
                "gold_outcome": "unknown",
                "grader_id": None,
                "grader_revision": None,
                "gold_source": "not_available"
            },
            "fault": {
                "kind": "none",
                "fault_id": None,
                "injected": False,
                "detected": None,
                "failure_exposed": None
            },
            "cost": {
                "duration_seconds": 12.0,
                "input_tokens": None,
                "output_tokens": None,
                "tool_calls": 1,
                "cost_usd": None
            }
        }

        self.assertNotEqual(historical_source_trace, record["trace_ref"])
        self.assertEqual(record["case_id"], "TRACE-CASE-001")
        self.assertEqual(len(record["dataset_sha256"]), 64)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records_path = root / "runtime-records.synthetic.jsonl"
            records_path.write_text(json.dumps(record) + "\\n", encoding="utf-8")
            loaded, errors = load_records(records_path)
            self.assertEqual(errors, [])
            self.assertEqual(len(loaded), 1)

            report = build_era_report(
                records_path,
                root / "era-report.synthetic.json",
                "0.0.3-synthetic",
                "trajectory-integration-fixture",
                "capability",
                bootstrap_resamples=100
            )

            self.assertEqual(validate_report(report), [])
            self.assertEqual(report["dataset"]["dataset_id"], "trajectory-derived-demo")
            self.assertEqual(report["dataset"]["sha256"], record["dataset_sha256"])
            self.assertEqual(report["runs"][0]["case_id"], record["case_id"])
            self.assertEqual(report["runs"][0]["trace_ref"], clean_run_trace)
            self.assertEqual(report["grader_validation"]["status"], "NOT_RUN")
            self.assertEqual(report["composite"]["status"], "NOT_VALIDATED")
            self.assertIsNone(report["composite"]["value"])


if __name__ == "__main__":
    unittest.main()
