"""Verify the supplied M1.16 evidence archive without running archived code."""
import argparse
import collections
import hashlib
import json
import zipfile
from pathlib import Path

from rdkit import Chem

ARCHIVE_SHA256 = "adb0a3ea2cd381caffcad1a3b3341e6450548bb2907d521adbdeff8d9a100078"
COUNTS = {"DORAnet": 170, "AiZynthFinder": 31, "BioPKS": 1,
          "RetroBioCat2": 15, "RetroPath2": 724}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check(path):
    require(hashlib.sha256(path.read_bytes()).hexdigest() == ARCHIVE_SHA256,
            "M1.16 archive SHA256 mismatch")
    with zipfile.ZipFile(path) as archive:
        def read(name):
            return json.loads(archive.read("outputs/" + name))

        rows = read("fresh_native_reactions.json")
        counts = dict(collections.Counter(row["engine"] for row in rows))
        require(counts == COUNTS, f"Unexpected archived exporter counts: {counts}")
        members = {name: hashlib.sha256(archive.read("outputs/" + name)).hexdigest()
                   for name in sorted({row["native_file"] for row in rows})}
        parsed = {smiles: Chem.MolFromSmiles(smiles) is not None for smiles in
                  {item for row in rows for side in ("reactants", "products")
                   for item in row[side].split(".")}}
        require(all(parsed.values()), "Invalid molecule in archived reaction export")
        usable = read("m116_acceptance/usable_reactions.json")
        quarantined = read("m116_acceptance/quarantined_reactions.json")
        require(len(usable) == 216 and len(quarantined) == 725, "Quarantine counts changed")
        require(sorted(row["index"] for row in usable + quarantined) == list(range(len(rows))),
                "Archived acceptance classification is incomplete or duplicated")
        require({row["engine"] for row in quarantined} == {"RetroPath2", "BioPKS"},
                "Quarantine engine identities changed")

        solved = {}
        for member in members:
            if "AiZynthFinder/" not in member:
                continue
            payload = read(member)
            target = Chem.MolToSmiles(Chem.MolFromSmiles(payload["target_smiles"]))
            native = set()

            def walk(node):
                for reaction in node.get("children", []):
                    require(reaction["type"] == "reaction", "Unexpected native tree node")
                    precursors = reaction["children"]
                    native.add(".".join(child["smiles"] for child in precursors) + ">>" + node["smiles"])
                    for child in precursors:
                        walk(child)

            for route in payload["routes"]:
                tree = route["tree"]
                require(Chem.MolToSmiles(Chem.MolFromSmiles(tree["smiles"])) == target,
                        "AiZynthFinder tree does not match its target")
                walk(tree)
            emitted = {row["reaction_smiles"] for row in rows if row["native_file"] == member}
            require(emitted == native, "AiZynthFinder tree/export regression")
            solved[target] = sum(route["route_metadata"]["is_solved"] for route in payload["routes"])

        retrotide = "native/RetroTide/external_evidence/native_design_release_records.json"
        biopks = "native/BioPKS/external_evidence/0_native_design_release_records.json"
        members[retrotide] = hashlib.sha256(archive.read("outputs/" + retrotide)).hexdigest()
        designs = {name: read(member) for name, member in (("BioPKS", biopks), ("RetroTide", retrotide))}
        require(all(len(records) == 113 for records in designs.values()), "PKS design counts changed")
        require(sum(row["exact_target_match"] for row in designs["BioPKS"]) == 1,
                "BioPKS release match changed")
        require(all(row["native_retrotide_designPKS_called"] and not row["native_te_called"]
                    for row in designs["RetroTide"]), "RetroTide native contract changed")
        gates = read("m116_acceptance/acceptance_gates.json")
        require(not any(value for value in gates.values() if isinstance(value, bool)),
                "Unexpected archived acceptance claim")
        return {"gate": "PASS_HISTORICAL_EVIDENCE", "archive_sha256": ARCHIVE_SHA256,
                "archived_export_counts": counts, "usable": len(usable), "quarantined": len(quarantined),
                "valid_smiles_count": len(parsed), "aizynthfinder_solved_routes": solved,
                "native_member_sha256": members, "archived_gates": gates}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.archive), indent=2, sort_keys=True))
