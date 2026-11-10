#!/usr/bin/env python3
"""Run one Builder-produced webapp-testing case in an isolated local fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def http_json(url: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        raw = response.read()
        return response.status, json.loads(raw.decode("utf-8"))


def wait_health(url: str, timeout: int = 30) -> dict:
    deadline = time.monotonic() + timeout
    last_error = "not ready"
    while time.monotonic() < deadline:
        try:
            status, payload = http_json(url + "/api/health")
            if status == 200 and payload.get("status") == "ok":
                return payload
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.25)
    raise TimeoutError(f"HTTP health check timed out: {last_error}")


def port_open(host: str, port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.2)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


def stop_process_group(process: subprocess.Popen | None, timeout: int = 8) -> None:
    if process is None:
        return
    # Kill the process group even when its leader has exited; browser/helper
    # children may still be alive in the same session.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=timeout)


def resolve_user_input(case: dict) -> tuple[str, str | None]:
    """Normalize schema-supported user_input values without guessing field names."""
    raw = case.get("user_input")
    if isinstance(raw, str):
        task = raw.strip()
        target_url = None
    elif isinstance(raw, dict):
        task_value = raw.get("task") or raw.get("prompt") or raw.get("content")
        task = task_value.strip() if isinstance(task_value, str) else ""
        url_value = raw.get("target_url") or raw.get("url")
        target_url = url_value.strip() if isinstance(url_value, str) and url_value.strip() else None
    elif isinstance(raw, list):
        task = json.dumps(raw, ensure_ascii=False, indent=2)
        target_url = None
    else:
        raise ValueError("case user_input must be a non-empty string, object, or array")
    if not task:
        raise ValueError("case user_input does not contain usable task text")
    return task, target_url


def resolve_case_timeout(environment: dict, override: int | None) -> int:
    raw = override if override is not None else environment.get("case_timeout_seconds", 900)
    if isinstance(raw, bool):
        raise ValueError("case_timeout_seconds must be an integer")
    try:
        timeout = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("case_timeout_seconds must be an integer") from exc
    if timeout < 1 or timeout > 900:
        raise ValueError("case timeout must be between 1 and 900 seconds")
    return timeout


def parse_trace(path: Path) -> dict:
    events = []
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    events.append(item)
            except json.JSONDecodeError:
                continue
    calls = [
        item for item in events
        if item.get("type") == "tool_call"
        and item.get("tool") == "skill"
        and (item.get("input") or {}).get("name") == "webapp-testing"
    ]
    results = {
        item.get("callId"): item
        for item in events
        if item.get("type") == "tool_result" and item.get("callId")
    }
    finals = [item for item in events if item.get("type") == "final"]
    return {
        "event_count": len(events),
        "webapp_testing_skill_calls": len(calls),
        "completed_skill_calls": sum(
            results.get(call.get("callId"), {}).get("status") == "completed"
            for call in calls
        ),
        "final_reason": (finals[-1].get("reason") or {}).get("kind") if finals else None,
    }


def self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "events.jsonl"
        path.write_text(
            json.dumps({"type": "tool_call", "tool": "skill",
                        "input": {"name": "webapp-testing"}, "callId": "c1"}) + "\n"
            + json.dumps({"type": "tool_result", "callId": "c1", "status": "completed"}) + "\n"
            + json.dumps({"type": "final", "reason": {"kind": "completed"}}) + "\n",
            encoding="utf-8",
        )
        parsed = parse_trace(path)
        assert parsed["webapp_testing_skill_calls"] == 1
        assert parsed["completed_skill_calls"] == 1
        assert parsed["final_reason"] == "completed"
        string_task, string_url = resolve_user_input({"user_input": "  run this task  "})
        assert string_task == "run this task" and string_url is None
        object_task, object_url = resolve_user_input({
            "user_input": {"task": "inspect the app", "target_url": "http://127.0.0.1:4173"}
        })
        assert object_task == "inspect the app"
        assert object_url == "http://127.0.0.1:4173"
        array_task, array_url = resolve_user_input({"user_input": ["step one", "step two"]})
        assert '"step one"' in array_task and array_url is None
        assert resolve_case_timeout({"case_timeout_seconds": 180}, None) == 180
        assert resolve_case_timeout({"case_timeout_seconds": 600}, None) == 600
        assert resolve_case_timeout({"case_timeout_seconds": 600}, 300) == 300
    print("PASS: runner self-test (trace, input formats, and case-specific timeout)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--dataset")
    parser.add_argument("--dataset-id")
    parser.add_argument("--case-id")
    parser.add_argument("--fixture-source")
    parser.add_argument("--public-assets")
    parser.add_argument("--skill-source")
    parser.add_argument("--work-root")
    parser.add_argument("--output-dir")
    parser.add_argument("--skill-commit")
    parser.add_argument("--fixture-profile", choices=("clean", "mutant"))
    parser.add_argument("--fixture-mutations")
    parser.add_argument("--case-timeout", type=int)
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    required = ("dataset", "dataset_id", "case_id", "fixture_source",
                "public_assets", "skill_source", "work_root", "output_dir",
                "skill_commit")
    missing = [name for name in required if not getattr(args, name)]
    if missing:
        parser.error("missing required arguments: " + ", ".join("--" + x.replace("_", "-") for x in missing))

    dataset = Path(args.dataset).resolve()
    fixture = Path(args.fixture_source).resolve()
    public_assets = Path(args.public_assets).resolve()
    skill_source = Path(args.skill_source).resolve()
    work_root = Path(args.work_root).resolve()
    output = Path(args.output_dir).resolve()
    for path in (dataset, fixture, public_assets, skill_source):
        if not path.exists():
            raise SystemExit(f"required path does not exist: {path}")
    output.mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=True, exist_ok=True)

    cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = [case for case in cases if case.get("case_id") == args.case_id]
    if len(selected) != 1:
        raise SystemExit(f"expected exactly one case_id={args.case_id!r}; found {len(selected)}")
    case = selected[0]
    if case.get("dataset_id") != args.dataset_id:
        raise SystemExit("dataset_id does not match selected case")

    execution = case.get("execution_requirements") or {}
    environment = execution.get("environment") or {}
    initial_state = execution.get("initial_state") or {}
    try:
        task, input_target_url = resolve_user_input(case)
    except ValueError as exc:
        raise SystemExit(str(exc))
    target_url = input_target_url or initial_state.get("url") or environment.get("app_url")
    if not target_url:
        raise SystemExit("case has no target URL in user_input or execution_requirements")
    parsed = urlparse(target_url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if parsed.scheme != "http" or host not in ("127.0.0.1", "localhost"):
        raise SystemExit(f"only local HTTP loopback targets are allowed: {target_url}")
    if port != 4173:
        raise SystemExit(f"unexpected fixture port {port}; expected 4173")

    profile = args.fixture_profile or initial_state.get("fixture_profile") or environment.get("fixture_profile") or "clean"
    case_mutations = initial_state.get("fixture_mutations") or environment.get("fixture_mutations") or []
    if args.fixture_mutations is not None:
        mutations = [item.strip() for item in args.fixture_mutations.split(",") if item.strip()]
    else:
        mutations = case_mutations
    allowed_mutations = {"search-case-sensitive", "stale-summary", "blank-title"}
    if not isinstance(mutations, list) or not set(mutations).issubset(allowed_mutations):
        raise SystemExit("invalid fixture mutations in case or pilot arguments")
    if profile == "clean" and mutations:
        raise SystemExit("clean fixture profile cannot include mutations")
    server_state = initial_state.get("server_state") or environment.get("server_state_at_start") or "running"
    if server_state != "running":
        raise SystemExit("pilot runner supports server_state=running only; stopped-server cases are deferred")
    if profile not in ("clean", "mutant"):
        raise SystemExit("invalid fixture profile in Builder case")
    try:
        case_timeout = resolve_case_timeout(environment, args.case_timeout)
    except ValueError as exc:
        raise SystemExit(str(exc))

    case_dir = output / args.case_id
    if case_dir.exists():
        raise SystemExit(f"refusing to overwrite existing evidence directory: {case_dir}")
    case_dir.mkdir(parents=True)
    workspace = work_root / args.case_id
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    shutil.copytree(public_assets, workspace / "assets" / "public")
    shutil.copytree(skill_source, workspace / ".dsh" / "skills" / "webapp-testing")

    audit_log = case_dir / "server-audit.jsonl"
    server_log = (case_dir / "server.log").open("w", encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "APP_HOST": host, "APP_PORT": str(port), "APP_PROFILE": profile,
        "APP_MUTATIONS": ",".join(mutations), "APP_AUDIT_LOG": str(audit_log),
    })
    if port_open(host, port):
        raise SystemExit(f"fixture port already occupied: {host}:{port}")

    server = None
    dsh = None
    error = None
    dsh_exit = None
    started = utc_now()
    pre_state = post_state = None
    try:
        server = subprocess.Popen(
            [sys.executable, str(fixture / "server.py")],
            cwd=str(fixture), env=env, stdout=server_log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        health = wait_health(target_url)
        _, reset_result = http_json(target_url + "/api/reset", "POST", {})
        _, pre_state = http_json(target_url + "/api/tasks")
        dsh_env = os.environ.copy()
        dsh_env.update({
            "DSH_TELEMETRY_MODE": "DISABLED",
            "DSH_TELEMETRY_DISABLED": "1",
        })
        events_path = case_dir / "dsh-events.jsonl"
        stderr_path = case_dir / "dsh-stderr.log"
        public_task = {
            "case_id": case["case_id"],
            "dataset_id": case["dataset_id"],
            "title": case.get("title"),
            "objective": case.get("objective"),
            "task": task,
            "target_url": target_url,
            "public_assets": "assets/public/",
            "constraints": [
                "Use the webapp-testing Skill and real Playwright browser interaction.",
                "Only access the local loopback application. Do not access external networks.",
                "Do not read, modify, or infer hidden Oracle data.",
                "Do not modify application source files.",
                "Save reports, screenshots, scripts, and evidence in artifacts/ only.",
                "Do not claim PASS without observable browser evidence.",
            ],
        }
        prompt = (
            "Execute the following Builder-generated web application test task. "
            "Follow the webapp-testing Skill instructions. The application is already "
            "running and healthy at the supplied URL. Use the public assets for rules. "
            "Do not inspect application source code. Create your own Playwright test "
            "script and a concise report with evidence.\n\n"
            + json.dumps(public_task, ensure_ascii=False, indent=2)
        )
        (case_dir / "consumer-task.json").write_text(
            json.dumps(public_task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (workspace / "TASK.md").write_text(prompt + "\n", encoding="utf-8")
        artifacts_dir = workspace / "artifacts"
        artifacts_dir.mkdir()
        with events_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
            dsh = subprocess.Popen(
                ["dsh", "--profile", "headless", "--json", "--permission-mode", "workspace-write", "-"],
                cwd=str(workspace), env=dsh_env, stdin=subprocess.PIPE,
                stdout=stdout, stderr=stderr, text=True, start_new_session=True,
            )
            try:
                dsh.communicate(prompt, timeout=case_timeout)
                dsh_exit = dsh.returncode
            except subprocess.TimeoutExpired:
                error = f"DSH timed out after {args.case_timeout}s"
                stop_process_group(dsh, timeout=5)
                dsh_exit = 124
        _, post_state = http_json(target_url + "/api/tasks")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        stop_process_group(dsh)
        stop_process_group(server)
        server_log.close()

    # Preserve all files created by the Skill in its isolated workspace.
    skill_artifact_root = workspace / "artifacts"
    if skill_artifact_root.is_dir():
        shutil.copytree(skill_artifact_root, case_dir / "skill-artifacts", dirs_exist_ok=True)
    skill_artifact_files = [
        path for path in (case_dir / "skill-artifacts").rglob("*")
        if path.is_file()
    ] if (case_dir / "skill-artifacts").exists() else []
    artifact_suffixes = {path.suffix.lower() for path in skill_artifact_files}
    has_markdown_report = ".md" in artifact_suffixes
    has_json_evidence_index = ".json" in artifact_suffixes
    has_screenshot = bool({".png", ".jpg", ".jpeg", ".webp"} & artifact_suffixes)

    port_closed = not port_open(host, port)
    trace = parse_trace(case_dir / "dsh-events.jsonl")
    evidence_files = []
    for path in sorted(case_dir.rglob("*")):
        if path.is_file():
            evidence_files.append({
                "path": str(path.relative_to(case_dir)),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
            })
    runner_status = (
        "INVOCATION_OK"
        if dsh_exit == 0
        and trace["webapp_testing_skill_calls"] > 0
        and trace["completed_skill_calls"] > 0
        and trace["final_reason"] == "completed"
        and port_closed
        and error is None
        and has_markdown_report
        and has_json_evidence_index
        and has_screenshot
        else "BLOCKED"
    )
    result = {
        "case_id": args.case_id,
        "dataset_id": args.dataset_id,
        "runner_status": runner_status,
        "scope": "pilot invocation evidence only; not grading or Oracle adjudication",
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "builder_case_sha256": sha256(dataset),
        "webapp_testing_skill_commit": args.skill_commit,
        "fixture_profile": profile,
        "fixture_mutations": mutations,
        "server_health": health if "health" in locals() else None,
        "reset_response": reset_result if "reset_result" in locals() else None,
        "pre_state": pre_state,
        "post_state": post_state,
        "dsh_exit_code": dsh_exit,
        "case_timeout_seconds": case_timeout,
        "trace": trace,
        "server_port_closed": port_closed,
        "skill_artifact_file_count": len(skill_artifact_files),
        "skill_artifact_types": sorted(artifact_suffixes),
        "required_skill_evidence": {
            "markdown_report": has_markdown_report,
            "json_evidence_index": has_json_evidence_index,
            "screenshot": has_screenshot,
        },
        "runner_error": error,
        "evidence_files": evidence_files,
    }
    (case_dir / "runner-result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "case_id": args.case_id, "dataset_id": args.dataset_id,
        "runner_status": runner_status, "trace": trace,
        "server_port_closed": port_closed, "runner_error": error,
    }, ensure_ascii=False))
    return 0 if runner_status == "INVOCATION_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
