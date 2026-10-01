"""Historical SynBioCrow 2.3 benchmark-bundle adapter.

This module reconstructs persisted ensemble routes from a frozen 2.3 benchmark
bundle without invoking candidate generation and without using benchmark truth
for model selection.

The route edge IDs are reproduced by the released v2.3.0 reaction-graph code.
Any mismatch is treated as an integrity failure.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple
from zipfile import ZipFile

from synbiocrow.core.models import LifecycleState, PathwayCandidate, ReactionStep
from synbiocrow.ensemble.graph import build_reaction_graph

from .adapters import AdaptedRoute
from .evidence import EvidenceLevel, ReactionEvidence, RankingFeatureVector, aggregate_route_evidence


@dataclass(frozen=True)
class Historical23RouteSet:
    target_id: str
    target_name: str
    run_id: str
    routes: Tuple[AdaptedRoute, ...]
    candidate_count: int
    edge_count: int


def _candidate_from_dict(raw: Mapping) -> PathwayCandidate:
    steps = tuple(
        ReactionStep(
            reaction=s["reaction"],
            rule_id=s.get("rule_id"),
            source_backend=s.get("source_backend"),
            feasibility=s.get("feasibility"),
            metadata=dict(s.get("metadata") or {}),
        )
        for s in raw.get("steps", [])
    )
    state = raw.get("lifecycle", "CANDIDATE")
    try:
        lifecycle = LifecycleState(state)
    except Exception:
        lifecycle = LifecycleState.CANDIDATE
    return PathwayCandidate(
        candidate_id=str(raw["candidate_id"]),
        target_smiles=str(raw.get("target_smiles") or ""),
        steps=steps,
        source_backends=tuple(raw.get("source_backends") or ()),
        lifecycle=lifecycle,
        provenance=dict(raw.get("provenance") or {}),
        evidence=dict(raw.get("evidence") or {}),
    )


def _tuple_string(value) -> Tuple[str, ...]:
    if value in (None, "", [], {}):
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(x) for x in value if x not in (None, ""))
    return (str(value),)


def _edge_evidence(edge) -> ReactionEvidence:
    ecs = set()
    rhea_ids = set()
    reviewed = set()
    literature = set()
    mapping_values = []
    thermo = None
    thermo_units = None
    for prov in edge.provenance:
        if not isinstance(prov, Mapping):
            continue
        for key in ("ec_number", "ec", "ec_numbers"):
            for v in _tuple_string(prov.get(key)):
                if v and v not in {"[NOEC]", "NOEC"}:
                    ecs.add(v)
        for key in ("rhea_id", "rhea", "rhea_ids"):
            rhea_ids.update(_tuple_string(prov.get(key)))
        for key in ("uniprot", "uniprot_id", "uniprot_ids", "protein_accessions"):
            reviewed.update(_tuple_string(prov.get(key)))
        for key in ("doi", "pmid", "literature_ids", "references"):
            literature.update(_tuple_string(prov.get(key)))
        for key in ("mapping_confidence", "map_confidence"):
            if prov.get(key) not in (None, ""):
                try:
                    mapping_values.append(float(prov[key]))
                except Exception:
                    pass
        if thermo is None and prov.get("thermo_dg") not in (None, ""):
            try:
                thermo = float(prov["thermo_dg"])
                thermo_units = prov.get("thermo_units")
            except Exception:
                pass

        # RetroBioCat2 stores enzyme choices/precedents inside nested metadata.
        tm = prov.get("template_metadata")
        if isinstance(tm, Mapping):
            for payload in tm.values():
                if not isinstance(payload, Mapping):
                    continue
                for e in payload.get("possible_enzymes") or ():
                    if e and str(e).lower() != "chemical":
                        ecs.add("enzyme-class:" + str(e))

        for prec in prov.get("precedents") or ():
            if not isinstance(prec, Mapping):
                continue
            pid = prec.get("precedent_id")
            if pid:
                literature.add(str(pid))
            data = prec.get("data")
            if isinstance(data, Mapping):
                if data.get("html_doi"):
                    literature.add(str(data["html_doi"]))
                if data.get("enzyme_name"):
                    reviewed.add("precedent-enzyme:" + str(data["enzyme_name"]))

    level = EvidenceLevel.UNKNOWN
    if reviewed:
        level = EvidenceLevel.REVIEWED
    elif literature:
        level = EvidenceLevel.LITERATURE
    elif rhea_ids or ecs:
        level = EvidenceLevel.DATABASE
    elif thermo is not None:
        level = EvidenceLevel.CALCULATED

    return ReactionEvidence(
        reaction_id=edge.edge_id,
        engines=tuple(edge.source_backends),
        rhea_exact=True if rhea_ids else None,
        rhea_connectivity=True if rhea_ids else None,
        ec_numbers=tuple(sorted(ecs)),
        reviewed_uniprot=tuple(sorted(reviewed)),
        literature_ids=tuple(sorted(literature)),
        thermo_dg=thermo,
        thermo_units=thermo_units,
        mapping_confidence=(sum(mapping_values) / len(mapping_values) if mapping_values else None),
        evidence_level=level,
        provenance=tuple(
            ["edge:" + edge.edge_id]
            + ["candidate:" + x for x in edge.candidate_ids]
            + ["rule:" + x for x in edge.rule_ids]
        ),
    )


def _adapt_verified_route(route_id: str, edge_ids: List[str], graph) -> AdaptedRoute:
    evidence = tuple(_edge_evidence(graph.edges[eid]) for eid in edge_ids)
    agg = aggregate_route_evidence(route_id, evidence)
    n = max(1, len(evidence))
    maps = [r.mapping_confidence for r in evidence if r.mapping_confidence is not None]
    features = RankingFeatureVector(
        route_id=route_id,
        structural_2d=None,
        structural_3d=None,
        reaction_evidence_fraction=agg.supported_reactions / n,
        reviewed_enzyme_fraction=agg.reviewed_enzyme_reactions / n,
        rhea_exact_fraction=agg.rhea_exact_reactions / n,
        thermo_coverage_fraction=agg.thermo_covered_reactions / n,
        engine_count=len(agg.independent_engines),
        route_length=len(evidence),
        unsupported_edge_count=len(evidence) - agg.supported_reactions,
        mapping_confidence_mean=(sum(maps) / len(maps) if maps else None),
    )
    return AdaptedRoute(route_id, evidence, features, "synbiocrow_2_3_persisted_route")


def load_historical_23_routes(bundle_path: str) -> List[Historical23RouteSet]:
    """Load only persisted generation outputs from the 2.3 breadth benchmark.

    Truth/scoring artifacts are intentionally not consumed here.
    """
    out: List[Historical23RouteSet] = []
    with ZipFile(bundle_path) as z:
        manifest = json.loads(z.read("benchmark_manifest.json"))
        if manifest.get("truth_accessed") is not False:
            raise ValueError("historical bundle does not assert truth_accessed=false")

        target_files = sorted(n for n in z.namelist() if n.startswith("targets/") and n.endswith(".json"))
        for target_file in target_files:
            target = json.loads(z.read(target_file))
            ensemble = (target.get("arms") or {}).get("ensemble") or {}
            run_id = ensemble.get("run_id")
            if not run_id:
                continue
            result_path = f"state/{run_id}/result.json"
            if result_path not in z.namelist():
                continue
            result = json.loads(z.read(result_path))
            candidates = [_candidate_from_dict(x) for x in result.get("candidates", [])]
            graph = build_reaction_graph(candidates)
            persisted_routes = result.get("routes") or []

            adapted = []
            for i, edge_ids in enumerate(persisted_routes):
                missing = [eid for eid in edge_ids if eid not in graph.edges]
                if missing:
                    raise ValueError(
                        f"{target.get('target_id')} route {i}: persisted edge IDs "
                        f"do not reconstruct: {missing}"
                    )
                adapted.append(
                    _adapt_verified_route(
                        f"{target.get('target_id')}::ensemble::{i:04d}",
                        list(edge_ids),
                        graph,
                    )
                )

            expected_edges = ((result.get("graph_summary") or {}).get("edge_count"))
            if expected_edges is not None and int(expected_edges) != len(graph.edges):
                raise ValueError(
                    f"{target.get('target_id')}: reconstructed edge_count "
                    f"{len(graph.edges)} != persisted {expected_edges}"
                )

            out.append(
                Historical23RouteSet(
                    target_id=str(target.get("target_id")),
                    target_name=str(target.get("target_name")),
                    run_id=str(run_id),
                    routes=tuple(adapted),
                    candidate_count=len(candidates),
                    edge_count=len(graph.edges),
                )
            )
    return out
