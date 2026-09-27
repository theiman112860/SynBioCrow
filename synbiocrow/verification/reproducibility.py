from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from synbiocrow.core.models import PathwayCandidate, ReactionStep, LifecycleState
from synbiocrow.ensemble import build_reaction_graph, resolve_compound
from synbiocrow.execution.state import stable_hash
from synbiocrow.sequence import ProteinEvidence, CDSEvidence, translate_dna
from synbiocrow.cassette import RegulatoryPart
from synbiocrow.design import design_expression_construct

@dataclass(frozen=True)
class ReproducibilityPanelReport:
    passed: bool
    checks: dict[str,bool]
    metrics: dict[str,Any]
    digest: str

def _candidate(cid:str,backend:str,reaction:str)->PathwayCandidate:
    return PathwayCandidate(
        candidate_id=cid,
        target_smiles="CCO",
        steps=(ReactionStep(
            reaction=reaction,
            source_backend=backend,
            metadata={"retrosynthetic_parent_side":"left"},
        ),),
        source_backends=(backend,),
    )

def run_reproducibility_panel()->ReproducibilityPanelReport:
    # Panel A: cross-engine route exists only after graph union.
    candidates=[
        _candidate("dora-fixture","doranet","CCO = CC=O"),
        _candidate("rbc-fixture","retrobiocat2","CC=O = CC"),
    ]
    graph=build_reaction_graph(candidates)
    target=resolve_compound("CCO",source="panel").key
    sink={resolve_compound("CC",source="panel").key}
    routes=graph.find_routes(target,sink,max_steps=3,max_routes=10)

    # Panel B: duplicate chemistry merges provenance.
    dup_graph=build_reaction_graph([
        _candidate("dup-a","doranet","CCO = CC=O"),
        _candidate("dup-b","retrobiocat2","CCO = CC=O"),
    ])
    dup_edge=next(iter(dup_graph.edges.values())) if len(dup_graph.edges)==1 else None

    # Panel C: deterministic digital construct design.
    protein=ProteinEvidence("PANEL-P","fixture",sequence="MKT",reviewed=True)
    cds=CDSEvidence("PANEL-CDS","fixture",cds_sequence="ATGAAAACC",protein_accession="PANEL-P")
    promoter=RegulatoryPart("PANEL-PROM","promoter","TTGACA","fixture")
    rbs=RegulatoryPart("PANEL-RBS","rbs","AGGAGG","fixture")
    terminator=RegulatoryPart("PANEL-TERM","terminator","TTTTGC","fixture")
    construct=design_expression_construct(
        pathway_id="panel-route",
        protein=protein,
        cds=cds,
        promoter=promoter,
        rbs=rbs,
        terminator=terminator,
    )

    checks={
        "cross_engine_route_recovered":len(routes)==1 and len(routes[0])==2,
        "graph_has_two_backends":graph.backend_set()==("doranet","retrobiocat2"),
        "duplicate_edge_merged":(
            dup_edge is not None
            and dup_edge.source_backends==("doranet","retrobiocat2")
            and set(dup_edge.candidate_ids)=={"dup-a","dup-b"}
        ),
        "construct_translation_preserved":(
            translate_dna(construct.optimization.dna_sequence).rstrip("*")=="MKT"
        ),
        "construct_candidate_only":(
            construct.cassette.candidate.lifecycle is LifecycleState.CANDIDATE
        ),
        "construct_validation_exact":construct.validation.exact_match,
    }
    metrics={
        "route_count":len(routes),
        "route_edge_count":len(routes[0]) if routes else 0,
        "graph_compounds":len(graph.compounds),
        "graph_edges":len(graph.edges),
        "duplicate_graph_edges":len(dup_graph.edges),
        "construct_id":construct.cassette.candidate.cassette_id,
        "optimized_cds":construct.optimization.dna_sequence,
        "optimized_cds_gc_percent":round(construct.optimized_cds_qc.gc_percent,6),
    }
    digest=stable_hash({"checks":checks,"metrics":metrics})
    return ReproducibilityPanelReport(all(checks.values()),checks,metrics,digest)
