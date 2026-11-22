"""Safety and idempotency contract for the scheduled Round 4 WB-12 retry."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "round4-wb12-free-retry.yml"


class ScheduledWB12RetryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_scheduled_after_daily_quota_monitor(self):
        self.assertIn('cron: "30 8 * * *"', self.text)
        self.assertIn(".github/dispatch/round4-wb12-free-retry-once.txt", self.text)
        self.assertIn('branches: ["main"]', self.text)
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("pull-requests: read", self.text)
        self.assertIn("/pulls/38", self.text)
        self.assertIn("PR #38 is not Draft/Open/Unmerged", self.text)
        self.assertIn("ref: dbbb11a5041f592da2238dd4ea303edd07b40151", self.text)

    def test_uses_only_openrouter_free_model_and_existing_secret(self):
        self.assertIn("secrets.OPENROUTER_API_KEY", self.text)
        self.assertNotIn("secrets.DEEPSEEK_API_KEY", self.text)
        self.assertNotIn("DEEPSEEK_API_KEY:", self.text)
        self.assertIn("inclusionai/ling-3.2-flash:free", self.text)
        self.assertIn("api: openai-completions", self.text)

    def test_quota_gate_is_read_only_and_preserves_original_budget(self):
        self.assertIn("https://openrouter.ai/api/v1/key", self.text)
        self.assertIn("minimum_free_requests_required\":37", self.text)
        self.assertIn("remaining >= 37", self.text)
        self.assertIn('"generation_requests_sent":0', self.text)
        self.assertIn('"paid_requests_sent":0', self.text)
        self.assertIn('"maximum_model_steps":32', self.text)
        self.assertIn("--max-model-steps 32", self.text)

    def test_one_time_marker_prevents_duplicate_model_attempts(self):
        self.assertIn("round4-wb12-attempt-started", self.text)
        self.assertIn("A previous WB-12 model attempt has already started", self.text)
        self.assertIn("paid_fallback", self.text)
        self.assertIn('"paid_fallback":False', self.text)

    def test_only_reuses_original_builder_case_and_two_completed_pilots(self):
        self.assertIn('SOURCE_RUN_ID: "44980451933"', self.text)
        self.assertIn("webapp-testing-pilot-WB-02", self.text)
        self.assertIn("webapp-testing-pilot-WB-10", self.text)
        self.assertIn('--case-id WB-12', self.text)
        self.assertIn('ids!={"WB-02","WB-10","WB-12"}', self.text)
        self.assertNotIn("run-builder-production", self.text)

    def test_oracle_adjudicates_exact_archived_three_case_matrix(self):
        self.assertIn("gold_oracle.py", self.text)
        self.assertIn("--pilot-matrix artifacts/source/pilot-matrix.json", self.text)
        self.assertIn("round4-wb12-free-retry-output", self.text)


if __name__ == "__main__":
    unittest.main()
