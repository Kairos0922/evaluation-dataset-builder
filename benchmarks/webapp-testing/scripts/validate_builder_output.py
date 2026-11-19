#!/usr/bin/env python3
"""Independently validate Evaluation Dataset Builder's generated webapp-testing suite.

This script validates only. It must never create, edit, repair, or select cases.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(os.environ.get("BUILDER_OUTPUT_DIR", "artifacts/webapp-testing-builder-output"))
CASE_SCHEMA_PATH = ROOT / "skills/evaluation-dataset-builder/references/dataset-schema.json"
MANIFEST_SCHEMA_PATH = ROOT / "skills/evaluation-dataset-builder/references/dataset-manifest-schema.json"
ALLOWED_QUALITY = {"candidate", "needs_info"}
ALLOWED_EXECUTION = {"NOT_RUN"}
SOURCE_ROOTS = (
    ROOT / "benchmarks/webapp-testing/assets/public",
    ROOT / "benchmarks/webapp-testing/fixtures/workboard",
    ROOT / "artifacts/webapp-testing-builder-input/assets/public",
    ROOT / "artifacts/webapp-testing-builder-input/fixtures/workboard",
    ROOT / "artifacts/webapp-testing-builder-input/upstream-skill",
    ROOT / ".audit/upstream-skills/skills/webapp-testing",
)
SOURCE_SUFFIXES = {".md", ".txt", ".py", ".html", ".js", ".css", ".json"}


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_nonempty_text(value, location: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{location} must be a non-empty string")


def require_nonempty_collection(value, location: str) -> None:
    if not isinstance(value, (list, dict)) or not value:
        raise SystemExit(f"{location} must be a non-empty list or object")


def require_nonempty_value(value, location: str) -> None:
    if value is None:
        raise SystemExit(f"{location} is required")
    if isinstance(value, str) and not value.strip():
        raise SystemExit(f"{location} must not be blank")
    if isinstance(value, (list, dict)) and not value:
        raise SystemExit(f"{location} must not be empty")


def normalize_source_text(value: str) -> str:
    value = unicodedata.normalize('NFKC', value).casefold()
    return re.sub(r'\s+', ' ', value).strip()


def load_source_corpus() -> dict[str, str]:
    corpus: dict[str, str] = {}
    for source_root in SOURCE_ROOTS:
        if not source_root.is_dir():
            continue
        for path in sorted(source_root.rglob('*')):
            if not path.is_file() or path.is_symlink() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            try:
                content = path.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            if content.strip():
                corpus[path.relative_to(ROOT).as_posix()] = normalize_source_text(content)
    # The upstream review is a first-class Builder input source at the benchmark root,
    # not under assets/public or fixtures. Include this exact file without broadening
    # the corpus to every benchmark implementation/script file.
    review_path = ROOT / "benchmarks/webapp-testing/UPSTREAM-ASSET-REVIEW.md"
    if review_path.is_file() and not review_path.is_symlink():
        try:
            review_content = review_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            review_content = ""
        if review_content.strip():
            corpus[review_path.relative_to(ROOT).as_posix()] = normalize_source_text(review_content)

    # The archived Builder input bundle is the authoritative snapshot for a
    # historical run. Include its exact task/review files so later repository
    # edits cannot invalidate or silently rewrite the source evidence.
    for filename in ("BUILDER-TASK.md", "UPSTREAM-ASSET-REVIEW.md"):
        archived_path = ROOT / "artifacts/webapp-testing-builder-input" / filename
        if archived_path.is_file() and not archived_path.is_symlink():
            try:
                archived_content = archived_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                archived_content = ""
            if archived_content.strip():
                corpus[archived_path.relative_to(ROOT).as_posix()] = normalize_source_text(archived_content)

    # The current task/review files remain available for non-replay validation.
    task_path = ROOT / "benchmarks/webapp-testing/BUILDER-TASK.md"
    if task_path.is_file() and not task_path.is_symlink():
        try:
            task_content = task_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            task_content = ""
        if task_content.strip():
            corpus[task_path.relative_to(ROOT).as_posix()] = normalize_source_text(task_content)

    if not corpus:
        raise SystemExit('No readable public source corpus is available for source-evidence verification')
    return corpus


def reject_case_insensitive_path_collisions(output: Path) -> None:
    """Reject paths that collide on case-insensitive filesystems."""
    seen: dict[str, str] = {}
    for path in sorted(output.rglob("*")):
        relative = path.relative_to(output).as_posix()
        key = relative.casefold()
        previous = seen.get(key)
        if previous is not None and previous != relative:
            raise SystemExit(
                "Builder output contains case-insensitive path collision: "
                f"{previous!r} and {relative!r}"
            )
        seen[key] = relative


def resolve_source_map_path(output: Path) -> Path:
    """Resolve the source-map JSON through the Suite Manifest's declared path."""
    reject_case_insensitive_path_collisions(output)
    suite_manifest_path = output / "SUITE-MANIFEST.json"
    suite_manifest = load_json(suite_manifest_path) if suite_manifest_path.is_file() else {}
    declared_path = (
        suite_manifest.get("source_map_json")
        if isinstance(suite_manifest, dict) else None
    )
    # Keep compatibility with earlier artifacts and focused unit fixtures
    # that contain only the documented uppercase source-map filename.
    if declared_path is None:
        declared_path = "SOURCE-MAP.json"
    require_nonempty_text(declared_path, "SUITE-MANIFEST.json.source_map_json")

    relative = Path(declared_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise SystemExit(f"Unsafe source_map_json path: {declared_path}")

    candidate = output / relative
    if candidate.is_symlink() or not candidate.is_file():
        raise SystemExit(
            f"Builder source_map_json does not resolve to a regular file: {declared_path}"
        )
    resolved = candidate.resolve()
    if output.resolve() not in resolved.parents:
        raise SystemExit(f"source_map_json escapes the Builder output directory: {declared_path}")
    if resolved.suffix.casefold() != ".json":
        raise SystemExit(f"source_map_json must identify a JSON file: {declared_path}")
    return resolved


def load_source_map(output: Path, corpus: dict[str, str]) -> dict[str, dict]:
    """Resolve Builder source IDs to immutable files in the trusted input corpus.

    Both the explicit sources[] form and the Builder's source_registry[] +
    files[] form are supported. In either form, source paths and SHA-256 values
    must resolve to the independently assembled public corpus. Case-level
    quotations are then verified directly against that exact source file.
    """
    path = resolve_source_map_path(output)
    source_map = load_json(path)
    if not isinstance(source_map, dict):
        raise SystemExit("source-map JSON must be an object")

    path_base = str(source_map.get("path_base") or "").strip().casefold()
    top_level_locators = source_map.get("locators", [])
    if not isinstance(top_level_locators, list):
        raise SystemExit("source-map JSON locators must be a list when present")
    locators_by_source_id: dict[str, list[dict]] = defaultdict(list)
    for locator_record in top_level_locators:
        if not isinstance(locator_record, dict):
            raise SystemExit("source-map JSON locators[] must contain objects")
        locator_source_id = locator_record.get("source_id")
        require_nonempty_text(locator_source_id, "source-map JSON locators[].source_id")
        require_nonempty_text(locator_record.get("locator"), f"{locator_source_id}.locators[].locator")
        # Locator records may identify source sections without duplicating
        # quotations. Case-level source_refs carry quoted_evidence and are
        # independently verified against the SHA-256 trusted source corpus.
        if "quoted_evidence" in locator_record:
            require_nonempty_text(
                locator_record.get("quoted_evidence"),
                f"{locator_source_id}.locators[].quoted_evidence",
            )
        locators_by_source_id[locator_source_id].append(locator_record)

    records = source_map.get("sources")
    registry = source_map.get("source_registry")
    file_records = source_map.get("files")
    # Prefer source_registry + files when both are present. This form binds
    # each source ID to a SHA-256-verified file without requiring a duplicate
    # quote map; every case-level quotation is checked against that exact file.
    if isinstance(registry, list) and registry and isinstance(file_records, list) and file_records:
        records = None
    if not isinstance(records, list) or not records:
        if not isinstance(registry, list) or not registry:
            raise SystemExit("source-map JSON must contain sources[] or source_registry[]")
        if not isinstance(file_records, list) or not file_records:
            raise SystemExit("source-map JSON source_registry[] requires a non-empty files[] array")

        files_by_path = {}
        for file_record in file_records:
            if not isinstance(file_record, dict):
                raise SystemExit("source-map JSON files[] must contain objects")
            file_path = file_record.get("path")
            require_nonempty_text(file_path, "source-map JSON files[].path")
            relative_file_path = Path(file_path)
            if relative_file_path.is_absolute() or ".." in relative_file_path.parts or "\\" in file_path:
                raise SystemExit(f"Unsafe source-map file path: {file_path}")
            if not re.fullmatch(r"[0-9a-f]{64}", str(file_record.get("sha256") or "")):
                raise SystemExit(f"source-map file record lacks a lowercase SHA-256: {file_path}")
            source_ids = file_record.get("source_ids")
            if not isinstance(source_ids, list) or not source_ids or any(
                not isinstance(item, str) or not item.strip() for item in source_ids
            ):
                raise SystemExit(f"source-map file record has invalid source_ids: {file_path}")
            if file_path in files_by_path:
                raise SystemExit(f"source-map JSON contains duplicate file path: {file_path}")
            files_by_path[file_path] = file_record

        records = []
        for registry_record in registry:
            if not isinstance(registry_record, dict):
                raise SystemExit("source-map JSON source_registry[] must contain objects")
            source_id = registry_record.get("source_id")
            declared_path = registry_record.get("path")
            require_nonempty_text(source_id, "source-map JSON source_registry[].source_id")
            require_nonempty_text(declared_path, f"{source_id}.path")
            file_record = files_by_path.get(declared_path)
            if file_record is None:
                raise SystemExit(f"{source_id}: source_registry path is absent from files[]: {declared_path}")
            source_ids = file_record.get("source_ids")
            if not isinstance(source_ids, list) or source_id not in source_ids:
                raise SystemExit(f"{source_id}: files[].source_ids does not include this source ID")
            records.append({
                "source_id": source_id,
                "title": registry_record.get("title"),
                "source_type": registry_record.get("source_type"),
                "path": declared_path,
                "sha256": file_record.get("sha256"),
                "_require_quote_map": False,
            })

    index: dict[str, dict] = {}
    seen_source_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise SystemExit("source-map JSON source records must be objects")
        source_id = record.get("source_id")
        require_nonempty_text(source_id, "source-map JSON source_id")
        if source_id in seen_source_ids:
            raise SystemExit(f"source-map JSON contains duplicate source_id: {source_id}")
        seen_source_ids.add(source_id)

        title = record.get("title")
        source_type = record.get("source_type")
        declared_path = record.get("path")
        declared_sha = record.get("sha256")
        require_nonempty_text(title, f"{source_id}.title")
        require_nonempty_text(source_type, f"{source_id}.source_type")
        require_nonempty_text(declared_path, f"{source_id}.path")
        if not re.fullmatch(r"[0-9a-f]{64}", str(declared_sha or "")):
            raise SystemExit(f"{source_id}: source-map JSON must include a lowercase SHA-256")

        relative = Path(declared_path)
        if relative.is_absolute() or ".." in relative.parts or "\\" in declared_path:
            raise SystemExit(f"{source_id}: unsafe source path in source-map JSON: {declared_path}")
        relative_text = relative.as_posix()
        path_candidates = [relative_text]
        # Builder source maps may use paths relative to the suite directory,
        # for example sources/assets/public/business-rules.md. Resolve that
        # prefix to the exact archived input path, never to the Builder's copy.
        if path_base == "suite directory" and relative_text.startswith("sources/"):
            path_candidates.append(relative_text[len("sources/"):])
        candidate_paths = [
            corpus_path for corpus_path in corpus
            if any(
                corpus_path == candidate or corpus_path.endswith("/" + candidate)
                for candidate in path_candidates
            )
        ]
        # Some provenance-only input records are not in the validator's trusted
        # evidence corpus. They remain unmapped and cannot be cited by a case.
        if not candidate_paths:
            continue

        verified_paths = []
        for corpus_path in candidate_paths:
            try:
                actual_sha = hashlib.sha256((ROOT / corpus_path).read_bytes()).hexdigest()
            except OSError:
                continue
            if actual_sha == declared_sha:
                verified_paths.append(corpus_path)
        if not verified_paths:
            raise SystemExit(
                f"{source_id}: source file SHA-256 does not match source-map JSON: {declared_path}"
            )

        quote_records = record.get("quotes")
        if quote_records is None:
            quote_records = record.get("locators")
        if quote_records is None and source_id in locators_by_source_id:
            # Some Builders normalize source metadata in sources[] and keep
            # section-level citation records in a top-level locators[] array.
            # Bind those records back to the source ID before validating titles
            # and exact locator/quotation pairs.
            quote_records = locators_by_source_id[source_id]
        # A quote map is optional. If the Builder supplies one, enforce the
        # locator/quote pair; otherwise verify each case quote directly against
        # the SHA-256-verified trusted source file below.
        record_requires_quotes = record.get("_require_quote_map", quote_records is not None)
        if quote_records is None:
            if record_requires_quotes:
                raise SystemExit(f"{source_id}: source-map JSON lacks quote records")
            quote_records = []
        if not isinstance(quote_records, list):
            raise SystemExit(f"{source_id}: source quote records must be a list")
        for item in quote_records:
            if not isinstance(item, dict):
                raise SystemExit(f"{source_id}: source quote entries must be objects")
            require_nonempty_text(item.get("locator"), f"{source_id}.quotes[].locator")
            require_nonempty_text(item.get("quoted_evidence"), f"{source_id}.quotes[].quoted_evidence")

        verified_record = dict(record)
        normalized_declared_path = relative_text
        if path_base == "suite directory" and normalized_declared_path.startswith("sources/"):
            normalized_declared_path = normalized_declared_path[len("sources/"):]
        verified_record["_normalized_path"] = normalized_declared_path
        verified_record["_verified_corpus_paths"] = verified_paths
        verified_record["_verified_quotes"] = quote_records
        verified_record["_require_quote_map"] = bool(record_requires_quotes)
        index[source_id] = verified_record

    if not index:
        raise SystemExit("source-map JSON has no source IDs that resolve to the trusted input corpus")
    return index

def verify_source_evidence(
    case_id: str,
    source: dict,
    corpus: dict[str, str],
    source_map: dict[str, dict] | None = None,
) -> None:
    title = source.get('title', '')
    locator = source.get('locator', '')
    quote = source.get('quoted_evidence')
    require_nonempty_text(quote, f'{case_id}.source_refs.quoted_evidence')
    normalized_quote = normalize_source_text(quote)
    if len(normalized_quote) < 6:
        raise SystemExit(f'{case_id}: source quote is too short to verify reliably')

    source_id = source.get("source_id")
    if source_id and source_map is not None:
        mapped = source_map.get(source_id)
        if mapped is None:
            raise SystemExit(
                f"{case_id}: source_id is not present in the verified source-map JSON: {source_id}"
            )
        normalized_title = normalize_source_text(str(source.get("title", "")))
        normalized_document_title = normalize_source_text(mapped["title"])
        matching_locator_records = [
            item for item in mapped.get("_verified_quotes", [])
            if normalize_source_text(str(item.get("locator", ""))) == normalize_source_text(str(locator))
            and normalize_source_text(str(item.get("quoted_evidence", ""))) == normalized_quote
        ]
        allowed_titles = {normalized_document_title}
        allowed_titles.update(
            normalize_source_text(str(item.get("title", "")))
            for item in matching_locator_records
            if isinstance(item.get("title"), str) and item.get("title", "").strip()
        )
        if normalized_title not in allowed_titles:
            raise SystemExit(
                f"{case_id}: source title does not match the source document or "
                f"the exact mapped locator title for {source_id}"
            )
        if source.get("source_type") != mapped["source_type"]:
            raise SystemExit(f"{case_id}: source_type does not match source-map JSON for {source_id}")
        if source.get("path"):
            source_path = str(source["path"])
            source_relative = Path(source_path)
            if source_relative.is_absolute() or ".." in source_relative.parts or "\\" in source_path:
                raise SystemExit(f"{case_id}: unsafe source path for {source_id}: {source_path}")
            source_path_text = source_relative.as_posix()
            mapped_path_text = mapped.get("_normalized_path", mapped["path"])
            if source_path_text.startswith("sources/") and not mapped_path_text.startswith("sources/"):
                source_path_text = source_path_text[len("sources/"):]
            if source_path_text != mapped_path_text:
                raise SystemExit(f"{case_id}: source path does not match source-map JSON for {source_id}")

        normalized_locator = normalize_source_text(str(locator))
        if mapped.get("_require_quote_map"):
            locator_quote_found = any(
                normalize_source_text(str(item.get("locator", ""))) == normalized_locator
                and normalize_source_text(str(item.get("quoted_evidence", ""))) == normalized_quote
                for item in mapped["_verified_quotes"]
            )
            if not locator_quote_found:
                raise SystemExit(
                    f"{case_id}: locator/quoted_evidence pair is absent from source-map JSON for {source_id}"
                )

        verified_paths = mapped["_verified_corpus_paths"]
        if not any(normalized_quote in corpus[corpus_path] for corpus_path in verified_paths):
            raise SystemExit(
                f"{case_id}: quoted_evidence cannot be found in the SHA-256 verified source file "
                f"({mapped['path']!r}, {locator!r})"
            )
        return

    title_locator = f'{title} {locator}'.casefold()
    candidates = {}

    # Resolve an explicit filename in the locator before broad title matching.
    # Titles may contain "webapp-testing" even when the cited source is an
    # upstream example rather than SKILL.md. Accept section/line anchors after
    # the filename (for example, file.md#Section or script.py#L21). Never
    # fall back to the whole
    # corpus: that would allow a quotation from an unrelated file to pass.
    filename_match = re.search(
        r'([A-Za-z0-9_.-]+\.(?:md|txt|py|html|js|css|json))(?=$|[#\s])',
        locator,
        flags=re.IGNORECASE,
    )
    if filename_match:
        filename = filename_match.group(1).casefold()
        candidates = {
            path: text for path, text in corpus.items()
            if Path(path).name.casefold() == filename
        }
        if not candidates:
            raise SystemExit(
                f'{case_id}: locator filename does not resolve to an available source file: {filename_match.group(1)}'
            )
    elif re.search(r'\bBR-\d+\b', title_locator) or '业务规则' in title_locator or 'business rule' in title_locator:
        candidates = {path: text for path, text in corpus.items() if path.endswith('business-rules.md')}
    elif 'skill.md' in title_locator:
        candidates = {path: text for path, text in corpus.items() if path.endswith('/SKILL.md')}
    else:
        raise SystemExit(
            f'{case_id}: source locator must identify an explicit source filename: {locator}'
        )

    if not candidates:
        raise SystemExit(f'{case_id}: source locator does not resolve to an available source file: {locator}')
    if not any(normalized_quote in text for text in candidates.values()):
        raise SystemExit(f'{case_id}: quoted_evidence cannot be found in the source selected by title/locator ({title!r}, {locator!r})')

def main() -> int:
    if not OUTPUT.is_dir():
        raise SystemExit(f"Builder output directory not found: {OUTPUT}")

    case_schema = load_schema(CASE_SCHEMA_PATH)
    manifest_schema = load_schema(MANIFEST_SCHEMA_PATH)
    case_validator = jsonschema.Draft202012Validator(
        case_schema, format_checker=jsonschema.FormatChecker()
    )
    manifest_validator = jsonschema.Draft202012Validator(
        manifest_schema, format_checker=jsonschema.FormatChecker()
    )

    source_corpus = load_source_corpus()
    source_map = load_source_map(OUTPUT, source_corpus)
    source_evidence_verified = 0
    dataset_files = sorted(OUTPUT.rglob("*.jsonl"))
    if not dataset_files:
        raise SystemExit("Builder did not produce any JSONL dataset files")

    all_cases: dict[str, dict] = {}
    datasets: dict[str, list[dict]] = defaultdict(list)
    # All tags are checked for referential integrity and forbidden needs_info tags.
    # Only candidate cases contribute to effective/full coverage.
    coverage_tag_counts: dict[str, int] = defaultdict(int)
    coverage_counts: dict[str, int] = defaultdict(int)
    case_file_count = {}
    file_dataset_ids: dict[str, set[str]] = defaultdict(set)

    for path in dataset_files:
        file_count = 0
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc

            errors = sorted(case_validator.iter_errors(case), key=lambda e: list(e.path))
            if errors:
                details = "; ".join(
                    f"{'/'.join(map(str, error.path)) or '$'}: {error.message}"
                    for error in errors[:8]
                )
                raise SystemExit(f"{path}:{line_no}: Dataset Schema validation failed: {details}")

            case_id = case["case_id"]
            if case_id in all_cases:
                raise SystemExit(f"Duplicate case_id across datasets: {case_id}")
            if case["quality_status"] not in ALLOWED_QUALITY:
                raise SystemExit(
                    f"Case {case_id} quality_status must remain candidate/needs_info, "
                    f"got {case['quality_status']}"
                )
            execution_status = case["execution_requirements"]["status"]
            if execution_status not in ALLOWED_EXECUTION:
                raise SystemExit(
                    f"Case {case_id} has unsupported execution_status {execution_status}"
                )

            require_nonempty_value(case.get("user_input"), f"{case_id}.user_input")
            require_nonempty_value(case.get("expected_behavior"), f"{case_id}.expected_behavior")
            require_nonempty_collection(case.get("preconditions"), f"{case_id}.preconditions")
            if "forbidden_behavior" not in case or not isinstance(case["forbidden_behavior"], list):
                raise SystemExit(f"Case {case_id} must declare forbidden_behavior as a list")
            require_nonempty_collection(case.get("source_refs"), f"{case_id}.source_refs")

            execution = case["execution_requirements"]
            for field in ("required_permissions", "allowed_actions", "steps",
                          "observable_assertions", "forbidden_side_effects"):
                require_nonempty_collection(execution.get(field), f"{case_id}.execution_requirements.{field}")
            require_nonempty_collection(execution.get("environment"), f"{case_id}.execution_requirements.environment")
            require_nonempty_value(execution.get("initial_state"), f"{case_id}.execution_requirements.initial_state")
            environment = execution["environment"]
            initial_state = execution["initial_state"]
            if environment.get("app_url") != "http://127.0.0.1:4173":
                raise SystemExit(f"{case_id}: app_url must target the local Workboard fixture")
            case_budget = environment.get("case_timeout_seconds")
            if type(case_budget) is not int or not 1 <= case_budget <= 900:
                raise SystemExit(f"{case_id}: case_timeout_seconds must be an integer from 1 to 900")
            server_state = initial_state.get("server_state") or environment.get("server_state_at_start") or "running"
            if server_state != "running":
                raise SystemExit(f"{case_id}: this pilot runner supports server_state=running only")
            for field in ("expected_end_state", "reset_plan", "cleanup_plan", "failure_cleanup"):
                require_nonempty_value(execution.get(field), f"{case_id}.execution_requirements.{field}")

            grading = case["grading"]
            if not grading.get("uncertainty_policy"):
                raise SystemExit(f"Case {case_id} grading lacks an explicit UNKNOWN policy")
            if not grading.get("pass_conditions") or not grading.get("fail_conditions"):
                raise SystemExit(f"Case {case_id} grading lacks PASS/FAIL conditions")
            if not grading.get("evidence_required"):
                raise SystemExit(f"Case {case_id} grading lacks required evidence")
            for criterion in grading.get("criteria", []):
                for field in ("criterion_id", "description", "pass_condition", "fail_condition", "evidence_required"):
                    if not criterion.get(field):
                        raise SystemExit(f"Case {case_id} grading criterion lacks {field}")

            for source in case.get("source_refs", []):
                require_nonempty_text(source.get("title"), f"{case_id}.source_refs.title")
                require_nonempty_text(source.get("locator"), f"{case_id}.source_refs.locator")
                verify_source_evidence(case_id, source, source_corpus, source_map)
                source_evidence_verified += 1

            all_cases[case_id] = case
            datasets[case["dataset_id"]].append(case)
            file_dataset_ids[path.relative_to(OUTPUT).as_posix()].add(case["dataset_id"])
            for tag in case.get("coverage_tags", []):
                item_id = tag["coverage_item_id"]
                coverage_tag_counts[item_id] += 1
                if case["quality_status"] == "candidate":
                    coverage_counts[item_id] += 1
            file_count += 1

        if file_count == 0:
            raise SystemExit(f"Dataset file contains no cases: {path}")
        relative_dataset_path = path.relative_to(OUTPUT).as_posix()
        if len(file_dataset_ids[relative_dataset_path]) != 1:
            raise SystemExit(f"Dataset file must contain cases from exactly one dataset: {relative_dataset_path}")
        case_file_count[relative_dataset_path] = file_count

    manifest_files = sorted(
        path for path in OUTPUT.rglob("*.json")
        if path.name.casefold().endswith(".manifest.json")
    )
    if not manifest_files:
        raise SystemExit("Builder did not produce a dataset Manifest JSON file")

    manifests: dict[str, dict] = {}
    manifest_path_by_id: dict[str, str] = {}
    for path in manifest_files:
        manifest = load_json(path)
        errors = sorted(manifest_validator.iter_errors(manifest), key=lambda e: list(e.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(map(str, error.path)) or '$'}: {error.message}"
                for error in errors[:8]
            )
            raise SystemExit(f"{path}: Manifest Schema validation failed: {details}")

        dataset_id = manifest["dataset_id"]
        if dataset_id in manifests:
            raise SystemExit(f"Duplicate Manifest dataset_id: {dataset_id}")
        if manifest["quality_status"] not in ALLOWED_QUALITY:
            raise SystemExit(
                f"Manifest {dataset_id} quality_status must remain candidate/needs_info"
            )
        if manifest["execution_status"] not in ALLOWED_EXECUTION:
            raise SystemExit(
                f"Manifest {dataset_id} execution_status must be NOT_RUN before any real execution"
            )

        owned_cases = datasets.get(dataset_id, [])
        if not owned_cases:
            raise SystemExit(f"Manifest {dataset_id} has no corresponding generated cases")
        if manifest["case_count"] != len(owned_cases):
            raise SystemExit(
                f"Manifest {dataset_id} case_count={manifest['case_count']} "
                f"but found {len(owned_cases)} generated cases"
            )
        manifests[dataset_id] = manifest
        manifest_path_by_id[dataset_id] = path.relative_to(OUTPUT).as_posix()

    suite_manifest_path = OUTPUT / "SUITE-MANIFEST.json"
    if not suite_manifest_path.is_file():
        raise SystemExit("Builder output lacks SUITE-MANIFEST.json")
    suite_manifest = load_json(suite_manifest_path)
    for field in ("suite_id", "version", "built_at", "evaluation_target"):
        require_nonempty_text(suite_manifest.get(field), f"SUITE-MANIFEST.json.{field}")
    suite_coverage = suite_manifest.get("coverage")
    require_nonempty_collection(suite_coverage, "SUITE-MANIFEST.json.coverage")
    require_nonempty_collection(suite_coverage.get("dimensions"), "SUITE-MANIFEST.json.coverage.dimensions")
    suite_entries = suite_manifest.get("datasets")
    if not isinstance(suite_entries, list) or not suite_entries:
        raise SystemExit("SUITE-MANIFEST.json must contain a non-empty datasets array")
    if suite_manifest.get("case_count") != len(all_cases):
        raise SystemExit(
            f"Suite Manifest case_count={suite_manifest.get('case_count')} "
            f"but found {len(all_cases)} generated cases"
        )
    if suite_manifest.get("quality_status") not in ALLOWED_QUALITY:
        raise SystemExit("Suite Manifest quality_status must remain candidate/needs_info")
    if suite_manifest.get("execution_status") not in ALLOWED_EXECUTION:
        raise SystemExit("Suite Manifest execution_status must be NOT_RUN before any real execution")

    suite_dataset_ids = set()
    for entry in suite_entries:
        if not isinstance(entry, dict):
            raise SystemExit("Each Suite Manifest dataset entry must be an object")
        dataset_id = entry.get("dataset_id")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise SystemExit("Suite Manifest dataset entry has an invalid dataset_id")
        if dataset_id in suite_dataset_ids:
            raise SystemExit(f"Duplicate dataset_id in Suite Manifest: {dataset_id}")
        suite_dataset_ids.add(dataset_id)
        require_nonempty_text(entry.get("purpose"), f"SUITE-MANIFEST.json.datasets[{dataset_id}].purpose")
        if entry.get("quality_status") not in ALLOWED_QUALITY:
            raise SystemExit(f"Suite Manifest dataset {dataset_id} quality_status must remain candidate/needs_info")
        if entry.get("execution_status") not in ALLOWED_EXECUTION:
            raise SystemExit(f"Suite Manifest dataset {dataset_id} execution_status must be NOT_RUN")
        jsonl_relative = entry.get("jsonl")
        manifest_relative = entry.get("manifest")
        if not isinstance(jsonl_relative, str) or not isinstance(manifest_relative, str):
            raise SystemExit(f"Suite Manifest {dataset_id} must reference JSONL and Manifest paths")
        jsonl_path = Path(jsonl_relative)
        manifest_path = Path(manifest_relative)
        for relative, label in ((jsonl_path, "jsonl"), (manifest_path, "manifest")):
            if relative.is_absolute() or ".." in relative.parts:
                raise SystemExit(f"Suite Manifest {dataset_id} has unsafe {label} path: {relative}")
        jsonl_key = jsonl_path.as_posix()
        manifest_key = manifest_path.as_posix()
        if jsonl_key not in case_file_count:
            raise SystemExit(f"Suite Manifest {dataset_id} references missing JSONL: {jsonl_key}")
        if file_dataset_ids[jsonl_key] != {dataset_id}:
            raise SystemExit(f"Suite Manifest {dataset_id} JSONL contains different dataset IDs")
        if entry.get("case_count") != case_file_count[jsonl_key]:
            raise SystemExit(f"Suite Manifest {dataset_id} case_count does not match JSONL")
        if manifest_path_by_id.get(dataset_id) != manifest_key:
            raise SystemExit(f"Suite Manifest {dataset_id} references the wrong dataset Manifest")
        if manifests[dataset_id]["case_count"] != case_file_count[jsonl_key]:
            raise SystemExit(f"Dataset Manifest {dataset_id} case_count does not match JSONL")

    if suite_dataset_ids != set(datasets):
        raise SystemExit(
            f"Suite Manifest dataset IDs do not match generated datasets: "
            f"suite={sorted(suite_dataset_ids)}, generated={sorted(datasets)}"
        )

    if set(datasets) != set(manifests):
        missing = sorted(set(datasets) - set(manifests))
        orphaned = sorted(set(manifests) - set(datasets))
        raise SystemExit(
            f"Dataset/Manifest IDs do not match; missing_manifests={missing}; "
            f"manifests_without_cases={orphaned}"
        )

    coverage_files = [p for p in OUTPUT.rglob("*") if p.is_file() and "coverage" in p.name.casefold()]
    coverage_matrix_files = [p for p in coverage_files if p.name.casefold() == "coverage-matrix.json"]
    if len(coverage_matrix_files) != 1:
        raise SystemExit("Builder output must contain exactly one coverage-matrix.json")
    coverage_matrix = load_json(coverage_matrix_files[0])
    if coverage_matrix.get("suite_id") != suite_manifest.get("suite_id"):
        raise SystemExit("Coverage matrix suite_id does not match SUITE-MANIFEST.json")
    if coverage_matrix.get("version") != suite_manifest.get("version"):
        raise SystemExit("Coverage matrix version does not match SUITE-MANIFEST.json")
    coverage_items = coverage_matrix.get("items")
    if not isinstance(coverage_items, list) or not coverage_items:
        raise SystemExit("coverage-matrix.json must contain a non-empty items array")
    coverage_item_by_id = {}
    for item in coverage_items:
        if not isinstance(item, dict):
            raise SystemExit("Coverage matrix items must be objects")
        item_id = item.get("coverage_item_id")
        if not isinstance(item_id, str) or not item_id.strip() or item_id in coverage_item_by_id:
            raise SystemExit(f"Invalid or duplicate coverage_item_id: {item_id!r}")
        if item.get("applicability") not in {"applicable", "not_applicable", "needs_info"}:
            raise SystemExit(f"{item_id}: invalid applicability value")
        if item["applicability"] != "applicable":
            require_nonempty_text(item.get("notes"), f"{item_id}.notes")
            if coverage_tag_counts.get(item_id, 0) > 0:
                raise SystemExit(f"{item_id}: not_applicable/needs_info item must not be tagged by a case")
        if item["applicability"] == "needs_info" and suite_manifest.get("quality_status") != "needs_info":
            raise SystemExit(f"{item_id}: suite quality_status must be needs_info")
        coverage_item_by_id[item_id] = item

    unknown_coverage_tags = sorted(set(coverage_tag_counts) - set(coverage_item_by_id))
    if unknown_coverage_tags:
        raise SystemExit(f"Cases reference unknown coverage items: {unknown_coverage_tags}")
    gap_priorities = suite_manifest["coverage"].get("gap_priorities") or []
    gap_by_id = {
        gap.get("gap_id"): gap
        for gap in gap_priorities
        if isinstance(gap, dict) and isinstance(gap.get("gap_id"), str)
    }
    if len(gap_by_id) != len(gap_priorities):
        raise SystemExit("Suite Manifest gap_priorities contains invalid or duplicate gap IDs")

    matrix_dimensions = {
        item.get("dimension"): item
        for item in coverage_matrix.get("dimensions", [])
        if isinstance(item, dict) and isinstance(item.get("dimension"), str)
    }
    suite_dimensions = {
        item.get("dimension"): item
        for item in suite_manifest["coverage"].get("dimensions", [])
        if isinstance(item, dict) and isinstance(item.get("dimension"), str)
    }
    if set(matrix_dimensions) != set(suite_dimensions):
        raise SystemExit("Coverage matrix and Suite Manifest dimensions do not match")

    for dimension, matrix_summary in matrix_dimensions.items():
        applicable_items = [
            item for item in coverage_items
            if item.get("dimension") == dimension and item.get("applicability") == "applicable"
        ]
        covered_items = [
            item for item in applicable_items
            if coverage_counts.get(item["coverage_item_id"], 0) > 0
        ]
        uncovered_items = [
            item for item in applicable_items
            if coverage_counts.get(item["coverage_item_id"], 0) == 0
        ]
        expected_uncovered = {
            f"{item['coverage_item_id']} {item.get('value', '')}".strip()
            for item in uncovered_items
        }
        for summary in (matrix_summary, suite_dimensions[dimension]):
            if summary.get("total") != len(applicable_items):
                raise SystemExit(f"{dimension}: coverage total does not match applicable items")
            if summary.get("covered") != len(covered_items):
                raise SystemExit(f"{dimension}: covered count does not match case coverage tags")
            if set(summary.get("uncovered", [])) != expected_uncovered:
                raise SystemExit(f"{dimension}: uncovered list does not match coverage items")
            expected_rate = (len(covered_items) / len(applicable_items)) if applicable_items else None
            actual_rate = summary.get("coverage_rate")
            if expected_rate is None:
                if actual_rate is not None:
                    raise SystemExit(f"{dimension}: coverage_rate must be null when total is zero")
            elif not isinstance(actual_rate, (int, float)) or abs(actual_rate - expected_rate) > 0.0001:
                raise SystemExit(f"{dimension}: coverage_rate does not match covered/total")

        for item in uncovered_items:
            gap = gap_by_id.get(item["coverage_item_id"])
            if gap is None:
                raise SystemExit(
                    f"Applicable coverage gap lacks a Suite Manifest gap_priority: {item['coverage_item_id']}"
                )
            if gap.get("priority") not in {"critical", "high", "medium", "low"}:
                raise SystemExit(f"{item['coverage_item_id']}: gap priority must be critical/high/medium/low")
            require_nonempty_text(gap.get("reason"), f"{item['coverage_item_id']}.gap_priority.reason")
            require_nonempty_text(gap.get("planned_action"), f"{item['coverage_item_id']}.gap_priority.planned_action")

    source_files = [p for p in OUTPUT.rglob("*") if p.is_file() and "source" in p.name.casefold()]
    quality_reports = [
        p for p in OUTPUT.rglob("*")
        if p.is_file() and "quality" in p.name.casefold()
        and p.suffix.lower() in {".md", ".json"}
    ]
    if not coverage_files:
        raise SystemExit("Builder output lacks a coverage matrix or coverage report")
    if not source_files:
        raise SystemExit("Builder output lacks a source map or source traceability file")
    if not quality_reports:
        raise SystemExit("Builder output lacks a quality report")
    report_templates = [
        p for p in OUTPUT.rglob("*")
        if p.is_file() and "template" in p.name.casefold()
        and p.suffix.lower() in {".md", ".json"}
    ]
    if not report_templates:
        raise SystemExit("Builder output lacks the requested report template")

    transient_files = [
        path.relative_to(OUTPUT).as_posix()
        for path in OUTPUT.rglob("*")
        if path.is_file() and (path.suffix.lower() == ".pyc" or "__pycache__" in path.parts)
    ]
    if transient_files:
        raise SystemExit(
            "Builder output contains Python cache artifacts: " + ", ".join(transient_files[:10])
        )

    summary = {
        "status": "PASS",
        "scope": "builder_output_validation_only",
        "formal_evaluation_cases_created_by_validator": False,
        "dataset_count": len(datasets),
        "case_count": len(all_cases),
        "case_files": case_file_count,
        "manifest_files": [p.relative_to(OUTPUT).as_posix() for p in manifest_files],
        "datasets": {
            dataset_id: {
                "case_count": len(cases),
                "manifest_quality_status": manifests[dataset_id]["quality_status"],
                "execution_status": manifests[dataset_id]["execution_status"],
            }
            for dataset_id, cases in sorted(datasets.items())
        },
        "coverage_item_counts": dict(sorted(coverage_counts.items())),
        "all_case_coverage_tag_counts": dict(sorted(coverage_tag_counts.items())),
        "schema_errors": 0,
        "source_evidence_refs_verified": source_evidence_verified,
        "source_evidence_check": "source_id resolved through the manifest-declared source map; source path/title/type matched; source SHA-256 verified against the exact archived Builder input; exact normalized quote rechecked in that source file",
        "quality_status_gate": "candidate/needs_info",
        "execution_status_gate": "NOT_RUN",
        "unknown_policy_gate": "present_in_every_case",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except jsonschema.SchemaError as exc:
        print(f"Invalid repository schema: {exc}", file=sys.stderr)
        raise SystemExit(2)
