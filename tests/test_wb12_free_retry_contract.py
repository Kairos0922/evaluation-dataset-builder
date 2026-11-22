"""Safety contract for the Round 4 WB-12 free-model-only retry."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "retry-wb12-only.yml"


class WB12FreeRetryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_uses_only_the_existing_openrouter_secret(self):
        self.assertIn("secrets.OPENROUTER_API_KEY", self.text)
        self.assertNotIn("secrets.DEEPSEEK_API_KEY", self.text)
        self.assertNotIn("DEEPSEEK_API_KEY:", self.text)
        self.assertNotIn("deepseek-flash", self.text)

    def test_model_is_explicitly_free_and_tool_capable_candidate(self):
        self.assertIn("inclusionai/ling-3.2-flash:free", self.text)
        self.assertIn("api: openai-completions", self.text)
        self.assertIn("baseURL: https://openrouter.ai/api/v1", self.text)

    def test_quota_gate_precedes_any_dsh_execution(self):
        quota = self.text.index("Check OpenRouter free quota before any model request")
        install = self.text.index("Install Node and pinned DSH CLI")
        execute = self.text.index("Execute only WB-12 with the verified free model")
        self.assertLess(quota, install)
        self.assertLess(install, execute)
        self.assertIn("remaining >= 37", self.text)
        self.assertIn('"generation_requests_sent":0', self.text)
        self.assertIn('"paid_requests_sent":0', self.text)

    def test_retry_is_bound_to_the_original_builder_case_only(self):
        self.assertIn('SOURCE_RUN_ID: "44980451933"', self.text)
        self.assertIn('--case-id WB-12', self.text)
        self.assertIn('--max-model-steps 40', self.text)
        self.assertNotIn("run-builder-production", self.text)
        self.assertNotIn("execute-builder-production", self.text)

    def test_telemetry_and_evidence_archival_remain_enabled(self):
        self.assertIn("DSH_TELEMETRY_DISABLED: \"1\"", self.text)
        self.assertIn("session-log-deepseek", self.text)
        self.assertIn("if: always()", self.text)
        self.assertIn("round4-wb12-retry-only", self.text)


if __name__ == "__main__":
    unittest.main()
