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


def write_dom(root: Path, html: str, filename: str = "snapshot.html") -> Path:
    artifacts = root / "skill-artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / filename).write_text(html, encoding="utf-8")
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





def render_board(rows, summary=SUMMARY, controls=""):
    row_html = "".join(f"<tr>{row}</tr>" for row in rows)
    return (
        '<table><tbody>' + row_html + '</tbody></table>'
        + controls + summary_html(summary)
    )


def adjudicate_fixture(role, case, html, audit_events, post_items=None, post_summary=None, report="Final verdict PASS.", screenshot_count=1):
    with tempfile.TemporaryDirectory() as temp:
        pilot = Path(temp) / "pilot"
        if isinstance(html, list):
            for index, snapshot in enumerate(html):
                write_dom(pilot, snapshot, f"snapshot-{index}.html")
        else:
            write_dom(pilot, html)
        full_audit = [{"method": "POST", "path": "/api/reset", "status": 200, "action": "reset"}, *audit_events]
        write_pilot_bundle(pilot, base_runner(post_items, post_summary), full_audit, report)
        if screenshot_count > 1:
            for index in range(1, screenshot_count):
                (pilot / "skill-artifacts" / f"step-{index}.png").write_bytes(b"offline-test-image")
        if role == "delete_cancel":
            return ORACLE.adjudicate(case, pilot, role)
        return ORACLE.adjudicate_remaining_case(case, pilot, role)

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


    def test_initial_board_role_checks_declared_baseline(self):
        rows = [f'<td>{item["title"]}</td><td>{item["priority"]}</td><td>{ORACLE.status_label(item["status"]) if hasattr(ORACLE, "status_label") else item["status"]}</td>' for item in INITIAL]
        case = {
            "case_id": "WB-CORE-01", "dataset_id": "D-WB",
            "execution_requirements": {"test_data": [{
                "kind": "initial_board",
                "expected_tasks": [{"data_id": item["id"], "title": item["title"], "priority": item["priority"], "status": item["status"].replace("_", " ").title()} for item in INITIAL],
                "expected_summary": SUMMARY,
            }]},
        }
        result = adjudicate_fixture("initial_board", case, render_board(rows), [])
        self.assertEqual(result["oracle_verdict"], "PASS", result["checks"])

    def test_description_and_empty_search_roles_use_server_and_dom_evidence(self):
        desc_case = {
            "case_id": "WB-CORE-03", "dataset_id": "D-WB",
            "execution_requirements": {"test_data": [{"kind": "search_description", "query": "token expiry", "expected_rows": [{"title": "Reset password flow"}], "expected_summary": SUMMARY}]},
        }
        desc_result = adjudicate_fixture(
            "search_description", desc_case,
            render_board(['<td>Reset password flow</td><td>High</td><td>Open</td>']),
            [{"method": "GET", "path": "/api/tasks", "query": "q=token+expiry&status=all", "result_count": 1}],
        )
        self.assertEqual(desc_result["oracle_verdict"], "PASS", desc_result["checks"])

        empty_case = {
            "case_id": "WB-CORE-04", "dataset_id": "D-WB",
            "execution_requirements": {"test_data": [{"kind": "search_empty", "query": "zzzz-no-such-task", "expected_row_count": 0, "expected_empty_text": "No tasks match the current filters.", "expected_summary": SUMMARY}]},
        }
        empty_html = '<p id="empty-state">No tasks match the current filters.</p>' + summary_html(SUMMARY)
        empty_result = adjudicate_fixture(
            "search_empty", empty_case, empty_html,
            [{"method": "GET", "path": "/api/tasks", "query": "q=zzzz-no-such-task&status=all", "result_count": 0}],
        )
        self.assertEqual(empty_result["oracle_verdict"], "PASS", empty_result["checks"])

    def test_status_and_combined_filter_roles_verify_every_query_state(self):
        status_case = {
            "case_id": "WB-CORE-05", "dataset_id": "D-WB",
            "execution_requirements": {"test_data": [{
                "kind": "status_filter", "filter_value": "in_progress",
                "expected_titles": ["Update onboarding guide", "Review accessibility"],
                "restore_value": "all", "expected_restored_count": 5, "expected_summary": SUMMARY,
            }]},
        }
        status_result = adjudicate_fixture(
            "status_filter", status_case,
            [
                render_board(['<td>Update onboarding guide</td>', '<td>Review accessibility</td>']),
                render_board([f'<td>{item["title"]}</td>' for item in INITIAL]),
            ],
            [
                {"method": "GET", "path": "/api/tasks", "query": "q=&status=in_progress", "result_count": 2},
                {"method": "GET", "path": "/api/tasks", "query": "q=&status=all", "result_count": 5},
            ],
        )
        self.assertEqual(status_result["oracle_verdict"], "PASS", status_result["checks"])

        combo_case = {
            "case_id": "WB-CORE-06", "dataset_id": "D-WB",
            "execution_requirements": {"test_data": [{
                "kind": "search_filter_combo", "query": "export",
                "states": [
                    {"status": "done", "expected_titles": ["Fix export timeout"], "expected_count": 1},
                    {"status": "open", "expected_titles": [], "expected_count": 0},
                    {"status": "all", "expected_titles": ["Fix export timeout"], "expected_count": 1},
                ],
                "expected_summary": SUMMARY,
            }]},
        }
        combo_result = adjudicate_fixture(
            "search_filter_combo", combo_case,
            [
                render_board(['<td>Fix export timeout</td><td>High</td><td>Done</td>']),
                '<p id="empty-state">No tasks match the current filters.</p>' + summary_html(SUMMARY),
                render_board(['<td>Fix export timeout</td><td>High</td><td>Done</td>']),
            ],
            [
                {"method": "GET", "path": "/api/tasks", "query": "q=export&status=done", "result_count": 1},
                {"method": "GET", "path": "/api/tasks", "query": "q=export&status=open", "result_count": 0},
                {"method": "GET", "path": "/api/tasks", "query": "q=export&status=all", "result_count": 1},
            ],
        )
        self.assertEqual(combo_result["oracle_verdict"], "PASS", combo_result["checks"])

    def test_accessible_names_role_requires_all_builder_declared_controls(self):
        expected = [
            {"role": "searchbox", "name": "Search tasks"},
            {"role": "combobox", "name": "Filter tasks by status"},
            {"role": "button", "name": "Create task"},
            {"role": "button", "name": "Delete"},
            {"role": "button", "name": "Move to In progress"},
            {"role": "button", "name": "Move to Done"},
            {"role": "button", "name": "Move to Open"},
            {"role": "dialog", "name": "Delete task?"},
            {"role": "button", "name": "Cancel"},
            {"role": "button", "name": "Delete task"},
        ]
        controls = (
            '<label for="task-search">Search tasks</label><input id="task-search" type="search">'
            '<select aria-label="Filter tasks by status"></select><button>Create task</button>'
            '<button>Delete</button><button>Move to In progress</button><button>Move to Done</button><button>Move to Open</button>'
            '<dialog open aria-labelledby="delete-heading"><h2 id="delete-heading">Delete task?</h2>'
            '<button>Cancel</button><button>Delete task</button></dialog>'
        )
        case = {
            "case_id": "WB-CORE-07", "dataset_id": "D-WB",
            "execution_requirements": {"test_data": [{"kind": "accessible_names", "dialog_target_visible_title": "Verify email notification", "expected_controls": expected}]},
        }
        board = [f'<td>{item["title"]}</td>' for item in INITIAL]
        open_html = render_board(board, controls=controls)
        closed_controls = (
            '<label for="task-search">Search tasks</label><input id="task-search" type="search">'
            '<select aria-label="Filter tasks by status"></select><button>Create task</button>'
            '<button>Delete</button><button>Move to In progress</button><button>Move to Done</button><button>Move to Open</button>'
            '<dialog aria-labelledby="delete-heading"><h2 id="delete-heading">Delete task?</h2>'
            '<button>Cancel</button><button>Delete task</button></dialog>'
        )
        closed_html = render_board(board, controls=closed_controls)
        result = adjudicate_fixture("accessible_names", case, [open_html, closed_html], [], screenshot_count=3)
        self.assertEqual(result["oracle_verdict"], "PASS", result["checks"])

    def test_accessible_names_is_unknown_without_post_cancel_closed_dialog_snapshot(self):
        expected = [
            {"role": "dialog", "name": "Delete task?"},
            {"role": "button", "name": "Cancel"},
            {"role": "button", "name": "Delete task"},
        ]
        controls = (
            '<dialog open aria-labelledby="heading"><h2 id="heading">Delete task?</h2>'
            '<button>Cancel</button><button>Delete task</button></dialog>'
        )
        case = {
            "case_id": "WB-CORE-07", "dataset_id": "D-WB",
            "execution_requirements": {"test_data": [{
                "kind": "accessible_names", "dialog_target_visible_title": "Verify email notification",
                "expected_controls": expected,
            }]},
        }
        html = render_board([f'<td>{item["title"]}</td>' for item in INITIAL], controls=controls)
        result = adjudicate_fixture("accessible_names", case, html, [])
        self.assertEqual(result["oracle_verdict"], "UNKNOWN", result["checks"])
        lifecycle = next(item for item in result["checks"] if item["check"].startswith("Cancel closes"))
        self.assertEqual(lifecycle["status"], "UNKNOWN")

    def test_visible_title_mapping_role_rejects_identifier_as_visible_text(self):
        case = {
            "case_id": "WB-CORE-08", "dataset_id": "D-WB",
            "execution_requirements": {"test_data": [{
                "kind": "recon_only", "target_data_id": "WB-101",
                "target_visible_title": "Reset password flow", "expected_status": "Open",
                "expected_button": "Move to In progress",
            }]},
        }
        html = render_board(['<td>Reset password flow</td><td>Open</td><td><button data-id="WB-101">Move to In progress</button></td>'])
        result = adjudicate_fixture("visible_title_mapping", case, html, [])
        self.assertEqual(result["oracle_verdict"], "PASS", result["checks"])

    def test_boundary_create_role_requires_exactly_eighty_characters(self):
        with tempfile.TemporaryDirectory() as temp:
            pilot = Path(temp) / "pilot"
            title = "Boundary check: " + ("a" * 64)
            self.assertEqual(len(title), 80)
            expected_summary = {"all": 6, "open": 3, "in_progress": 2, "done": 1}
            created = {"id": "WB-106", "title": title, "description": "", "priority": "High", "status": "open"}
            post = copy.deepcopy(INITIAL) + [created]
            html = render_board([f'<td>{title}</td><td>High</td><td>Open</td>'], summary=expected_summary) + '<p id="status-message">Created WB-106</p>'
            write_dom(pilot, html)
            case = {
                "case_id": "WB-CORE-11", "dataset_id": "D-WB",
                "execution_requirements": {"test_data": [{
                    "kind": "boundary_create", "title_input": title, "title_length": 80,
                    "priority": "High", "expected_status": "Open", "expected_summary": expected_summary,
                }]},
            }
            audit = [{"method": "POST", "path": "/api/reset", "status": 200, "action": "reset"},
                     {"method": "POST", "path": "/api/tasks", "status": 201, "action": "created", "item": created}]
            write_pilot_bundle(pilot, base_runner(post, expected_summary), audit, "Created 80-character task WB-106. PASS.")
            result = ORACLE.adjudicate_remaining_case(case, pilot, "create_boundary_80")
            self.assertEqual(result["oracle_verdict"], "PASS", result["checks"])

    def test_delete_cancel_role_checks_no_delete_and_retained_visible_title(self):
        case = {
            "case_id": "WB-CORE-13", "dataset_id": "D-WB",
            "user_input": "取消对 Verify email notification 的删除。",
            "reference_outcome": {"task_id": "WB-104"},
            "execution_requirements": {"test_data": [{
                "kind": "delete_cancel", "target_data_id": "WB-104", "target_visible_title": "Verify email notification",
            }]},
        }
        html = [
            render_board([f'<td>{item["title"]}</td>' for item in INITIAL]) +
            '<dialog id="delete-dialog" open aria-labelledby="delete-heading"><h2 id="delete-heading">Delete task?</h2>'
            '<button>Cancel</button><button>Delete task</button></dialog>',
            render_board([f'<td>{item["title"]}</td>' for item in INITIAL]) +
            '<dialog id="delete-dialog" aria-labelledby="delete-heading"><h2 id="delete-heading">Delete task?</h2>'
            '<button>Cancel</button><button>Delete task</button></dialog>',
        ]
        result = adjudicate_fixture(
            "delete_cancel", case, html, [],
            report="WB-104 Verify email notification: dialog opened; clicked Cancel. "
                   "The task remains; 没有发出 DELETE 请求。 Delete task was not clicked. PASS.",
            screenshot_count=3,
        )
        self.assertEqual(result["oracle_verdict"], "PASS", result["checks"])
        self.assertTrue(any("target-produced" in item for item in result["limitations"]), result["limitations"])


    def test_missing_dom_snapshot_is_unknown_not_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            pilot = Path(temp) / "pilot"
            case = {
                "case_id": "WB-CORE-03", "dataset_id": "D-WB",
                "execution_requirements": {"test_data": [{
                    "kind": "search_description", "query": "token expiry",
                    "expected_rows": [{"title": "Reset password flow"}],
                    "expected_summary": SUMMARY,
                }]},
            }
            audit = [{"method": "POST", "path": "/api/reset", "status": 200, "action": "reset"},
                     {"method": "GET", "path": "/api/tasks", "query": "q=token+expiry&status=all", "result_count": 1}]
            write_pilot_bundle(pilot, base_runner(), audit, "Search evidence recorded. PASS.")
            result = ORACLE.adjudicate_remaining_case(case, pilot, "search_description")
            self.assertEqual(result["oracle_verdict"], "UNKNOWN", result["checks"])
            self.assertEqual(result["business_behavior_verdict"], "UNKNOWN")

    def test_missing_server_audit_is_unknown_not_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            pilot = Path(temp) / "pilot"
            case = {
                "case_id": "WB-CORE-03", "dataset_id": "D-WB",
                "execution_requirements": {"test_data": [{
                    "kind": "search_description", "query": "token expiry",
                    "expected_rows": [{"title": "Reset password flow"}],
                    "expected_summary": SUMMARY,
                }]},
            }
            html = render_board(['<td>Reset password flow</td><td>High</td><td>Open</td>'])
            audit = [{"method": "POST", "path": "/api/reset", "status": 200, "action": "reset"},
                     {"method": "GET", "path": "/api/tasks", "query": "q=token+expiry&status=all", "result_count": 1}]
            write_dom(pilot, html)
            write_pilot_bundle(pilot, base_runner(), audit, "Search evidence recorded. PASS.")
            (pilot / "server-audit.jsonl").unlink()
            result = ORACLE.adjudicate_remaining_case(case, pilot, "search_description")
            self.assertEqual(result["oracle_verdict"], "UNKNOWN", result["checks"])
            self.assertEqual(result["business_behavior_verdict"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
