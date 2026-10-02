"""SynBioCrow 2.4.21 consensus-positive development reranker.

Uses only ranking features with positive Spearman association to corrected
internal-anchor proximity in BOTH ranking-limited development targets.
No numeric weight fitting is performed; shared-positive features receive equal
weight after within-target percentile transformation. The frozen 2.4.16 score
is retained only as a deterministic secondary tie-breaker.
"""
from __future__ import annotations
from typing import Mapping,Any
import math

CONSENSUS_FEATURES=(
 "route_length",
 "precedent_step_fraction",
 "template_metadata_fraction",
 "reaction_domain_fraction",
 "reaction_type_fraction",
)

def _percentiles(values:list[float])->list[float]:
    if not values:return []
    order=sorted(range(len(values)),key=lambda i:(values[i],i))
    out=[0.0]*len(values);i=0;n=len(values)
    while i<n:
        j=i+1
        while j<n and values[order[j]]==values[order[i]]:j+=1
        pct=((i+j-1)/2)/(n-1) if n>1 else 0.5
        for k in order[i:j]:out[k]=pct
        i=j
    return out

def rerank_target(rows:list[dict])->list[dict]:
    transformed={f:[None]*len(rows) for f in CONSENSUS_FEATURES}
    for f in CONSENSUS_FEATURES:
        idx=[];vals=[]
        for i,r in enumerate(rows):
            v=r.get(f)
            try:
                v=float(v)
                if math.isfinite(v):idx.append(i);vals.append(v)
            except Exception:pass
        p=_percentiles(vals)
        for i,x in zip(idx,p):transformed[f][i]=x

    out=[]
    for i,r in enumerate(rows):
        vals=[transformed[f][i] for f in CONSENSUS_FEATURES if transformed[f][i] is not None]
        score=sum(vals)/len(vals) if vals else None
        q=dict(r)
        q["consensus_positive_score"]=score
        q["consensus_positive_feature_coverage"]=len(vals)/len(CONSENSUS_FEATURES)
        q["consensus_positive_components"]={f:transformed[f][i] for f in CONSENSUS_FEATURES}
        out.append(q)
    out.sort(key=lambda r:(
        -(r["consensus_positive_score"] if r["consensus_positive_score"] is not None else -1e9),
        -(float(r.get("coverage_adjusted_score")) if r.get("coverage_adjusted_score") is not None else -1e9),
        int(r.get("rank") or 10**9),
        r["route_id"],
    ))
    for i,r in enumerate(out,1):
        r["rank_2_4_21"]=i
    return out

def rerank_all(rows:list[dict],record_ids:set[str])->list[dict]:
    by={}
    for r in rows:
        if r["record_id"] in record_ids:by.setdefault(r["record_id"],[]).append(r)
    out=[]
    for rid in sorted(by):out.extend(rerank_target(by[rid]))
    return out
