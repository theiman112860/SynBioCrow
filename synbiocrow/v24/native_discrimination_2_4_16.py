"""SynBioCrow 2.4.16 dense generator-native evidence ranking.

Consumes persisted DEVELOPMENT candidate artifacts plus optional 2.4.15 evidence
enrichment.  No route generation, no validation/evaluation truth, no learned
weights without real development labels.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from typing import Any,Mapping,Iterable
import json,math

from synbiocrow.v24.discrimination_2_4_14 import load_development_artifact

def _nums(x:Any):
    out=[]
    if x is None:return out
    if isinstance(x,bool):return out
    if isinstance(x,(int,float)):
        try:
            v=float(x)
            if math.isfinite(v):out.append(v)
        except Exception:pass
        return out
    if isinstance(x,Mapping):
        for v in x.values():out.extend(_nums(v))
        return out
    if isinstance(x,(list,tuple,set)):
        for v in x:out.extend(_nums(v))
    return out

def _count_precedents(x:Any)->int:
    if x is None:return 0
    if isinstance(x,Mapping):return len(x)
    if isinstance(x,(list,tuple,set)):return len(x)
    if isinstance(x,str):return int(bool(x.strip()))
    return int(bool(x))

def _coverage(vals):
    return sum(bool(v) for v in vals)/len(vals) if vals else 0.0

def candidate_native_features(path:str|Path)->list[dict]:
    obj,cands=load_development_artifact(path)
    rows=[]
    for c in cands:
        feas=[]
        filt=[]
        precedent_counts=[]
        rule_cov=[]
        template_cov=[]
        domain_cov=[]
        type_cov=[]
        for s in c.steps:
            if s.feasibility is not None:
                try:
                    v=float(s.feasibility)
                    if math.isfinite(v):feas.append(v)
                except Exception:pass
            md=dict(s.metadata or {})
            filt.extend(_nums(md.get("feasability_filter_scores")))
            precedent_counts.append(_count_precedents(md.get("precedents")))
            rule_cov.append(bool(md.get("rule_smarts") or s.rule_id))
            template_cov.append(bool(md.get("template_metadata")))
            domain_cov.append(bool(md.get("rxn_domain")))
            type_cov.append(bool(md.get("rxn_type")))
        nsteps=len(c.steps)
        rows.append({
          "record_id":obj["record_id"],"target_name":obj["target_name"],
          "route_id":"candidate:"+c.candidate_id,"route_length":nsteps,
          "source_backends":list(c.source_backends),
          "step_feasibility_mean":sum(feas)/len(feas) if feas else None,
          "step_feasibility_min":min(feas) if feas else None,
          "step_feasibility_max":max(feas) if feas else None,
          "filter_score_mean":sum(filt)/len(filt) if filt else None,
          "filter_score_min":min(filt) if filt else None,
          "filter_score_max":max(filt) if filt else None,
          "precedent_total":sum(precedent_counts),
          "precedent_step_fraction":sum(x>0 for x in precedent_counts)/nsteps if nsteps else 0.0,
          "rule_coverage_fraction":_coverage(rule_cov),
          "template_metadata_fraction":_coverage(template_cov),
          "reaction_domain_fraction":_coverage(domain_cov),
          "reaction_type_fraction":_coverage(type_cov),
        })
    return rows

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

def merge_and_rank(native_rows:list[dict],enriched_rows:list[dict]|None=None,weights:Mapping[str,float]|None=None):
    weights=dict(DEFAULT_WEIGHTS if weights is None else weights)
    ext={(r["record_id"],r["route_id"]):r for r in (enriched_rows or [])}
    merged=[]
    for n in native_rows:
        x=dict(n); e=ext.get((n["record_id"],n["route_id"]),{})
        for k in ("rhea_connectivity_fraction","ec_context_fraction",
                  "reviewed_ec_context_fraction","evidence_query_coverage","unqueried_edge_count"):
            x[k]=e.get(k)
        x["route_length_penalty"]=min(int(x.get("route_length") or 0),12)/12.0
        comps={}
        for k in weights:
            v=x.get(k)
            if k.startswith("step_feasibility") or k.startswith("filter_score"):
                v=_clip01(v)
            elif k!="route_length_penalty":
                v=_clip01(v)
            comps[k]=v
        numer=denom=0.0; observed=0
        for k,w in weights.items():
            v=comps.get(k)
            if v is None:continue
            numer+=float(w)*float(v);denom+=abs(float(w));observed+=1
        coverage=observed/len(weights)
        raw=(numer/denom) if denom else None
        adjusted=(raw*coverage) if raw is not None else None
        x["component_values"]=comps
        x["observed_component_count"]=observed
        x["component_coverage"]=coverage
        x["raw_score"]=raw
        x["coverage_adjusted_score"]=adjusted
        merged.append(x)
    by={}
    for x in merged:by.setdefault(x["record_id"],[]).append(x)
    ranked=[]
    for rid,rows in sorted(by.items()):
        rows.sort(key=lambda x:(-(x["coverage_adjusted_score"] if x["coverage_adjusted_score"] is not None else -1e9),
                                -x["component_coverage"],x["route_length"],x["route_id"]))
        for i,x in enumerate(rows,1):
            y=dict(x);y["rank"]=i;ranked.append(y)
    return ranked

def load_enriched_rows(path:str|Path|None):
    if not path:return []
    p=Path(path)
    if not p.is_file():return []
    return json.loads(p.read_text())

def score_diversity(rows:list[dict])->dict:
    by={}
    for x in rows:
        by.setdefault(x["record_id"],[]).append(x)
    out={}
    for rid,rr in by.items():
        vals=[x["coverage_adjusted_score"] for x in rr if x["coverage_adjusted_score"] is not None]
        out[rid]={
          "route_count":len(rr),
          "distinct_score_count":len(set(round(v,12) for v in vals)),
          "score_min":min(vals) if vals else None,
          "score_max":max(vals) if vals else None,
        }
    return out
