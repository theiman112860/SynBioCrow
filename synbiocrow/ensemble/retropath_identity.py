from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from synbiocrow.ensemble.graph import EnsembleGraph, ReactionEdge
from synbiocrow.ensemble.identity import resolve_compound

@dataclass(frozen=True)
class RetroPathIdentityRecord:
    identifier: str
    smiles: str
    source: str = "retropath_mapping"

def load_identity_csv(path: str | Path) -> dict[str, RetroPathIdentityRecord]:
    """Load identifier→SMILES mappings.

    Required columns: identifier, smiles. Extra columns are ignored.
    """
    out = {}
    with Path(path).open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ident = str(row.get("identifier", "")).strip()
            smiles = str(row.get("smiles", "")).strip()
            if ident and smiles:
                out[ident] = RetroPathIdentityRecord(ident, smiles)
    return out

def resolve_retropath_graph_identities(
    graph: EnsembleGraph,
    mapping: Mapping[str, RetroPathIdentityRecord],
) -> EnsembleGraph:
    """Return a new graph with mapped RetroPath raw IDs canonicalized.

    Unmapped identifiers stay unchanged and source-scoped.
    """
    key_map = {}
    new = EnsembleGraph()

    for old_key, ident in graph.compounds.items():
        record = mapping.get(ident.display) if ident.source == "retropath2" else None
        if record is not None:
            resolved = resolve_compound(record.smiles, source="retropath2")
        else:
            resolved = ident
        key_map[old_key] = resolved.key
        new.compounds.setdefault(resolved.key, resolved)

    for edge in graph.edges.values():
        parent = key_map.get(edge.parent_key, edge.parent_key)
        precursors = tuple(sorted(key_map.get(k, k) for k in edge.precursor_keys))
        payload = "\n".join([parent, *precursors])
        import hashlib
        eid = "rxn:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
        compounds = [new.compounds[parent], *(new.compounds[k] for k in precursors)]
        new.add_edge(
            ReactionEdge(
                edge_id=eid,
                parent_key=parent,
                precursor_keys=precursors,
                reaction=edge.reaction,
                rule_ids=edge.rule_ids,
                source_backends=edge.source_backends,
                candidate_ids=edge.candidate_ids,
                provenance=edge.provenance + ({"identity_resolution": "retropath_mapping"},),
            ),
            compounds,
        )

    for key in list(new.by_parent):
        new.by_parent[key] = sorted(set(new.by_parent[key]))
    return new
