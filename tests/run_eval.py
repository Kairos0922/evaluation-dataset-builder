#!/usr/bin/env python3
"""Multi-provider release-gate evaluator with matched baseline and repeat-run checks."""
import argparse
import json
import hashlib
import math

import os
import re
import sys
import time
from collections import deque
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
API_URL = DEEPSEEK_BASE_URL + "/chat/completions"
POLICY = {
    "behavior_pass_rate": 0.90,
    "trigger_precision": 0.95,
    "trigger_recall": 0.95,
    "max_stability_spread": 0.05,
    "minimum_runs": 2,
}
CRITICAL_CASE_IDS = ["SE03", "SE04", "SE05", "SE08", "SE09", "SE11", "SE12"]
DEFAULT_GENERATOR_MODEL = "deepseek-flash"
DEFAULT_JUDGE_MODEL = "deepseek-v4-pro"
JUDGE_BASE_URL = (os.getenv("EVAL_JUDGE_BASE_URL") or DEEPSEEK_BASE_URL).rstrip("/")
JUDGE_API_URL = JUDGE_BASE_URL + "/chat/completions"
DEFAULT_USER_AGENT = "evaluation-dataset-builder/0.0.1 (+https://github.com/Kairos0922/evaluation-dataset-builder)"
# Paid API safety controls. Price estimates use peak-hour cache-miss rates so
# the guard remains conservative even when actual cache/off-peak billing is cheaper.
MAX_COMPLETION_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "16384"))
MAX_ESTIMATED_COST_USD = float(os.getenv("DEEPSEEK_MAX_ESTIMATED_COST_USD", "1.50"))
MAX_API_REQUESTS = int(os.getenv("DEEPSEEK_MAX_API_REQUESTS", "220"))
MAX_ESTIMATED_REQUEST_TOKENS = int(os.getenv("DEEPSEEK_MAX_ESTIMATED_REQUEST_TOKENS", "950000"))
MODEL_CONTEXT_LIMITS = {"openai/gpt-oss-120b": 131072}
MODEL_RATE_LIMITS = {
    "openai/gpt-oss-120b": {
        "rpm": int(os.getenv("GROQ_JUDGE_RPM", "30")),
        "tpm": int(os.getenv("GROQ_JUDGE_TPM", "8000")),
        "tpd": int(os.getenv("GROQ_JUDGE_TPD", "200000")),
    }
}
MODEL_RATE_HISTORY = {}
MODEL_PRICING_USD_PER_MILLION = {
    "deepseek-flash": {"input": 0.30, "output": 1.20},
    "deepseek-v4-pro": {"input": 0.30, "output": 1.20},
}
USAGE_BY_MODEL = {}
API_REQUEST_COUNT = 0
ESTIMATED_COST_RESERVED_USD = 0.0
CACHE_HITS_BY_MODEL = {}
CURRENT_RUN_INDEX = 0
CHECKPOINT_PATH = None
CHECKPOINT_STORE = {"schema_version": 6, "signature": None, "responses": {}, "pending_requests": {}, "uncertain_requests": {}}


def effective_model_identity(base_url, model):
    """Resolve documented provider aliases before claiming model independence."""
    normalized_base = base_url.rstrip("/")
    if normalized_base == "https://api.deepseek.com" and model in {
        "deepseek-flash", "deepseek-v4-pro", "deepseek-v4-flash",
        "deepseek-v4-flash-vision-exp",
    }:
        # DeepSeek announced all deepseek-v4-pro requests route to V4.1 Flash
        # from 2026-09-14 until V4.1-Pro is launched.
        return "deepseek:DeepSeek-V4.1-Flash-1017"
    return normalized_base + "::" + model


def evaluation_git_sha():
    return os.getenv("EVAL_GIT_SHA", os.getenv("GITHUB_SHA", "local"))


def build_payload(model, system, user, max_completion_tokens=900,
                  json_mode=False, temperature=0.2, thinking=False,
                  deepseek_fields=True):
    """Build a DeepSeek-compatible Chat Completions request body."""
    if not isinstance(max_completion_tokens, int) or not (
        1 <= max_completion_tokens <= MAX_COMPLETION_TOKENS
    ):
        raise ValueError(
            f"max_completion_tokens must be between 1 and {MAX_COMPLETION_TOKENS}"
        )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_completion_tokens,
    }
    if deepseek_fields:
        payload["thinking"] = {"type": "enabled" if thinking else "disabled"}
        payload["reasoning_effort"] = "low" if thinking else "none"
    # DeepSeek ignores temperature in thinking mode. OpenAI-compatible Judge
    # providers receive standard Chat Completions fields only.
    if not thinking:
        payload["temperature"] = temperature
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    return payload


def estimate_request_tokens(system, user, max_completion_tokens):
    """Conservatively estimate total tokens for a request before sending it.

    DeepSeek exposes exact prompt/completion usage in successful responses. Before the
    call, use half the UTF-8 byte length as a conservative proxy: this intentionally
    overestimates typical English text and avoids undercounting CJK characters.
    Add the full requested completion budget.
    """
    prompt_bytes = len(system.encode("utf-8")) + len(user.encode("utf-8"))
    return math.ceil(prompt_bytes / 2) + max_completion_tokens


def throttle_model(model, estimated_tokens):
    """Apply provider context and conservative rolling-window rate limits."""
    local_limit = min(
        MAX_ESTIMATED_REQUEST_TOKENS,
        MODEL_CONTEXT_LIMITS.get(model, MAX_ESTIMATED_REQUEST_TOKENS),
    )
    if estimated_tokens > local_limit:
        raise EvaluationBudgetExceeded(
            f"Estimated request size {estimated_tokens} exceeds the local/provider "
            f"context safety limit {local_limit} for {model}."
        )
    limits = MODEL_RATE_LIMITS.get(model)
    if not limits:
        return
    if estimated_tokens > limits["tpm"]:
        raise EvaluationBudgetExceeded(
            f"One {model} request is estimated at {estimated_tokens} tokens, above "
            f"the configured per-minute token allowance {limits['tpm']}."
        )
    history = MODEL_RATE_HISTORY.setdefault(model, deque())
    while True:
        now = time.monotonic()
        while history and now - history[0][0] >= 60:
            history.popleft()
        used_tokens = sum(item[1] for item in history)
        wait_seconds = 0.0
        if len(history) >= limits["rpm"]:
            wait_seconds = max(wait_seconds, 60 - (now - history[0][0]))
        if used_tokens + estimated_tokens > limits["tpm"]:
            running = used_tokens
            for timestamp, token_count in history:
                running -= token_count
                if running + estimated_tokens <= limits["tpm"]:
                    wait_seconds = max(wait_seconds, 60 - (now - timestamp))
                    break
        if wait_seconds <= 0:
            break
        time.sleep(wait_seconds + 0.05)
    history.append((time.monotonic(), estimated_tokens))


def reserve_model_daily_tokens(model, estimated_tokens):
    """Persist conservative per-model daily token reservations before each HTTP attempt."""
    limits = MODEL_RATE_LIMITS.get(model)
    if not limits:
        return
    reservations = CHECKPOINT_STORE.setdefault("estimated_tokens_reserved_by_model", {})
    current = int(reservations.get(model, 0) or 0)
    if current + estimated_tokens > limits["tpd"]:
        raise EvaluationBudgetExceeded(
            f"Conservative {model} daily token reservation would exceed "
            f"{limits['tpd']} tokens; stopping before another provider request."
        )
    reservations[model] = current + estimated_tokens
    save_checkpoint()


def estimate_request_cost_usd(model, system, user, max_completion_tokens):
    """Estimate worst-case request cost at peak-hour cache-miss prices."""
    pricing = MODEL_PRICING_USD_PER_MILLION.get(model)
    if pricing is None:
        raise ProviderStopError(
            f"No conservative price entry is configured for provider model {model!r}; refusing an unbudgeted call."
        )
    prompt_tokens = estimate_request_tokens(system, user, 0)
    return (
        prompt_tokens * pricing["input"]
        + max_completion_tokens * pricing["output"]
    ) / 1_000_000


class ProviderStopError(RuntimeError):
    """Non-retryable provider/billing failure; stop before further paid requests."""


class EvaluationBudgetExceeded(ProviderStopError):
    """Local cost or request cap reached; stop before further paid requests."""


def configure_checkpoint(path, signature):
    """Load only a checkpoint whose inputs exactly match this evaluation."""
    global CHECKPOINT_PATH, CHECKPOINT_STORE, API_REQUEST_COUNT, ESTIMATED_COST_RESERVED_USD
    CHECKPOINT_PATH = Path(path)
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CHECKPOINT_PATH.exists():
        try:
            existing = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
            if existing.get("schema_version") == 6 and existing.get("signature") == signature and isinstance(existing.get("responses"), dict):
                CHECKPOINT_STORE = existing
                CHECKPOINT_STORE.setdefault("pending_requests", {})
                CHECKPOINT_STORE.setdefault("uncertain_requests", {})
                CHECKPOINT_STORE.setdefault("estimated_tokens_reserved_by_model", {})
                API_REQUEST_COUNT = int(existing.get("api_requests", 0) or 0)
                ESTIMATED_COST_RESERVED_USD = float(
                    existing.get("estimated_cost_reserved_usd", 0.0) or 0.0
                )
                print(
                    f"Resuming checkpoint with {len(CHECKPOINT_STORE['responses'])} cached API responses.",
                    flush=True,
                )
                return
            print("Existing checkpoint does not match this SHA/model/suite; starting a clean checkpoint.", flush=True)
        except (OSError, ValueError):
            print("Existing checkpoint is unreadable; starting a clean checkpoint.", flush=True)
    CHECKPOINT_STORE = {
        "schema_version": 6,
        "signature": signature,
        "api_requests": 0,
        "estimated_cost_reserved_usd": 0.0,
        "estimated_tokens_reserved_by_model": {},
        "pending_requests": {},
        "uncertain_requests": {},
        "responses": {},
    }
    save_checkpoint()


def save_checkpoint():
    if CHECKPOINT_PATH is None:
        return
    temporary = CHECKPOINT_PATH.with_suffix(CHECKPOINT_PATH.suffix + ".tmp")
    temporary.write_text(
        json.dumps(CHECKPOINT_STORE, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    temporary.replace(CHECKPOINT_PATH)


def checkpoint_key(payload):
    serialized = json.dumps(
        {"run_index": CURRENT_RUN_INDEX, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def api_call(api_key, model, system, user, max_completion_tokens=900,
             json_mode=False, temperature=0.2, thinking=False, api_url=API_URL):
    global API_REQUEST_COUNT, ESTIMATED_COST_RESERVED_USD
    deepseek_fields = api_url.rstrip("/").startswith(DEEPSEEK_BASE_URL)
    payload = build_payload(
        model, system, user,
        max_completion_tokens=max_completion_tokens,
        json_mode=json_mode,
        temperature=temperature,
        thinking=thinking,
        deepseek_fields=deepseek_fields,
    )
    key = checkpoint_key({"endpoint": api_url, "payload": payload})
    uncertain = CHECKPOINT_STORE.setdefault("uncertain_requests", {})
    if key in uncertain:
        raise ProviderStopError(
            "A prior generation request has an ambiguous network outcome; refusing to resend "
            "and risk duplicate billing. Inspect provider request/billing logs before manually "
            "resolving this checkpoint."
        )
    cached = CHECKPOINT_STORE.get("responses", {}).get(key)
    if cached is not None:
        CACHE_HITS_BY_MODEL[model] = CACHE_HITS_BY_MODEL.get(model, 0) + 1
        # A resumed response was billed in the earlier attempt. Count its tokens,
        # cost reservation, and original provider request toward this evaluation's cap.
        usage = cached.get("usage") or {}
        metrics = USAGE_BY_MODEL.setdefault(model, {
            "requests": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "peak_price_cost_usd_estimate": 0.0,
            "resumed_requests": 0,
        })
        metrics["requests"] += 1
        metrics["resumed_requests"] += 1
        for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
            metrics[field] += int(usage.get(field, 0) or 0)
        metrics["peak_price_cost_usd_estimate"] += float(cached.get("actual_peak_price_cost_usd", 0.0))
        return cached["content"]

    pending = CHECKPOINT_STORE.setdefault("pending_requests", {})
    if key in pending:
        raise ProviderStopError(
            "A prior generation request was interrupted while in flight; its billing outcome "
            "is unknown. Refusing to resend. Inspect provider request/billing logs before "
            "manually resolving this checkpoint."
        )

    estimated_tokens = estimate_request_tokens(system, user, max_completion_tokens)
    estimated_cost = estimate_request_cost_usd(model, system, user, max_completion_tokens)
    def make_request(request_payload):
        return urllib.request.Request(
            api_url,
            data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
                "User-Agent": DEFAULT_USER_AGENT,
            },
            method="POST",
        )

    request = make_request(payload)
    for attempt in range(3):
        # Reserve every physical HTTP attempt (including retries) before sending it.
        if API_REQUEST_COUNT >= MAX_API_REQUESTS:
            raise EvaluationBudgetExceeded(
                f"API request cap reached ({MAX_API_REQUESTS}); stopping before another paid request."
            )
        if ESTIMATED_COST_RESERVED_USD + estimated_cost > MAX_ESTIMATED_COST_USD:
            raise EvaluationBudgetExceeded(
                f"Estimated peak-price spend would exceed the configured USD {MAX_ESTIMATED_COST_USD:.2f} run cap; "
                "stopping before another paid request."
            )
        throttle_model(model, estimated_tokens)
        reserve_model_daily_tokens(model, estimated_tokens)
        API_REQUEST_COUNT += 1
        ESTIMATED_COST_RESERVED_USD += estimated_cost
        CHECKPOINT_STORE["api_requests"] = API_REQUEST_COUNT
        CHECKPOINT_STORE["estimated_cost_reserved_usd"] = ESTIMATED_COST_RESERVED_USD
        pending[key] = {
            "model": model,
            "endpoint": api_url,
            "attempt": attempt + 1,
            "status": "in_flight",
        }
        save_checkpoint()
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                data = json.loads(response.read())
                response_headers = response.headers
            choices = data.get("choices") or []
            if not choices:
                pending.pop(key, None)
                uncertain[key] = {
                    "model": model, "endpoint": api_url, "attempt": attempt + 1,
                    "reason": "provider response contained no choices",
                    "status": "completed_without_usable_content",
                }
                save_checkpoint()
                raise ProviderStopError("Provider response contained no choices; stopping to protect the paid budget.")
            finish_reason = choices[0].get("finish_reason")
            if finish_reason == "length":
                usage = data.get("usage") or {}
                prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
                completion_tokens = int(usage.get("completion_tokens", 0) or 0)
                pricing = MODEL_PRICING_USD_PER_MILLION[model]
                truncated_cost = (
                    prompt_tokens * pricing["input"]
                    + completion_tokens * pricing["output"]
                ) / 1_000_000
                metrics = USAGE_BY_MODEL.setdefault(model, {
                    "requests": 0, "prompt_tokens": 0, "completion_tokens": 0,
                    "total_tokens": 0, "peak_price_cost_usd_estimate": 0.0,
                    "resumed_requests": 0,
                })
                metrics["requests"] += 1
                metrics["prompt_tokens"] += prompt_tokens
                metrics["completion_tokens"] += completion_tokens
                metrics["total_tokens"] += int(usage.get("total_tokens", 0) or 0)
                metrics["peak_price_cost_usd_estimate"] += truncated_cost
                pending.pop(key, None)
                uncertain[key] = {
                    "model": model, "endpoint": api_url, "attempt": attempt + 1,
                    "reason": "provider response reached max_tokens limit",
                    "status": "completed_but_truncated",
                    "usage": usage,
                }
                save_checkpoint()
                raise ProviderStopError(
                    f"Provider response reached its max_tokens limit for model {model}; "
                    f"provider usage: {prompt_tokens} input and {completion_tokens} output tokens. "
                    "Increase the per-call output cap or shorten the request before retrying."
                )
            message = choices[0].get("message") or {}
            result = message.get("content")
            if isinstance(result, list):
                result = "".join(
                    part.get("text", "") for part in result
                    if isinstance(part, dict) and part.get("type") == "text"
                )
            if not isinstance(result, str) or not result.strip():
                pending.pop(key, None)
                uncertain[key] = {
                    "model": model, "endpoint": api_url, "attempt": attempt + 1,
                    "reason": "provider returned empty message content",
                    "status": "completed_without_usable_content",
                }
                save_checkpoint()
                raise ProviderStopError(
                    "Provider returned empty message content; finish_reason="
                    + str(choices[0].get("finish_reason"))
                    + "; stopping before further paid requests."
                )
            usage = data.get("usage") or {}
            metrics = USAGE_BY_MODEL.setdefault(model, {
                "requests": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "peak_price_cost_usd_estimate": 0.0,
                "resumed_requests": 0,
            })
            prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens = int(usage.get("completion_tokens", 0) or 0)
            pricing = MODEL_PRICING_USD_PER_MILLION[model]
            actual_cost = (
                prompt_tokens * pricing["input"]
                + completion_tokens * pricing["output"]
            ) / 1_000_000
            metrics["requests"] += 1
            metrics["prompt_tokens"] += prompt_tokens
            metrics["completion_tokens"] += completion_tokens
            metrics["total_tokens"] += int(usage.get("total_tokens", 0) or 0)
            metrics["peak_price_cost_usd_estimate"] += actual_cost
            remaining = response_headers.get("x-ratelimit-remaining-requests")
            if remaining is not None:
                metrics["last_reported_remaining_requests"] = remaining
            pending.pop(key, None)
            CHECKPOINT_STORE.setdefault("responses", {})[key] = {
                "content": result,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": int(usage.get("total_tokens", 0) or 0),
                },
                "reserved_cost_usd": estimated_cost,
                "actual_peak_price_cost_usd": actual_cost,
                "request_count": attempt + 1,
            }
            save_checkpoint()
            return result
        except urllib.error.HTTPError as exc:
            pending.pop(key, None)
            save_checkpoint()
            body = exc.read().decode("utf-8", errors="replace")
            message = body[:1200]
            lowered = message.lower()
            if exc.code == 400 and json_mode and "json_validate_failed" in lowered:
                # Retry JSON mode once without provider response_format. Local JSON validation remains mandatory.
                json_mode = False
                payload = build_payload(
                    model, system, user,
                    max_completion_tokens=max_completion_tokens,
                    json_mode=False,
                    temperature=temperature,
                    thinking=thinking,
                    deepseek_fields=deepseek_fields,
                )
                request = make_request(payload)
                continue
            if exc.code in (401, 403):
                raise ProviderStopError(
                    f"Provider authentication/model-permission error HTTP {exc.code}: {message}"
                ) from exc
            if exc.code == 402 or any(term in lowered for term in (
                "insufficient balance", "insufficient quota", "account balance",
            )):
                raise ProviderStopError(
                    "Provider paid API balance/quota is unavailable: " + message
                ) from exc
            if exc.code == 429:
                if any(term in lowered for term in (
                    "per day", "daily limit", "tokens per day", "requests per day",
                    "quota exceeded", "insufficient quota", "insufficient balance",
                )):
                    raise ProviderStopError("Provider paid API quota is exhausted: " + message) from exc
                if attempt < 2:
                    retry_after = exc.headers.get("retry-after")
                    try:
                        wait = float(retry_after) if retry_after else None
                    except (TypeError, ValueError):
                        wait = None
                    if wait is None:
                        reset_match = re.search(
                            r"try again in\s+([0-9]+(?:\.[0-9]+)?)\s*s",
                            message,
                            flags=re.IGNORECASE,
                        )
                        wait = float(reset_match.group(1)) + 0.5 if reset_match else (attempt + 1) * 2
                    time.sleep(min(max(wait, 1.0), 15.0))
                    continue
            if exc.code in (500, 502, 503, 504) and attempt < 2:
                time.sleep((attempt + 1) * 2)
                continue
            raise ProviderStopError(
                f"Provider API HTTP {exc.code}; stopping paid evaluation: {message}"
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            # A POST timeout/network disconnect may occur after the provider accepted
            # and billed the request. Without a provider idempotency key, blind retry
            # can duplicate a paid generation. Persist an uncertainty marker and stop.
            pending.pop(key, None)
            uncertain[key] = {
                "model": model,
                "endpoint": api_url,
                "attempt": attempt + 1,
                "reason": str(exc)[:500],
                "status": "outcome_unknown",
            }
            save_checkpoint()
            raise ProviderStopError(
                "Provider generation request ended with an ambiguous network outcome; "
                "it was not retried to avoid duplicate billing. Inspect provider request/"
                "billing logs before manually resolving the checkpoint."
            ) from exc
    raise ProviderStopError("Provider API request failed after bounded retries.")


def extract_json(raw):
    text = raw.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("No JSON object found")
    return json.loads(text[start:end + 1])


def judge_case(api_key, model, criteria, candidate, api_url=JUDGE_API_URL):
    """Judge each property and require verifiable evidence from the candidate."""
    criterion_lines = "\n".join(
        f"{index}. {criterion}" for index, criterion in enumerate(criteria)
    )
    system = (
        "You are an independent, strict evaluation judge. Evaluate only the "
        "observable content of the candidate output. Do not infer that omitted "
        "steps were completed and do not reward stated intent. A criterion passes "
        "only when the output itself clearly demonstrates it. For every criterion, "
        "cite 1-3 short VERBATIM substrings (each 6-120 characters) copied "
        "exactly from the candidate output; never invent or paraphrase evidence. "
        "Use the minimum number of quotes needed, and ensure the quotes collectively "
        "support every material part of the criterion. For a failure, quote the "
        "closest relevant passage(s) if they exist and explain the missing part in "
        "a rationale of at most 80 characters. Keep the JSON concise. Return only: "
        '{"checks":[{"index":0,"score":0,"rationale":"brief reason",'
        '"evidence":["exact quote 1","exact quote 2"]}]}. Include every index exactly once.'
    )
    user = (
        "Evaluate the following criteria independently.\n\n"
        "CRITERIA:\n" + criterion_lines
        + "\n\nCANDIDATE OUTPUT (quote evidence verbatim from here):\n" + candidate
    )
    try:
        raw = api_call(
            api_key, model, system, user,
            max_completion_tokens=1200, json_mode=True, temperature=0.0,
            thinking=False, api_url=api_url,
        )
    except ProviderStopError:
        raise
    except Exception as exc:
        return [{
            "criterion": criterion,
            "score": 0,
            "rationale": "Judge API call failed closed: " + str(exc)[:400],
            "evidence": [],
            "evidence_validated": False,
            "judge_api_error": True,
        } for criterion in criteria]
    try:
        obj = extract_json(raw)
        items = obj.get("checks", [])
        if not isinstance(items, list):
            raise ValueError("checks must be a JSON array")
        by_index = {}
        duplicates = set()
        for item in items:
            if not isinstance(item, dict) or type(item.get("index")) is not int:
                continue
            index = item["index"]
            if index in by_index:
                duplicates.add(index)
            else:
                by_index[index] = item
    except Exception as exc:
        return [{
            "criterion": criterion,
            "score": 0,
            "rationale": "Judge response was invalid JSON: " + str(exc),
            "evidence": [],
            "evidence_validated": False,
            "judge_parse_error": raw[:500],
        } for criterion in criteria]

    def compact(text):
        return " ".join(str(text).split())

    candidate_compact = compact(candidate)
    results = []
    for index, criterion in enumerate(criteria):
        item = by_index.get(index)
        if not item:
            results.append({
                "criterion": criterion, "score": 0,
                "rationale": "Judge omitted this criterion.",
                "evidence": [], "evidence_validated": False,
                "judge_parse_error": raw[:500],
            })
            continue
        score = item.get("score")
        score_valid = (type(score) is bool) or (type(score) is int and score in (0, 1))
        rationale = str(item.get("rationale", "")).strip()[:500]
        evidence = item.get("evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        evidence = [str(value).strip() for value in evidence if str(value).strip()]
        valid_evidence = [
            quote for quote in evidence[:3]
            if 6 <= len(compact(quote)) <= 120
            and compact(quote) in candidate_compact
        ]
        # Every supplied quotation must be short and locally verifiable. A
        # passing property may need multiple snippets when it has several
        # independent sub-requirements (e.g. two source versions and clauses).
        evidence_validated = (
            1 <= len(evidence) <= 3
            and len(valid_evidence) == len(evidence)
        )
        reasons = []
        if index in duplicates:
            reasons.append("Judge returned a duplicate result for this criterion.")
        if not score_valid:
            reasons.append("Judge returned a non-binary score.")
        if not rationale:
            reasons.append("Judge omitted its rationale.")
        if not evidence_validated:
            reasons.append("No verbatim evidence could be verified in the candidate output.")
        if reasons:
            score_value = 0
            rationale = (rationale + " " if rationale else "") + " ".join(reasons)
        else:
            score_value = 1 if score is True or score == 1 else 0
        results.append({
            "criterion": criterion,
            "score": score_value,
            "rationale": rationale[:500],
            "evidence": valid_evidence if evidence_validated else [],
            "evidence_validated": evidence_validated,
        })
    return results

def classify_trigger(api_key, model, query, api_url=JUDGE_API_URL):
    system = (
        "Classify whether a user request should invoke the Evaluation Dataset "
        "Builder Skill. Trigger only when the user asks to create, plan, evaluate, "
        "audit, repair, or update evaluation datasets, benchmarks, or graders. "
        "Do not trigger for general explanations, ordinary software tests, "
        "summaries, translation, or unrelated work. Return JSON only: "
        '{"should_trigger":true} or {"should_trigger":false}.'
    )
    try:
        raw = api_call(
            api_key, model, system, query,
            max_completion_tokens=180, json_mode=True, temperature=0.0,
            api_url=api_url,
        )
        value = extract_json(raw).get("should_trigger")
        if not isinstance(value, bool):
            raise ValueError("should_trigger must be a JSON boolean")
        return value, None
    except ProviderStopError:
        raise
    except Exception as exc:
        return False, str(exc)


def load_skill():
    """Load the concise Skill entrypoint; references remain packaged for runtime use.

    The entrypoint now contains the operational requirements needed for this
    portable proxy. Appending every reference verbatim duplicated those rules
    and exceeded the configured local request pacing budget.
    """
    return (ROOT / "SKILL.md").read_text(encoding="utf-8").strip()

def binary_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return precision, recall


def gate_metrics(behavior_rate, precision, recall):
    return {
        "behavior_pass_rate": {
            "value": behavior_rate,
            "threshold": POLICY["behavior_pass_rate"],
            "pass": behavior_rate >= POLICY["behavior_pass_rate"],
        },
        "trigger_precision": {
            "value": precision,
            "threshold": POLICY["trigger_precision"],
            "pass": precision >= POLICY["trigger_precision"],
        },
        "trigger_recall": {
            "value": recall,
            "threshold": POLICY["trigger_recall"],
            "pass": recall >= POLICY["trigger_recall"],
        },
    }


def summarize(values):
    return {
        "min": min(values), "max": max(values),
        "spread": max(values) - min(values),
        "mean": sum(values) / len(values),
    }


def evaluate_once(index, generator_api_key, judge_api_key, generator_model, judge_model,
                  skill, baseline, suite, trigger_suite, judge_api_url=JUDGE_API_URL):
    run = {
        "run_index": index,
        "skill_cases": [],
        "baseline_cases": [],
        "trigger_cases": [],
    }
    skill_passed = skill_total = baseline_passed = baseline_total = 0

    for case in suite["cases"]:
        prompt = case["prompt"] + (
            "\n\nRespond as if fulfilling the request. Provide a complete but "
            "appropriately scoped output."
        )
        skill_generation_error = None
        try:
            skill_output = api_call(
                generator_api_key, generator_model, skill, prompt,
                max_completion_tokens=16384, temperature=0.3,
            )
            skill_checks = judge_case(judge_api_key, judge_model, case["expected"], skill_output, api_url=judge_api_url)
        except ProviderStopError:
            raise
        except Exception as exc:
            skill_output = ""
            skill_generation_error = str(exc)[:500]
            skill_checks = [{
                "criterion": criterion, "score": 0,
                "rationale": "Generator API call failed closed: " + skill_generation_error,
                "evidence": [], "evidence_validated": False,
                "generator_api_error": True,
            } for criterion in case["expected"]]
        skill_passed += sum(item["score"] for item in skill_checks)
        skill_total += len(skill_checks)
        run["skill_cases"].append({
            "id": case["id"],
            "category": case["category"],
            "pass": all(item["score"] == 1 for item in skill_checks),
            "checks": skill_checks,
            "output": skill_output,
            "generation_error": skill_generation_error,
        })

        baseline_generation_error = None
        try:
            baseline_output = api_call(
                generator_api_key, generator_model, baseline, prompt,
                max_completion_tokens=16384, temperature=0.3,
            )
            baseline_checks = judge_case(
                judge_api_key, judge_model, case["expected"], baseline_output, api_url=judge_api_url
            )
        except ProviderStopError:
            raise
        except Exception as exc:
            baseline_output = ""
            baseline_generation_error = str(exc)[:500]
            baseline_checks = [{
                "criterion": criterion, "score": 0,
                "rationale": "Baseline Generator API call failed closed: " + baseline_generation_error,
                "evidence": [], "evidence_validated": False,
                "generator_api_error": True,
            } for criterion in case["expected"]]
        baseline_passed += sum(item["score"] for item in baseline_checks)
        baseline_total += len(baseline_checks)
        run["baseline_cases"].append({
            "id": case["id"],
            "pass": all(item["score"] == 1 for item in baseline_checks),
            "checks": baseline_checks,
            "output": baseline_output,
            "generation_error": baseline_generation_error,
        })
        print(
            f"run {index} behavior {case['id']}: "
            f"{'PASS' if all(x['score'] == 1 for x in skill_checks) else 'FAIL'} "
            f"({sum(x['score'] for x in skill_checks)}/{len(skill_checks)})",
            flush=True,
        )

    tp = fp = fn = tn = 0
    trigger_parse_errors = 0
    for item in trigger_suite["evals"]:
        predicted, parse_error = classify_trigger(
            judge_api_key, judge_model, item["query"], api_url=judge_api_url
        )
        expected = item["should_trigger"]
        if parse_error:
            trigger_parse_errors += 1
        if predicted and expected:
            tp += 1
        elif predicted and not expected:
            fp += 1
        elif not predicted and expected:
            fn += 1
        else:
            tn += 1
        run["trigger_cases"].append({
            "query": item["query"],
            "expected": expected,
            "predicted": predicted,
            "pass": predicted == expected,
            "parse_error": parse_error,
        })

    behavior_rate = skill_passed / skill_total if skill_total else 0.0
    baseline_rate = baseline_passed / baseline_total if baseline_total else 0.0
    precision, recall = binary_metrics(tp, fp, fn)
    run["trigger_confusion"] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn}
    run["trigger_parse_errors"] = trigger_parse_errors
    run["metrics"] = {
        "behavior_pass_rate": behavior_rate,
        "behavior_checks_passed": skill_passed,
        "behavior_checks_total": skill_total,
        "baseline_behavior_pass_rate": baseline_rate,
        "baseline_checks_passed": baseline_passed,
        "baseline_checks_total": baseline_total,
        "behavior_uplift_vs_baseline": behavior_rate - baseline_rate,
        "trigger_precision": precision,
        "trigger_recall": recall,
    }
    run["gates"] = gate_metrics(behavior_rate, precision, recall)
    run["gates"]["trigger_classifier_valid"] = {
        "value": trigger_parse_errors, "threshold": 0,
        "pass": trigger_parse_errors == 0,
    }
    run["automated_run_pass"] = all(
        gate["pass"] for gate in run["gates"].values()
    )
    return run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator-model",
        default=os.getenv("DEEPSEEK_GENERATOR_MODEL", DEFAULT_GENERATOR_MODEL),
    )
    parser.add_argument(
        "--judge-model",
        default=(os.getenv("EVAL_JUDGE_MODEL") or os.getenv("DEEPSEEK_JUDGE_MODEL") or DEFAULT_JUDGE_MODEL),
    )
    parser.add_argument("--output", default="artifacts/eval-report.json")
    parser.add_argument("--checkpoint", default="artifacts/eval-checkpoint.json")
    parser.add_argument("--runs", type=int, default=POLICY["minimum_runs"])
    args = parser.parse_args()

    shared_api_key = os.getenv("DEEPSEEK_API_KEY", "")
    generator_api_key = os.getenv("DEEPSEEK_GENERATOR_API_KEY", shared_api_key)
    judge_api_base_url = JUDGE_BASE_URL
    judge_api_url = JUDGE_API_URL
    external_judge = judge_api_base_url != DEEPSEEK_BASE_URL
    if external_judge:
        judge_api_key = os.getenv("EVAL_JUDGE_API_KEY", "")
        input_price = os.getenv("EVAL_JUDGE_INPUT_PRICE_USD_PER_MILLION", "")
        output_price = os.getenv("EVAL_JUDGE_OUTPUT_PRICE_USD_PER_MILLION", "")
        if not judge_api_key or not input_price or not output_price:
            print(
                "ERROR: external Judge requires EVAL_JUDGE_API_KEY, EVAL_JUDGE_BASE_URL, "
                "EVAL_JUDGE_MODEL, and explicit input/output USD-per-million-token prices.",
                file=sys.stderr,
            )
            return 2
        if not os.getenv("EVAL_JUDGE_MODEL") and args.judge_model == DEFAULT_JUDGE_MODEL:
            print("ERROR: set EVAL_JUDGE_MODEL for the external Judge provider.", file=sys.stderr)
            return 2
        try:
            MODEL_PRICING_USD_PER_MILLION[args.judge_model] = {
                "input": float(input_price),
                "output": float(output_price),
            }
        except ValueError:
            print("ERROR: external Judge token prices must be numeric.", file=sys.stderr)
            return 2
    else:
        judge_api_key = os.getenv("DEEPSEEK_JUDGE_API_KEY", shared_api_key)
    if not generator_api_key or not judge_api_key:
        print(
            "ERROR: set DEEPSEEK_GENERATOR_API_KEY and DEEPSEEK_JUDGE_API_KEY, "
            "or set shared DEEPSEEK_API_KEY",
            file=sys.stderr,
        )
        return 2
    if args.runs < POLICY["minimum_runs"]:
        parser.error("at least two complete runs are required")
    if effective_model_identity(DEEPSEEK_BASE_URL, args.generator_model) == effective_model_identity(
        judge_api_base_url, args.judge_model
    ):
        print(
            "ERROR: Generator and Judge resolve to the same deployed model. "
            "DeepSeek routes deepseek-v4-pro to V4.1 Flash, so configure a genuinely "
            "independent Judge provider/model before spending evaluation quota.",
            file=sys.stderr,
        )
        return 2

    suite = json.loads(
        (ROOT / "tests/self-eval-cases.json").read_text(encoding="utf-8")
    )
    trigger_suite = json.loads(
        (ROOT / "tests/trigger-evals.json").read_text(encoding="utf-8")
    )
    skill = load_skill()
    baseline = (
        "You are a helpful assistant. Follow the user's request directly. "
        "Do not assume access to an evaluation-dataset-builder skill."
    )
    global CURRENT_RUN_INDEX, API_REQUEST_COUNT, ESTIMATED_COST_RESERVED_USD
    USAGE_BY_MODEL.clear()
    CACHE_HITS_BY_MODEL.clear()
    MODEL_RATE_HISTORY.clear()
    API_REQUEST_COUNT = 0
    ESTIMATED_COST_RESERVED_USD = 0.0
    signature_payload = {
        "suite": suite,
        "trigger_suite": trigger_suite,
        "skill_sha256": hashlib.sha256(skill.encode("utf-8")).hexdigest(),
        "generator_model": args.generator_model,
        "judge_model": args.judge_model,
        "judge_api_url": judge_api_url,
        "judge_pricing": MODEL_PRICING_USD_PER_MILLION.get(args.judge_model),
        "model_context_limits": MODEL_CONTEXT_LIMITS,
        "model_rate_limits": MODEL_RATE_LIMITS,
        "runs": args.runs,
    }
    signature = hashlib.sha256(json.dumps(
        signature_payload, ensure_ascii=False, sort_keys=True
    ).encode("utf-8")).hexdigest()
    configure_checkpoint(args.checkpoint, signature)
    runs = []
    for index in range(1, args.runs + 1):
        CURRENT_RUN_INDEX = index
        print(f"Starting repeated evaluation {index}/{args.runs}", flush=True)
        try:
            runs.append(evaluate_once(
                index, generator_api_key, judge_api_key, args.generator_model, args.judge_model,
                skill, baseline, suite, trigger_suite, judge_api_url=judge_api_url,
            ))
        except ProviderStopError as exc:
            partial_report = {
                "schema_version": "1.2",
                "status": "INCOMPLETE",
                "provider": "multi-provider",
                "api_base_url": DEEPSEEK_BASE_URL,
                "judge_api_base_url": judge_api_base_url,
                "git_sha": evaluation_git_sha(),
                "models": {"generator": args.generator_model, "judge_and_trigger": args.judge_model},
                "completed_runs": len(runs),
                "required_runs": args.runs,
                "interrupted_run_index": index,
                "execution_error": str(exc),
                "runs": runs,
                "api_usage_by_model": USAGE_BY_MODEL,
                "cost_control": {
                    "max_estimated_cost_usd": MAX_ESTIMATED_COST_USD,
                    "estimated_cost_reserved_usd": round(ESTIMATED_COST_RESERVED_USD, 6),
                    "max_api_requests": MAX_API_REQUESTS,
                    "api_requests": API_REQUEST_COUNT,
                    "checkpoint_cache_hits": CACHE_HITS_BY_MODEL,
                    "checkpoint_path": args.checkpoint,
                    "estimated_tokens_reserved_by_model": CHECKPOINT_STORE.get("estimated_tokens_reserved_by_model", {}),
                    "model_context_limits": MODEL_CONTEXT_LIMITS,
                    "model_rate_limits": MODEL_RATE_LIMITS,
                    "pricing_usd_per_million_tokens": MODEL_PRICING_USD_PER_MILLION,
                },
                "automated_gate_pass": False,
                "release_approved": False,
            }
            output = ROOT / args.output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(partial_report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(partial_report, ensure_ascii=False, indent=2))
            return 2

    metric_names = [
        "behavior_pass_rate", "trigger_precision", "trigger_recall",
    ]
    stability = {
        name: summarize([run["metrics"][name] for run in runs])
        for name in metric_names
    }
    stability_gates = {
        name: {
            "spread": value["spread"],
            "max_allowed": POLICY["max_stability_spread"],
            "pass": value["spread"] <= POLICY["max_stability_spread"],
        }
        for name, value in stability.items()
    }
    baseline_complete = all(
        len(run["baseline_cases"]) == len(suite["cases"])
        and run["metrics"]["baseline_checks_total"]
            == run["metrics"]["behavior_checks_total"]
        and all(case.get("generation_error") is None for case in run["baseline_cases"])
        and all(
            not check.get("judge_api_error") and not check.get("judge_parse_error")
            for case in run["baseline_cases"] for check in case["checks"]
        )
        for run in runs
    )
    generation_calls_complete = all(
        all(case.get("generation_error") is None for case in run["skill_cases"])
        and all(case.get("generation_error") is None for case in run["baseline_cases"])
        for run in runs
    )
    judge_responses_complete = all(
        not check.get("judge_api_error") and not check.get("judge_parse_error")
        for run in runs
        for case_type in ("skill_cases", "baseline_cases")
        for case in run[case_type]
        for check in case["checks"]
    )
    report = {
        "schema_version": "1.2",
        "status": "COMPLETE",
        "provider": "DeepSeek",
        "api_base_url": DEEPSEEK_BASE_URL,
        "judge_api_base_url": judge_api_base_url,
        "suite_id": suite["suite_id"],
        "models": {
            "generator": args.generator_model,
            "judge_and_trigger": args.judge_model,
        },
        "timestamp_utc": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        ),
        "git_sha": evaluation_git_sha(),
        "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
        "runner": "tests/run_eval.py",
        "policy": {
            **POLICY,
            "actual_runs": args.runs,
            "critical_case_ids_for_human_review": CRITICAL_CASE_IDS,
            "trigger_eval_count": len(trigger_suite["evals"]),
        },
        "runs": runs,
        "stability": stability,
        "stability_gates": stability_gates,
        "baseline_comparison": {
            "required": True,
            "complete": baseline_complete,
            "mean_skill_behavior_pass_rate": sum(
                run["metrics"]["behavior_pass_rate"] for run in runs
            ) / len(runs),
            "mean_baseline_behavior_pass_rate": sum(
                run["metrics"]["baseline_behavior_pass_rate"] for run in runs
            ) / len(runs),
            "mean_uplift": sum(
                run["metrics"]["behavior_uplift_vs_baseline"] for run in runs
            ) / len(runs),
            "per_run_uplift": [
                run["metrics"]["behavior_uplift_vs_baseline"] for run in runs
            ],
            "human_interpretation_required": True,
        },
        "api_usage_by_model": USAGE_BY_MODEL,
        "cost_control": {
            "pricing_basis": "conservative peak-hour cache-miss prices",
            "pricing_usd_per_million_tokens": MODEL_PRICING_USD_PER_MILLION,
            "max_estimated_cost_usd": MAX_ESTIMATED_COST_USD,
            "estimated_cost_reserved_usd": round(ESTIMATED_COST_RESERVED_USD, 6),
            "actual_peak_price_cost_usd_estimate": round(sum(
                item.get("peak_price_cost_usd_estimate", 0.0)
                for item in USAGE_BY_MODEL.values()
            ), 6),
            "max_api_requests": MAX_API_REQUESTS,
            "api_requests": API_REQUEST_COUNT,
            "checkpoint_cache_hits": CACHE_HITS_BY_MODEL,
            "checkpoint_path": args.checkpoint,
            "estimated_tokens_reserved_by_model": CHECKPOINT_STORE.get("estimated_tokens_reserved_by_model", {}),
            "model_context_limits": MODEL_CONTEXT_LIMITS,
            "model_rate_limits": MODEL_RATE_LIMITS,
        },
    }
    all_runs_pass = all(run["automated_run_pass"] for run in runs)
    stability_pass = all(
        gate["pass"] for gate in stability_gates.values()
    )
    report["automated_gates"] = {
        "all_repeated_runs_pass": {
            "pass": all_runs_pass, "runs": len(runs),
        },
        "generation_calls_complete": {"pass": generation_calls_complete},
        "judge_responses_complete": {"pass": judge_responses_complete},
        "trigger_classifier_valid": {
            "pass": all(run["trigger_parse_errors"] == 0 for run in runs),
            "parse_errors": sum(run["trigger_parse_errors"] for run in runs),
        },
        "baseline_comparison_complete": {"pass": baseline_complete},
        "stochastic_stability": {"pass": stability_pass},
    }
    report["automated_gate_pass"] = all(
        gate["pass"] for gate in report["automated_gates"].values()
    )
    report["human_review"] = {
        "required": True,
        "status": "PENDING",
        "critical_case_ids": CRITICAL_CASE_IDS,
        "note": (
            "Independent reviewer must inspect critical cases, failures, judge "
            "evidence, generated samples, and baseline uplift, then approve the PR."
        ),
    }
    report["release_approved"] = False

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({
        "report": str(output),
        "automated_gate_pass": report["automated_gate_pass"],
        "automated_gates": report["automated_gates"],
        "stability": report["stability"],
        "baseline_comparison": report["baseline_comparison"],
        "api_usage_by_model": report["api_usage_by_model"],
        "release_approved": False,
        "reason": (
            "Independent human critical-case review and PR approval remain mandatory."
        ),
    }, ensure_ascii=False, indent=2))
    return 0 if report["automated_gate_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
