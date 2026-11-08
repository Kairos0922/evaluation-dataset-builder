#!/usr/bin/env python3
"""Build the public input bundle for Evaluation Dataset Builder.

This script copies and fingerprints source assets only. It never creates formal
evaluation cases, expected answers, grading contracts, or Oracle data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

UPSTREAM_COMMIT = "2c5958ecac7cee2b583967a2c4981d0f4a75c579"
UPSTREAM_REPO = "anthropics/skills"
UPSTREAM_SKILL_PATH = "skills/webapp-testing"

ASSET_ROOTS = [
    ("assets/public", "benchmarks/webapp-testing/assets/public", "business_and_capability_asset"),
    ("fixtures/workboard", "benchmarks/webapp-testing/fixtures/workboard", "application_fixture"),
    ("upstream-skill", "skills/webapp-testing", "upstream_skill_asset"),
]


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise SystemExit(f"Required asset directory does not exist: {source}")
    for path in source.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"Symlinks are not allowed in Builder input assets: {path}")
    shutil.copytree(source, destination, dirs_exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-dir", type=Path, required=True)
    parser.add_argument("--upstream-repo-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-revision", required=True)
    args = parser.parse_args()

    repo = args.repo_dir.resolve()
    upstream = args.upstream_repo_dir.resolve()
    output = args.output.resolve()

    upstream_head = git(upstream, "rev-parse", "HEAD")
    if upstream_head != UPSTREAM_COMMIT:
        raise SystemExit(
            f"Upstream checkout mismatch: {upstream_head}; expected {UPSTREAM_COMMIT}"
        )

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    task_source = repo / "benchmarks/webapp-testing/BUILDER-TASK.md"
    if not task_source.is_file():
        raise SystemExit(f"Builder task file missing: {task_source}")
    shutil.copy2(task_source, output / "BUILDER-TASK.md")

    for target, source_relative, _ in ASSET_ROOTS:
        copy_tree(repo / source_relative if source_relative.startswith("benchmarks/") else upstream / source_relative,
                  output / target)

    provenance = output / "provenance"
    provenance.mkdir()
    shutil.copy2(
        repo / "benchmarks/webapp-testing/upstream-asset-manifest.json",
        provenance / "upstream-asset-manifest.json",
    )
    shutil.copy2(
        repo / "benchmarks/webapp-testing/UPSTREAM-ASSET-REVIEW.md",
        provenance / "upstream-asset-review.md",
    )

    records: list[dict[str, Any]] = []
    source_by_prefix = {
        "assets/public/": {
            "repository": "Kairos0922/evaluation-dataset-builder",
            "revision": args.repo_revision,
            "source_root": "benchmarks/webapp-testing/assets/public",
            "asset_type": "business_and_capability_asset",
        },
        "fixtures/workboard/": {
            "repository": "Kairos0922/evaluation-dataset-builder",
            "revision": args.repo_revision,
            "source_root": "benchmarks/webapp-testing/fixtures/workboard",
            "asset_type": "application_fixture",
        },
        "upstream-skill/": {
            "repository": UPSTREAM_REPO,
            "revision": UPSTREAM_COMMIT,
            "source_root": UPSTREAM_SKILL_PATH,
            "asset_type": "upstream_skill_asset",
        },
        "provenance/": {
            "repository": "Kairos0922/evaluation-dataset-builder",
            "revision": args.repo_revision,
            "source_root": "benchmarks/webapp-testing",
            "asset_type": "provenance_record",
        },
    }

    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "asset-manifest.json":
            continue
        relative = path.relative_to(output).as_posix()
        prefix = next((key for key in source_by_prefix if relative.startswith(key)), None)
        if prefix is None and relative != "BUILDER-TASK.md":
            raise SystemExit(f"Unclassified Builder input file: {relative}")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()

        if relative == "BUILDER-TASK.md":
            source = {
                "repository": "Kairos0922/evaluation-dataset-builder",
                "revision": args.repo_revision,
                "source_path": "benchmarks/webapp-testing/BUILDER-TASK.md",
                "asset_type": "task_instruction",
            }
        else:
            meta = source_by_prefix[prefix]
            inner = relative[len(prefix):]
            source_path = f"{meta['source_root']}/{inner}"
            source = {
                "repository": meta["repository"],
                "revision": meta["revision"],
                "source_path": source_path,
                "asset_type": meta["asset_type"],
            }

        records.append({
            "asset_id": f"webapp-testing:{relative}",
            "path": relative,
            "sha256": digest,
            "size_bytes": len(data),
            "visibility": "PUBLIC",
            "source": source,
        })

    canonical_records = json.dumps(
        records, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    package_hash = hashlib.sha256(canonical_records).hexdigest()

    manifest = {
        "schema_version": "1.0",
        "bundle_status": "COMPLETE",
        "visibility": "PUBLIC_FOR_BUILDER_AND_CONSUMER",
        "formal_evaluation_cases_included": False,
        "grading_contracts_included": False,
        "gold_oracle_included": False,
        "source_snapshot": {
            "builder_repository": "Kairos0922/evaluation-dataset-builder",
            "builder_revision": args.repo_revision,
            "upstream_repository": UPSTREAM_REPO,
            "upstream_skill_path": UPSTREAM_SKILL_PATH,
            "upstream_commit": UPSTREAM_COMMIT,
        },
        "file_count": len(records),
        "package_manifest_sha256": package_hash,
        "hash_spec": (
            "SHA-256 of UTF-8 JSON for sorted asset records containing asset_id, "
            "path, sha256, size_bytes, visibility, and source; sort_keys=true, "
            "ensure_ascii=false, separators=(',', ':')."
        ),
        "assets": records,
    }

    (output / "asset-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "PASS",
        "scope": "public_input_bundle_only",
        "formal_evaluation_cases_created": False,
        "gold_oracle_included": False,
        "upstream_commit": UPSTREAM_COMMIT,
        "file_count": len(records),
        "package_manifest_sha256": package_hash,
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
