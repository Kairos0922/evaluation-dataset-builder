"""Offline unit tests for DeepSeek-backed release-gate logic and fixtures."""
import importlib.util
import io
import json
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_eval", ROOT / "tests" / "run_eval.py")
RUN_EVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN_EVAL)
VERIFY_SPEC = importlib.util.spec_from_file_location(
    "verify_release", ROOT / "scripts" / "verify_release.py"
)
VERIFY_RELEASE = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(VERIFY_RELEASE)
import sys
sys.path.insert(0, str(ROOT / "scripts"))
DOC_SPEC = importlib.util.spec_from_file_location(
    "update_release_doc", ROOT / "scripts" / "update_release_doc.py"
)
UPDATE_RELEASE_DOC = importlib.util.module_from_spec(DOC_SPEC)
DOC_SPEC.loader.exec_module(UPDATE_RELEASE_DOC)
sys.path.pop(0)


class ReleaseGateUnitTests(unittest.TestCase):
    def _valid_release_report(self):
        return {
            "git_sha": "candidate-sha",
            "workflow_run_id": 12345,
            "automated_gate_pass": True,
            "models": {"generator": "deepseek-flash", "judge_and_trigger": "openai/gpt-oss-120b"},
            "api_base_url": "https://api.deepseek.com",
            "judge_api_base_url": "https://api.groq.com/openai/v1",
            "automated_gates": {
                "all_repeated_runs_pass": {"pass": True},
                "baseline_comparison_complete": {"pass": True},
                "stochastic_stability": {"pass": True},
            },
            "policy": {"actual_runs": 2, "trigger_eval_count": 40},
            "runs": [
                {
                    "automated_run_pass": True,
                    "trigger_parse_errors": 0,
                    "skill_cases": [{
                        "id": "SE01",
                        "checks": [{"score": 1, "evidence_validated": True, "evidence": ["quoted evidence"]}],
                    }],
                    "baseline_cases": [{
                        "id": "SE01",
                        "checks": [{"score": 1, "evidence_validated": True, "evidence": ["quoted evidence"]}],
                    }],
                    "trigger_cases": [{} for _ in range(40)],
                    "metrics": {
                        "behavior_pass_rate": 0.92,
                        "trigger_precision": 0.95,
                        "trigger_recall": 0.96,
                    },
                },
                {
                    "automated_run_pass": True,
                    "trigger_parse_errors": 0,
                    "skill_cases": [{
                        "id": "SE01",
                        "checks": [{"score": 1, "evidence_validated": True, "evidence": ["quoted evidence"]}],
                    }],
                    "baseline_cases": [{
                        "id": "SE01",
                        "checks": [{"score": 1, "evidence_validated": True, "evidence": ["quoted evidence"]}],
                    }],
                    "trigger_cases": [{} for _ in range(40)],
                    "metrics": {
                        "behavior_pass_rate": 0.91,
                        "trigger_precision": 0.96,
                        "trigger_recall": 0.96,
                    },
                },
            ],
            "baseline_comparison": {"required": True, "complete": True},
            "stability_gates": {
                "behavior_pass_rate": {"pass": True, "spread": 0.01},
                "trigger_precision": {"pass": True, "spread": 0.01},
                "trigger_recall": {"pass": True, "spread": 0.0},
            },
        }

    def test_release_verifier_accepts_complete_exact_sha_report(self):
        report = self._valid_release_report()
        result = VERIFY_RELEASE.verify_report(report, "candidate-sha", 12345)
        self.assertIs(result, report)

    def test_release_verifier_rejects_behavior_or_baseline_failure(self):
        report = self._valid_release_report()
        report["runs"][1]["metrics"]["behavior_pass_rate"] = 0.8999
        with self.assertRaisesRegex(ValueError, "behavior pass-rate"):
            VERIFY_RELEASE.verify_report(report, "candidate-sha", 12345)
        report = self._valid_release_report()
        report["baseline_comparison"]["complete"] = False
        with self.assertRaisesRegex(ValueError, "matched baseline"):
            VERIFY_RELEASE.verify_report(report, "candidate-sha", 12345)

    def test_release_verifier_rejects_missing_or_unverifiable_suite_evidence(self):
        report = self._valid_release_report()
        report["models"]["judge_and_trigger"] = report["models"]["generator"]
        with self.assertRaisesRegex(ValueError, "distinct"):
            VERIFY_RELEASE.verify_report(report, "candidate-sha", 12345)
        report = self._valid_release_report()
        report["runs"][0]["skill_cases"][0]["checks"][0]["evidence_validated"] = False
        with self.assertRaisesRegex(ValueError, "verified evidence"):
            VERIFY_RELEASE.verify_report(report, "candidate-sha", 12345)
        report = self._valid_release_report()
        report["runs"][1]["trigger_cases"].pop()
        with self.assertRaisesRegex(ValueError, "missing trigger"):
            VERIFY_RELEASE.verify_report(report, "candidate-sha", 12345)

    def test_release_verifier_rejects_wrong_candidate_sha(self):
        with self.assertRaisesRegex(ValueError, "SHA does not match"):
            VERIFY_RELEASE.verify_report(
                self._valid_release_report(), "different-sha", 12345
            )

    def test_release_verifier_requires_independent_approval_on_exact_sha(self):
        critical = "SE03 SE04 SE05 SE08 SE09 SE11 SE12"
        body = (
            "Reviewed " + critical
            + " baseline comparison and spread assessment: acceptable. "
            + "https://github.com/example/repo/actions/runs/12345 "
            + "target-runtime: PASS https://example.com/runtime-report/12345"
        )
        reviews = [{
            "user": {"login": "independent-reviewer"},
            "state": "APPROVED",
            "submitted_at": "2026-11-01T10:00:00Z",
            "commit_id": "candidate-sha",
            "body": body,
        }]
        result = VERIFY_RELEASE.latest_approved_review(
            reviews, "pr-author", "candidate-sha", 12345
        )
        self.assertEqual(result["user"]["login"], "independent-reviewer")
        with self.assertRaisesRegex(ValueError, "No independent APPROVED review"):
            VERIFY_RELEASE.latest_approved_review(
                reviews, "pr-author", "different-sha", 12345
            )

    def test_release_verifier_requires_independent_judge_endpoint(self):
        report = self._valid_release_report()
        report["judge_api_base_url"] = report["api_base_url"]
        with self.assertRaisesRegex(ValueError, "separately configured provider endpoint"):
            VERIFY_RELEASE.verify_report(report, "candidate-sha", 12345)

    def test_release_verifier_requires_target_runtime_evidence_in_review(self):
        critical = "SE03 SE04 SE05 SE08 SE09 SE11 SE12"
        body = (
            "Reviewed " + critical + " baseline and spread. "
            "https://github.com/example/repo/actions/runs/12345"
        )
        reviews = [{
            "user": {"login": "independent-reviewer"},
            "state": "APPROVED",
            "submitted_at": "2026-11-01T10:00:00Z",
            "commit_id": "candidate-sha",
            "body": body,
        }]
        with self.assertRaisesRegex(ValueError, "No independent APPROVED review"):
            VERIFY_RELEASE.latest_approved_review(
                reviews, "pr-author", "candidate-sha", 12345
            )

    def test_release_verifier_rejects_author_self_approval_and_changes_requested(self):
        critical = "SE03 SE04 SE05 SE08 SE09 SE11 SE12"
        body = (
            "Reviewed " + critical + " baseline and spread. "
            "https://github.com/example/repo/actions/runs/12345"
        )
        self_approval = [{
            "user": {"login": "pr-author"}, "state": "APPROVED",
            "submitted_at": "2026-11-01T10:00:00Z",
            "commit_id": "candidate-sha", "body": body,
        }]
        with self.assertRaisesRegex(ValueError, "No independent APPROVED review"):
            VERIFY_RELEASE.latest_approved_review(
                self_approval, "pr-author", "candidate-sha", 12345
            )
        blocking = self_approval + [{
            "user": {"login": "independent-reviewer"}, "state": "CHANGES_REQUESTED",
            "submitted_at": "2026-11-01T10:01:00Z",
            "commit_id": "candidate-sha", "body": "Fix SE04.",
        }]
        with self.assertRaisesRegex(ValueError, "CHANGES_REQUESTED"):
            VERIFY_RELEASE.latest_approved_review(
                blocking, "pr-author", "candidate-sha", 12345
            )

    def test_tag_workflow_runs_verifier_before_release_creation(self):
        workflow = (ROOT / ".github" / "workflows" / "publish-release.yml").read_text(encoding="utf-8")
        self.assertNotIn('push:', workflow)
        self.assertNotIn("python scripts/verify_release.py", workflow)
        self.assertIn("create_release_tag.py", workflow)
        self.assertIn("python scripts/create_release_tag.py", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("candidate_sha:", workflow)
        self.assertIn("confirm_publish:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn("gh release create", workflow)
        self.assertLess(workflow.index("python scripts/create_release_tag.py"),
                        workflow.index("gh release create"))
        self.assertIn("python scripts/update_release_doc.py", workflow)
        self.assertLess(workflow.index("gh release create"),
                        workflow.index("python scripts/update_release_doc.py"))
        self.assertIn("pull-requests: read", workflow)
        self.assertIn("actions: read", workflow)

    def test_manual_behavior_workflow_is_exact_sha_and_independent_judge_gated(self):
        workflow = (ROOT / ".github" / "workflows" / "behavioral-eval.yml").read_text(encoding="utf-8")
        self.assertIn("run-name: Behavioral Skill Evaluation", workflow)
        self.assertIn("candidate_sha:", workflow)
        self.assertIn("PR_HEAD", workflow)
        self.assertIn("EVAL_JUDGE_BASE_URL", workflow)
        self.assertIn("EVAL_JUDGE_API_KEY", workflow)
        self.assertIn('DEEPSEEK_MAX_TOKENS: "16384"', workflow)
        self.assertIn("candidate-evaluation-report-", workflow)

    def test_release_tag_creator_is_present_and_compiles(self):
        path = ROOT / "scripts" / "create_release_tag.py"
        self.assertTrue(path.is_file())
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_release_document_is_marked_published_only_with_evidence(self):
        current = (
            "# Release 0.0.1 — Candidate (not yet published)\n\n"
            "## Release gates\n"
            "- [ ] Behavioral pass rate >= 90% on every run\n"
            "- [ ] Trigger Precision >= 95% and Recall >= 95% on every run\n"
            "- [ ] Baseline comparison reviewed and accepted\n"
            "- [ ] Stability spread <= 5 percentage points for all three metrics\n"
            "- [ ] Independent human review of critical cases and generated outputs\n"
            "- [ ] Target-runtime validation\n"
            "This is a release candidate only. Do not publish tag v0.0.1 until every "
            "automated and human gate in RELEASE-GATE.md has passed on the exact release commit."
        )
        report = {
            "models": {"generator": "qwen-test", "judge_and_trigger": "judge-test"},
            "policy": {"actual_runs": 2},
            "workflow_run_id": 12345,
            "stability": {
                "behavior_pass_rate": {"mean": 0.92, "spread": 0.01},
                "trigger_precision": {"mean": 0.96, "spread": 0.0},
                "trigger_recall": {"mean": 0.97, "spread": 0.01},
            },
            "baseline_comparison": {
                "mean_baseline_behavior_pass_rate": 0.88,
                "mean_skill_behavior_pass_rate": 0.92,
                "mean_uplift": 0.04,
            },
        }
        updated = UPDATE_RELEASE_DOC.build_published_release_doc(
            current, report, "candidate-sha", "release-merge-sha", "independent-reviewer"
        )
        self.assertIn("# Release 0.0.1 — Published", updated)
        self.assertIn("- [x] Behavioral pass rate", updated)
        self.assertIn("- [x] Independent human review", updated)
        self.assertIn("Target-runtime validation remains a deployment follow-up", updated)
        self.assertIn("candidate-sha", updated)
        self.assertIn("release-merge-sha", updated)
        self.assertIn("independent-reviewer", updated)
        self.assertIn("Matched baseline mean uplift: +4.0%", updated)

    def test_policy_thresholds_are_exact(self):
        self.assertEqual(RUN_EVAL.POLICY["behavior_pass_rate"], 0.90)
        self.assertEqual(RUN_EVAL.POLICY["trigger_precision"], 0.95)
        self.assertEqual(RUN_EVAL.POLICY["trigger_recall"], 0.95)
        self.assertEqual(RUN_EVAL.POLICY["max_stability_spread"], 0.05)
        self.assertGreaterEqual(RUN_EVAL.POLICY["minimum_runs"], 2)
        self.assertEqual(RUN_EVAL.DEFAULT_GENERATOR_MODEL, "deepseek-flash")
        self.assertEqual(RUN_EVAL.DEFAULT_JUDGE_MODEL, "deepseek-v4-pro")

    def test_deepseek_pro_alias_is_not_treated_as_an_independent_judge(self):
        self.assertEqual(
            RUN_EVAL.effective_model_identity("https://api.deepseek.com", "deepseek-flash"),
            RUN_EVAL.effective_model_identity("https://api.deepseek.com", "deepseek-v4-pro"),
        )
        self.assertNotEqual(
            RUN_EVAL.effective_model_identity("https://api.deepseek.com", "deepseek-flash"),
            RUN_EVAL.effective_model_identity("https://api.openai.com/v1", "gpt-4.1-mini"),
        )

    def test_partial_and_complete_reports_use_configured_candidate_sha(self):
        with mock.patch.dict("os.environ", {"EVAL_GIT_SHA": "candidate-sha"}):
            self.assertEqual(RUN_EVAL.evaluation_git_sha(), "candidate-sha")

    def test_api_retries_are_reserved_as_separate_physical_requests(self):
        saved = {
            "api_requests": RUN_EVAL.API_REQUEST_COUNT,
            "reserved_cost": RUN_EVAL.ESTIMATED_COST_RESERVED_USD,
            "max_requests": RUN_EVAL.MAX_API_REQUESTS,
            "max_cost": RUN_EVAL.MAX_ESTIMATED_COST_USD,
            "checkpoint_path": RUN_EVAL.CHECKPOINT_PATH,
            "checkpoint_store": RUN_EVAL.CHECKPOINT_STORE,
            "usage": dict(RUN_EVAL.USAGE_BY_MODEL),
            "cache_hits": dict(RUN_EVAL.CACHE_HITS_BY_MODEL),
            "run_index": RUN_EVAL.CURRENT_RUN_INDEX,
        }

        class Response:
            headers = {}
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps({
                    "choices": [{
                        "finish_reason": "stop",
                        "message": {"content": "complete response"},
                    }],
                    "usage": {
                        "prompt_tokens": 5,
                        "completion_tokens": 3,
                        "total_tokens": 8,
                    },
                }).encode("utf-8")

        transient = RUN_EVAL.urllib.error.HTTPError(
            "https://api.deepseek.com/chat/completions",
            503, "temporary", {}, io.BytesIO(b"temporary server error"),
        )
        try:
            RUN_EVAL.API_REQUEST_COUNT = 0
            RUN_EVAL.ESTIMATED_COST_RESERVED_USD = 0.0
            RUN_EVAL.MAX_API_REQUESTS = 10
            RUN_EVAL.MAX_ESTIMATED_COST_USD = 5.0
            RUN_EVAL.CHECKPOINT_PATH = None
            RUN_EVAL.CHECKPOINT_STORE = {"responses": {}}
            RUN_EVAL.USAGE_BY_MODEL.clear()
            RUN_EVAL.CACHE_HITS_BY_MODEL.clear()
            RUN_EVAL.CURRENT_RUN_INDEX = 1
            with mock.patch.object(
                RUN_EVAL.urllib.request, "urlopen", side_effect=[transient, Response()]
            ) as urlopen, mock.patch.object(RUN_EVAL.time, "sleep"):
                value = RUN_EVAL.api_call(
                    "test-key", "deepseek-flash", "system", "user",
                    max_completion_tokens=10,
                )
            one_attempt = RUN_EVAL.estimate_request_cost_usd(
                "deepseek-flash", "system", "user", 10
            )
            self.assertEqual(value, "complete response")
            self.assertEqual(urlopen.call_count, 2)
            self.assertEqual(RUN_EVAL.API_REQUEST_COUNT, 2)
            self.assertAlmostEqual(
                RUN_EVAL.ESTIMATED_COST_RESERVED_USD, one_attempt * 2
            )
        finally:
            RUN_EVAL.API_REQUEST_COUNT = saved["api_requests"]
            RUN_EVAL.ESTIMATED_COST_RESERVED_USD = saved["reserved_cost"]
            RUN_EVAL.MAX_API_REQUESTS = saved["max_requests"]
            RUN_EVAL.MAX_ESTIMATED_COST_USD = saved["max_cost"]
            RUN_EVAL.CHECKPOINT_PATH = saved["checkpoint_path"]
            RUN_EVAL.CHECKPOINT_STORE = saved["checkpoint_store"]
            RUN_EVAL.USAGE_BY_MODEL.clear()
            RUN_EVAL.USAGE_BY_MODEL.update(saved["usage"])
            RUN_EVAL.CACHE_HITS_BY_MODEL.clear()
            RUN_EVAL.CACHE_HITS_BY_MODEL.update(saved["cache_hits"])
            RUN_EVAL.CURRENT_RUN_INDEX = saved["run_index"]

    def test_ambiguous_network_failure_is_not_retried_or_resent(self):
        saved = {
            "api_requests": RUN_EVAL.API_REQUEST_COUNT,
            "reserved_cost": RUN_EVAL.ESTIMATED_COST_RESERVED_USD,
            "checkpoint_path": RUN_EVAL.CHECKPOINT_PATH,
            "checkpoint_store": RUN_EVAL.CHECKPOINT_STORE,
            "max_requests": RUN_EVAL.MAX_API_REQUESTS,
            "max_cost": RUN_EVAL.MAX_ESTIMATED_COST_USD,
        }
        try:
            RUN_EVAL.API_REQUEST_COUNT = 0
            RUN_EVAL.ESTIMATED_COST_RESERVED_USD = 0.0
            RUN_EVAL.CHECKPOINT_PATH = None
            RUN_EVAL.CHECKPOINT_STORE = {"responses": {}}
            RUN_EVAL.MAX_API_REQUESTS = 10
            RUN_EVAL.MAX_ESTIMATED_COST_USD = 5.0
            with mock.patch.object(
                RUN_EVAL.urllib.request, "urlopen",
                side_effect=TimeoutError("read timed out"),
            ) as urlopen:
                with self.assertRaisesRegex(
                    RUN_EVAL.ProviderStopError, "ambiguous network outcome"
                ):
                    RUN_EVAL.api_call(
                        "test-key", "deepseek-flash", "system", "user",
                        max_completion_tokens=10,
                    )
            self.assertEqual(urlopen.call_count, 1)
            self.assertEqual(RUN_EVAL.API_REQUEST_COUNT, 1)
            self.assertEqual(len(RUN_EVAL.CHECKPOINT_STORE["uncertain_requests"]), 1)
            self.assertEqual(RUN_EVAL.CHECKPOINT_STORE["pending_requests"], {})

            with mock.patch.object(
                RUN_EVAL.urllib.request, "urlopen"
            ) as resumed_urlopen:
                with self.assertRaisesRegex(
                    RUN_EVAL.ProviderStopError, "refusing to resend"
                ):
                    RUN_EVAL.api_call(
                        "test-key", "deepseek-flash", "system", "user",
                        max_completion_tokens=10,
                    )
                resumed_urlopen.assert_not_called()
        finally:
            RUN_EVAL.API_REQUEST_COUNT = saved["api_requests"]
            RUN_EVAL.ESTIMATED_COST_RESERVED_USD = saved["reserved_cost"]
            RUN_EVAL.CHECKPOINT_PATH = saved["checkpoint_path"]
            RUN_EVAL.CHECKPOINT_STORE = saved["checkpoint_store"]
            RUN_EVAL.MAX_API_REQUESTS = saved["max_requests"]
            RUN_EVAL.MAX_ESTIMATED_COST_USD = saved["max_cost"]

    def test_interrupted_inflight_request_is_never_resent(self):
        saved = {
            "checkpoint_path": RUN_EVAL.CHECKPOINT_PATH,
            "checkpoint_store": RUN_EVAL.CHECKPOINT_STORE,
            "api_requests": RUN_EVAL.API_REQUEST_COUNT,
            "reserved_cost": RUN_EVAL.ESTIMATED_COST_RESERVED_USD,
        }
        try:
            RUN_EVAL.CHECKPOINT_PATH = None
            payload = RUN_EVAL.build_payload(
                "deepseek-flash", "system", "user", max_completion_tokens=10
            )
            key = RUN_EVAL.checkpoint_key({
                "endpoint": RUN_EVAL.API_URL, "payload": payload
            })
            RUN_EVAL.CHECKPOINT_STORE = {
                "responses": {},
                "pending_requests": {key: {"status": "in_flight"}},
                "uncertain_requests": {},
            }
            with mock.patch.object(RUN_EVAL.urllib.request, "urlopen") as urlopen:
                with self.assertRaisesRegex(
                    RUN_EVAL.ProviderStopError, "interrupted while in flight"
                ):
                    RUN_EVAL.api_call(
                        "test-key", "deepseek-flash", "system", "user",
                        max_completion_tokens=10,
                    )
                urlopen.assert_not_called()
        finally:
            RUN_EVAL.CHECKPOINT_PATH = saved["checkpoint_path"]
            RUN_EVAL.CHECKPOINT_STORE = saved["checkpoint_store"]
            RUN_EVAL.API_REQUEST_COUNT = saved["api_requests"]
            RUN_EVAL.ESTIMATED_COST_RESERVED_USD = saved["reserved_cost"]

    def test_inflight_marker_is_persisted_before_send_and_cleared_on_success(self):
        saved = {
            "checkpoint_path": RUN_EVAL.CHECKPOINT_PATH,
            "checkpoint_store": RUN_EVAL.CHECKPOINT_STORE,
            "api_requests": RUN_EVAL.API_REQUEST_COUNT,
            "reserved_cost": RUN_EVAL.ESTIMATED_COST_RESERVED_USD,
            "max_requests": RUN_EVAL.MAX_API_REQUESTS,
            "max_cost": RUN_EVAL.MAX_ESTIMATED_COST_USD,
        }
        class Response:
            headers = {}
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps({
                    "choices": [{"finish_reason": "stop", "message": {"content": "ok"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
                }).encode("utf-8")
        try:
            RUN_EVAL.CHECKPOINT_PATH = None
            RUN_EVAL.CHECKPOINT_STORE = {
                "responses": {}, "pending_requests": {}, "uncertain_requests": {}
            }
            RUN_EVAL.API_REQUEST_COUNT = 0
            RUN_EVAL.ESTIMATED_COST_RESERVED_USD = 0.0
            RUN_EVAL.MAX_API_REQUESTS = 10
            RUN_EVAL.MAX_ESTIMATED_COST_USD = 5.0
            def inspect_pending(request, timeout):
                self.assertEqual(len(RUN_EVAL.CHECKPOINT_STORE["pending_requests"]), 1)
                return Response()
            with mock.patch.object(
                RUN_EVAL.urllib.request, "urlopen", side_effect=inspect_pending
            ) as urlopen:
                self.assertEqual(
                    RUN_EVAL.api_call(
                        "test-key", "deepseek-flash", "system", "user",
                        max_completion_tokens=10,
                    ),
                    "ok",
                )
            self.assertEqual(urlopen.call_count, 1)
            self.assertEqual(RUN_EVAL.CHECKPOINT_STORE["pending_requests"], {})
            self.assertEqual(len(RUN_EVAL.CHECKPOINT_STORE["responses"]), 1)
        finally:
            RUN_EVAL.CHECKPOINT_PATH = saved["checkpoint_path"]
            RUN_EVAL.CHECKPOINT_STORE = saved["checkpoint_store"]
            RUN_EVAL.API_REQUEST_COUNT = saved["api_requests"]
            RUN_EVAL.ESTIMATED_COST_RESERVED_USD = saved["reserved_cost"]
            RUN_EVAL.MAX_API_REQUESTS = saved["max_requests"]
            RUN_EVAL.MAX_ESTIMATED_COST_USD = saved["max_cost"]

    def test_external_judge_payload_omits_deepseek_specific_fields(self):
        payload = RUN_EVAL.build_payload(
            "openai/gpt-oss-120b", "system prompt", "candidate output",
            max_completion_tokens=1200, json_mode=True, thinking=False,
            deepseek_fields=False,
        )
        self.assertEqual(payload["model"], "openai/gpt-oss-120b")
        self.assertEqual(payload["max_tokens"], 1200)
        self.assertIn("response_format", payload)
        self.assertNotIn("thinking", payload)
        self.assertNotIn("reasoning_effort", payload)

    def test_groq_judge_context_and_rate_budgets_fail_closed(self):
        saved_history = RUN_EVAL.MODEL_RATE_HISTORY
        saved_store = RUN_EVAL.CHECKPOINT_STORE
        try:
            RUN_EVAL.MODEL_RATE_HISTORY = {}
            with self.assertRaisesRegex(
                RUN_EVAL.EvaluationBudgetExceeded, "context safety limit"
            ):
                RUN_EVAL.throttle_model("openai/gpt-oss-120b", 131073)
            with self.assertRaisesRegex(
                RUN_EVAL.EvaluationBudgetExceeded, "per-minute token allowance"
            ):
                RUN_EVAL.throttle_model("openai/gpt-oss-120b", 8001)
            RUN_EVAL.CHECKPOINT_STORE = {
                "estimated_tokens_reserved_by_model": {"openai/gpt-oss-120b": 199500},
                "estimated_tokens_reserved_by_model_by_day": {
                    "2026-11-02": {"openai/gpt-oss-120b": 199500}
                },
            }
            with mock.patch.object(RUN_EVAL, "utc_date_key", return_value="2026-11-02"):
                with self.assertRaisesRegex(
                    RUN_EVAL.EvaluationBudgetExceeded, "UTC-day token reservation"
                ):
                    RUN_EVAL.reserve_model_daily_tokens("openai/gpt-oss-120b", 1000)
            with mock.patch.object(RUN_EVAL, "utc_date_key", return_value="2026-11-03"):
                RUN_EVAL.reserve_model_daily_tokens("openai/gpt-oss-120b", 1000)
            self.assertEqual(
                RUN_EVAL.CHECKPOINT_STORE["estimated_tokens_reserved_by_model_by_day"]["2026-11-03"]["openai/gpt-oss-120b"],
                1000,
            )
            self.assertEqual(
                RUN_EVAL.CHECKPOINT_STORE["estimated_tokens_reserved_by_model"]["openai/gpt-oss-120b"],
                200500,
            )
        finally:
            RUN_EVAL.MODEL_RATE_HISTORY = saved_history
            RUN_EVAL.CHECKPOINT_STORE = saved_store

    def test_payload_uses_deepseek_openai_chat_compatibility(self):
        payload = RUN_EVAL.build_payload(
            "deepseek-v4-pro", "system prompt", "user prompt",
            max_completion_tokens=321, json_mode=True, thinking=True,
        )
        self.assertEqual(payload["model"], "deepseek-v4-pro")
        self.assertEqual(payload["max_tokens"], 321)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["role"], "user")
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(payload["thinking"], {"type": "enabled"})
        self.assertEqual(payload["reasoning_effort"], "low")
        self.assertNotIn("temperature", payload)
        self.assertTrue(RUN_EVAL.DEFAULT_USER_AGENT.startswith("evaluation-dataset-builder/"))
        self.assertLessEqual(payload["max_tokens"], RUN_EVAL.MAX_COMPLETION_TOKENS)

    def test_flash_generator_uses_non_thinking_mode_to_control_cost(self):
        payload = RUN_EVAL.build_payload(
            "deepseek-flash", "system", "prompt", max_completion_tokens=321,
            thinking=False, temperature=0.2,
        )
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertEqual(payload["reasoning_effort"], "none")
        self.assertEqual(payload["temperature"], 0.2)

    def test_default_output_caps_are_large_enough_for_complete_skill_and_baseline_outputs(self):
        source = (ROOT / "tests" / "run_eval.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("max_completion_tokens=16384"), 2)
        self.assertNotIn("max_completion_tokens=2048", source)
        self.assertEqual(RUN_EVAL.MAX_COMPLETION_TOKENS, 16384)
        self.assertEqual(RUN_EVAL.MAX_ESTIMATED_REQUEST_TOKENS, 950000)

    def test_output_token_cap_is_enforced(self):
        with self.assertRaises(ValueError):
            RUN_EVAL.build_payload(
                "deepseek-flash", "system", "prompt",
                max_completion_tokens=RUN_EVAL.MAX_COMPLETION_TOKENS + 1,
            )

    def test_request_token_estimator_includes_prompt_and_output_budget(self):
        estimated = RUN_EVAL.estimate_request_tokens("s" * 1000, "u" * 200, 900)
        self.assertEqual(estimated, 1500)
        self.assertLessEqual(estimated, RUN_EVAL.MAX_ESTIMATED_REQUEST_TOKENS)

    def test_request_token_estimator_is_safe_for_cjk_text(self):
        english = RUN_EVAL.estimate_request_tokens("a" * 1000, "b" * 200, 900)
        chinese = RUN_EVAL.estimate_request_tokens("测" * 1000, "试" * 200, 900)
        self.assertEqual(english, 1500)
        self.assertGreater(chinese, english)
        self.assertEqual(chinese, 2700)

    def test_paid_model_peak_prices_and_spend_guard_are_configured(self):
        self.assertEqual(RUN_EVAL.MODEL_PRICING_USD_PER_MILLION["deepseek-flash"]["input"], 0.30)
        self.assertEqual(RUN_EVAL.MODEL_PRICING_USD_PER_MILLION["deepseek-v4-pro"]["output"], 1.20)
        self.assertGreater(RUN_EVAL.MAX_ESTIMATED_COST_USD, 0)
        self.assertLessEqual(RUN_EVAL.MAX_ESTIMATED_COST_USD, 2.0)
        self.assertLessEqual(RUN_EVAL.MAX_API_REQUESTS, 250)

    def test_json_extraction(self):
        self.assertEqual(RUN_EVAL.extract_json('prefix {"ok": true} suffix'), {"ok": True})

    def test_invalid_json_is_rejected(self):
        with self.assertRaises(ValueError):
            RUN_EVAL.extract_json("not a json response")

    def test_trigger_metrics_at_exact_95_percent_boundary(self):
        precision, recall = RUN_EVAL.binary_metrics(tp=19, fp=1, fn=1)
        self.assertAlmostEqual(precision, 0.95)
        self.assertAlmostEqual(recall, 0.95)

    def test_release_gate_threshold_boundary(self):
        gates = RUN_EVAL.gate_metrics(0.90, 0.95, 0.95)
        self.assertTrue(all(value["pass"] for value in gates.values()))
        self.assertFalse(RUN_EVAL.gate_metrics(0.8999, 0.95, 0.95)["behavior_pass_rate"]["pass"])
        self.assertFalse(RUN_EVAL.gate_metrics(0.90, 0.9499, 0.95)["trigger_precision"]["pass"])
        self.assertFalse(RUN_EVAL.gate_metrics(0.90, 0.95, 0.9499)["trigger_recall"]["pass"])

    def test_stability_spread(self):
        result = RUN_EVAL.summarize([0.95, 1.00])
        self.assertAlmostEqual(result["spread"], 0.05)
        self.assertAlmostEqual(result["mean"], 0.975)

    def test_trigger_fixture_is_balanced_and_sufficient(self):
        fixture = json.loads((ROOT / "tests" / "trigger-evals.json").read_text(encoding="utf-8"))
        positives = sum(item["should_trigger"] is True for item in fixture["evals"])
        negatives = sum(item["should_trigger"] is False for item in fixture["evals"])
        self.assertEqual(positives, 20)
        self.assertEqual(negatives, 20)
        self.assertEqual(len({item["query"] for item in fixture["evals"]}), 40)

    def test_judge_pass_requires_verbatim_candidate_evidence(self):
        response = {
            "checks": [
                {"index": 0, "score": 1, "rationale": "The objective is explicit.",
                 "evidence": ["Target: Billing Support."]},
                {"index": 1, "score": 1, "rationale": "Expected result is stated.",
                 "evidence": ["This fabricated sentence is not in the output."]},
            ]
        }
        with mock.patch.object(RUN_EVAL, "api_call", return_value=json.dumps(response)):
            results = RUN_EVAL.judge_case(
                "test-key", "judge-model",
                ["states objective", "states expected outcome"],
                "Target: Billing Support. Expected result: deny the refund.",
            )
        self.assertEqual(results[0]["score"], 1)
        self.assertTrue(results[0]["evidence_validated"])
        self.assertEqual(results[1]["score"], 0)
        self.assertFalse(results[1]["evidence_validated"])

    def test_judge_prompt_uses_real_section_line_breaks(self):
        response = {
            "checks": [{
                "index": 0, "score": 0, "rationale": "Not demonstrated.",
                "evidence": ["Output."],
            }]
        }
        with mock.patch.object(RUN_EVAL, "api_call", return_value=json.dumps(response)) as api:
            RUN_EVAL.judge_case("key", "judge-model", ["criterion"], "Output.")
        user_prompt = api.call_args.args[3]
        self.assertIn("\n\nCRITERIA:\n", user_prompt)
        self.assertIn("\n\nCANDIDATE OUTPUT", user_prompt)
        self.assertNotIn("\\\\n", user_prompt)

    def test_judge_rejects_trivial_evidence_substrings(self):
        response = {
            "checks": [{
                "index": 0, "score": 1, "rationale": "A short token is not sufficient evidence.",
                "evidence": ["OK"],
            }]
        }
        with mock.patch.object(RUN_EVAL, "api_call", return_value=json.dumps(response)):
            results = RUN_EVAL.judge_case(
                "key", "judge-model", ["criterion"], "OK"
            )
        self.assertEqual(results[0]["score"], 0)
        self.assertFalse(results[0]["evidence_validated"])

    def test_judge_duplicate_and_missing_indices_fail_closed(self):
        response = {
            "checks": [
                {"index": 0, "score": 1, "rationale": "first", "evidence": ["A"]},
                {"index": 0, "score": 1, "rationale": "duplicate", "evidence": ["A"]},
            ]
        }
        with mock.patch.object(RUN_EVAL, "api_call", return_value=json.dumps(response)):
            results = RUN_EVAL.judge_case(
                "test-key", "judge-model", ["criterion A", "criterion B"], "A"
            )
        self.assertEqual([item["score"] for item in results], [0, 0])

    def test_skill_and_matched_baseline_fit_free_tier_budget_per_case(self):
        skill = RUN_EVAL.load_skill()
        fixture = json.loads(
            (ROOT / "tests" / "self-eval-cases.json").read_text(encoding="utf-8")
        )
        baseline = (
            "You are a helpful assistant. Follow the user's request directly. "
            "Do not assume access to an evaluation-dataset-builder skill."
        )
        combined_estimates = [
            RUN_EVAL.estimate_request_tokens(skill, case["prompt"], 900)
            + RUN_EVAL.estimate_request_tokens(baseline, case["prompt"], 900)
            for case in fixture["cases"]
        ]
        self.assertLessEqual(max(combined_estimates), RUN_EVAL.MAX_ESTIMATED_REQUEST_TOKENS)

    def test_skill_contains_explicit_operational_response_contract(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "Missing evidence: continue safely",
            "Conflict handling: record, do not hand-wave",
            "Deduplication and coverage",
            "Quality gates and repair plan",
            "Execution readiness and side effects",
            "Incremental updates and version changes",
            "Output contract",
        ):
            self.assertIn(required, skill)

    def test_required_artifact_formats_define_jsonl_manifest_coverage_and_completeness(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "one complete JSON object per line",
            "coverage_universe",
            "covered/total counts by dimension",
            "pass/fail conditions",
            "Final completeness pass",
            "requested counts and schema",
        ):
            self.assertIn(required, skill)

    def test_output_completeness_template_covers_all_required_deliverables(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "plan/coverage", "cases/dedup", "repairs", "graders",
            "execution", "changes/JSONL", "Never invent",
        ):
            self.assertIn(required, skill)

    def test_deepseek_json_mode_validation_error_retries_once_without_response_format(self):
        error_body = json.dumps({
            "error": {
                "message": "Failed to validate JSON. Please adjust your prompt.",
                "code": "json_validate_failed",
            }
        }).encode("utf-8")
        http_error = RUN_EVAL.urllib.error.HTTPError(
            RUN_EVAL.API_URL, 400, "Bad Request", {}, io.BytesIO(error_body)
        )

        class FakeResponse:
            headers = {}
            def __init__(self, body):
                self.body = body
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return self.body

        response_body = json.dumps({
            "choices": [{"message": {"content": '{"should_trigger": true}'}}],
            "usage": {},
        }).encode("utf-8")
        calls = []
        def fake_urlopen(request, timeout):
            calls.append(request)
            if len(calls) == 1:
                raise http_error
            return FakeResponse(response_body)

        with mock.patch.object(RUN_EVAL, "throttle_model"):
            with mock.patch.object(RUN_EVAL.urllib.request, "urlopen", side_effect=fake_urlopen):
                result = RUN_EVAL.api_call(
                    "test-key", "deepseek-v4-pro", "return JSON", "classify",
                    max_completion_tokens=180, json_mode=True, temperature=0.0,
                )
        self.assertEqual(result, '{"should_trigger": true}')
        self.assertEqual(len(calls), 2)
        first_payload = json.loads(calls[0].data.decode("utf-8"))
        second_payload = json.loads(calls[1].data.decode("utf-8"))
        self.assertIn("response_format", first_payload)
        self.assertNotIn("response_format", second_payload)

    def test_deepseek_output_tpm_limit_retries_after_reset_instead_of_failing(self):
        body = json.dumps({
            "error": {
                "message": (
                    "Rate limit reached for output tokens per minute (OTPM). "
                    "Please try again in 0.2s."
                )
            }
        }).encode("utf-8")
        http_error = RUN_EVAL.urllib.error.HTTPError(
            RUN_EVAL.API_URL, 429, "Too Many Requests", {}, io.BytesIO(body)
        )

        class FakeResponse:
            headers = {}
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps({
                    "choices": [{"message": {"content": "generated output"}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                }).encode("utf-8")

        calls = []
        def fake_urlopen(request, timeout):
            calls.append(request)
            if len(calls) == 1:
                raise http_error
            return FakeResponse()

        with mock.patch.object(RUN_EVAL, "throttle_model") as throttle:
            with mock.patch.object(RUN_EVAL.urllib.request, "urlopen", side_effect=fake_urlopen):
                with mock.patch.object(RUN_EVAL.time, "sleep") as sleep:
                    result = RUN_EVAL.api_call(
                        "test-key", "deepseek-flash", "system", "user",
                        max_completion_tokens=100, json_mode=False,
                    )
        self.assertEqual(result, "generated output")
        self.assertEqual(len(calls), 2)
        self.assertEqual(throttle.call_count, 2)
        sleep.assert_called_once_with(1.0)

    def test_spend_guard_blocks_before_network_request(self):
        with mock.patch.object(RUN_EVAL, "MAX_ESTIMATED_COST_USD", 0.000000001):
            with mock.patch.object(RUN_EVAL, "API_REQUEST_COUNT", 0):
                with mock.patch.object(RUN_EVAL, "ESTIMATED_COST_RESERVED_USD", 0.0):
                    with mock.patch.object(RUN_EVAL.urllib.request, "urlopen") as urlopen:
                        with self.assertRaises(RUN_EVAL.EvaluationBudgetExceeded):
                            RUN_EVAL.api_call(
                                "key", "deepseek-v4-pro", "system", "user",
                                max_completion_tokens=900,
                            )
                        urlopen.assert_not_called()

    def test_checkpoint_key_is_scoped_to_repeated_run(self):
        payload = RUN_EVAL.build_payload("deepseek-flash", "system", "user")
        RUN_EVAL.CURRENT_RUN_INDEX = 1
        first = RUN_EVAL.checkpoint_key(payload)
        RUN_EVAL.CURRENT_RUN_INDEX = 2
        second = RUN_EVAL.checkpoint_key(payload)
        self.assertNotEqual(first, second)

    def test_judge_and_trigger_propagate_paid_budget_stop_errors(self):
        with mock.patch.object(RUN_EVAL, "api_call", side_effect=RUN_EVAL.EvaluationBudgetExceeded("budget cap")):
            with self.assertRaises(RUN_EVAL.EvaluationBudgetExceeded):
                RUN_EVAL.judge_case("key", "deepseek-v4-pro", ["criterion"], "candidate")
            with self.assertRaises(RUN_EVAL.EvaluationBudgetExceeded):
                RUN_EVAL.classify_trigger("key", "deepseek-v4-pro", "query")

    def test_judge_accepts_multiple_short_quotes_for_compound_criteria(self):
        response = {"checks": [{
            "index": 0, "score": 1, "rationale": "Both required facts are stated.",
            "evidence": ["Target: Billing Support.", "Objective: verify monthly totals."],
        }]}
        with mock.patch.object(RUN_EVAL, "api_call", return_value=json.dumps(response)) as call:
            results = RUN_EVAL.judge_case(
                "key", "judge-model",
                ["states target and objective"],
                "Target: Billing Support. Objective: verify monthly totals.",
            )
        self.assertIn("1-3 short VERBATIM substrings", call.call_args.args[2])
        self.assertEqual(call.call_args.kwargs["max_completion_tokens"], 1200)
        self.assertLessEqual(call.call_args.kwargs["max_completion_tokens"], RUN_EVAL.MAX_COMPLETION_TOKENS)
        self.assertEqual(results[0]["score"], 1)
        self.assertTrue(results[0]["evidence_validated"])
        self.assertEqual(results[0]["evidence"], [
            "Target: Billing Support.", "Objective: verify monthly totals."
        ])

    def test_judge_uses_pro_non_thinking_mode_with_bounded_json_output(self):
        response = {"checks": [{
            "index": 0, "score": 0, "rationale": "Missing evidence.",
            "evidence": ["Closest available sentence."],
        }]}
        with mock.patch.object(RUN_EVAL, "api_call", return_value=json.dumps(response)) as call:
            RUN_EVAL.judge_case(
                "key", "deepseek-v4-pro", ["criterion"], "Closest available sentence."
            )
        self.assertEqual(call.call_args.kwargs["max_completion_tokens"], 1200)
        self.assertFalse(call.call_args.kwargs["thinking"])
        self.assertEqual(call.call_args.kwargs["temperature"], 0.0)

    def test_judge_fails_closed_when_any_quote_is_unverifiable(self):
        response = {"checks": [{
            "index": 0, "score": 1, "rationale": "Both facts appear.",
            "evidence": ["Target: Billing Support.", "This sentence was fabricated."],
        }]}
        with mock.patch.object(RUN_EVAL, "api_call", return_value=json.dumps(response)):
            results = RUN_EVAL.judge_case(
                "key", "judge-model", ["states target and objective"],
                "Target: Billing Support. Objective: verify monthly totals.",
            )
        self.assertEqual(results[0]["score"], 0)
        self.assertFalse(results[0]["evidence_validated"])
        self.assertEqual(results[0]["evidence"], [])

    def test_judge_rejects_more_than_three_quotes(self):
        quotes = ["Quote alpha is present.", "Quote beta is present.",
                  "Quote gamma is present.", "Quote delta is present."]
        response = {"checks": [{
            "index": 0, "score": 1, "rationale": "All evidence is present.",
            "evidence": quotes,
        }]}
        with mock.patch.object(RUN_EVAL, "api_call", return_value=json.dumps(response)):
            results = RUN_EVAL.judge_case(
                "key", "judge-model", ["criterion"], " ".join(quotes)
            )
        self.assertEqual(results[0]["score"], 0)
        self.assertFalse(results[0]["evidence_validated"])

    def test_trigger_provider_error_is_recorded_as_parse_error(self):
        with mock.patch.object(RUN_EVAL, "api_call", side_effect=RuntimeError("provider unavailable")):
            predicted, error = RUN_EVAL.classify_trigger("key", "judge-model", "query")
        self.assertFalse(predicted)
        self.assertIn("provider unavailable", error)

    def test_judge_provider_error_fails_each_criterion_closed(self):
        with mock.patch.object(RUN_EVAL, "api_call", side_effect=RuntimeError("provider unavailable")):
            results = RUN_EVAL.judge_case("key", "judge-model", ["criterion A", "criterion B"], "text")
        self.assertEqual([item["score"] for item in results], [0, 0])
        self.assertTrue(all(item["judge_api_error"] for item in results))

    def test_evaluate_once_records_generator_and_trigger_provider_errors(self):
        suite = {
            "cases": [{
                "id": "SE-TEMP",
                "category": "provider_error",
                "prompt": "generate one case",
                "expected": ["criterion one", "criterion two"],
            }]
        }
        trigger_suite = {
            "evals": [{"query": "build an evaluation dataset", "should_trigger": True}]
        }
        with mock.patch.object(RUN_EVAL, "api_call", side_effect=RuntimeError("provider unavailable")):
            result = RUN_EVAL.evaluate_once(
                1, "generator-key", "judge-key", "deepseek-flash", "deepseek-v4-pro",
                "skill text", "baseline text", suite, trigger_suite,
            )
        self.assertTrue(result["skill_cases"][0]["generation_error"])
        self.assertTrue(result["baseline_cases"][0]["generation_error"])
        self.assertEqual([x["score"] for x in result["skill_cases"][0]["checks"]], [0, 0])
        self.assertEqual(result["trigger_parse_errors"], 1)
        self.assertFalse(result["gates"]["trigger_classifier_valid"]["pass"])
        self.assertFalse(result["automated_run_pass"])

    def test_workflow_blocks_pull_requests_not_targeting_main(self):
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        self.assertIn("require-master-target:", workflow)
        self.assertIn("github.event.pull_request.base.ref", workflow)
        self.assertIn('if [ "$BASE_REF" != "master" ]', workflow)

    def test_report_declares_provider_completeness_hard_gates(self):
        source = (ROOT / "tests" / "run_eval.py").read_text(encoding="utf-8")
        self.assertIn('"generation_calls_complete"', source)
        self.assertIn('"judge_responses_complete"', source)
        self.assertIn('"trigger_classifier_valid"', source)
        self.assertIn("json_validate_failed", source)

    def test_trigger_parse_errors_fail_closed(self):
        source = (ROOT / "tests" / "run_eval.py").read_text(encoding="utf-8")
        self.assertIn('trigger_parse_errors = 0', source)
        self.assertIn('"trigger_classifier_valid"', source)
        self.assertIn('trigger_parse_errors == 0', source)

    def test_behavior_suite_has_concrete_nonfabricated_scenarios(self):
        fixture = json.loads(
            (ROOT / "tests" / "self-eval-cases.json").read_text(encoding="utf-8")
        )
        cases = {item["id"]: item for item in fixture["cases"]}
        self.assertEqual(len(cases), 12)
        self.assertTrue(all(item.get("prompt") and item.get("expected") for item in cases.values()))
        self.assertTrue(all(2 <= len(item["expected"]) <= 5 for item in cases.values()))
        self.assertIn("POLICY-A", cases["SE04"]["prompt"])
        self.assertIn("POLICY-B", cases["SE04"]["prompt"])
        self.assertIn("C01", cases["SE07"]["prompt"])
        self.assertIn("C06", cases["SE07"]["prompt"])
        self.assertIn("SLA-v1", cases["SE12"]["prompt"])
        self.assertIn("SLA-v2", cases["SE12"]["prompt"])
        self.assertIn("synthetic", fixture["purpose"].lower())

    def test_case_schema_defines_evidence_and_side_effect_execution_fields(self):
        schema = json.loads(
            (ROOT / "references" / "dataset-schema.json").read_text(encoding="utf-8")
        )
        grading = schema["properties"]["grading"]["properties"]
        for field in ("acceptable_variants", "uncertainty_policy",
                      "reference_authority", "calibration_cases"):
            self.assertIn(field, grading)
        execution = schema["properties"]["execution_requirements"]
        props = execution["properties"]
        for field in ("status", "initial_state", "required_permissions", "environment",
                      "steps", "expected_end_state", "observable_assertions",
                      "forbidden_side_effects", "reset_plan", "cleanup_plan",
                      "execution_evidence"):
            self.assertIn(field, props)
        self.assertEqual(len(execution["allOf"]), 2)
        self.assertIn("cleanup_plan", execution["allOf"][0]["then"]["required"])
        self.assertIn("execution_evidence", execution["allOf"][1]["then"]["required"])

    def test_critical_case_expectations_are_operational(self):
        fixture = json.loads(
            (ROOT / "tests" / "self-eval-cases.json").read_text(encoding="utf-8")
        )
        cases = {item["id"]: item for item in fixture["cases"]}
        for case_id in ("SE03", "SE04", "SE05", "SE08", "SE09", "SE11", "SE12"):
            self.assertGreaterEqual(len(cases[case_id]["expected"]), 4 if case_id != "SE11" else 2)
        self.assertTrue(any("needs_info" in criterion or "UNKNOWN" in criterion
                            for criterion in cases["SE03"]["expected"]))
        self.assertTrue(any("does not select" in criterion
                            for criterion in cases["SE04"]["expected"]))
        self.assertTrue(any("end-result" in criterion or "state" in criterion
                            for criterion in cases["SE05"]["expected"]))
        self.assertTrue(any("approval" in criterion for criterion in cases["SE08"]["expected"]))
        self.assertTrue(any("not performed" in criterion
                            for criterion in cases["SE09"]["expected"]))
        self.assertTrue(any("unexecuted reruns" in criterion
                            for criterion in cases["SE12"]["expected"]))

    def test_critical_cases_exist(self):
        fixture = json.loads((ROOT / "tests" / "self-eval-cases.json").read_text(encoding="utf-8"))
        available = {item["id"] for item in fixture["cases"]}
        self.assertTrue(set(RUN_EVAL.CRITICAL_CASE_IDS).issubset(available))

    def test_baseline_and_trigger_cannot_be_skipped(self):
        source = (ROOT / "tests" / "run_eval.py").read_text(encoding="utf-8")
        self.assertNotIn("--skip-baseline", source)
        self.assertNotIn("--skip-trigger", source)
        self.assertNotIn("ANTHROPIC_API_KEY", source)
        self.assertIn("DEEPSEEK_API_KEY", source)


if __name__ == "__main__":
    unittest.main()
