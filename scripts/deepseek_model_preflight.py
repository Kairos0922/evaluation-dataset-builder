#!/usr/bin/env python3
"""Read DeepSeek model metadata and preflight a token budget without generation."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL_ID = "deepseek-flash"


def parse_model_metadata(payload: dict[str, Any], model_id: str = DEFAULT_MODEL_ID) -> dict[str, Any]:
    """Select one model and require live, numeric capacity metadata."""
    models = payload.get("data")
    if not isinstance(models, list):
        raise ValueError("Model catalog response has no data array")

    model = next(
        (item for item in models if isinstance(item, dict) and item.get("id") == model_id),
        None,
    )
    if model is None:
        available = [item.get("id") for item in models if isinstance(item, dict) and item.get("id")]
        raise ValueError(f"Model {model_id!r} is not listed; available IDs: {', '.join(available) or 'unknown'}")

    context_window = model.get("context_window")
    max_output_tokens = model.get("max_output_tokens")
    if not isinstance(context_window, int) or context_window <= 0:
        raise ValueError(f"Model {model_id!r} has no valid context_window metadata")
    if not isinstance(max_output_tokens, int) or max_output_tokens <= 0:
        raise ValueError(f"Model {model_id!r} has no valid max_output_tokens metadata")

    return {
        "id": model_id,
        "name": model.get("name"),
        "context_window": context_window,
        "max_output_tokens": max_output_tokens,
        "input_modalities": model.get("input_modalities", []),
        "output_modalities": model.get("output_modalities", []),
        "effort": model.get("effort"),
    }


def fetch_model_metadata(
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 15.0,
    model_id: str = DEFAULT_MODEL_ID,
) -> dict[str, Any]:
    """Fetch GET /models. This function never makes a model generation request."""
    if not api_key.strip():
        raise ValueError("DEEPSEEK_API_KEY is empty")
    url = base_url.rstrip("/") + "/models"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "evaluation-dataset-builder-preflight/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"DeepSeek model metadata request failed with HTTP {exc.code}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"DeepSeek model metadata request failed: {exc.reason}") from None
    except (TimeoutError, OSError) as exc:
        raise RuntimeError(f"DeepSeek model metadata request failed: {exc}") from None
    except json.JSONDecodeError:
        raise RuntimeError("DeepSeek model metadata endpoint returned invalid JSON") from None

    if not isinstance(payload, dict):
        raise RuntimeError("DeepSeek model metadata endpoint returned an unexpected payload")
    return parse_model_metadata(payload, model_id=model_id)


def calculate_budget(
    model: dict[str, Any],
    estimated_input_tokens: int,
    estimated_output_tokens: int | None = None,
    headroom: float = 1.15,
    safety_margin_ratio: float = 0.01,
) -> dict[str, Any]:
    """Calculate a non-truncating output ceiling; reject estimates that do not fit."""
    if estimated_input_tokens < 0:
        raise ValueError("estimated_input_tokens must be >= 0")
    if estimated_output_tokens is not None and estimated_output_tokens < 1:
        raise ValueError("estimated_output_tokens must be >= 1")
    if headroom < 1.0:
        raise ValueError("headroom must be >= 1.0")
    if not 0 <= safety_margin_ratio <= 0.10:
        raise ValueError("safety_margin_ratio must be between 0 and 0.10")

    context_window = int(model["context_window"])
    max_output_tokens = int(model["max_output_tokens"])
    margin = max(4096, math.ceil(context_window * safety_margin_ratio))
    context_remaining = context_window - estimated_input_tokens - margin
    if context_remaining < 1:
        raise ValueError(
            f"Input estimate ({estimated_input_tokens:,}) leaves no usable output capacity "
            f"inside the {context_window:,}-token context after a {margin:,}-token margin"
        )

    available_output = min(max_output_tokens, context_remaining)
    result: dict[str, Any] = {
        "model": model["id"],
        "context_window": context_window,
        "max_output_tokens": max_output_tokens,
        "estimated_input_tokens": estimated_input_tokens,
        "safety_margin_tokens": margin,
        "available_output_tokens": available_output,
        "generation_call_made": False,
    }

    if estimated_output_tokens is not None:
        requested_budget = math.ceil(estimated_output_tokens * headroom)
        if requested_budget > available_output:
            raise ValueError(
                f"Estimated complete output with headroom needs {requested_budget:,} tokens, "
                f"but only {available_output:,} are available. Do not silently truncate; "
                "revise the estimate or split at a meaningful case/dataset boundary."
            )
        result.update(
            {
                "estimated_complete_output_tokens": estimated_output_tokens,
                "headroom_factor": headroom,
                "suggested_max_output_tokens": requested_budget,
            }
        )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read DeepSeek model metadata and check a planned request budget; no generation call is made."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL_ID, help="API model ID (default: deepseek-flash)")
    parser.add_argument("--base-url", default=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--input-tokens", type=int, help="Estimated full request input tokens")
    parser.add_argument("--estimated-output-tokens", type=int, help="Estimated complete output, including reasoning if applicable")
    parser.add_argument("--headroom", type=float, default=1.15, help="Output-estimate multiplier; default: 1.15")
    parser.add_argument("--safety-margin-ratio", type=float, default=0.01, help="Context margin ratio; default: 0.01")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if (args.input_tokens is None) != (args.estimated_output_tokens is None):
        parser.error("--input-tokens and --estimated-output-tokens must be supplied together")
    if args.timeout <= 0:
        parser.error("--timeout must be > 0")

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    try:
        model = fetch_model_metadata(
            api_key=api_key,
            base_url=args.base_url,
            timeout=args.timeout,
            model_id=args.model,
        )
        if args.input_tokens is None:
            budget = calculate_budget(model, estimated_input_tokens=0)
        else:
            budget = calculate_budget(
                model,
                estimated_input_tokens=args.input_tokens,
                estimated_output_tokens=args.estimated_output_tokens,
                headroom=args.headroom,
                safety_margin_ratio=args.safety_margin_ratio,
            )
    except (ValueError, RuntimeError) as exc:
        print(f"PRECHECK FAILED: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({"model_metadata": model, "budget": budget}, ensure_ascii=False, indent=2))
    print("PASS: metadata/budget preflight only; no generation request was sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
