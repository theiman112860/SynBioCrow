#!/usr/bin/env python3
"""Offline governance contract check; does not claim seven native engines ran."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "AGENTS.md": ["Goal", "Context", "Constraints", "Done-when", "DORAnet", "AiZynthFinder", "ChemEnzyRetroPlanner", "RetroBioCat2", "RetroPath2", "BioPKS", "RetroTide", "FAILURE_LEDGER.md"],
    "ACCEPTANCE.md": ["PASS_REPRODUCED", "PASS_HISTORICAL_EVIDENCE", "FAIL", "NOT_VERIFIED", "all seven"],
    "FAILURE_LEDGER.md": ["AiZynth", "RetroPath2", "PKS"],
}
errors = []
for filename, tokens in REQUIRED.items():
    path = ROOT / filename
    if not path.is_file():
        errors.append(f"Missing {filename}")
        continue
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token.lower() not in text.lower():
            errors.append(f"{filename}: missing required term {token!r}")
baseline = ROOT / "core_certification" / "baseline.json"
if baseline.is_file():
    data = json.loads(baseline.read_text(encoding="utf-8"))
    if data.get("decision") == "CERTIFIED":
        gates = data.get("gates", {})
        if not gates or any(value != "PASS_REPRODUCED" for value in gates.values()):
            errors.append("CERTIFIED requires all gates PASS_REPRODUCED")
print(json.dumps({"check": "governance-contract", "status": "FAIL" if errors else "PASS", "errors": errors}, indent=2))
sys.exit(1 if errors else 0)
