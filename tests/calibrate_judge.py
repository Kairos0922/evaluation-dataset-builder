#!/usr/bin/env python3
"""Run a small, synthetic calibration suite against the configured independent Judge."""
import argparse, hashlib, json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_eval as runner

def main():
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
    runner.MODEL_PRICING_USD_PER_MILLION[model] = {"input": float(input_price), "output": float(output_price)}
    runner.JUDGE_BASE_URL = base_url
    runner.JUDGE_API_URL = base_url + "/chat/completions"
    runner.MAX_API_REQUESTS = 8
    runner.MAX_ESTIMATED_COST_USD = float(os.getenv("JUDGE_CALIBRATION_MAX_COST_USD", "0.10"))
    runner.MAX_COMPLETION_TOKENS = int(os.getenv("JUDGE_CALIBRATION_MAX_COMPLETION_TOKENS", "500"))
    runner.CURRENT_RUN_INDEX = 0
    fixture = json.loads((ROOT / "tests/judge-calibration-cases.json").read_text(encoding="utf-8"))
    signature_source = json.dumps({"suite":fixture,"base_url":base_url,"model":model,"candidate_sha":os.getenv("GITHUB_SHA","local")},ensure_ascii=False,sort_keys=True)
    signature = hashlib.sha256(signature_source.encode("utf-8")).hexdigest()
    runner.configure_checkpoint(ROOT / args.checkpoint, signature)
    results = []
    for case in fixture["cases"]:
        check = runner.judge_case(api_key, model, [case["criterion"]], case["candidate"], api_url=runner.JUDGE_API_URL)[0]
        results.append({"case_id":case["id"],"risk":case["risk"],"expected_status":case["expected_status"],"actual_status":check["status"],"match":check["status"]==case["expected_status"],"evidence_validated":check.get("evidence_validated",False),"evidence":check.get("evidence",[]),"judge_basis":check.get("judge_basis"),"rationale":check.get("rationale"),"absence_reason":check.get("absence_reason")})
    exact = sum(x["match"] for x in results)
    false_passes = [x["case_id"] for x in results if x["expected_status"]!="PASS" and x["actual_status"]=="PASS"]
    accuracy = exact / len(results) if results else 0.0
    passed = accuracy >= 0.80 and not false_passes and len(results)==len(fixture["cases"])
    report = {"schema_version":"1.0","suite_id":fixture["suite_id"],"purpose":fixture["purpose"],"judge":{"base_url":base_url,"model":model},"candidate_sha":os.getenv("GITHUB_SHA","local"),"results":results,"summary":{"case_count":len(results),"exact_matches":exact,"accuracy":accuracy,"false_passes":false_passes,"minimum_accuracy":0.80,"pass":passed},"cost_control":{"max_requests":runner.MAX_API_REQUESTS,"actual_requests":runner.API_REQUEST_COUNT,"max_estimated_cost_usd":runner.MAX_ESTIMATED_COST_USD,"estimated_cost_reserved_usd":round(runner.ESTIMATED_COST_RESERVED_USD,6),"usage_by_model":runner.USAGE_BY_MODEL},"limitations":["该小型合成校准集只检查基础判定行为，不证明 Judge 对复杂业务语义具有充分可靠性。","通过校准不替代人工审查，也不代表 Skill 的 L3 或 L4 验证通过。"]}
    output = ROOT / args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if passed else 1
if __name__=="__main__":
    sys.exit(main())
