"""Compare captured native runs and exercise SynBioCrow's reaction graph."""
import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from rdkit import Chem
from synbiocrow.core.models import PathwayCandidate, ReactionStep
from synbiocrow.ensemble import build_reaction_graph
from synbiocrow.ensemble.identity import resolve_compound

from check_doranet_native import TARGETS, canonical, verify as verify_doranet


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(value, message):
    if not value:
        raise ValueError(message)


def normalize(reaction):
    left, right = reaction.split(">>")
    return tuple(tuple(sorted(canonical(smiles) for smiles in side.split(".")))
                 for side in (left, right))


def rbc2_records(root, attempt):
    path = root / f"retrobiocat2-{attempt}.json"
    result = {}
    payload = read(path)
    require(payload["status"] == "COMPLETED", "RetroBioCat2 run failed")
    for target in payload["targets"]:
        rows = []
        expected = canonical(target["smiles"])
        for row in target["reactions"]:
            pair = normalize(row["reaction_smiles"])
            require(expected in pair[1], f"RetroBioCat2 output does not produce {expected}")
            rows.append((pair, row["reaction_name"]))
        result[expected] = rows
    return path, result


def chemenzy_records(run, targets=TARGETS):
    raw, normalized = run / "routes.json", run / "reactions.json"
    status = read(run / "status.json")
    require(status["status"] == "NATIVE_OUTPUT", f"ChemEnzy run failed: {status}")
    for path, key in ((raw, "routes_sha256"), (normalized, "reactions_sha256"),
                      (run / "effective_config.json", "config_sha256")):
        require(digest(path) == status[key], f"ChemEnzy digest mismatch: {path}")
    data = read(raw)
    result = {}
    for row in read(normalized):
        target = canonical(row["target_smiles"])
        pair = normalize(row["reaction_smiles"])
        components = row["native_pointer"].lstrip("/").split("/")
        parent = data
        for item in components[:-2]:
            parent = parent[int(item)] if isinstance(parent, list) else parent[item]
        obj = parent["children"][int(components[-1])]
        require(pair[1] == (canonical(parent["smiles"]),),
                "ChemEnzy parser changed the native product")
        require(row["native_template"] == obj.get("template"),
                "ChemEnzy parser changed native template provenance")
        native_precursors = tuple(sorted(canonical(child["smiles"]) for child in obj["children"]))
        require(pair[0] == native_precursors, "ChemEnzy parser discarded or changed precursors")
        template = json.dumps(row["native_template"], sort_keys=True)
        result.setdefault(target, []).append((pair, template))
    for target in targets:
        expected = canonical(target)
        require(any(expected in pair[1] for pair, _ in result[expected]),
                f"ChemEnzy output lacks the requested target {target}")
    return raw, result


def retropath_records(root, attempt):
    targets = {"butanal": "CCCC=O", "3_hydroxypropionic_acid": "O=C(O)CCO"}
    result = {}
    for name, smiles in targets.items():
        path = root / f"retropath2-{attempt}-{name}.csv.gz"
        expected = Chem.MolToInchi(Chem.MolFromSmiles(smiles))
        with gzip.open(path, "rt", newline="") as stream:
            rows = list(csv.DictReader(stream))
        require(rows and all(row["Substrate InChI"] == expected for row in rows),
                f"RetroPath2 source-side identity changed for {name}")
        transitions = Counter((row["Substrate InChI"], row["Product InChI"]) for row in rows)
        rule_transitions = Counter((row["Rule ID"], row["Substrate InChI"], row["Product InChI"])
                                   for row in rows)
        result[name] = transitions, rule_transitions
    return result


def main(root):
    summary = {"doranet": verify_doranet(root, replay=True)}
    candidates = []
    for target in TARGETS:
        path = root / f"doranet-{target}-1.json"
        source_sha = digest(path)
        for record in read(path):
            for step in record["steps"]:
                candidates.append(PathwayCandidate(
                    record["candidate_id"], target,
                    (ReactionStep(step["reaction"], step["rule_id"], "doranet",
                                  metadata={**step["metadata"], "source_sha256": source_sha,
                                            "source_engine": "doranet"}),),
                    ("doranet",),
                ))
    rbc2_runs = [rbc2_records(root, attempt) for attempt in (1, 2)]
    chemenzy_runs = [chemenzy_records(root / f"chemenzy-{attempt}") for attempt in (1, 2)]
    for engine, runs in (("retrobiocat2", rbc2_runs), ("chemenzyretroplanner", chemenzy_runs)):
        (path, first), (_, second) = runs
        require({target: Counter(rows) for target, rows in first.items()}
                == {target: Counter(rows) for target, rows in second.items()},
                f"{engine} reaction identities did not reproduce")
        summary[engine] = {target: len(rows) for target, rows in sorted(first.items())}
        source_sha = digest(path)
        for target, rows in first.items():
            for index, ((substrates, products), rule) in enumerate(rows):
                candidates.append(PathwayCandidate(
                    f"{engine}:{target}:{index}", target,
                    (ReactionStep(" + ".join(substrates) + " = " + " + ".join(products),
                                  rule, engine, metadata={"retrosynthetic_parent_side": "right",
                                                         "source_sha256": source_sha,
                                                         "source_engine": engine}),),
                    (engine,),
                ))

    hexanoic = "CCCCCC(=O)O"
    _, master = chemenzy_records(root / "chemenzy-master", (*TARGETS, hexanoic))
    _, direct = chemenzy_records(root / "chemenzy-hex-repeat", (hexanoic,))
    require(Counter(master[hexanoic]) == Counter(direct[hexanoic]),
            "ChemEnzy master and standalone hexanoic outputs differ")
    summary["chemenzy_master_hexanoic"] = {
        "native_reaction_nodes": len(direct[hexanoic]),
        "native_routes": read(root / "chemenzy-master/status.json")["route_counts"][hexanoic],
    }

    first, second = (retropath_records(root, attempt) for attempt in (1, 2))
    expansions = {}
    for name, (transitions, rule_transitions) in first.items():
        repeated, repeated_rules = second[name]
        require(transitions == repeated, f"RetroPath2 compound transitions changed for {name}")
        expansions[name] = {
            "compound_transitions": sum(transitions.values()),
            "rule_attributions_only_in_run_1": sum((rule_transitions - repeated_rules).values()),
            "rule_attributions_only_in_run_2": sum((repeated_rules - rule_transitions).values()),
        }
    summary["retropath2_source_expansion"] = expansions
    eligible, unresolved = [], Counter()
    for candidate in candidates:
        step, = candidate.steps
        species = step.reaction.replace(" = ", " + ").split(" + ")
        if any(atom.GetAtomicNum() == 0
               for molecule in map(Chem.MolFromSmiles, species)
               for atom in molecule.GetAtoms()):
            unresolved[step.source_backend] += 1
        else:
            eligible.append(candidate)
    graph = build_reaction_graph(eligible)
    for target in TARGETS:
        key = resolve_compound(target).key
        backends = {backend for edge_id in graph.by_parent[key]
                    for backend in graph.edges[edge_id].source_backends}
        require(backends == {"doranet", "retrobiocat2", "chemenzyretroplanner"},
                f"Combined graph lost source engines for {target}: {backends}")
    for edge in graph.edges.values():
        require(set(edge.source_backends) == {item["source_engine"] for item in edge.provenance},
                "Combined reaction edge lost source attribution")
    summary["combined_graph"] = {
        "engines": graph.backend_set(), "edges": len(graph.edges),
        "composite_edges": graph.composite_edge_count(),
        "placeholder_rows_quarantined": dict(unresolved),
        "scope": "direction-explicit candidate output and provenance only",
    }
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(main(args.directory), indent=2, sort_keys=True))
