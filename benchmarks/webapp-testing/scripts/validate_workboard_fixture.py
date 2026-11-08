#!/usr/bin/env python3
"""Verify Workboard Lite control and mutation profiles.

These checks validate the application fixture itself. They are not Builder
outputs, formal evaluation cases, or tests executed by the webapp-testing Skill.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import traceback
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("PREFLIGHT_BASE_URL", "http://127.0.0.1:4173")
ARTIFACT_DIR = Path(os.environ.get("PREFLIGHT_ARTIFACT_DIR", "artifacts/runtime-preflight"))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_counts(page) -> dict[str, int]:
    return {
        "all": int(page.locator("#count-all").inner_text()),
        "open": int(page.locator("#count-open").inner_text()),
        "in_progress": int(page.locator("#count-in-progress").inner_text()),
        "done": int(page.locator("#count-done").inner_text()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("clean", "mutant"), required=True)
    args = parser.parse_args()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "FAIL",
        "scope": "fixture_contract_check_only",
        "formal_evaluation_case": False,
        "builder_invoked": False,
        "webapp_testing_skill_invoked": False,
        "profile": args.profile,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "playwright_version": version("playwright"),
        "base_url": BASE_URL,
        "checks": [],
        "page_errors": [],
        "screenshot": str(ARTIFACT_DIR / f"workboard-{args.profile}.png"),
    }

    browser = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            result["browser_version"] = browser.version
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda error: result["page_errors"].append(str(error)))
            response = page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
            expect(response is not None and response.status == 200, "Workboard page did not return HTTP 200")
            expect(page.title() == "Workboard Lite", "Unexpected Workboard page title")
            page.locator("#count-all").wait_for()
            initial = read_counts(page)
            expect(initial == {"all": 5, "open": 2, "in_progress": 2, "done": 1}, f"Unexpected initial counts: {initial}")
            result["initial_counts"] = initial
            result["checks"].append("initial-page-and-seed-state")

            if args.profile == "clean":
                search = page.get_by_role("searchbox", name="Search tasks")
                search.fill("PASSWORD")
                page.wait_for_function("document.querySelectorAll('#task-rows tr').length === 1")
                expect(page.locator("#task-rows tr").filter(has_text="WB-101").count() == 1, "Case-insensitive title search failed")
                search.fill("screenshots")
                page.wait_for_function("document.querySelectorAll('#task-rows tr').length === 1")
                expect(page.locator("#task-rows tr").filter(has_text="WB-102").count() == 1, "Description search failed")
                result["checks"].extend(["case-insensitive-search", "description-search"])

                search.fill("")
                search.fill("")
                row = page.locator("#task-rows tr").filter(has_text="WB-101")
                row.get_by_role("button", name="Move to In progress").click()
                page.wait_for_function("""() => {
                    const row = [...document.querySelectorAll('#task-rows tr')].find(item => item.innerText.includes('WB-101'));
                    return row && row.children[2].innerText.includes('In progress')
                        && document.querySelector('#count-open').textContent === '1';
                }""")
                updated = read_counts(page)
                expect(updated == {"all": 5, "open": 1, "in_progress": 3, "done": 1}, f"Summary did not update after status change: {updated}")
                result["checks"].append("status-transition-and-summary")

                row = page.locator("#task-rows tr").filter(has_text="WB-104")
                row.get_by_role("button", name="Delete").click()
                page.get_by_role("dialog").get_by_role("button", name="Cancel").click()
                expect(page.locator("#task-rows tr").filter(has_text="WB-104").count() == 1, "Cancel deleted the task")
                result["checks"].append("delete-cancel-preserves-state")

                page.get_by_label("Title").fill("   ")
                page.get_by_role("button", name="Create task").click()
                page.wait_for_function("document.querySelector('#status-message').innerText.includes('Title is required')")
                expect("Title is required" in page.locator("#status-message").inner_text(), "Whitespace-only title was not rejected")
                expect(page.locator("#count-all").inner_text() == "5", "Invalid task was created")
                result["checks"].append("blank-title-rejected")

                page.get_by_label("Title").fill("Fixture contract task")
                page.get_by_label("Priority").select_option(label="High")
                page.get_by_role("button", name="Create task").click()
                page.get_by_text("Fixture contract task").wait_for()
                expect(read_counts(page)["all"] == 6, "Valid task creation did not update summary")
                result["checks"].append("valid-task-creation")

                row = page.locator("#task-rows tr").filter(has_text="WB-104")
                row.get_by_role("button", name="Delete").click()
                page.get_by_role("dialog").get_by_role("button", name="Delete task").click()
                page.wait_for_function("!document.querySelector('#task-rows').innerText.includes('WB-104')")
                expect(read_counts(page)["all"] == 5, "Confirmed deletion did not update task count")
                result["checks"].append("confirmed-delete")
            else:
                search = page.get_by_role("searchbox", name="Search tasks")
                search.fill("PASSWORD")
                page.wait_for_function("document.querySelector('#empty-state').hidden === false")
                expect(page.locator("#task-rows tr").count() == 0, "Expected search mutation was not observed")
                search.fill("screenshots")
                page.wait_for_function("document.querySelector('#empty-state').hidden === false")
                expect(page.locator("#task-rows tr").count() == 0, "Expected description-search mutation was not observed")
                result["checks"].append("mutation-search-case-sensitive-title-only")

                search.fill("")
                search.fill("")
                row = page.locator("#task-rows tr").filter(has_text="WB-101")
                row.get_by_role("button", name="Move to In progress").click()
                page.wait_for_function("""() => {
                    const row = [...document.querySelectorAll('#task-rows tr')].find(item => item.innerText.includes('WB-101'));
                    return row && row.children[2].innerText.includes('In progress');
                }""")
                mutant_counts = read_counts(page)
                expect(mutant_counts == initial, f"Expected stale summary was not observed: {mutant_counts}")
                result["checks"].append("mutation-stale-summary")

                page.get_by_label("Title").fill("   ")
                page.get_by_role("button", name="Create task").click()
                page.wait_for_function("document.querySelector('#task-rows').innerText.includes('WB-106')")
                expect(page.locator("#task-rows tr").count() == 6, "Whitespace-only task was not added")
                result["checks"].append("mutation-blank-title-accepted")

            if result["page_errors"]:
                raise AssertionError(f"Browser page errors: {result['page_errors']}")
            page.screenshot(path=result["screenshot"], full_page=True)
            result["status"] = "PASS"
        return_code = 0
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        return_code = 1
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception as exc:
                result.setdefault("cleanup_errors", []).append(str(exc))
        output = ARTIFACT_DIR / f"workboard-{args.profile}.json"
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
