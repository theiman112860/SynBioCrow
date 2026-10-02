"""SynBioCrow 2.4.20 development-only ranking feature attribution."""
from __future__ import annotations
from typing import Any
import math

FEATURES=("rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length")

def _rank(v):
    idx=sorted(range(len(v)),key=lambda i:(v[i],i));r=[0.0]*len(v);i=0
    while i<len(idx):
        j=i+1
        while j<len(idx) and v[idx[j]]==v[idx[i]]:j+=1
        q=(i+j-1)/2+1
        for k in idx[i:j]:r[k]=q
        i=j
    return r
def pearson(x,y):
    if len(x)<3:return None
    mx=sum(x)/len(x);my=sum(y)/len(y)
    a=sum((u-mx)*(v-my) for u,v in zip(x,y));b=sum((u-mx)**2 for u in x);c=sum((v-my)**2 for v in y)
    return a/math.sqrt(b*c) if b>0 and c>0 else None
def spearman(x,y):return pearson(_rank(x),_rank(y))
def attribute(ranked:list[dict],audit:list[dict],record_id:str)->dict:
    rr={str(x["route_id"]).removeprefix("candidate:"):x for x in ranked if x["record_id"]==record_id}
    aa={x["candidate_id"]:x for x in audit}
    joined=[]
    for cid,a in aa.items():
        r=rr.get(cid); y=a.get("internal_anchor_similarity_mean")
        if r is not None and y is not None:joined.append((r,float(y)))
    feats=[]
    for f in FEATURES:
        pairs=[]
        for r,y in joined:
            v=r.get(f)
            if v is not None:
                try:
                    v=float(v)
                    if math.isfinite(v):pairs.append((v,y))
                except Exception:pass
        rho=spearman([p[0] for p in pairs],[p[1] for p in pairs]) if len(pairs)>=3 else None
        feats.append({"feature":f,"n":len(pairs),"coverage":len(pairs)/len(joined) if joined else 0.0,"spearman_vs_internal_anchor_similarity":rho})
    feats.sort(key=lambda x:-(abs(x["spearman_vs_internal_anchor_similarity"]) if x["spearman_vs_internal_anchor_similarity"] is not None else -1))
    return {"record_id":record_id,"joined_candidate_count":len(joined),"feature_attribution":feats}
