#!/usr/bin/env python3
"""Verify DSH evidence that Evaluation Dataset Builder was actually invoked."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def event_kind(event: dict) -> str:
    value = event.get("type", event.get("event", ""))
    return str(value).strip().lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.exit_code != 0:
        raise SystemExit(f"DSH exited with non-zero code: {args.exit_code}")
    if not args.events.is_file():
        raise SystemExit(f"DSH event log missing: {args.events}")
    if not args.output_dir.is_dir():
        raise SystemExit(f"Builder output directory missing: {args.output_dir}")

    events = []
    for line_no, line in enumerate(args.events.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{args.events}:{line_no}: invalid NDJSON: {exc}") from exc
        if not isinstance(event, dict):
            raise SystemExit(f"{args.events}:{line_no}: event must be a JSON object")
        events.append(event)

    if not events:
        raise SystemExit("DSH produced an empty event trace")

    builder_calls = []
    for event in events:
        if event_kind(event) != "tool_call":
            continue
        tool = str(event.get("tool", "")).lower()
        payload = event.get("input", {})
        if tool == "skill" and isinstance(payload, dict) and payload.get("name") == "evaluation-dataset-builder":
            builder_calls.append(event)

    if not builder_calls:
        raise SystemExit(
            "DSH trace does not prove a skill tool_call for evaluation-dataset-builder"
        )

    call_ids = {event.get("callId") for event in builder_calls if event.get("callId")}
    matching_results = [
        event for event in events
        if event_kind(event) == "tool_result" and event.get("callId") in call_ids
    ]
    if not matching_results:
        raise SystemExit("Builder tool_call has no matching tool_result in DSH trace")

    finals = [event for event in events if event_kind(event) == "final"]
    if not finals:
        raise SystemExit("DSH trace has no final event")
    final = finals[-1]
    reason = final.get("reason", {})
    reason_kind = reason.get("kind") if isinstance(reason, dict) else reason
    if reason_kind != "completed":
        raise SystemExit(f"DSH final reason is not completed: {reason_kind!r}")

    session_ids = []
    for event in events:
        if event_kind(event) == "session":
            value = event.get("session_id", event.get("id"))
            if value and str(value) not in session_ids:
                session_ids.append(str(value))

    generated_files = sorted(
        path.relative_to(args.output_dir).as_posix()
        for path in args.output_dir.rglob("*")
        if path.is_file()
    )
    if not generated_files:
        raise SystemExit("Builder output directory is empty")

    print(json.dumps({
        "status": "PASS",
        "scope": "actual_builder_invocation_evidence",
        "dsh_exit_code": args.exit_code,
        "event_count": len(events),
        "builder_skill_tool_calls": len(builder_calls),
        "final_reason": reason_kind,
        "session_ids": session_ids,
        "generated_files": generated_files,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
