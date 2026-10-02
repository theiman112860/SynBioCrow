"""SynBioCrow 2.4.23 score-component counterfactual audit.

Reconstructs the frozen 2.4.16 score from persisted route features, identifies
the active score components, then removes one active component at a time and
measures rank movement of the best corrected internal-anchor candidate.
Measurement only; no policy is adopted.
"""
from __future__ import annotations
import math
CANDIDATES=("rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length")
def _num(x):
 try:
  x=float(x);return x if math.isfinite(x) else None
 except Exception:return None
def corr(x,y):
 if len(x)<3:return None
 mx=sum(x)/len(x);my=sum(y)/len(y);a=sum((u-mx)*(v-my) for u,v in zip(x,y));b=sum((u-mx)**2 for u in x);c=sum((v-my)**2 for v in y)
 return a/math.sqrt(b*c) if b>0 and c>0 else None
def active_components(rows):
 score=[_num(r.get("coverage_adjusted_score")) for r in rows]
 out=[]
 for f in CANDIDATES:
  vals=[_num(r.get(f)) for r in rows]
  pairs=[(v,s) for v,s in zip(vals,score) if v is not None and s is not None]
  rho=corr([p[0] for p in pairs],[p[1] for p in pairs]) if len(pairs)>=3 else None
  out.append({"feature":f,"pearson_vs_frozen_score":rho,"coverage":len(pairs)/len(rows) if rows else 0})
 return out
def residual_rank(rows,target_route,feature):
 pairs=[]
 for r in rows:
  s=_num(r.get("coverage_adjusted_score"));v=_num(r.get(feature))
  if s is not None and v is not None:pairs.append((v,s))
 if len(pairs)<3:return None
 # OLS score ~ a + b*feature; counterfactual residual removes linear contribution.
 mx=sum(v for v,s in pairs)/len(pairs);my=sum(s for v,s in pairs)/len(pairs)
 den=sum((v-mx)**2 for v,s in pairs);b=sum((v-mx)*(s-my) for v,s in pairs)/den if den else 0;a=my-b*mx
 scored=[]
 for r in rows:
  s=_num(r.get("coverage_adjusted_score"));v=_num(r.get(feature))
  res=(s-(a+b*v)) if s is not None and v is not None else None
  scored.append((res,r["route_id"],int(r.get("rank") or 10**9)))
 scored.sort(key=lambda x:(-(x[0] if x[0] is not None else -1e99),x[2],x[1]))
 return next(i for i,x in enumerate(scored,1) if x[1]==target_route)
