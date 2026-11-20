"""Deterministic tests for DSH trace accounting and execution ceilings."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "benchmarks" / "webapp-testing" / "scripts" / "run_webapp_testing.py"
SPEC = importlib.util.spec_from_file_location("webapp_testing_runner", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RUNNER)


class DshTraceBudgetTests(unittest.TestCase):
    def test_steps_are_not_misreported_as_turns(self):
        events = [
            {"type": "status", "phase": "turn_start", "turn": 1},
            *[
                {
                    "type": "status",
                    "phase": "step_end",
                    "turn": 1,
                    "step": step,
                    "usage": {
                        "inputTokens": 10,
                        "outputTokens": 20,
                        "cacheReadTokens": 30,
                        "cacheWriteTokens": 0,
                        "totalTokens": 60,
                    },
                }
                for step in range(1, 41)
            ],
            {"type": "status", "phase": "turn_end", "turn": 1},
        ]
        summary = RUNNER.summarize_trace_events(events)
        self.assertEqual(summary["usage_record_count"], 40)
        self.assertEqual(summary["model_step_count"], 40)
        self.assertEqual(summary["model_turn_count"], 1)
        self.assertEqual(summary["usage_totals"]["outputTokens"], 800)
        self.assertEqual(summary["usage_totals"]["cacheReadTokens"], 1200)

    def test_budget_violations_are_explicit_and_deterministic(self):
        trace = {
            "usage": {
                "model_step_count": 33,
                "usage_totals": {
                    "inputTokens": 100,
                    "outputTokens": 55001,
                    "cacheReadTokens": 1600001,
                    "totalTokens": 1700000,
                },
            }
        }
        limits = {
            "model_steps": 32,
            "input_tokens": 60000,
            "output_tokens": 55000,
            "cache_read_tokens": 1600000,
            "total_tokens": 1750000,
        }
        self.assertEqual(
            RUNNER.trace_budget_violations(trace, limits),
            [
                "model_steps=33 exceeds limit 32",
                "output_tokens=55001 exceeds limit 55000",
                "cache_read_tokens=1600001 exceeds limit 1600000",
            ],
        )

    def test_dsh_wall_clock_never_exceeds_case_budget(self):
        self.assertEqual(RUNNER.resolve_effective_dsh_timeout(240, None), 240)
        self.assertEqual(RUNNER.resolve_effective_dsh_timeout(900, 600), 600)
        self.assertEqual(RUNNER.resolve_effective_dsh_timeout(300, 1500), 300)

    def test_runtime_monitor_stops_process_after_trace_budget_is_crossed(self):
        with tempfile.TemporaryDirectory() as temp:
            trace_path = Path(temp) / "events.jsonl"
            child = (
                "import json, pathlib, sys, time; "
                "p=pathlib.Path(sys.argv[1]); "
                "e={'type':'status','phase':'step_end','turn':1,'step':1,"
                "'usage':{'inputTokens':0,'outputTokens':2,'cacheReadTokens':0,"
                "'cacheWriteTokens':0,'totalTokens':2}}; "
                "p.write_text(json.dumps(e)+'\\n', encoding='utf-8'); "
                "time.sleep(20)"
            )
            process = subprocess.Popen(
                [sys.executable, "-c", child, str(trace_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                start_new_session=True,
            )
            exit_code, error = RUNNER.wait_for_dsh_with_budget(
                process,
                "",
                trace_path,
                10,
                {
                    "model_steps": 32,
                    "input_tokens": 60000,
                    "output_tokens": 1,
                    "cache_read_tokens": 1600000,
                    "total_tokens": 1750000,
                },
            )
            self.assertEqual(exit_code, 124)
            self.assertIn("output_tokens=2 exceeds limit 1", error)
            self.assertIsNotNone(process.poll())

    def test_trace_parser_preserves_turn_and_step_counts(self):
        events = [
            {"type": "session", "sessionId": "session-1"},
            {"type": "status", "phase": "turn_start", "turn": 1},
            {
                "type": "status",
                "phase": "step_end",
                "turn": 1,
                "step": 1,
                "usage": {
                    "inputTokens": 1,
                    "outputTokens": 2,
                    "cacheReadTokens": 3,
                    "cacheWriteTokens": 0,
                    "totalTokens": 6,
                },
            },
            {"type": "status", "phase": "turn_end", "turn": 1},
            {"type": "final", "sessionId": "session-1", "reason": {"kind": "completed"}},
        ]
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "trace.jsonl"
            path.write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )
            trace = RUNNER.parse_trace(path)
        self.assertEqual(trace["turn_start_count"], 1)
        self.assertEqual(trace["usage"]["model_step_count"], 1)
        self.assertEqual(trace["usage"]["model_turn_count"], 1)
        self.assertEqual(trace["usage"]["usage_totals"]["totalTokens"], 6)


if __name__ == "__main__":
    unittest.main()
