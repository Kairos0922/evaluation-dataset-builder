#!/usr/bin/env python3
"""Regression tests for source locators with section and line anchors."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "benchmarks" / "webapp-testing" / "scripts" / "validate_builder_output.py"
SPEC = importlib.util.spec_from_file_location("validate_builder_output", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class BuilderSourceLocatorTests(unittest.TestCase):
    def test_markdown_filename_with_unicode_section_anchor_resolves(self):
        source = {
            "title": "Workboard Lite 应用说明",
            "locator": "assets/public/application-overview.md#3. 初始数据 (L33-L41)",
            "quoted_evidence": "应用启动时提供五条合成任务。",
        }
        corpus = {
            "assets/public/application-overview.md":
                "## 3. 初始数据\n应用启动时提供五条合成任务。"
        }
        VALIDATOR.verify_source_evidence("WB-CORE-01", source, corpus)

    def test_source_filename_with_line_anchor_resolves(self):
        source = {
            "title": "上游示例 static_html_automation.py",
            "locator": "upstream-skill/examples/static_html_automation.py#L21",
            "quoted_evidence": "page.fill('#name', 'John Doe')",
        }
        corpus = {
            "upstream-skill/examples/static_html_automation.py":
                "page.fill('#name', 'John Doe')"
        }
        VALIDATOR.verify_source_evidence("WB-CORE-03", source, corpus)

    def test_locator_without_explicit_filename_fails_closed(self):
        source = {
            "title": "Unknown source",
            "locator": "Section 3 (L20-L25)",
            "quoted_evidence": "some source quotation",
        }
        with self.assertRaisesRegex(SystemExit, "must identify an explicit source filename"):
            VALIDATOR.verify_source_evidence("CASE-UNKNOWN", source, {})

    def test_locator_with_missing_filename_fails_closed(self):
        source = {
            "title": "Workboard Lite 应用说明",
            "locator": "assets/public/not-present.md#Section",
            "quoted_evidence": "some source quotation",
        }
        with self.assertRaisesRegex(SystemExit, "does not resolve to an available source file"):
            VALIDATOR.verify_source_evidence("CASE-MISSING", source, {})


if __name__ == "__main__":
    unittest.main()
