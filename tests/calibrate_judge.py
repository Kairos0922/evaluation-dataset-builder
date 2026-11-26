#!/usr/bin/env python3
"""Run a bounded synthetic smoke suite against the configured independent Judge.

The resulting report is explicitly NOT_VALIDATED: this fixture exercises the
execution and evidence pipeline, not empirical Judge validity.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT))
import run_eval as runner
from scripts.validate_judge_calibration import validate_report


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_contract_report(
    fixture: dict,
    results: list[dict],
    *,
    base_url: str,
    model: str,
    candidate_sha: str,
    run_id: str | None = None,
) -> dict:
    """Translate execution results into the v0.0.2 evidence contract."""
    suite_path = ROOT / "tests" / "judge-calibration-cases.json"
    suite_bytes = suite_path.read_bytes()
    case_ids = [case["id"] for case in fixture["cases"]]
    adjudicable = [item for item in results if item["gold_status"] in {"PASS", "FAIL"}]
    exact = sum(item["gold_status"] == item["judge_status"] for item in adjudicable)
    false_passes = sum(
        item["gold_status"] == "FAIL" and item["judge_status"] == "PASS"
        for item in adjudicable
    )
    false_fails = sum(
        item["gold_status"] == "PASS" and item["judge_status"] == "FAIL"
        for item in adjudicable
    )
    abstentions = sum(item["judge_status"] == "UNKNOWN" for item in results)
    accuracy = exact / len(adjudicable) if adjudicable else None
    judge_source = inspect.getsource(runner.judge_case).encode("utf-8")
    implementation = (ROOT / "tests" / "run_eval.py").read_bytes()
    commit = candidate_sha if len(candidate_sha) in {40, 64} else None
    if commit and any(ch not in "0123456789abcdefABCDEF" for ch in commit):
        commit = None

    return {
        "schema_version": "0.0.2",
        "report_id": "judge-calibration-" + sha256_bytes(suite_bytes + candidate_sha.encode())[:16],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "calibration_kind": "synthetic_smoke",
        "status": "NOT_VALIDATED",
        "dataset": {
            "suite_id": fixture["suite_id"],
            "suite_sha256": sha256_bytes(suite_bytes),
            "case_ids": case_ids,
            "label_source": "synthetic_fixture",
            "independent_gold": False,
            "split_id": None,
            "held_out": False,
        },
        "judge": {
            "provider": urlsplit(base_url).hostname or "unknown",
            "endpoint_origin": base_url,
            "model_id": model,
            "model_revision": None,
            "prompt_sha256": sha256_bytes(judge_source),
            "implementation_sha256": sha256_bytes(implementation),
            "separate_from_subject": base_url != runner.DEEPSEEK_BASE_URL,
        },
        "protocol": {
            "blinded": False,
            "independent_review": False,
            "repeats_per_case": 1,
            "abstention_policy": "Insufficient or unverifiable evidence => UNKNOWN",
            "run_id": run_id,
            "commit_sha": commit,
        },
        "results": results,
        "summary": {
            "case_count": len(results),
            "adjudicable_count": len(adjudicable),
            "exact_matches": exact,
            "false_passes": false_passes,
            "false_fails": false_fails,
            "abstentions": abstentions,
            "accuracy": accuracy,
        },
        "limitations": [
            "This suite uses synthetic fixture labels and is not independent Gold.",
            "A successful smoke run verifies only the bounded execution/evidence path; it does not establish empirical Judge validity.",
            "No claims about complex business semantics, inter-rater agreement, or generalization are supported.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/judge-calibration.json")
    parser.add_argument("--checkpoint", default="artifacts/judge-calibration-checkpoint.json")
    args = parser.parse_args()
    api_key = os.getenv("EVAL_JUDGE_API_KEY", "")
    model = os.getenv("EVAL_JUDGE_MODEL", "")
    base_url = os.getenv("EVAL_JUDGE_BASE_URL", "").rstrip("/")
    input_price = os.getenv("EVAL_JUDGE_INPUT_PRICE_USD_PER_MILLION", "")
    output_price = os.getenv("EVAL_JUDGE_OUTPUT_PRICE_USD_PER_MILLION", "")
    if not all((api_key, model, base_url, input_price, output_price)):
        raise SystemExit("Judge 凭证、模型、服务地址或价格配置缺失。")
    if base_url == runner.DEEPSEEK_BASE_URL:
        raise SystemExit("Judge 必须使用独立于生成端的服务地址。")
    runner.MODEL_PRICING_USD_PER_MILLION[model] = {
        "input": float(input_price), "output": float(output_price)
    }
    runner.JUDGE_BASE_URL = base_url
    runner.JUDGE_API_URL = base_url + "/chat/completions"
    runner.MAX_API_REQUESTS = 8
    runner.MAX_ESTIMATED_COST_USD = float(os.getenv("JUDGE_CALIBRATION_MAX_COST_USD", "0.10"))
    runner.MAX_COMPLETION_TOKENS = int(os.getenv("JUDGE_CALIBRATION_MAX_COMPLETION_TOKENS", "500"))
    runner.CURRENT_RUN_INDEX = 0

    suite_path = ROOT / "tests" / "judge-calibration-cases.json"
    fixture = json.loads(suite_path.read_text(encoding="utf-8"))
    candidate_sha = os.getenv("GITHUB_SHA", "local")
    signature_source = json.dumps(
        {"suite": fixture, "base_url": base_url, "model": model, "candidate_sha": candidate_sha},
        ensure_ascii=False, sort_keys=True,
    )
    signature = hashlib.sha256(signature_source.encode("utf-8")).hexdigest()
    runner.configure_checkpoint(ROOT / args.checkpoint, signature)

    results = []
    for case in fixture["cases"]:
        check = runner.judge_case(
            api_key, model, [case["criterion"]], case["candidate"],
            api_url=runner.JUDGE_API_URL,
        )[0]
        output_sha = sha256_bytes(case["candidate"].encode("utf-8"))
        results.append({
            "case_id": case["id"],
            "gold_status": case["expected_status"],
            "judge_status": check["status"],
            "evidence_validated": bool(check.get("evidence_validated", False)),
            "output_sha256": output_sha,
            "gold_evidence_ref": "synthetic-fixture://" + case["id"],
        })

    report = build_contract_report(
        fixture, results, base_url=base_url, model=model,
        candidate_sha=candidate_sha, run_id=os.getenv("GITHUB_RUN_ID"),
    )
    errors = validate_report(report, suite_path)
    if errors:
        for error in errors:
            print("ERROR: " + error, file=sys.stderr)
        return 2

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["accuracy"] == 1.0 and report["summary"]["false_passes"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
