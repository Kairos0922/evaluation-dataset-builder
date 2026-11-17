"""Tests for Builder DSH failure and external quota classification."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "classify_builder_run.py"
SPEC = importlib.util.spec_from_file_location("classify_builder_run", SCRIPT)
CLASSIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLASSIFIER)


class BuilderRunClassificationTests(unittest.TestCase):
    def make_artifacts(self, root: Path) -> Path:
        artifacts = root / "artifacts"
        artifacts.mkdir()
        return artifacts

    def write_exit(self, artifacts: Path, code: int) -> None:
        (artifacts / "builder-dsh-exit-code.txt").write_text(str(code), encoding="utf-8")

    def test_http_402_in_builder_stderr_is_external_quota_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = self.make_artifacts(Path(directory))
            self.write_exit(artifacts, 1)
            (artifacts / "builder-dsh-stderr.log").write_text(
                "HTTP 402 Insufficient Balance", encoding="utf-8"
            )
            output = artifacts / "webapp-testing-builder-output"
            output.mkdir()
            (output / "partial.json").write_text("{}", encoding="utf-8")
            result = CLASSIFIER.classify_builder_run(artifacts)
            self.assertEqual(result["status"], "EXTERNAL_MODEL_QUOTA_BLOCKED")
            self.assertEqual(result["quota_error_sources"], ["builder_invocation"])
            self.assertEqual(result["partial_output_disposition"], "DIAGNOSTIC_ONLY")
            self.assertFalse(result["independent_validation_allowed"])
            self.assertFalse(result["automatic_full_builder_retry"])

    def test_quota_probe_is_classified_without_builder_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = self.make_artifacts(Path(directory))
            (artifacts / "builder-connectivity-probe.json").write_text(
                json.dumps({"status": "EXTERNAL_MODEL_QUOTA_BLOCKED"}),
                encoding="utf-8",
            )
            result = CLASSIFIER.classify_builder_run(artifacts)
            self.assertEqual(result["status"], "EXTERNAL_MODEL_QUOTA_BLOCKED")
            self.assertEqual(result["quota_error_sources"], ["connectivity_probe"])
            self.assertFalse(result["builder_invocation_started"])

    def test_quota_keyword_in_builder_event_is_classified(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = self.make_artifacts(Path(directory))
            self.write_exit(artifacts, 1)
            (artifacts / "builder-dsh-events.jsonl").write_text(
                '{"type":"error","message":"QUOTA_EXCEEDED"}\\n',
                encoding="utf-8",
            )
            result = CLASSIFIER.classify_builder_run(artifacts)
            self.assertEqual(result["status"], "EXTERNAL_MODEL_QUOTA_BLOCKED")

    def test_non_quota_failure_remains_an_invocation_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = self.make_artifacts(Path(directory))
            self.write_exit(artifacts, 2)
            (artifacts / "builder-dsh-stderr.log").write_text(
                "unexpected process termination", encoding="utf-8"
            )
            result = CLASSIFIER.classify_builder_run(artifacts)
            self.assertEqual(result["status"], "BUILDER_INVOCATION_FAILED")
            self.assertEqual(result["partial_output_disposition"], "DIAGNOSTIC_ONLY")
            self.assertFalse(result["independent_validation_allowed"])

    def test_success_only_allows_trace_verification_not_independent_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = self.make_artifacts(Path(directory))
            self.write_exit(artifacts, 0)
            (artifacts / "builder-dsh-events.jsonl").write_text(
                '{"type":"final","reason":{"kind":"completed"}}\\n',
                encoding="utf-8",
            )
            result = CLASSIFIER.classify_builder_run(artifacts)
            self.assertEqual(result["status"], "DSH_EXIT_ZERO")
            self.assertTrue(result["trace_verification_allowed"])
            self.assertFalse(result["independent_validation_allowed"])

    def test_non_quota_probe_failure_is_classified_before_builder(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = self.make_artifacts(Path(directory))
            (artifacts / "builder-connectivity-probe.json").write_text(
                json.dumps({"status": "PROBE_FAILED"}),
                encoding="utf-8",
            )
            result = CLASSIFIER.classify_builder_run(artifacts)
            self.assertEqual(result["status"], "CONNECTIVITY_PROBE_FAILED")
            self.assertFalse(result["builder_invocation_started"])


if __name__ == "__main__":
    unittest.main()
