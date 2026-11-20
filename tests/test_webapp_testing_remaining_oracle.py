"""Offline regression tests for the eleven remaining Webapp Testing Oracle roles."""
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


ORACLE = load_module(
    "webapp_testing_remaining_oracle",
    ROOT / "benchmarks" / "webapp-testing" / "scripts" / "gold_oracle.py",
)
INITIAL = copy.deepcopy(ORACLE.INITIAL)
SUMMARY = copy.deepcopy(ORACLE.INITIAL_SUMMARY)


def write_dom(root: Path, html: str) -> Path:
    artifacts = root / "skill-artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "snapshot.html").write_text(html, encoding="utf-8")
    return root


def summary_html(summary):
    ids = {
        "all": "count-all",
        "open": "count-open",
        "in_progress": "count-in-progress",
        "done": "count-done",
    }
    return "".join(f'<strong id="{ids[key]}">{value}</strong>' for key, value in summary.items())


def base_runner(post_items=None, post_summary=None):
    post_items = copy.deepcopy(INITIAL if post_items is None else post_items)
    return {
        "pre_state": {"items": copy.deepcopy(INITIAL), "summary": copy.deepcopy(SUMMARY)},
        "post_state": {
            "items": post_items,
            "summary": copy.deepcopy(SUMMARY if post_summary is None else post_summary),
        },
    }



def write_pilot_bundle(root, runner, audit, report):
    artifacts = root / "skill-artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "report.md").write_text(report, encoding="utf-8")
    (artifacts / "step.png").write_bytes(b"offline-test-image")
    runner = {
        **runner,
        "case_id": "offline-test",
        "runner_status": "INVOCATION_OK",
        "dsh_exit_code": 0,
        "completed_user_turn_count": 1,
        "session_turn_results": [{"turn_id": "T1", "dsh_exit_code": 0, "final_reason": "completed"}],
        "server_port_closed": True,
        "fixture_profile": "clean",
        "fixture_mutations": [],
        "required_skill_evidence": {"markdown_report": True, "json_evidence_index": True, "screenshot": True},
    }
    (root / "runner-result.json").write_text(__import__("json").dumps(runner), encoding="utf-8")
    events = [
        {"type": "session", "sessionId": "offline-session"},
        {"type": "status", "phase": "turn_start", "turn": 1},
        {"type": "tool_call", "tool": "skill", "input": {"name": "webapp-testing"}, "callId": "call-1"},
        {"type": "tool_result", "callId": "call-1", "status": "completed"},
        {"type": "status", "phase": "turn_end", "turn": 1},
        {"type": "final", "reason": {"kind": "completed"}},
    ]
    (root / "dsh-events.jsonl").write_text("".join(__import__("json").dumps(item) + "\n" for item in events), encoding="utf-8")
    (root / "server-audit.jsonl").write_text("".join(__import__("json").dumps(item) + "\n" for item in audit), encoding="utf-8")


class RemainingOracleTests(unittest.TestCase):
    def test_accessible_names_resolve_labels_and_open_dialog_name(self):
        with tempfile.TemporaryDirectory() as temp:
            pilot = Path(temp) / "pilot"
            write_dom(
                pilot,
                '<label for="task-search"><span>Search tasks</span></label>'
                '<input id="task-search" type="search">'
                '<select aria-label="Filter tasks by status"></select>'
                '<dialog id="delete-dialog" open aria-labelledby="delete-heading">'
                '<h2 id="delete-heading">Delete task?</h2>'
                '<button>Cancel</button><button>Delete task</button></dialog>',
            )
            controls = ORACLE.dom_controls(ORACLE.parse_dom_snapshots(pilot))
            observed = {(item["role"], item["name"]) for item in controls}
            self.assertIn(("searchbox", "Search tasks"), observed)
            self.assertIn(("combobox", "Filter tasks by status"), observed)
            self.assertIn(("dialog", "Delete task?"), observed)
            self.assertIn(("button", "Cancel"), observed)
            self.assertIn(("button", "Delete task"), observed)

    def test_closed_native_dialog_is_not_exposed_as_an_accessible_control(self):
        with tempfile.TemporaryDirectory() as temp:
            pilot = Path(temp) / "pilot"
            write_dom(pilot, '<dialog aria-labelledby="heading"><h2 id="heading">Delete task?</h2></dialog>')
            controls = ORACLE.dom_controls(ORACLE.parse_dom_snapshots(pilot))
            self.assertNotIn(("dialog", "Delete task?"), {(item["role"], item["name"]) for item in controls})

    def test_query_audit_decodes_query_and_status_filter(self):
        events = ORACLE._query_events([
            {"method": "GET", "path": "/api/tasks", "query": "q=token+expiry&status=all", "result_count": 1},
        ])
        self.assertEqual(events[0]["q"], "token expiry")
        self.assertEqual(events[0]["status_filter"], "all")
        self.assertEqual(events[0]["result_count"], 1)

    def test_rejected_blank_title_is_not_misclassified_as_successful_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            pilot = Path(temp) / "pilot"
            html = (
                '<table><tbody>' + "".join(f'<tr><td>{item["title"]}</td></tr>' for item in INITIAL)
                + '</tbody></table><p id="status-message" data-state="error">Title is required</p>'
                + summary_html(SUMMARY)
            )
            write_dom(pilot, html)
            case = {
                "case_id": "WB-CORE-10",
                "dataset_id": "D-WB",
                "execution_requirements": {"test_data": [{
                    "kind": "invalid_create", "expected_error_contains": "Title",
                    "expected_row_count": 5, "expected_summary": SUMMARY,
                }]},
            }
            audit = [{"method": "POST", "path": "/api/reset", "status": 200, "action": "reset"}, {
                "method": "POST", "path": "/api/tasks", "status": 400,
                "action": "create-rejected", "reason": "blank-title",
            }]
            write_pilot_bundle(pilot, base_runner(), audit, "Blank title was rejected. Final result PASS.")
            result = ORACLE.adjudicate_remaining_case(case, pilot, "create_rejected")
            self.assertEqual(result["oracle_verdict"], "PASS", result["checks"])
            self.assertEqual(result["business_behavior_verdict"], "PASS")

    def test_successful_create_requires_server_state_and_rendered_success_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            pilot = Path(temp) / "pilot"
            created = {
                "id": "WB-106", "title": "Release checklist",
                "description": "Draft the release checklist.",
                "priority": "Medium", "status": "open",
            }
            expected_summary = {"all": 6, "open": 3, "in_progress": 2, "done": 1}
            post = copy.deepcopy(INITIAL) + [created]
            html = (
                f'<table><tbody><tr><td>{created["title"]}</td><td>Medium</td><td>Open</td></tr></tbody></table>'
                '<p id="status-message">Created WB-106</p>' + summary_html(expected_summary)
            )
            write_dom(pilot, html)
            case = {
                "case_id": "WB-CORE-09", "dataset_id": "D-WB",
                "execution_requirements": {"test_data": [{
                    "kind": "create_task", "expected_stored_title": "Release checklist",
                    "expected_priority": "Medium", "expected_status": "Open",
                    "expected_summary": expected_summary,
                }]},
            }
            audit = [{"method": "POST", "path": "/api/reset", "status": 200, "action": "reset"}, {
                "method": "POST", "path": "/api/tasks", "status": 201,
                "action": "created", "item": created,
            }]
            write_pilot_bundle(pilot, base_runner(post, expected_summary), audit, "Created WB-106 Release checklist. PASS.")
            result = ORACLE.adjudicate_remaining_case(case, pilot, "create_success")
            self.assertEqual(result["oracle_verdict"], "PASS", result["checks"])
            self.assertEqual(result["business_behavior_verdict"], "PASS")

    def test_delete_cancel_uses_builder_target_data_id(self):
        case = {
            "user_input": "仅取消对 Verify email notification 的删除。",
            "execution_requirements": {"test_data": [{
                "kind": "delete_cancel", "target_data_id": "WB-104",
            }]},
        }
        self.assertTrue(ORACLE.is_delete_cancel_case(case))
        target = ORACLE.target_task(case, INITIAL)
        self.assertIsNotNone(target)
        self.assertEqual(target["id"], "WB-104")

    def test_report_does_not_count_unknown_as_failed_case(self):
        entries = [{"case_id": str(i), "dataset_id": "D", "pilot_role": role}
                   for i, role in enumerate(sorted(ORACLE.REMAINING_ROLES))]
        results = [{"case_id": str(i), "oracle_verdict": "UNKNOWN", "business_behavior_verdict": "UNKNOWN"}
                   for i in range(11)]
        report = ORACLE.build_report({"suite_id": "test", "version": "test"}, entries, results)
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertEqual(report["failed_cases"], 0)
        self.assertEqual(report["scope"], "independent_remaining_eleven_case_adjudication")


if __name__ == "__main__":
    unittest.main()
