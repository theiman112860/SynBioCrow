"""SynBioCrow 2.4.24 route-level score provenance audit."""
from __future__ import annotations
import math
FEATURES=("rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction","step_feasibility_mean","step_feasibility_min","precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction","reaction_domain_fraction","reaction_type_fraction","route_length")
def _num(x):
 try:
  x=float(x);return x if math.isfinite(x) else None
 except:return None
def summarize(r):
 return {"route_id":r["route_id"],"rank_2_4_16":int(r["rank"]),"coverage_adjusted_score":_num(r.get("coverage_adjusted_score")),"features":{f:_num(r.get(f)) for f in FEATURES},"missing_features":[f for f in FEATURES if _num(r.get(f)) is None]}
def provenance(rows,target_route):
 rows=sorted(rows,key=lambda r:int(r["rank"]));t=next(r for r in rows if r["route_id"]==target_route);rank=int(t["rank"])
 # representative outrankers: top, quartiles of the outranking set, and immediate predecessor
 above=[r for r in rows if int(r["rank"])<rank]
 idx=sorted(set([0,max(0,len(above)//4),max(0,len(above)//2),max(0,3*len(above)//4),max(0,len(above)-1)])) if above else []
 reps=[above[i] for i in idx]
 return {"target":summarize(t),"representative_outrankers":[summarize(r) for r in reps],
 "score_distribution":{"n":len(rows),"target_rank":rank,"outranking_n":len(above),
 "target_score":_num(t.get("coverage_adjusted_score")),
 "top_score":_num(rows[0].get("coverage_adjusted_score")) if rows else None}}
