#!/usr/bin/env python3
"""Classify Builder DSH failures without retrying paid model calls."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

QUOTA_PATTERN = re.compile(
    r"(?i)(HTTP\s*402|QUOTA|"
    r"INSUFFICIENT\s+BALANCE|INSUFFICIENT_BALANCE)"
)


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def read_exit_code(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Invalid Builder DSH exit-code evidence: {exc}") from exc


def classify_builder_run(artifacts_dir: Path) -> dict[str, Any]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    probe_report = read_json(artifacts_dir / "builder-connectivity-probe.json")
    probe_text = "\n".join(
        (
            read_text(artifacts_dir / "builder-connectivity-probe-events.jsonl"),
            read_text(artifacts_dir / "builder-connectivity-probe-stderr.log"),
        )
    )
    builder_text = "\n".join(
        (
            read_text(artifacts_dir / "builder-dsh-events.jsonl"),
            read_text(artifacts_dir / "builder-dsh-stderr.log"),
        )
    )
    exit_code = read_exit_code(artifacts_dir / "builder-dsh-exit-code.txt")

    quota_sources: list[str] = []
    if (
        probe_report.get("status") == "EXTERNAL_MODEL_QUOTA_BLOCKED"
        or QUOTA_PATTERN.search(probe_text)
    ):
        quota_sources.append("connectivity_probe")
    if QUOTA_PATTERN.search(builder_text):
        quota_sources.append("builder_invocation")

    builder_invocation_started = (
        exit_code is not None
        or (artifacts_dir / "builder-dsh-events.jsonl").exists()
        or (artifacts_dir / "builder-dsh-stderr.log").exists()
    )
    output_dir = artifacts_dir / "webapp-testing-builder-output"
    partial_output_files = (
        sum(1 for path in output_dir.rglob("*") if path.is_file())
        if output_dir.is_dir()
        else 0
    )
    probe_status = probe_report.get("status")

    if quota_sources:
        status = "EXTERNAL_MODEL_QUOTA_BLOCKED"
        message = (
            "HTTP 402, QUOTA, or Insufficient Balance was detected. "
            "Stop model calls. Do not retry the full Builder or switch providers."
        )
    elif not builder_invocation_started and probe_status not in (None, "PASS"):
        status = "CONNECTIVITY_PROBE_FAILED"
        message = "The connectivity probe failed. Builder invocation did not start."
    elif not builder_invocation_started:
        status = "BUILDER_NOT_STARTED_OR_INTERRUPTED"
        message = "No Builder DSH invocation evidence was found."
    elif exit_code is None:
        status = "BUILDER_INTERRUPTED"
        message = "Builder DSH started but no exit-code evidence was written."
    elif exit_code == 0:
        status = "DSH_EXIT_ZERO"
        message = "DSH exited with code zero. Trace verification is still required."
    else:
        status = "BUILDER_INVOCATION_FAILED"
        message = (
            "Builder DSH exited non-zero without a recognized quota error. "
            "Inspect the archived event log and stderr before classifying a code defect."
        )

    output_disposition = (
        "AWAITING_TRACE_VERIFICATION"
        if status == "DSH_EXIT_ZERO"
        else "DIAGNOSTIC_ONLY"
    )
    result = {
        "schema_version": "1.0",
        "status": status,
        "message": message,
        "quota_error_detected": bool(quota_sources),
        "quota_error_sources": quota_sources,
        "connectivity_probe_status": probe_status,
        "builder_dsh_exit_code": exit_code,
        "builder_invocation_started": builder_invocation_started,
        "partial_output_file_count": partial_output_files,
        "partial_output_disposition": output_disposition,
        "trace_verification_allowed": status == "DSH_EXIT_ZERO",
        "independent_validation_allowed": False,
        "automatic_full_builder_retry": False,
    }
    (artifacts_dir / "builder-run-failure-classification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    result = classify_builder_run(args.artifacts_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 78 if result["status"] == "EXTERNAL_MODEL_QUOTA_BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
