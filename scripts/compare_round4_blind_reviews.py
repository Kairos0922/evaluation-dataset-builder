#!/usr/bin/env python3
"""Validate and compare two blinded Round 4 Oracle design reviews without adjudicating them."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "docs/quality-assessment-v0.0.2/schemas/round4-blind-review-submission.schema.json"
EXPECTED_DATASET_SHA256 = "000d38b110b60eae902f86737ea6bd1368f98c6632c42a47bb9470a4a08bfc45"
EXPECTED_CASE_IDS = {
    "WB-01", "WB-03", "WB-04", "WB-05", "WB-06", "WB-07",
    "WB-08", "WB-09", "WB-11", "WB-13", "WB-14", "WB-15",
}
EXPECTED_LABELS = {
    "A": {f"RA-ITEM-{index:02d}" for index in range(1, 13)},
    "B": {f"RB-ITEM-{index:02d}" for index in range(1, 13)},
}
COMPARE_FIELDS = (
    "construct_relevance",
    "clarity",
    "executability",
    "freeze_decision",
    "max_write_actions",
    "max_script_runs",
    "application_skill_separation",
    "ambiguity_notes",
    "prohibited_side_effects",
)


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON submission {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"submission must be a JSON object: {path}")
    return value


def load_crosswalk(path: Path) -> dict[str, dict[str, str]]:
    mapped: dict[str, dict[str, str]] = {"A": {}, "B": {}}
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"reviewer_slot", "blind_label", "case_id", "case_sha256"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError("crosswalk must contain reviewer_slot, blind_label, case_id, case_sha256")
            for row in reader:
                slot, label, case_id = row["reviewer_slot"], row["blind_label"], row["case_id"]
                if slot not in mapped:
                    raise ValueError(f"invalid reviewer slot in crosswalk: {slot}")
                if label in mapped[slot]:
                    raise ValueError(f"duplicate crosswalk label: {slot}/{label}")
                if case_id not in EXPECTED_CASE_IDS:
                    raise ValueError(f"unexpected case ID in crosswalk: {case_id}")
                mapped[slot][label] = case_id
    except OSError as exc:
        raise ValueError(f"cannot read coordinator crosswalk {path}: {exc}") from exc

    for slot in ("A", "B"):
        if set(mapped[slot]) != EXPECTED_LABELS[slot]:
            raise ValueError(f"crosswalk {slot} labels do not match the 12-item packet")
        if set(mapped[slot].values()) != EXPECTED_CASE_IDS:
            raise ValueError(f"crosswalk {slot} does not map the exact 12 target cases")
        if len(set(mapped[slot].values())) != 12:
            raise ValueError(f"crosswalk {slot} maps multiple labels to the same case")
    return mapped


def validate_submission(submission: dict, *, slot: str, schema: dict) -> list[str]:
    errors = []
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in validator.iter_errors(submission):
        location = ".".join(str(part) for part in error.absolute_path)
        errors.append(f"{slot}.{location}: {error.message}")

    if submission.get("reviewer_slot") != slot:
        errors.append(f"{slot}: reviewer_slot must be {slot}")
    items = submission.get("items", [])
    labels = [item.get("blind_label") for item in items if isinstance(item, dict)]
    if len(labels) != 12 or set(labels) != EXPECTED_LABELS[slot] or len(set(labels)) != len(labels):
        errors.append(f"{slot}: items must contain each of the 12 packet labels exactly once")
    return errors


def compare_reviews(submission_a: dict, submission_b: dict, crosswalk: dict[str, dict[str, str]]) -> dict:
    by_label = {
        slot: {item["blind_label"]: item for item in submission["items"]}
        for slot, submission in (("A", submission_a), ("B", submission_b))
    }
    case_to_label = {
        slot: {case_id: label for label, case_id in crosswalk[slot].items()}
        for slot in ("A", "B")
    }

    cases = []
    for case_id in sorted(EXPECTED_CASE_IDS):
        label_a = case_to_label["A"][case_id]
        label_b = case_to_label["B"][case_id]
        item_a, item_b = by_label["A"][label_a], by_label["B"][label_b]
        differences = []
        for field in COMPARE_FIELDS:
            if item_a.get(field) != item_b.get(field):
                differences.append({
                    "field": field,
                    "reviewer_a": item_a.get(field),
                    "reviewer_b": item_b.get(field),
                })

        assertions_a = item_a.get("assertions", [])
        assertions_b = item_b.get("assertions", [])
        signatures_a = {
            (a.get("assertion_id"), a.get("normative_ref"), tuple(sorted(a.get("observation_method", []))),
             a.get("pass_condition"), a.get("fail_condition"), a.get("unknown_condition"))
            for a in assertions_a
        }
        signatures_b = {
            (a.get("assertion_id"), a.get("normative_ref"), tuple(sorted(a.get("observation_method", []))),
             a.get("pass_condition"), a.get("fail_condition"), a.get("unknown_condition"))
            for a in assertions_b
        }
        if signatures_a != signatures_b:
            differences.append({
                "field": "assertions",
                "reviewer_a_assertions": assertions_a,
                "reviewer_b_assertions": assertions_b,
            })

        cases.append({
            "case_id": case_id,
            "reviewer_a_label": label_a,
            "reviewer_b_label": label_b,
            "reviewer_a_freeze_decision": item_a.get("freeze_decision"),
            "reviewer_b_freeze_decision": item_b.get("freeze_decision"),
            "differences": differences,
            "human_adjudication_required": True,
        })

    return {
        "report_schema_version": "1.0.0",
        "status": "REQUIRES_HUMAN_ADJUDICATION",
        "dataset_sha256": EXPECTED_DATASET_SHA256,
        "reviewers": {
            "A": {"reviewer_id": submission_a["reviewer_id"], "packet_sha256": submission_a["packet_sha256"]},
            "B": {"reviewer_id": submission_b["reviewer_id"], "packet_sha256": submission_b["packet_sha256"]},
        },
        "reviewer_ids_distinct": submission_a["reviewer_id"] != submission_b["reviewer_id"],
        "case_count": len(cases),
        "cases_with_differences": sum(bool(case["differences"]) for case in cases),
        "cases": cases,
        "guardrail": (
            "This report only aligns independently submitted reviews. It does not resolve disagreements, "
            "create Gold labels, approve an Oracle, or authorize execution."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer-a", type=Path, required=True)
    parser.add_argument("--reviewer-b", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True, help="Coordinator-only CSV; never share with reviewers")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path, help="Optional path for the comparison report")
    args = parser.parse_args()

    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        submission_a = load_json(args.reviewer_a)
        submission_b = load_json(args.reviewer_b)
        errors = (
            validate_submission(submission_a, slot="A", schema=schema)
            + validate_submission(submission_b, slot="B", schema=schema)
        )
        if submission_a.get("reviewer_id") == submission_b.get("reviewer_id"):
            errors.append("reviewer IDs must be distinct to establish independent submissions")
        if submission_a.get("dataset_sha256") != EXPECTED_DATASET_SHA256:
            errors.append("reviewer A dataset SHA-256 does not match the frozen dataset")
        if submission_b.get("dataset_sha256") != EXPECTED_DATASET_SHA256:
            errors.append("reviewer B dataset SHA-256 does not match the frozen dataset")
        if errors:
            print("Blind review validation FAILED:")
            for error in errors:
                print(f"- {error}")
            return 1

        crosswalk = load_crosswalk(args.crosswalk)
        report = compare_reviews(submission_a, submission_b, crosswalk)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
