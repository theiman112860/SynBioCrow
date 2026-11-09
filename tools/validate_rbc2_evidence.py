"""Validate native RBC2 candidate evidence; no RBC2 dependency or fake chemistry.

Usage:
  python tools/validate_rbc2_evidence.py path/to/results.json O=C(O)CCO CCCC=O
"""
import json
import sys
from pathlib import Path

EXPECTED_COMMIT = "c5f32561b1ed99d0701a6dbb472dc448d6c082e8"


def validate(report, expected_targets):
    errors = []
    if report.get("engine") != "RetroBioCat2":
        errors.append("incorrect engine")
    if report.get("source_commit") != EXPECTED_COMMIT:
        errors.append("missing or unexpected upstream commit")
    targets = report.get("targets")
    if not isinstance(targets, list):
        return errors + ["targets must be a list"]
    by_smiles = {}
    for target in targets:
        if not isinstance(target, dict):
            errors.append("malformed target entry")
            continue
        smiles = target.get("smiles")
        if smiles in by_smiles:
            errors.append("duplicate target " + str(smiles))
        by_smiles[smiles] = target
    for smiles in expected_targets:
        target = by_smiles.get(smiles)
        if target is None:
            errors.append("missing target " + smiles)
            continue
        if target.get("status") != "NATIVE_EXECUTED":
            errors.append("native invocation not successful for " + smiles)
        reactions = target.get("reactions")
        if not isinstance(reactions, list) or not reactions:
            errors.append("no native reactions for " + smiles)
            continue
        if target.get("count") != len(reactions):
            errors.append("reaction count mismatch for " + smiles)
        for idx, reaction in enumerate(reactions):
            label = smiles + " reaction " + str(idx)
            if not isinstance(reaction, dict):
                errors.append("malformed " + label)
                continue
            if reaction.get("target_smiles") != smiles:
                errors.append("target mismatch in " + label)
            if reaction.get("engine") != "RetroBioCat2":
                errors.append("engine mismatch in " + label)
            if reaction.get("source_commit") != EXPECTED_COMMIT:
                errors.append("source mismatch in " + label)
            rs = reaction.get("reaction_smiles")
            if not isinstance(rs, str) or rs.count(">>") != 1 or not all(rs.split(">>")):
                errors.append("missing reaction SMILES in " + label)
            if reaction.get("reaction_smiles_parseable") is not True:
                errors.append("reaction SMILES not parseable in " + label)
            if reaction.get("candidate_only") is not True:
                errors.append("candidate-only provenance missing in " + label)
    return errors


def main(argv):
    if len(argv) < 3:
        print("Usage: validate_rbc2_evidence.py results.json TARGET_SMILES [TARGET_SMILES ...]")
        return 2
    try:
        report = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        errors = validate(report, argv[2:])
    except (OSError, ValueError, TypeError) as exc:
        print("FAIL: cannot read evidence:", exc)
        return 2
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print("PASS: RBC2 native candidate evidence structure for", len(argv) - 2, "targets")
    print("NOTE: not certification of stoichiometry, enzyme feasibility, or pathway closure")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
