#!/usr/bin/env python3
"""Structural and packaging validator for Evaluation Dataset Builder."""
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
warnings = []

def check(condition, message):
    if not condition:
        errors.append(message)

def read_json(relative):
    try:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{relative} is invalid or unreadable: {exc}")
        return None

# Release metadata
version_file = ROOT / "VERSION"
check(version_file.is_file(), "VERSION missing")
version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else ""
check(bool(re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version)), "VERSION must be semantic version x.y.z")
for rel in ["README.md", "CHANGELOG.md", "RELEASE.md", "LICENSE", "SKILL.md"]:
    check((ROOT / rel).is_file(), f"{rel} missing")

# Skill frontmatter and size
skill_path = ROOT / "SKILL.md"
skill_text = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
check(skill_text.startswith("---\n"), "SKILL.md must start with YAML frontmatter")
parts = skill_text.split("---", 2)
if len(parts) >= 3:
    frontmatter = parts[1].strip()
    name = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", frontmatter)
    description = re.search(r"(?m)^description:\s*(.+)$", frontmatter)
    check(bool(name), "name missing or invalid kebab-case")
    check(bool(description), "description missing")
    if name:
        check(len(name.group(1)) <= 64, "name exceeds 64 chars")
    if description:
        check(len(description.group(1)) <= 1024, "description exceeds 1024 chars")
check(len(skill_text.splitlines()) <= 500, "SKILL.md exceeds recommended 500 lines")

# Referenced knowledge and test assets
required_files = [
    "references/quality-standard.md", "references/quality-standard.yaml",
    "references/dataset-schema.json", "references/grader-guidelines.md",
    "references/coverage-design-guideline.md", "references/source-and-evidence-policy.md",
    "tests/self-eval-cases.json", "tests/trigger-evals.json", "tests/README.md",
    "scripts/validate_skill.py"
]
for rel in required_files:
    check((ROOT / rel).is_file(), f"required file missing: {rel}")
for rel in re.findall(r"references/[A-Za-z0-9._-]+|tests/[A-Za-z0-9._-]+", skill_text):
    check((ROOT / rel).is_file(), f"SKILL.md references missing file: {rel}")

schema = read_json("references/dataset-schema.json")
if schema:
    check(schema.get("type") == "object", "case schema root must be object")
    check(bool(schema.get("required")), "case schema required fields missing")

suite = read_json("tests/self-eval-cases.json")
if suite:
    cases = suite.get("cases", [])
    ids = [case.get("id") for case in cases]
    check(len(cases) >= 10, "self-eval suite needs at least 10 cases")
    check(len(ids) == len(set(ids)), "duplicate self-eval IDs")
    check(all(case.get("prompt") and case.get("expected") for case in cases), "incomplete self-eval case")

trigger_suite = read_json("tests/trigger-evals.json")
if trigger_suite:
    evals = trigger_suite.get("evals", [])
    check(len(evals) >= 10, "trigger eval suite needs at least 10 queries")
    check(any(item.get("should_trigger") is True for item in evals), "trigger suite needs positive examples")
    check(any(item.get("should_trigger") is False for item in evals), "trigger suite needs negative examples")
    check(all(item.get("query") and isinstance(item.get("should_trigger"), bool) for item in evals), "invalid trigger eval entry")

try:
    import yaml
    cfg = yaml.safe_load((ROOT / "references/quality-standard.yaml").read_text(encoding="utf-8"))
    weights = cfg["scoring"]["weights"]
    check(sum(weights.values()) == 100, "quality weights must sum to 100")
    check(all(0 < value <= 100 for value in weights.values()), "quality weights must be positive and <= 100")
    check(len(cfg["scoring"]["critical_gates"]) >= 1, "critical gates missing")
except ImportError:
    warnings.append("PyYAML unavailable; YAML validation skipped")
except Exception as exc:
    errors.append(f"quality YAML invalid: {exc}")

if errors:
    print("FAIL\n" + "\n".join("- " + error for error in errors))
    sys.exit(1)
for warning in warnings:
    print("WARN: " + warning)
print(f"PASS: structural/package checks (version {version})")
print("NOTE: semantic behavior requires model-based execution of tests/self-eval-cases.json")
