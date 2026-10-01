"""Interpretable fixed-candidate ranking policies for SynBioCrow 2.4.2."""
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
from .adapters import AdaptedRoute

@dataclass(frozen=True)
class RankingPolicy:
    policy_id: str
    weights: Dict[str,float]

BASELINE_2D=RankingPolicy("v24-baseline-2d",{"structural_2d":1.0})
REACTION_EVIDENCE=RankingPolicy("v24-2d-reaction-evidence",{"structural_2d":1.0,"reaction_evidence_fraction":0.5,"rhea_exact_fraction":0.5})
ENZYME_EVIDENCE=RankingPolicy("v24-2d-enzyme-evidence",{"structural_2d":1.0,"reviewed_enzyme_fraction":0.75})
ENGINE_AGREEMENT=RankingPolicy("v24-2d-engine-agreement",{"structural_2d":1.0,"engine_count":0.10})
COMBINED=RankingPolicy("v24-combined-provisional",{
 "structural_2d":1.0,"reaction_evidence_fraction":0.35,
 "reviewed_enzyme_fraction":0.50,"rhea_exact_fraction":0.35,
 "thermo_coverage_fraction":0.20,"engine_count":0.05,
 "unsupported_edge_count":-0.10,
})
POLICIES=(BASELINE_2D,REACTION_EVIDENCE,ENZYME_EVIDENCE,ENGINE_AGREEMENT,COMBINED)

def score(route: AdaptedRoute, policy: RankingPolicy) -> Tuple[float,int]:
    """Return score and number of weighted features that were actually observed."""
    f=route.features
    total=0.0; observed=0
    for name,w in policy.weights.items():
        value=getattr(f,name,None)
        if value is None: continue
        total += w*float(value); observed += 1
    return total,observed

def rank(routes: Iterable[AdaptedRoute], policy: RankingPolicy) -> List[dict]:
    rows=[]
    for r in routes:
        s,n=score(r,policy)
        rows.append({"route_id":r.route_id,"score":s,"observed_weighted_features":n})
    rows.sort(key=lambda x:(-x["score"],x["route_id"]))
    for i,row in enumerate(rows,1): row["rank"]=i
    return rows
