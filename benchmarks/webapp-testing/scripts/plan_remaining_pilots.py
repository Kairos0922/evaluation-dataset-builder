#!/usr/bin/env python3
"""Create a conservative, non-executing plan for the eleven remaining Builder cases."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ORDER = (
    "initial_board",
    "search_description",
    "search_empty",
    "status_filter",
    "search_filter_combo",
    "visible_title_mapping",
    "accessible_names",
    "delete_cancel",
    "create_rejected",
    "create_success",
    "create_boundary_80",
)
TIMEOUTS = {
    "initial_board": 180,
    "search_description": 180,
    "search_empty": 180,
    "status_filter": 180,
    "search_filter_combo": 240,
    "visible_title_mapping": 180,
    "accessible_names": 180,
    "delete_cancel": 180,
    "create_rejected": 240,
    "create_success": 240,
    "create_boundary_80": 240,
}
CLASSES = {
    "initial_board": "read_only",
    "search_description": "read_only",
    "search_empty": "read_only",
    "status_filter": "read_only",
    "search_filter_combo": "read_only",
    "visible_title_mapping": "read_only",
    "accessible_names": "dialog_cancel",
    "delete_cancel": "dialog_cancel",
    "create_rejected": "rejected_write",
    "create_success": "successful_write",
    "create_boundary_80": "successful_write",
}


def build_plan(matrix: dict) -> dict:
    include = matrix.get("include")
    if not isinstance(include, list):
        raise ValueError("matrix.include must be a list")
    by_role = {}
    for item in include:
        role = item.get("pilot_role")
        if role not in ORDER:
            raise ValueError(f"unexpected role: {role!r}")
        if role in by_role:
            raise ValueError(f"duplicate role: {role}")
        case_id, dataset_id = item.get("case_id"), item.get("dataset_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"{role}: case_id missing")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise ValueError(f"{role}: dataset_id missing")
        by_role[role] = item
    missing = sorted(set(ORDER) - set(by_role))
    extra = sorted(set(by_role) - set(ORDER))
    if missing or extra:
        raise ValueError(f"matrix coverage mismatch; missing={missing}, extra={extra}")
    if len({item["case_id"] for item in by_role.values()}) != len(ORDER):
        raise ValueError("case IDs must be unique across remaining roles")

    steps = []
    for index, role in enumerate(ORDER, 1):
        item = by_role[role]
        steps.append({
            "sequence": index,
            "case_id": item["case_id"],
            "dataset_id": item["dataset_id"],
            "pilot_role": role,
            "side_effect_class": CLASSES[role],
            "case_timeout_seconds": TIMEOUTS[role],
            "execution": "NOT_AUTHORIZED",
            "run_policy": "one_case_at_a_time; inspect evidence and cost before proceeding",
        })
    return {
        "plan_version": "1",
        "source": "Builder-resolved matrix; case definitions are not modified",
        "execution_authorized": False,
        "execution_started": False,
        "status": "DRY_RUN_PLAN_ONLY",
        "required_roles": list(ORDER),
        "case_count": len(steps),
        "sum_case_timeout_seconds": sum(item["case_timeout_seconds"] for item in steps),
        "sum_case_timeout_minutes": sum(item["case_timeout_seconds"] for item in steps) / 60,
        "sequential_policy": True,
        "stop_conditions": [
            "Any case reports BLOCKED, FAIL, UNKNOWN, or evidence-integrity failure",
            "Any DSH token, step, or time budget is exceeded",
            "Credential or secret is detected in evidence",
            "Artifact integrity or Builder source provenance cannot be verified",
        ],
        "steps": steps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", required=True, help="JSON matrix resolved from original Builder output")
    parser.add_argument("--output", required=True, help="Write dry-run plan JSON")
    args = parser.parse_args()
    matrix = json.loads(Path(args.matrix).read_text(encoding="utf-8"))
    plan = build_plan(matrix)
    Path(args.output).write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": plan["status"], "cases": plan["case_count"], "timeout_budget_seconds": plan["sum_case_timeout_seconds"], "execution_started": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
