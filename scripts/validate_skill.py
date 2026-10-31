#!/usr/bin/env python3
"""Structural validator for Evaluation Dataset Builder."""
from pathlib import Path
import json, re, sys
root=Path(__file__).resolve().parents[1]
errors=[]
def check(ok,msg):
    if not ok: errors.append(msg)
p=root/"SKILL.md"
check(p.exists(),"SKILL.md missing")
if p.exists():
    s=p.read_text(encoding="utf-8")
    check(s.startswith("---\n"),"SKILL.md must start with YAML frontmatter")
    parts=s.split("---",2)
    if len(parts)>=3:
        fm=parts[1]
        m=re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$",fm)
        d=re.search(r"(?m)^description:\s*(.+)$",fm)
        check(bool(m),"name missing or invalid kebab-case")
        check(bool(d),"description missing")
        if m: check(len(m.group(1))<=64,"name exceeds 64 chars")
        if d: check(len(d.group(1))<=1024,"description exceeds 1024 chars")
    check(len(s.splitlines())<=500,"SKILL.md exceeds recommended 500 lines")
for rel in ["references/quality-standard.md","references/quality-standard.yaml","references/dataset-schema.json","references/grader-guidelines.md","references/coverage-design-guideline.md","references/source-and-evidence-policy.md","tests/self-eval-cases.json"]:
    check((root/rel).is_file(),f"missing {rel}")
try:
    schema=json.loads((root/"references/dataset-schema.json").read_text())
    check(bool(schema.get("required")),"schema required fields missing")
except Exception as e: errors.append(f"schema JSON invalid: {e}")
try:
    suite=json.loads((root/"tests/self-eval-cases.json").read_text())
    cases=suite["cases"]; ids=[c["id"] for c in cases]
    check(len(cases)>=10,"self-eval suite needs at least 10 cases")
    check(len(ids)==len(set(ids)),"duplicate self-eval IDs")
    check(all(c.get("prompt") and c.get("expected") for c in cases),"incomplete self-eval case")
except Exception as e: errors.append(f"self-eval JSON invalid: {e}")
try:
    import yaml
    cfg=yaml.safe_load((root/"references/quality-standard.yaml").read_text())
    check(sum(cfg["scoring"]["weights"].values())==100,"quality weights must sum to 100")
except ImportError:
    print("WARN: PyYAML unavailable; YAML validation skipped")
except Exception as e: errors.append(f"quality YAML invalid: {e}")
if errors:
    print("FAIL\n"+"\n".join("- "+x for x in errors)); sys.exit(1)
print("PASS: structural checks")
print("NOTE: semantic behavior requires model-based execution of tests/self-eval-cases.json")
