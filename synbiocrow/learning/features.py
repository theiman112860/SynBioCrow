from __future__ import annotations
from collections import Counter
from synbiocrow.ensemble.graph import EnsembleGraph

def route_feature_vector(graph:EnsembleGraph, edge_ids:list[str])->dict[str,float]:
    edges=[graph.edges[eid] for eid in edge_ids]
    backends=sorted({b for e in edges for b in e.source_backends})
    composite=sum(1 for e in edges if len(e.source_backends)>1)
    features={
        "route_length":float(len(edges)),
        "backend_diversity":float(len(backends)),
        "composite_edges":float(composite),
        "single_backend_fraction":(
            sum(1 for e in edges if len(e.source_backends)==1)/len(edges)
            if edges else 0.0
        ),
    }
    for backend in backends:
        features[f"backend:{backend}"]=float(
            sum(1 for e in edges if backend in e.source_backends)
        )
    return features

def route_feature_matrix(graph:EnsembleGraph,routes:list[list[str]])->dict[str,dict[str,float]]:
    return {
        f"route-{i:04d}":route_feature_vector(graph,route)
        for i,route in enumerate(routes)
    }


def evidence_aware_route_feature_vector(
    graph: EnsembleGraph,
    edge_ids: list[str],
    evidence_report=None,
)->dict[str,float]:
    """Route features for bounded DBTL learning.

    Extends graph-topology features with Test-stage evidence fractions.
    Missing evidence remains explicit and never becomes positive evidence.
    """
    features=route_feature_vector(graph,edge_ids)
    if evidence_report is None:
        features.update({
            "closure_pass_fraction":0.0,
            "rhea_pass_fraction":0.0,
            "thermo_pass_fraction":0.0,
            "enzyme_pass_fraction":0.0,
            "evidence_pass_fraction":0.0,
            "evidence_abstain_fraction":1.0 if edge_ids else 0.0,
            "evidence_fail_fraction":0.0,
        })
        return features

    from synbiocrow.evidence.gates import GateDecision
    reports=list(getattr(evidence_report,"edge_reports",()) or ())
    if not reports:
        return evidence_aware_route_feature_vector(graph,edge_ids,None)

    def frac(attr,decision):
        vals=[getattr(getattr(r,attr), "decision", None) for r in reports]
        return sum(v is decision for v in vals)/len(vals)

    overall=[getattr(r,"overall",None) for r in reports]
    features.update({
        "closure_pass_fraction":frac("closure",GateDecision.PASS),
        "rhea_pass_fraction":frac("rhea",GateDecision.PASS),
        "thermo_pass_fraction":frac("thermodynamics",GateDecision.PASS),
        "enzyme_pass_fraction":frac("enzyme",GateDecision.PASS),
        "evidence_pass_fraction":sum(v is GateDecision.PASS for v in overall)/len(overall),
        "evidence_abstain_fraction":sum(v is GateDecision.ABSTAIN for v in overall)/len(overall),
        "evidence_fail_fraction":sum(v is GateDecision.FAIL for v in overall)/len(overall),
    })
    return features
