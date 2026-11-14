#!/usr/bin/env python3
"""Deterministic Workboard Lite test application.

The implementation profile is controlled by APP_PROFILE:
- clean: follows the published application rules.
- mutant: enables deterministic defects for later mutation experiments.

The profile is a runtime setting. It is not rendered in the UI or returned by
the public application API.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
HOST = os.environ.get("APP_HOST", "127.0.0.1")
PORT = int(os.environ.get("APP_PORT", "4173"))
PROFILE = os.environ.get("APP_PROFILE", "clean").strip().lower()
MUTATIONS = {
    item.strip()
    for item in os.environ.get("APP_MUTATIONS", "").split(",")
    if item.strip()
}
if PROFILE == "mutant" and not MUTATIONS:
    MUTATIONS = {"search-case-sensitive", "stale-summary", "blank-title"}
AUDIT_PATH = Path(os.environ.get("APP_AUDIT_LOG", "/tmp/workboard-audit.jsonl"))

INITIAL_TASKS = [
    {
        "id": "WB-101",
        "title": "Reset password flow",
        "description": "Review password reset email and token expiry.",
        "priority": "High",
        "status": "open",
    },
    {
        "id": "WB-102",
        "title": "Update onboarding guide",
        "description": "Add screenshots for the first project setup.",
        "priority": "Low",
        "status": "in_progress",
    },
    {
        "id": "WB-103",
        "title": "Fix export timeout",
        "description": "CSV export stops after a large result set.",
        "priority": "High",
        "status": "done",
    },
    {
        "id": "WB-104",
        "title": "Verify email notification",
        "description": "Check delivery after a task status change.",
        "priority": "Medium",
        "status": "open",
    },
    {
        "id": "WB-105",
        "title": "Review accessibility",
        "description": "Check labels, keyboard order, and status messages.",
        "priority": "Medium",
        "status": "in_progress",
    },
]
TASKS = deepcopy(INITIAL_TASKS)
NEXT_ID = 106
SUMMARY_CACHE = None


def summary(items: list[dict]) -> dict[str, int]:
    return {
        "all": len(items),
        "open": sum(task["status"] == "open" for task in items),
        "in_progress": sum(task["status"] == "in_progress" for task in items),
        "done": sum(task["status"] == "done" for task in items),
    }


def record(event: dict) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with AUDIT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


class Handler(BaseHTTPRequestHandler):
    server_version = "WorkboardFixture/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        # Request audit records are written as structured JSONL by record().
        return

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Request body must be a JSON object")
        return value

    def send_static(self, name: str, content_type: str) -> None:
        path = STATIC / name
        if not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_static("index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/assets/app.js":
            self.send_static("app.js", "text/javascript; charset=utf-8")
            return
        if parsed.path == "/assets/style.css":
            self.send_static("style.css", "text/css; charset=utf-8")
            return
        if parsed.path == "/api/health":
            self.send_json(200, {"status": "ok"})
            return
        if parsed.path == "/api/tasks":
            params = parse_qs(parsed.query)
            query = params.get("q", [""])[0]
            status_filter = params.get("status", ["all"])[0]
            if "search-case-sensitive" in MUTATIONS:
                matches = [
                    task for task in TASKS
                    if query in task["title"]
                ] if query else list(TASKS)
            else:
                needle = query.casefold()
                matches = [
                    task for task in TASKS
                    if not needle
                    or needle in task["title"].casefold()
                    or needle in task["description"].casefold()
                ]
            if status_filter != "all":
                matches = [task for task in matches if task["status"] == status_filter]
            counts = SUMMARY_CACHE if "stale-summary" in MUTATIONS and SUMMARY_CACHE is not None else summary(TASKS)
            self.send_json(200, {"items": deepcopy(matches), "summary": deepcopy(counts)})
            record({"method": "GET", "path": "/api/tasks", "query": parsed.query, "status": 200, "result_count": len(matches)})
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        global TASKS, NEXT_ID, SUMMARY_CACHE
        parsed = urlparse(self.path)
        try:
            data = self.read_json()
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self.send_json(400, {"error": f"Invalid JSON: {exc}"})
            return
        if parsed.path == "/api/reset":
            TASKS = deepcopy(INITIAL_TASKS)
            NEXT_ID = 106
            SUMMARY_CACHE = summary(TASKS)
            self.send_json(200, {"status": "reset", "summary": summary(TASKS)})
            record({"method": "POST", "path": parsed.path, "status": 200, "action": "reset"})
            return
        if parsed.path == "/api/tasks":
            raw_title = str(data.get("title", ""))
            if "blank-title" in MUTATIONS:
                title = raw_title
            else:
                title = raw_title.strip()
                if not title:
                    self.send_json(400, {"error": "Title is required"})
                    record({"method": "POST", "path": parsed.path, "status": 400, "action": "create-rejected", "reason": "blank-title"})
                    return
            if len(title) > 80:
                self.send_json(400, {"error": "Title must be 80 characters or fewer"})
                return
            priority = str(data.get("priority", "Medium"))
            if priority not in {"Low", "Medium", "High"}:
                self.send_json(400, {"error": "Priority is invalid"})
                return
            task = {
                "id": f"WB-{NEXT_ID}",
                "title": title,
                "description": str(data.get("description", "")).strip(),
                "priority": priority,
                "status": "open",
            }
            NEXT_ID += 1
            TASKS.append(task)
            if "stale-summary" not in MUTATIONS:
                SUMMARY_CACHE = summary(TASKS)
            self.send_json(201, {"item": deepcopy(task), "summary": summary(TASKS)})
            record({"method": "POST", "path": parsed.path, "status": 201, "action": "created", "item": deepcopy(task)})
            return
        self.send_error(404)

    def do_PATCH(self) -> None:  # noqa: N802
        global SUMMARY_CACHE
        parsed = urlparse(self.path)
        prefix = "/api/tasks/"
        if not parsed.path.startswith(prefix):
            self.send_error(404)
            return
        task_id = parsed.path[len(prefix):]
        try:
            data = self.read_json()
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self.send_json(400, {"error": f"Invalid JSON: {exc}"})
            return
        task = next((item for item in TASKS if item["id"] == task_id), None)
        if task is None:
            self.send_json(404, {"error": "Task not found"})
            return
        old_status = task["status"]
        new_status = str(data.get("status", old_status))
        if new_status not in {"open", "in_progress", "done"}:
            self.send_json(400, {"error": "Status is invalid"})
            return
        task["status"] = new_status
        if "stale-summary" not in MUTATIONS:
            SUMMARY_CACHE = summary(TASKS)
        self.send_json(200, {"item": deepcopy(task), "summary": summary(TASKS)})
        record({"method": "PATCH", "path": parsed.path, "status": 200, "action": "status-changed", "old_status": old_status, "new_status": new_status})
        return

    def do_DELETE(self) -> None:  # noqa: N802
        global TASKS, SUMMARY_CACHE
        parsed = urlparse(self.path)
        prefix = "/api/tasks/"
        if not parsed.path.startswith(prefix):
            self.send_error(404)
            return
        task_id = parsed.path[len(prefix):]
        task = next((item for item in TASKS if item["id"] == task_id), None)
        if task is None:
            self.send_json(404, {"error": "Task not found"})
            return
        TASKS = [item for item in TASKS if item["id"] != task_id]
        if "stale-summary" not in MUTATIONS:
            SUMMARY_CACHE = summary(TASKS)
        self.send_json(200, {"deleted_id": task_id, "summary": summary(TASKS)})
        record({"method": "DELETE", "path": parsed.path, "status": 200, "action": "deleted", "item": deepcopy(task)})


def main() -> None:
    global SUMMARY_CACHE
    SUMMARY_CACHE = summary(TASKS)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Workboard Lite listening on http://{HOST}:{PORT} (profile={PROFILE})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
