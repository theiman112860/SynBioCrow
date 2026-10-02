"""SynBioCrow 2.4.22 pairwise suppression audit.

Diagnoses why the best corrected internal-anchor candidate is outranked by the
frozen 2.4.16 policy. No reranking is performed.
"""
from __future__ import annotations
from typing import Any
import math

FEATURES=("rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length")

def _num(x):
 try:
  x=float(x); return x if math.isfinite(x) else None
 except Exception:return None

def audit_target(rows:list[dict], best:dict)->dict:
    cid=best["candidate_id"]; route_id="candidate:"+cid
    target=next((r for r in rows if r["route_id"]==route_id),None)
    if target is None:raise ValueError("best near-miss candidate absent from ranking")
    rank=int(target["rank"])
    above=[r for r in rows if int(r["rank"])<rank]
    feats=[]
    for f in FEATURES:
        tv=_num(target.get(f)); vals=[_num(r.get(f)) for r in above]; vals=[v for v in vals if v is not None]
        if tv is None or not vals:
            feats.append({"feature":f,"target_value":tv,"n_above":len(vals),"fraction_above_greater":None,"fraction_above_less":None,"median_above":None,"target_minus_median":None})
            continue
        sv=sorted(vals); n=len(sv); med=sv[n//2] if n%2 else (sv[n//2-1]+sv[n//2])/2
        feats.append({"feature":f,"target_value":tv,"n_above":n,
          "fraction_above_greater":sum(v>tv for v in vals)/n,
          "fraction_above_less":sum(v<tv for v in vals)/n,
          "median_above":med,"target_minus_median":tv-med})
    feats.sort(key=lambda x:-(x["fraction_above_greater"] if x["fraction_above_greater"] is not None else -1))
    return {"candidate_id":cid,"rank_2_4_16":rank,"outranking_candidate_count":len(above),
      "best_internal_anchor_similarity_mean":best["internal_anchor_similarity_mean"],
      "feature_suppression_audit":feats}

def compare_failed_policy(summary:dict)->dict:
    ev=summary.get("evaluations") or []
    return {"all_worsened":bool(ev) and all((x.get("rank_improvement") or 0)<0 for x in ev),
      "evaluations":ev}
