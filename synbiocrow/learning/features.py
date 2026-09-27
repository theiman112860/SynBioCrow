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
