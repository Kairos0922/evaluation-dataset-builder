"""HTTP-level tests that rejected fixture API requests remain visible in the audit log."""
import copy
import http.client
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "workboard_fixture_server",
    ROOT / "benchmarks" / "webapp-testing" / "fixtures" / "workboard" / "server.py",
)
SERVER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(SERVER)


class WorkboardAuditTests(unittest.TestCase):
    def test_rejected_and_unmatched_api_requests_are_audited(self):
        with tempfile.TemporaryDirectory() as temp:
            SERVER.AUDIT_PATH = Path(temp) / "audit.jsonl"
            SERVER.TASKS = copy.deepcopy(SERVER.INITIAL_TASKS)
            SERVER.NEXT_ID = 106
            SERVER.SUMMARY_CACHE = SERVER.summary(SERVER.TASKS)
            httpd = SERVER.ThreadingHTTPServer(("127.0.0.1", 0), SERVER.Handler)
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            connection = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=3)
            try:
                requests = [
                    ("POST", "/api/tasks", {"title": "x" * 81, "priority": "Medium"}),
                    ("POST", "/api/tasks", {"title": "valid", "priority": "Urgent"}),
                    ("PATCH", "/api/tasks/WB-101", {"status": "archived"}),
                    ("PATCH", "/api/tasks/WB-999", {"status": "done"}),
                    ("DELETE", "/api/tasks/WB-999", None),
                    ("GET", "/api/missing", None),
                ]
                for method, path, body in requests:
                    payload = json.dumps(body) if body is not None else None
                    connection.request(method, path, body=payload, headers={"Content-Type": "application/json"})
                    response = connection.getresponse()
                    response.read()
                    self.assertIn(response.status, {400, 404})

                connection.request("POST", "/api/tasks", body="{", headers={"Content-Type": "application/json"})
                response = connection.getresponse()
                response.read()
                self.assertEqual(response.status, 400)
            finally:
                connection.close()
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=3)

            events = [json.loads(line) for line in SERVER.AUDIT_PATH.read_text(encoding="utf-8").splitlines()]
            observed = [(item["method"], item["path"], item["status"], item["action"]) for item in events]
            self.assertEqual(len(observed), 7, observed)
            self.assertEqual(
                [item[3] for item in observed],
                [
                    "create-rejected",
                    "create-rejected",
                    "update-rejected",
                    "update-rejected",
                    "delete-rejected",
                    "not-found",
                    "request-rejected",
                ],
            )
            self.assertTrue(all(item[0] in {"GET", "POST", "PATCH", "DELETE"} for item in observed))


if __name__ == "__main__":
    unittest.main()
