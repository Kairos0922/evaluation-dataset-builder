import json
import tempfile
import unittest
from pathlib import Path

from scripts.assess_runtime_quality import build_era_report
from scripts.validate_quality_assessment import validate_report


def runtime_record(run_id, revision, case_id, agent_outcome, gold_outcome, grader_outcome,
                   pair_id=None, repeat_group_id=None, fault_kind="none", fault_id=None,
                   fault_detected=None, failure_exposed=None, grader_id="judge-a"):
    return {
        "record_version": "0.0.2",
        "run_id": run_id,
        "dataset_id": "runtime-demo",
        "dataset_sha256": "c" * 64,
        "case_id": case_id,
        "configuration_id": f"config-{revision}",
        "target_revision": revision,
        "target_type": "agent_with_skill",
        "model": {"provider": "example", "model_id": "model-a", "revision": "r1"},
        "harness": {"name": "test-harness", "version": "1.0"},
        "environment": {"name": "sandbox", "version": "1", "digest": "sha256:abc"},
        "tool_versions": {"search": "1.0"},
        "status": "valid",
        "seed": 7,
        "pair_id": pair_id,
        "repeat_group_id": repeat_group_id,
        "started_at": "2026-11-25T07:00:00Z",
        "trace_ref": f"trace://{run_id}",
        "result_ref": f"result://{run_id}",
        "outcomes": {
            "agent_outcome": agent_outcome,
            "process_outcome": "pass",
            "grader_outcome": grader_outcome,
            "gold_outcome": gold_outcome,
            "grader_id": grader_id,
            "grader_revision": "1",
            "gold_source": "independent_oracle" if gold_outcome != "unknown" else "not_available"
        },
        "fault": {
            "kind": fault_kind,
            "fault_id": fault_id,
            "injected": fault_kind != "none",
            "detected": fault_detected,
            "failure_exposed": failure_exposed
        },
        "cost": {
            "duration_seconds": 10.0,
            "input_tokens": 100,
            "output_tokens": 50,
            "tool_calls": 2,
            "cost_usd": 0.01
        }
    }


class RuntimeAssessmentTests(unittest.TestCase):
    def write_records(self, directory, records):
        path = directory / "runtime-records.jsonl"
        path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
        return path

    def test_runtime_report_computes_grader_and_paired_regression_metrics(self):
        records = [
            runtime_record("b1", "baseline", "CASE-1", "pass", "fail", "pass", pair_id="P1", repeat_group_id="R1"),
            runtime_record("c1", "candidate", "CASE-1", "fail", "fail", "fail", pair_id="P1"),
            runtime_record("b2", "baseline", "CASE-2", "fail", "pass", "fail", pair_id="P2"),
            runtime_record("c2", "candidate", "CASE-2", "pass", "pass", "pass", pair_id="P2"),
            runtime_record("b1-repeat", "baseline", "CASE-1", "fail", "unknown", "unknown", repeat_group_id="R1"),
            runtime_record("h1", "candidate", "CASE-3", "fail", "unknown", "unknown", fault_kind="historical", fault_id="H1", fault_detected=False, failure_exposed=False),
            runtime_record("m1", "candidate", "CASE-4", "pass", "unknown", "unknown", fault_kind="mutation", fault_id="M1", fault_detected=False, failure_exposed=False),
            runtime_record("j1", "candidate", "CASE-5", "pass", "pass", "abstain")
        ]
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            records_path = self.write_records(directory, records)
            report = build_era_report(
                records_path,
                directory / "era-report.json",
                "1.0.0",
                "demo-agent",
                "both",
                baseline_revision="baseline",
                candidate_revision="candidate",
                bootstrap_resamples=200
            )
            self.assertEqual(report["grader_validation"]["sample_count"], 5)
            grader_false_pass = next(item for item in report["metric_results"] if item["metric_id"] == "ERA-GRD-01")
            self.assertEqual(grader_false_pass["value"], 0.5)
            grader_abstention = next(item for item in report["metric_results"] if item["metric_id"] == "ERA-GRD-03")
            self.assertEqual(grader_abstention["value"], 0.2)
            grader_false_fail = next(item for item in report["metric_results"] if item["metric_id"] == "ERA-GRD-02")
            self.assertEqual(grader_false_fail["value"], 0.5)
            historical_detection = next(item for item in report["metric_results"] if item["metric_id"] == "REG-01")
            self.assertEqual(historical_detection["value"], 0.0)
            historical_exposure = next(item for item in report["metric_results"] if item["metric_id"] == "REG-07")
            self.assertEqual(historical_exposure["value"], 0.0)
            all_fault_exposure = next(item for item in report["metric_results"] if item["metric_id"] == "ERA-RUN-05")
            self.assertEqual(all_fault_exposure["value"], 0.0)
            regression = next(item for item in report["metric_results"] if item["metric_id"] == "REG-03")
            self.assertEqual(regression["value"]["candidate_minus_baseline_pass_rate"], 0.0)
            self.assertEqual(regression["value"]["baseline_pass_to_candidate_fail"], 1)
            self.assertEqual(regression["value"]["baseline_fail_to_candidate_pass"], 1)
            flakiness = next(item for item in report["metric_results"] if item["metric_id"] == "REG-06")
            self.assertEqual(flakiness["value"], 1.0)
            self.assertEqual(report["composite"]["status"], "NOT_VALIDATED")
            self.assertIsNone(report["composite"]["value"])
            self.assertEqual(validate_report(report), [])

    def test_missing_judge_is_not_misreported_as_abstention_or_zero_false_pass(self):
        record = runtime_record("oracle-only", "current", "CASE-1", "pass", "pass", "unknown", grader_id=None)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            records_path = self.write_records(directory, [record])
            report = build_era_report(records_path, directory / "era-report.json", "1.0.0", "demo-agent", "capability")
            self.assertEqual(report["grader_validation"]["status"], "NOT_RUN")
            self.assertEqual(report["grader_validation"]["sample_count"], 0)
            self.assertTrue(any(f["finding_id"] == "ERA-NO-GRADER" for f in report["findings"]))
            for metric_id in ("ERA-GRD-01", "ERA-GRD-02", "ERA-GRD-03", "ERA-GRD-04"):
                metric = next(item for item in report["metric_results"] if item["metric_id"] == metric_id)
                self.assertEqual(metric["status"], "NOT_ASSESSED")
                self.assertIsNone(metric["value"])
            self.assertEqual(validate_report(report), [])

    def test_runtime_analyzer_rejects_invalid_records(self):
        record = runtime_record("bad", "candidate", "CASE-1", "pass", "pass", "pass")
        record["trace_ref"] = None
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            records_path = self.write_records(directory, [record])
            with self.assertRaises(ValueError):
                build_era_report(
                    records_path,
                    directory / "era-report.json",
                    "1.0.0",
                    "demo-agent",
                    "capability"
                )

    def test_capability_only_report_does_not_require_regression_pairing(self):
        record = runtime_record("one", "current", "CASE-1", "pass", "unknown", "unknown")
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            records_path = self.write_records(directory, [record])
            report = build_era_report(
                records_path,
                directory / "era-report.json",
                "1.0.0",
                "demo-agent",
                "capability",
                bootstrap_resamples=100
            )
            self.assertIsNone(report["regression_analysis"])
            self.assertEqual(report["capability_analysis"]["status"], "PARTIAL")
            self.assertEqual(validate_report(report), [])


if __name__ == "__main__":
    unittest.main()
