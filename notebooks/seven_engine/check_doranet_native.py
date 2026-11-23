"""Run the real DORAnet adapter twice per target and verify reaction identity."""
import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from rdkit import Chem

from synbiocrow import DesignRequest, design


TARGETS = ("CCCC=O", "O=C(O)CCO")


def canonical(smiles):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"Invalid native SMILES: {smiles}")
    return Chem.MolToSmiles(molecule)


def identities(rows, target):
    expected = canonical(target)
    result = []
    for row in rows:
        step, = row["steps"]
        left, right = step["reaction"].split(" = ")
        parents = sorted(canonical(smiles) for smiles in left.split(" + "))
        products = sorted(canonical(smiles) for smiles in right.split(" + "))
        if expected not in parents or step["metadata"]["direction"] != "retro":
            raise ValueError(f"Native reaction does not originate at {target}")
        if row["source_backends"] not in (["doranet"], ("doranet",)):
            raise ValueError("Unexpected native provenance")
        if len(row["provenance"]["native_network_sha256"]) != 64:
            raise ValueError("Missing native network hash")
        result.append((parents, products, step["rule_id"]))
    return sorted(result)


def verify(out, *, replay=False):
    if not replay:
        out.mkdir(parents=True)
    summary = {}
    for target in TARGETS:
        repeat_identities = []
        for repeat in (1, 2):
            file = out / f"doranet-{target}-{repeat}.json"
            if not replay:
                result = design(DesignRequest(target_smiles=target, backend_ids=("doranet",)),
                                resume=False)
                if result.backend_status["doranet"]["status"] != "COMPLETE":
                    raise RuntimeError(result.backend_status["doranet"])
                rows = [asdict(row) for row in result.candidates]
                file.write_text(json.dumps(rows, sort_keys=True) + "\n")
            repeat_identities.append(identities(json.loads(file.read_text()), target))
        first, second = repeat_identities
        if not first or first != second:
            raise ValueError(f"Native DORAnet identities did not reproduce for {target}")
        summary[target] = {"candidates": len(first),
                           "reproducible_identity_sha256":
                               hashlib.sha256(json.dumps(first).encode()).hexdigest()}
    if not replay:
        (out / "doranet-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--replay", action="store_true", help="Verify saved native results")
    args = parser.parse_args()
    print(json.dumps(verify(args.directory, replay=args.replay), indent=2))
