"""Compare captured native runs and exercise SynBioCrow's reaction graph."""
import argparse
import csv
import gzip
import hashlib
import json
import zipfile
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


def inventory(species):
    atoms = Counter()
    charge = 0
    for molecule in species:
        for atom in Chem.AddHs(molecule).GetAtoms():
            atoms[atom.GetAtomicNum()] += 1
            charge += atom.GetFormalCharge()
    return atoms, charge


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


def aizynth_records(root, attempt):
    directory = root / f"aizynth-{attempt}"
    result = {}
    paths = {}
    for path in sorted(directory.glob("*_native_routes.json")):
        payload = read(path)
        target = canonical(payload["target_smiles"])
        paths[target] = path
        rows = []

        def walk(node):
            require(node["type"] == "mol", "Unexpected AiZynthFinder molecule node")
            for reaction in node.get("children", []):
                require(reaction["type"] == "reaction", "Unexpected AiZynthFinder reaction node")
                children = reaction["children"]
                pair = (tuple(sorted(canonical(child["smiles"]) for child in children)),
                        (canonical(node["smiles"]),))
                require(pair[0], "AiZynthFinder reaction is missing precursors")
                rows.append((pair, reaction["metadata"]["template_hash"]))
                for child in children:
                    walk(child)

        for route in payload["routes"]:
            tree = route["tree"]
            require(canonical(tree["smiles"]) == target, "AiZynthFinder route target changed")
            require(route["route_metadata"]["is_solved"], "AiZynthFinder route is unsolved")
            walk(tree)
        require(rows and len(rows) == len(payload["native_reaction_nodes"]),
                "AiZynthFinder native reaction count mismatch")
        result[target] = rows
    require(set(result) == {canonical(target) for target in TARGETS},
            "AiZynthFinder evidence is missing a target")
    return paths, result


def pks_designs(root, engine):
    expected_targets = {canonical(smiles) for smiles in (*TARGETS, "CCCCCC(=O)O")}
    identities = []
    summary = {}
    for attempt in (1, 2):
        rows = read(root / f"{engine}-{attempt}.json")
        require({canonical(row["target_smiles"]) for row in rows} == expected_targets,
                f"{engine} is missing a native target")
        matches = Counter()
        keys = []
        for row in rows:
            target = canonical(row["target_smiles"])
            product = row.get("native_release_product_smiles")
            exact = product is not None and canonical(product) == target
            require(exact == row["exact_target_match"], f"{engine} release mismatch")
            require(row["native_te_called"] == (engine == "biopks"), f"{engine} TE call status changed")
            if engine == "retrotide":
                require(row["native_retrotide_designPKS_called"], "Native RetroTide call missing")
            if exact:
                matches[target] += 1
            keys.append((target, canonical(row["native_bound_smiles"]), row["round"],
                         product, row["score"]))
        identities.append(Counter(keys))
        summary = {"native_designs": len(rows), "native_release_calls": sum(
            row["native_te_called"] for row in rows), "exact_released_targets": dict(matches)}
    require(identities[0] == identities[1], f"{engine} typed native designs did not reproduce")
    return summary


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


def master_campaign(root):
    with zipfile.ZipFile(root / "master-native-evidence.zip") as archive:
        report_bytes = archive.read("summary.json")
        require(report_bytes == (root / "master-campaign-summary.json").read_bytes(),
                "Master campaign summary mismatch")
        report = json.loads(report_bytes)
        source_summaries = ("master-initial-summary.json", "master-retrobiocat2-retry-summary.json")
        require([digest(root / name) for name in source_summaries] == report["source_run_summary_sha256"],
                "Master campaign source run hash mismatch")
        rows = json.loads(archive.read("fresh_native_reactions.json"))
        native_digests = {name: hashlib.sha256(archive.read(name)).hexdigest()
                          for name in {row["native_file"] for row in rows}}
        require(len(rows) == report["fresh_native_records"] and
                all(row["native_sha256"] == native_digests[row["native_file"]] and
                    row["native_pointer"] and row["fresh_native"] for row in rows),
                "Master output lost source provenance")
        for engine, state in report["engine_states"].items():
            require(state["run"]["status"] == "PROCESS_PASS", f"{engine} did not execute")
            if "specialist_evidence" in state:
                evidence = state["specialist_evidence"]
                require(hashlib.sha256(archive.read(evidence["evidence_file"])).hexdigest()
                        == evidence["evidence_sha256"], f"{engine} specialist provenance mismatch")
        gates = json.loads(archive.read("m116_acceptance/acceptance_gates.json"))
        require(gates == read(root / "master-acceptance-gates.json"),
                "Master campaign gates mismatch")
    return {"engines_completed": sorted(report["engine_states"]),
            "native_candidate_rows": len(rows),
            "execution": report["seven_engine_execution_gate"],
            "multi_engine_target_pathway": gates["complete_multi_engine_target_pathway_demonstrated"]}


def main(root):
    summary = {"doranet": verify_doranet(root, replay=True),
               "master_campaign": master_campaign(root)}
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

    (aizynth_paths, first), (_, second) = (aizynth_records(root, attempt) for attempt in (1, 2))
    require({target: Counter(rows) for target, rows in first.items()}
            == {target: Counter(rows) for target, rows in second.items()},
            "AiZynthFinder native reaction identities did not reproduce")
    summary["aizynthfinder"] = {target: len(rows) for target, rows in first.items()}
    for target, rows in first.items():
        source_sha = digest(aizynth_paths[target])
        for index, ((substrates, products), rule) in enumerate(rows):
            candidates.append(PathwayCandidate(
                f"aizynthfinder:{target}:{index}", target,
                (ReactionStep(" + ".join(substrates) + " = " + " + ".join(products), rule,
                              "aizynthfinder", metadata={"retrosynthetic_parent_side": "right",
                                                         "source_sha256": source_sha,
                                                         "source_engine": "aizynthfinder"}),),
                ("aizynthfinder",),
            ))
    for engine in ("biopks", "retrotide"):
        summary[engine] = pks_designs(root, engine)

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
    balance = {}
    for candidate in candidates:
        step, = candidate.steps
        left, right = ([Chem.MolFromSmiles(smiles) for smiles in side.split(" + ")]
                       for side in step.reaction.split(" = "))
        if any(atom.GetAtomicNum() == 0 for molecule in left + right
               for atom in molecule.GetAtoms()):
            unresolved[step.source_backend] += 1
            continue
        eligible.append(candidate)
        counts = balance.setdefault(step.source_backend, {"balanced": 0, "unbalanced": 0})
        counts["balanced" if inventory(left) == inventory(right) else "unbalanced"] += 1
    summary["explicit_atom_and_charge_balance"] = balance
    graph = build_reaction_graph(eligible)
    for target in TARGETS:
        key = resolve_compound(target).key
        backends = {backend for edge_id in graph.by_parent[key]
                    for backend in graph.edges[edge_id].source_backends}
        require(backends == {"doranet", "retrobiocat2", "chemenzyretroplanner", "aizynthfinder"},
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
