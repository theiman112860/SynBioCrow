"""SynBioCrow 2.4.21 bounded development-only reranking experiment."""
from __future__ import annotations
from typing import Mapping,Any
from synbiocrow.v24.native_discrimination_2_4_16 import DEFAULT_WEIGHTS,merge_and_rank

VARIANTS={
 "frozen_2_4_16":dict(DEFAULT_WEIGHTS),
 "no_short_route_bias":{**DEFAULT_WEIGHTS,"route_length_penalty":0.0},
 "consensus_positive":{**DEFAULT_WEIGHTS,
   "route_length_penalty":0.20,
   "precedent_step_fraction":1.00,
   "template_metadata_fraction":0.35,
   "reaction_domain_fraction":0.25,
   "reaction_type_fraction":0.25},
}

def rerank(native_rows:list[dict],enriched_rows:list[dict]|None=None)->dict[str,list[dict]]:
    return {name:merge_and_rank(native_rows,enriched_rows,weights=w) for name,w in VARIANTS.items()}

def evaluate_variant(rows:list[dict],audit_by_id:Mapping[str,Mapping[str,Any]],record_ids:set[str])->dict:
    by={}
    for x in rows:
        if x["record_id"] in record_ids:by.setdefault(x["record_id"],[]).append(x)
    out={}
    for rid,rr in by.items():
        ar=audit_by_id[rid]
        sim={x["candidate_id"]:x.get("internal_anchor_similarity_mean") for x in ar["candidate_audit"]}
        scored=[]
        for x in rr:
            cid=str(x["route_id"]).removeprefix("candidate:")
            s=sim.get(cid)
            if s is not None:scored.append((float(s),int(x["rank"]),cid))
        best=max(scored,key=lambda z:(z[0],-z[1])) if scored else (None,None,None)
        top={}
        for k in (1,5,10,50,100):
            vals=[s for s,r,_ in scored if r<=k]
            top[str(k)]=max(vals) if vals else None
        out[rid]={"best_similarity":best[0],"best_similarity_rank":best[1],
                  "best_similarity_candidate":best[2],"topk_max_similarity":top}
    return out
