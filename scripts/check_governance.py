#!/usr/bin/env python3
"""Fail-closed governance checker; does not certify scientific readiness."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["AGENTS.md", "PROJECT_STATUS.md", "ACCEPTANCE_TESTS.md", "FAILURE_LEDGER.md", "ENGINE_REGISTRY.yaml", "DEFERRED_BACKLOG.md"]
errors = []
for name in REQUIRED:
    path = ROOT / name
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        errors.append(f"Missing/empty: {name}")
status = (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8") if (ROOT / "PROJECT_STATUS.md").exists() else ""
for milestone in range(1, 7):
    if not re.search(rf"\bM{milestone}\b", status):
        errors.append(f"Missing milestone M{milestone} in status")
for token in ["Goal", "Context", "Constraints", "Done-when"]:
    if token not in (ROOT / "AGENTS.md").read_text(encoding="utf-8"):
        errors.append(f"Missing contract field {token}")
if "NOT YET COMPLETE" not in status and "Canonical source" not in status:
    errors.append("Missing source reconciliation declaration")
if errors:
    print("GOVERNANCE FAIL")
    for error in errors:
        print("-", error)
    sys.exit(1)
print("GOVERNANCE STRUCTURE PASS; scientific and runtime acceptance NOT assessed")
