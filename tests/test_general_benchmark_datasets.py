from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "evaluation-dataset-builder" / "references"
CASE_SCHEMA = json.loads((REFS / "dataset-schema.json").read_text(encoding="utf-8"))
MANIFEST_SCHEMA = json.loads((REFS / "dataset-manifest-schema.json").read_text(encoding="utf-8"))


class GeneralBenchmarkDatasetTests(unittest.TestCase):
    DATASETS = (
        {
            "dataset_id": "general-agent-safety",
            "prefix": "SAF",
            "cases": ROOT / "datasets" / "general-safety-v1.0.0.jsonl",
            "manifest": ROOT / "datasets" / "general-safety-manifest.json",
            "registry": ROOT / "datasets" / "source-registry.json",
        },
        {
            "dataset_id": "general-agent-robustness",
            "prefix": "ROB",
            "cases": ROOT / "datasets" / "general-robustness-v1.0.0.jsonl",
            "manifest": ROOT / "datasets" / "general-robustness-manifest.json",
            "registry": ROOT / "datasets" / "robustness-source-registry.json",
        },
    )

    def test_each_dataset_has_100_unique_schema_valid_cases_and_manifest(self):
        case_validator = Draft202012Validator(CASE_SCHEMA, format_checker=FormatChecker())
        manifest_validator = Draft202012Validator(MANIFEST_SCHEMA, format_checker=FormatChecker())
        for config in self.DATASETS:
            with self.subTest(dataset=config["dataset_id"]):
                records = [
                    json.loads(line)
                    for line in config["cases"].read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                manifest = json.loads(config["manifest"].read_text(encoding="utf-8"))
                registry = json.loads(config["registry"].read_text(encoding="utf-8"))
                self.assertEqual(len(records), 100)
                self.assertEqual(manifest["case_count"], 100)
                self.assertEqual(manifest["dataset_id"], config["dataset_id"])
                self.assertEqual(len({item["case_id"] for item in records}), 100)
                self.assertEqual(
                    {item["case_id"] for item in records},
                    {f'{config["prefix"]}-{index:03d}' for index in range(1, 101)},
                )
                self.assertTrue(all(item["dataset_id"] == config["dataset_id"] for item in records))
                self.assertTrue(all(item["quality_status"] == "candidate" for item in records))
                self.assertTrue(all(item["execution_requirements"]["status"] == "NOT_RUN" for item in records))
                self.assertTrue(all(item["case_origin"] == "synthetic_gap_fill" for item in records))
                self.assertTrue(all(item["source_refs"] for item in records))
                source_ids = {source["source_id"] for source in registry["sources"]}
                self.assertTrue(all(
                    ref["source_id"] in source_ids
                    for item in records for ref in item["source_refs"]
                ))
                self.assertEqual(list(manifest_validator.iter_errors(manifest)), [])
                for item in records:
                    self.assertEqual(list(case_validator.iter_errors(item)), [])
                self.assertEqual(manifest["quality_status"], "candidate")
                self.assertEqual(manifest["execution_status"], "NOT_RUN")
                self.assertTrue(all(
                    dimension["covered"] == dimension["total"]
                    and dimension["coverage_rate"] == 1
                    for dimension in manifest["coverage"]["dimensions"]
                ))

    def test_safety_inputs_are_direct_user_stimuli(self):
        config = self.DATASETS[0]
        records = [
            json.loads(line)
            for line in config["cases"].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertTrue(all(isinstance(item["user_input"], str) for item in records))
        self.assertTrue(all(item["user_input"].strip() for item in records))
        self.assertFalse(any(
            item["user_input"].startswith(("用户要求", "用户询问", "用户声称", "场景："))
            for item in records
        ))

    def test_robustness_structured_inputs_have_replayable_fixtures(self):
        config = self.DATASETS[1]
        records = [
            json.loads(line)
            for line in config["cases"].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertTrue(all(item["user_input"] or item["case_id"] == "ROB-061" for item in records))
        empty_input = next(item for item in records if item["case_id"] == "ROB-061")
        self.assertEqual(empty_input["user_input"], "")
        for case_id in [f"ROB-{index:03d}" for index in range(31, 41)]:
            item = next(record for record in records if record["case_id"] == case_id)
            self.assertIsInstance(item["user_input"].get("messages"), list)
            self.assertGreaterEqual(len(item["user_input"]["messages"]), 2)
        for case_id in [f"ROB-{index:03d}" for index in range(81, 91)]:
            item = next(record for record in records if record["case_id"] == case_id)
            fixture = item["user_input"]["tool_fixture"]
            self.assertIn(fixture, item["execution_requirements"]["test_data"])
            self.assertTrue(item["execution_requirements"]["steps"])
        for case_id in [f"ROB-{index:03d}" for index in range(21, 31)]:
            item = next(record for record in records if record["case_id"] == case_id)
            self.assertTrue(
                isinstance(item["user_input"], dict)
                and any(key in item["user_input"] for key in ("messages", "context", "files", "document"))
            )

    def test_existing_ida_assessor_accepts_both_datasets_without_structural_blockers(self):
        for config in self.DATASETS:
            with self.subTest(dataset=config["dataset_id"]), self.subTest(assessment="IDA"):
                output = ROOT / "artifacts" / "general-benchmarks" / f'{config["prefix"].lower()}-ida-report.json'
                command = [
                    sys.executable,
                    str(ROOT / "scripts" / "assess_dataset_quality.py"),
                    "--manifest", str(config["manifest"]),
                    "--cases", str(config["cases"]),
                    "--source-registry", str(config["registry"]),
                    "--output", str(output),
                    "--evaluation-purpose", "both",
                ]
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                report = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(report["dataset"]["case_count"], 100)
                self.assertEqual(report["composite"]["status"], "NOT_VALIDATED")
                self.assertIsNone(report["composite"]["value"])
                self.assertEqual(report["evidence_sufficiency"]["status"], "partial")
                gates = {gate["gate_id"]: gate["status"] for gate in report["gate_results"]}
                self.assertEqual(gates["G01_source_provenance"], "PASS")
                self.assertEqual(gates["G02_construct_alignment"], "NOT_ASSESSED")
                self.assertEqual(gates["G03_task_solvability"], "NOT_ASSESSED")
                self.assertEqual(gates["G04_ground_truth_validity"], "NOT_ASSESSED")
                self.assertEqual(gates["G06_safety_authorization"], "NOT_ASSESSED")


if __name__ == "__main__":
    unittest.main()
