#!/usr/bin/env python3
"""Verify the pinned upstream webapp-testing Skill inventory.

The manifest is deterministic. It records Git blob identities and sizes; the
SHA-256 digest covers the canonical inventory fields documented in the output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

UPSTREAM_COMMIT = "2c5958ecac7cee2b583967a2c4981d0f4a75c579"
SKILL_PATH = "skills/webapp-testing"
SKILL_TREE_SHA = "5ffb7dc66b9fd4c25c3e400a4c00da99a349b714"
INVENTORY_SHA256 = "ca5f067e6fc69cd9b6286df33517fd7e0b45fb6fa9d643b23309865b7e47ab88"

EXPECTED_FILES = {
    "skills/webapp-testing/LICENSE.txt": {
        "mode": "100644",
        "type": "blob",
        "blob_sha": "4f881c52d1f72f4cfb720e339e2d35c3058d01a9",
        "size": 11345,
        "role": "license",
    },
    "skills/webapp-testing/SKILL.md": {
        "mode": "100644",
        "type": "blob",
        "blob_sha": "4726215301db64a0cc4d41fc3219c61f37a30f4a",
        "size": 3913,
        "role": "instructions",
    },
    "skills/webapp-testing/examples/console_logging.py": {
        "mode": "100644",
        "type": "blob",
        "blob_sha": "9329b5e232ed53d944bfe95e750070117d31b9ab",
        "size": 1027,
        "role": "example",
    },
    "skills/webapp-testing/examples/element_discovery.py": {
        "mode": "100644",
        "type": "blob",
        "blob_sha": "917ba72f52421a1b324f93ae8e38af72010a87b9",
        "size": 1463,
        "role": "example",
    },
    "skills/webapp-testing/examples/static_html_automation.py": {
        "mode": "100644",
        "type": "blob",
        "blob_sha": "90bbedcc08cdb345c74fb938ebad02c0baf56603",
        "size": 953,
        "role": "example",
    },
    "skills/webapp-testing/scripts/with_server.py": {
        "mode": "100755",
        "type": "blob",
        "blob_sha": "431f2eba16b268b7f3e2ae4daae9db41c0289b6d",
        "size": 3693,
        "role": "helper_script",
    },
}

DIRECTORIES = {
    "skills/webapp-testing/examples": "d18b45eccd4e8cafe1cc7b3e060e5aa811f76689",
    "skills/webapp-testing/scripts": "7266adeb444f007795fd860b01572e6e4379fdfc",
}


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    repo = args.repo_dir.resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"Not a Git checkout: {repo}")

    checked_out = git(repo, "rev-parse", "HEAD").decode().strip()
    if checked_out != UPSTREAM_COMMIT:
        raise SystemExit(
            f"Unexpected upstream commit: {checked_out}; expected {UPSTREAM_COMMIT}"
        )

    tree_sha = git(repo, "rev-parse", f"{UPSTREAM_COMMIT}:{SKILL_PATH}").decode().strip()
    if tree_sha != SKILL_TREE_SHA:
        raise SystemExit(f"Unexpected Skill tree SHA: {tree_sha}")

    raw_entries = git(
        repo, "ls-tree", "-r", "-z", "--full-tree",
        UPSTREAM_COMMIT, "--", SKILL_PATH,
    )
    actual: dict[str, dict[str, Any]] = {}
    for raw_entry in raw_entries.split(b"\\0"):
        if not raw_entry:
            continue
        metadata, raw_path = raw_entry.split(b"\\t", 1)
        mode, object_type, blob_sha = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8")
        if path in actual:
            raise SystemExit(f"Duplicate path in Git tree: {path}")
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise SystemExit(
                f"Unsupported asset type or mode: {path} ({mode}, {object_type})"
            )
        size = int(git(repo, "cat-file", "-s", blob_sha).decode().strip())
        actual[path] = {
            "mode": mode,
            "type": object_type,
            "blob_sha": blob_sha,
            "size": size,
            "role": EXPECTED_FILES.get(path, {}).get("role", "unclassified"),
        }

    if actual != EXPECTED_FILES:
        expected_paths = set(EXPECTED_FILES)
        actual_paths = set(actual)
        missing = sorted(expected_paths - actual_paths)
        unexpected = sorted(actual_paths - expected_paths)
        mismatched = sorted(
            path for path in expected_paths & actual_paths
            if actual[path] != EXPECTED_FILES[path]
        )
        raise SystemExit(
            "Upstream inventory differs from the reviewed baseline. "
            f"missing={missing}; unexpected={unexpected}; mismatched={mismatched}"
        )

    for directory, expected_sha in DIRECTORIES.items():
        actual_sha = git(repo, "rev-parse", f"{UPSTREAM_COMMIT}:{directory}").decode().strip()
        if actual_sha != expected_sha:
            raise SystemExit(f"Unexpected tree SHA for {directory}: {actual_sha}")

    inventory_fields = [
        {
            "path": path,
            "mode": entry["mode"],
            "type": entry["type"],
            "blob_sha": entry["blob_sha"],
            "size": entry["size"],
        }
        for path, entry in sorted(actual.items())
    ]
    canonical = json.dumps(
        inventory_fields, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    inventory_sha = hashlib.sha256(canonical).hexdigest()
    if inventory_sha != INVENTORY_SHA256:
        raise SystemExit(
            f"Inventory SHA-256 mismatch: {inventory_sha}; expected {INVENTORY_SHA256}"
        )

    manifest = {
        "schema_version": "1.0",
        "status": "COMPLETE",
        "source": {
            "repository": "https://github.com/anthropics/skills",
            "path": SKILL_PATH,
            "commit": UPSTREAM_COMMIT,
            "license": "Apache-2.0",
        },
        "completeness": {
            "recursive_tree_verified": True,
            "recursive_tree_truncated": False,
            "full_file_inventory_verified": True,
            "file_count": len(actual),
            "directory_count": 2,
            "symlink_count": 0,
            "submodule_count": 0,
            "git_tree_sha": tree_sha,
            "inventory_sha256": inventory_sha,
            "inventory_hash_spec": (
                "SHA-256 of UTF-8 JSON for the sorted file records containing "
                "path, mode, type, blob_sha, and size; JSON uses sort_keys=true, "
                "ensure_ascii=false, and separators=(',', ':')."
            ),
        },
        "directories": [
            {"path": path, "git_tree_sha": sha}
            for path, sha in sorted(DIRECTORIES.items())
        ],
        "files": [
            {"path": path, **entry}
            for path, entry in sorted(actual.items())
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\\n",
        encoding="utf-8",
    )
    print(f"Verified {len(actual)} files under {SKILL_PATH}")
    print(f"Git tree SHA: {tree_sha}")
    print(f"Inventory SHA-256: {inventory_sha}")
    print(f"Manifest: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr.decode("utf-8", errors="replace"))
        raise SystemExit(exc.returncode)
