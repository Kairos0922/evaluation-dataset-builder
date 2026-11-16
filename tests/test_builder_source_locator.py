#!/usr/bin/env python3
"""Regression tests for source locators with section and line anchors."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
                VALIDATOR.normalize_source_text("page.fill('#name', 'John Doe')")
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



    def test_source_map_uses_manifest_declared_lowercase_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "artifacts/webapp-testing-builder-input/assets/public/application-overview.md"
            content = "## 3 初始数据\\n应用启动时提供五条合成任务。"
            source_path = root / relative
            source_path.parent.mkdir(parents=True)
            source_path.write_text(content, encoding="utf-8")
            output = root / "output"
            output.mkdir()
            record = {
                "source_id": "SRC-APP",
                "title": "Workboard Lite 应用说明",
                "source_type": "synthetic_scenario",
                "path": "assets/public/application-overview.md",
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "quotes": [{
                    "locator": "§3 初始数据",
                    "quoted_evidence": "应用启动时提供五条合成任务。",
                }],
            }
            (output / "SUITE-MANIFEST.json").write_text(
                json.dumps({"source_map_json": "source-map.json"}),
                encoding="utf-8",
            )
            (output / "source-map.json").write_text(
                json.dumps({"sources": [record]}, ensure_ascii=False),
                encoding="utf-8",
            )
            corpus = {relative: VALIDATOR.normalize_source_text(content)}
            with patch.object(VALIDATOR, "ROOT", root):
                source_map = VALIDATOR.load_source_map(output, corpus)
            self.assertIn("SRC-APP", source_map)

    def test_source_map_rejects_unsafe_manifest_path(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            output.mkdir()
            (output / "SUITE-MANIFEST.json").write_text(
                json.dumps({"source_map_json": "../source-map.json"}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "Unsafe source_map_json path"):
                VALIDATOR.resolve_source_map_path(output)

    def test_source_id_resolves_heading_locator_through_sha_verified_source_map(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "artifacts/webapp-testing-builder-input/assets/public/application-overview.md"
            source_path = root / relative
            source_path.parent.mkdir(parents=True)
            content = "## 3 初始数据\\n应用启动时提供五条合成任务。"
            source_path.write_text(content, encoding="utf-8")
            output = root / "output"
            output.mkdir()
            record = {
                "source_id": "SRC-APP",
                "title": "Workboard Lite 应用说明",
                "source_type": "synthetic_scenario",
                "path": "assets/public/application-overview.md",
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "locators": [{
                    "locator": "§3 初始数据",
                    "quoted_evidence": "应用启动时提供五条合成任务。",
                }],
            }
            (output / "SOURCE-MAP.json").write_text(
                json.dumps({"sources": [record]}, ensure_ascii=False),
                encoding="utf-8",
            )
            corpus = {relative: VALIDATOR.normalize_source_text(content)}
            source = {
                "source_id": "SRC-APP",
                "source_type": "synthetic_scenario",
                "title": "Workboard Lite 应用说明",
                "locator": "§3 初始数据",
                "quoted_evidence": "应用启动时提供五条合成任务。",
            }
            with patch.object(VALIDATOR, "ROOT", root):
                source_map = VALIDATOR.load_source_map(output, corpus)
                VALIDATOR.verify_source_evidence("WB-C01", source, corpus, source_map)

    def test_source_map_rejects_file_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "artifacts/webapp-testing-builder-input/assets/public/application-overview.md"
            source_path = root / relative
            source_path.parent.mkdir(parents=True)
            source_path.write_text("真实来源文本。", encoding="utf-8")
            output = root / "output"
            output.mkdir()
            record = {
                "source_id": "SRC-APP",
                "title": "应用说明",
                "source_type": "synthetic_scenario",
                "path": "assets/public/application-overview.md",
                "sha256": "0" * 64,
                "locators": [{"locator": "§3", "quoted_evidence": "真实来源文本。"}],
            }
            (output / "SOURCE-MAP.json").write_text(
                json.dumps({"sources": [record]}, ensure_ascii=False),
                encoding="utf-8",
            )
            corpus = {relative: VALIDATOR.normalize_source_text("真实来源文本。")}
            with patch.object(VALIDATOR, "ROOT", root):
                with self.assertRaisesRegex(SystemExit, "SHA-256 does not match"):
                    VALIDATOR.load_source_map(output, corpus)

    def test_source_reference_must_match_the_mapped_locator_and_quote(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "artifacts/webapp-testing-builder-input/assets/public/application-overview.md"
            source_path = root / relative
            source_path.parent.mkdir(parents=True)
            content = "## 3 初始数据\\n应用启动时提供五条合成任务。"
            source_path.write_text(content, encoding="utf-8")
            output = root / "output"
            output.mkdir()
            record = {
                "source_id": "SRC-APP",
                "title": "Workboard Lite 应用说明",
                "source_type": "synthetic_scenario",
                "path": "assets/public/application-overview.md",
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "locators": [{
                    "locator": "§3 初始数据",
                    "quoted_evidence": "应用启动时提供五条合成任务。",
                }],
            }
            (output / "SOURCE-MAP.json").write_text(
                json.dumps({"sources": [record]}, ensure_ascii=False),
                encoding="utf-8",
            )
            corpus = {relative: VALIDATOR.normalize_source_text(content)}
            source = {
                "source_id": "SRC-APP",
                "source_type": "synthetic_scenario",
                "title": "Workboard Lite 应用说明",
                "locator": "§4 不同章节",
                "quoted_evidence": "应用启动时提供五条合成任务。",
            }
            with patch.object(VALIDATOR, "ROOT", root):
                source_map = VALIDATOR.load_source_map(output, corpus)
                with self.assertRaisesRegex(SystemExit, "locator/quoted_evidence pair"):
                    VALIDATOR.verify_source_evidence("WB-C01", source, corpus, source_map)


    def test_source_map_accepts_canonical_quotes_field(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "artifacts/webapp-testing-builder-input/assets/public/business-rules.md"
            content = "BR-02 搜索必须不区分大小写。"
            source_path = root / relative
            source_path.parent.mkdir(parents=True)
            source_path.write_text(content, encoding="utf-8")
            output = root / "output"
            output.mkdir()
            record = {
                "source_id": "SRC-BR",
                "title": "业务规则",
                "source_type": "authoritative_policy",
                "path": "assets/public/business-rules.md",
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "quotes": [{
                    "locator": "BR-02 (line 1)",
                    "quoted_evidence": "BR-02 搜索必须不区分大小写。",
                }],
            }
            (output / "SOURCE-MAP.json").write_text(
                json.dumps({"sources": [record]}, ensure_ascii=False),
                encoding="utf-8",
            )
            corpus = {relative: VALIDATOR.normalize_source_text(content)}
            source = {
                "source_id": "SRC-BR",
                "source_type": "authoritative_policy",
                "title": "业务规则",
                "locator": "BR-02 (line 1)",
                "quoted_evidence": "BR-02 搜索必须不区分大小写。",
            }
            with patch.object(VALIDATOR, "ROOT", root):
                source_map = VALIDATOR.load_source_map(output, corpus)
                VALIDATOR.verify_source_evidence("CASE-BR02", source, corpus, source_map)

if __name__ == "__main__":
    unittest.main()
