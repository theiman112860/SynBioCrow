"""SynBioCrow 2.4.25 exact score-formula provenance audit.

Reproduces the frozen 2.4.16 score exactly and exposes each component,
normalization denominator, count-based coverage multiplier, and a diagnostic
weight-aware coverage alternative. No production ranking policy is changed.
"""
from __future__ import annotations
from typing import Mapping,Any
import math

DEFAULT_WEIGHTS={
 "rhea_connectivity_fraction":1.00,
 "ec_context_fraction":0.50,
 "reviewed_ec_context_fraction":0.30,
 "step_feasibility_mean":0.80,
 "step_feasibility_min":0.60,
 "filter_score_mean":0.55,
 "filter_score_min":0.35,
 "precedent_step_fraction":0.75,
 "rule_coverage_fraction":0.20,
 "template_metadata_fraction":0.20,
 "reaction_domain_fraction":0.15,
 "reaction_type_fraction":0.15,
 "route_length_penalty":-0.25,
}

def _clip01(v):
    if v is None:return None
    try:v=float(v)
    except Exception:return None
    if not math.isfinite(v):return None
    return max(0.0,min(1.0,v))

def normalized_components(row:Mapping[str,Any])->dict:
    x=dict(row)
    x["route_length_penalty"]=min(int(x.get("route_length") or 0),12)/12.0
    out={}
    for k in DEFAULT_WEIGHTS:
        v=x.get(k)
        if k!="route_length_penalty":
            v=_clip01(v)
        out[k]=v
    return out

def exact_score_provenance(row:Mapping[str,Any])->dict:
    comps=normalized_components(row)
    terms=[]
    numerator=0.0; observed_weight=0.0; observed=0
    total_abs_weight=sum(abs(w) for w in DEFAULT_WEIGHTS.values())
    for k,w in DEFAULT_WEIGHTS.items():
        v=comps.get(k)
        term=None if v is None else float(w)*float(v)
        if v is not None:
            numerator+=term
            observed_weight+=abs(float(w))
            observed+=1
        terms.append({
          "feature":k,"value":v,"weight":w,"weighted_term":term,
          "observed":v is not None,
        })
    raw=numerator/observed_weight if observed_weight else None
    count_coverage=observed/len(DEFAULT_WEIGHTS)
    exact_adjusted=raw*count_coverage if raw is not None else None
    weight_coverage=observed_weight/total_abs_weight if total_abs_weight else None
    weight_adjusted=raw*weight_coverage if raw is not None else None
    return {
      "route_id":row.get("route_id"),
      "persisted_raw_score":row.get("raw_score"),
      "persisted_coverage_adjusted_score":row.get("coverage_adjusted_score"),
      "reconstructed_numerator":numerator,
      "observed_abs_weight_denominator":observed_weight,
      "total_abs_weight":total_abs_weight,
      "observed_component_count":observed,
      "total_component_count":len(DEFAULT_WEIGHTS),
      "count_coverage":count_coverage,
      "weight_coverage":weight_coverage,
      "reconstructed_raw_score":raw,
      "reconstructed_count_adjusted_score":exact_adjusted,
      "diagnostic_weight_adjusted_score":weight_adjusted,
      "terms":terms,
    }

def close(a,b,tol=1e-12):
    if a is None or b is None:return a is b
    return abs(float(a)-float(b))<=tol

def verify_exact(row):
    p=exact_score_provenance(row)
    return {
      "raw_match":close(p["persisted_raw_score"],p["reconstructed_raw_score"]),
      "adjusted_match":close(p["persisted_coverage_adjusted_score"],p["reconstructed_count_adjusted_score"]),
      "provenance":p,
    }

def rerank_weight_coverage(rows:list[dict])->list[dict]:
    out=[]
    for r in rows:
        p=exact_score_provenance(r)
        q=dict(r)
        q["diagnostic_weight_adjusted_score"]=p["diagnostic_weight_adjusted_score"]
        q["count_coverage"]=p["count_coverage"]
        q["weight_coverage"]=p["weight_coverage"]
        out.append(q)
    out.sort(key=lambda x:(
      -(x["diagnostic_weight_adjusted_score"] if x["diagnostic_weight_adjusted_score"] is not None else -1e99),
      int(x.get("rank") or 10**9),x["route_id"]))
    for i,x in enumerate(out,1):x["diagnostic_weight_coverage_rank"]=i
    return out
