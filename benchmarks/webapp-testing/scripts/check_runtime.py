#!/usr/bin/env python3
"""Smoke-check a pinned Playwright runtime against the local preflight fixture.

This is an environment test only. It does not invoke DSH or either Skill.
"""
from __future__ import annotations

import json
import os
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_PLAYWRIGHT = "1.64.1"
BASE_URL = os.environ.get("PREFLIGHT_BASE_URL", "http://127.0.0.1:4173")
ARTIFACT_DIR = Path(os.environ.get("PREFLIGHT_ARTIFACT_DIR", "artifacts/runtime-preflight"))
RESULT_PATH = ARTIFACT_DIR / "result.json"
SCREENSHOT_PATH = ARTIFACT_DIR / "browser.png"


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "FAIL",
        "scope": "runtime_preflight_only",
        "skill_invoked": False,
        "builder_invoked": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "base_url": BASE_URL,
        "expected_playwright_version": EXPECTED_PLAYWRIGHT,
        "browser": "chromium",
        "browser_version": None,
        "http_status": None,
        "page_title": None,
        "initial_value": None,
        "final_value": None,
        "page_errors": [],
        "screenshot": str(SCREENSHOT_PATH),
    }

    try:
        from importlib.metadata import version
        installed_version = version("playwright")
        result["playwright_version"] = installed_version
        if installed_version != EXPECTED_PLAYWRIGHT:
            raise RuntimeError(
                f"Playwright version mismatch: {installed_version}; "
                f"expected {EXPECTED_PLAYWRIGHT}"
            )

        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                result["browser_version"] = browser.version
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.on("pageerror", lambda error: result["page_errors"].append(str(error)))

                response = page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
                if response is None:
                    raise RuntimeError("Navigation did not return an HTTP response")
                result["http_status"] = response.status
                if response.status != 200:
                    raise RuntimeError(f"Expected HTTP 200, received {response.status}")

                result["page_title"] = page.title()
                if result["page_title"] != "webapp-testing runtime preflight":
                    raise RuntimeError(f"Unexpected page title: {result['page_title']!r}")

                counter = page.locator("#counter")
                result["initial_value"] = counter.inner_text()
                if result["initial_value"] != "Value: 0":
                    raise RuntimeError(f"Unexpected initial value: {result['initial_value']!r}")

                page.get_by_role("button", name="Increase value").click()
                result["final_value"] = counter.inner_text()
                if result["final_value"] != "Value: 1":
                    raise RuntimeError(f"Button interaction failed: {result['final_value']!r}")

                if result["page_errors"]:
                    raise RuntimeError(f"Browser page errors: {result['page_errors']}")

                page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
            finally:
                browser.close()

        result["status"] = "PASS"
        return_code = 0
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        return_code = 1
    finally:
        RESULT_PATH.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
