#!/usr/bin/env python3
"""Discover reviewable task candidates from an explicitly supplied redacted trajectory JSONL."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

try:
    from scripts.validate_trajectory_assets import validate_assets
except ModuleNotFoundError:  # direct script execution puts scripts/ on sys.path
    from validate_trajectory_assets import validate_assets

ROOT = Path(__file__).resolve().parents[1]
EVENT_SCHEMA_PATH = ROOT / "schemas" / "v0.0.3" / "trajectory-event.schema.json"
CANDIDATE_SCHEMA_PATH = ROOT / "schemas" / "v0.0.3" / "task-candidate.schema.json"


def reject_constant(token: str):
    raise ValueError(f"non-standard JSON numeric constant: {token}")


def load_schema(path: Path) -> dict:
    schema = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    Draft202012Validator.check_schema(schema)
    return schema


def read_events(path: Path) -> list[dict]:
    event_schema = load_schema(EVENT_SCHEMA_PATH)
    validator = Draft202012Validator(event_schema, format_checker=FormatChecker())
    events: list[dict] = []
    seen: set[tuple[str, str]] = set()
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line, parse_constant=reject_constant)
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"line {line_number}: invalid JSON: {exc}") from exc
            errors = sorted(validator.iter_errors(event), key=lambda e: list(e.absolute_path))
            if errors:
                detail = "; ".join(error.message for error in errors)
                raise ValueError(f"line {line_number}: invalid trajectory event: {detail}")
            identity = (event["session_id"], event["event_id"])
            if identity in seen:
                raise ValueError(f"line {line_number}: duplicate event_id {event['event_id']!r} in session")
            seen.add(identity)
            events.append(event)

    by_session: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        by_session[event["session_id"]].append(event)
    for session_id, session_events in by_session.items():
        session_events.sort(key=lambda item: item["sequence"])
        sequences = [item["sequence"] for item in session_events]
        if len(sequences) != len(set(sequences)):
            raise ValueError(f"session {session_id!r}: duplicate sequence number")
    return events


def discover_candidates(
    events: list[dict], source_id: str, candidate_prefix: str = "candidate", min_turns: int = 4
) -> list[dict]:
    """Return heuristic discovery leads; never infer a model-capability verdict."""
    if min_turns < 1:
        raise ValueError("min_turns must be >= 1")
    by_session: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        by_session[event["session_id"]].append(event)

    candidate_schema = load_schema(CANDIDATE_SCHEMA_PATH)
    candidate_validator = Draft202012Validator(candidate_schema, format_checker=FormatChecker())
    candidates: list[dict] = []
    ordinal = 0

    for session_id in sorted(by_session):
        session = sorted(by_session[session_id], key=lambda item: item["sequence"])
        for feedback_index, feedback in enumerate(session):
            if feedback["event_type"] != "user_feedback":
                continue
            if feedback.get("feedback_kind") not in {"correction", "unsatisfied", "rework_requested"}:
                continue

            prior_artifacts = [
                event for event in session[:feedback_index]
                if event["event_type"] == "artifact_created"
            ]
            later_artifacts = [
                event for event in session[feedback_index + 1:]
                if event["event_type"] == "artifact_created"
            ]
            previous_artifact = prior_artifacts[-1] if prior_artifacts else None
            revised_artifact = next(
                (event for event in later_artifacts
                 if previous_artifact and event.get("revision_of") == previous_artifact["artifact_ref"]),
                None,
            )

            signals: list[str] = []
            if feedback["feedback_kind"] in {"correction", "rework_requested"}:
                signals.append("user_correction")
            if feedback["feedback_kind"] == "unsatisfied":
                signals.append("explicit_failure_feedback")
            if revised_artifact is not None:
                signals.append("rework_or_revision")
                if previous_artifact.get("artifact_sha256") != revised_artifact.get("artifact_sha256"):
                    signals.append("material_output_change")

            conversational_turns = sum(
                event["actor"] in {"user", "assistant"}
                and event["event_type"] in {"user_message", "assistant_message", "user_feedback"}
                for event in session
            )
            if conversational_turns >= min_turns:
                signals.append("multi_turn_interaction")
            if len(session) >= max(3 * min_turns, 12):
                signals.append("long_horizon_execution")

            task_input = next(
                (event for event in session[:feedback_index]
                 if event.get("task_marker") == "task_input"),
                session[0],
            )
            end_event = revised_artifact or feedback
            ordinal += 1
            safe_session = re.sub(r"[^A-Za-z0-9._-]+", "-", session_id).strip("-")[:40] or "session"
            safe_event = re.sub(r"[^A-Za-z0-9._-]+", "-", feedback["event_id"]).strip("-")[:40] or str(ordinal)
            candidate = {
                "schema_version": "0.0.3",
                "candidate_id": f"{candidate_prefix}-{safe_session}-{safe_event}-{ordinal}",
                "source_id": source_id,
                "discovery_signals": sorted(set(signals)),
                "evidence_refs": [{
                    "event_start": task_input["event_id"],
                    "event_end": end_event["event_id"],
                    "description": (
                        f"Heuristic lead from {feedback['feedback_kind']} feedback; "
                        "requires independent qualification."
                    ),
                }],
                "status": "discovered",
                "created_at": feedback["timestamp"],
                "priority_rationale": "Candidate discovery signal only; not a capability-failure verdict.",
                "reviewer_notes": None,
            }
            errors = list(candidate_validator.iter_errors(candidate))
            if errors:
                raise ValueError("generated candidate violates schema: " + "; ".join(e.message for e in errors))
            candidates.append(candidate)

    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", required=True, type=Path, help="Redacted normalized trajectory JSONL")
    parser.add_argument("--source", required=True, type=Path, help="Authorized and redaction-reviewed trajectory source JSON")
    parser.add_argument("--output", required=True, type=Path, help="Output candidate JSONL path")
    parser.add_argument("--candidate-prefix", default="candidate")
    parser.add_argument("--min-turns", type=int, default=4, help="Heuristic signal only; does not gate qualification")
    args = parser.parse_args()

    try:
        source = json.loads(args.source.read_text(encoding="utf-8"), parse_constant=reject_constant)
        source_errors = validate_assets(source=source)
        if source_errors:
            raise ValueError("trajectory source is not eligible for discovery: " + "; ".join(source_errors))
        events = read_events(args.events)
        candidates = discover_candidates(events, source["source_id"], args.candidate_prefix, args.min_turns)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as stream:
            for candidate in candidates:
                stream.write(json.dumps(candidate, ensure_ascii=False, sort_keys=True) + "\n")
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print(f"PASS: discovered {len(candidates)} reviewable candidate(s); no capability verdict was inferred")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
