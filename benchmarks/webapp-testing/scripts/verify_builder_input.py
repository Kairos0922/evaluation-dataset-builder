#!/usr/bin/env python3
"""Independently verify the public Builder input bundle and its SHA-256 records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("artifacts/webapp-testing-builder-input")
MANIFEST_PATH = ROOT / "asset-manifest.json"
EXPECTED_UPSTREAM = {
    "upstream-skill/LICENSE.txt",
    "upstream-skill/SKILL.md",
    "upstream-skill/examples/console_logging.py",
    "upstream-skill/examples/element_discovery.py",
    "upstream-skill/examples/static_html_automation.py",
    "upstream-skill/scripts/with_server.py",
}


def main() -> int:
    if not MANIFEST_PATH.is_file():
        raise SystemExit(f"Input manifest missing: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    if manifest.get("bundle_status") != "COMPLETE":
        raise SystemExit("Builder input bundle is not marked COMPLETE")
    if manifest.get("visibility") != "PUBLIC_FOR_BUILDER_AND_CONSUMER":
        raise SystemExit("Unexpected Builder input visibility")
    if manifest.get("formal_evaluation_cases_included") is not False:
        raise SystemExit("Formal cases must not be present in the Builder input bundle")
    if manifest.get("grading_contracts_included") is not False:
        raise SystemExit("Grading contracts must not be present in the Builder input bundle")
    if manifest.get("gold_oracle_included") is not False:
        raise SystemExit("Gold Oracle must not be present in the Builder input bundle")

    actual_paths = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != MANIFEST_PATH
    }
    records = manifest.get("assets")
    if not isinstance(records, list) or not records:
        raise SystemExit("Manifest assets must be a non-empty list")
    declared_paths = {record["path"] for record in records}
    if actual_paths != declared_paths:
        raise SystemExit(
            f"Input file set mismatch; missing_records={sorted(actual_paths - declared_paths)}; "
            f"missing_files={sorted(declared_paths - actual_paths)}"
        )

    record_by_path = {record["path"]: record for record in records}
    if len(record_by_path) != len(records):
        raise SystemExit("Duplicate input asset paths")
    for path in sorted(actual_paths):
        file_path = ROOT / path
        if file_path.is_symlink() or not file_path.is_file():
            raise SystemExit(f"Unsupported file type: {path}")
        data = file_path.read_bytes()
        record = record_by_path[path]
        digest = hashlib.sha256(data).hexdigest()
        if record.get("sha256") != digest:
            raise SystemExit(f"SHA-256 mismatch: {path}")
        if record.get("size_bytes") != len(data):
            raise SystemExit(f"Size mismatch: {path}")
        if record.get("visibility") != "PUBLIC":
            raise SystemExit(f"Asset is not marked PUBLIC: {path}")
        if not record.get("asset_id") or not record.get("source", {}).get("revision"):
            raise SystemExit(f"Asset lacks stable ID or source revision: {path}")

    if not EXPECTED_UPSTREAM.issubset(actual_paths):
        raise SystemExit(f"Pinned upstream Skill inventory incomplete: {sorted(EXPECTED_UPSTREAM - actual_paths)}")
    for required in (
        "BUILDER-TASK.md",
        "UPSTREAM-ASSET-REVIEW.md",
        "assets/public/ASSET-INDEX.md",
        "assets/public/business-rules.md",
        "assets/public/application-overview.md",
        "assets/public/capability-description.md",
        "assets/public/runtime-and-tool-contracts.md",
        "fixtures/workboard/server.py",
        "fixtures/workboard/static/index.html",
    ):
        if required not in actual_paths:
            raise SystemExit(f"Required public input asset missing: {required}")

    forbidden_markers = ("gold-oracle", "gold_oracle", "hidden-oracle", "hidden_oracle")
    forbidden = [
        path for path in actual_paths
        if any(marker in path.casefold() for marker in forbidden_markers)
    ]
    if forbidden:
        raise SystemExit(f"Oracle-related files must not enter Builder input: {forbidden}")

    canonical = json.dumps(
        records, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    if digest != manifest.get("package_manifest_sha256"):
        raise SystemExit("Package manifest digest mismatch")

    print(json.dumps({
        "status": "PASS",
        "scope": "public_builder_input_bundle_integrity",
        "file_count": len(actual_paths),
        "upstream_skill_file_count": len(EXPECTED_UPSTREAM),
        "per_file_sha256_verified": len(actual_paths),
        "package_manifest_sha256": digest,
        "formal_evaluation_cases_included": False,
        "gold_oracle_included": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
