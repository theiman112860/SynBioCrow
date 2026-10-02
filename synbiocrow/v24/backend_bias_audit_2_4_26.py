"""SynBioCrow 2.4.26 backend/metadata score-bias audit."""
from __future__ import annotations
from collections import defaultdict
import math
FEATURES=("rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction","step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min","precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction","reaction_domain_fraction","reaction_type_fraction","route_length_penalty")
def _backend(r):
 b=r.get("source_backends") or []
 return "+".join(sorted(map(str,b))) if b else "UNKNOWN"
def _mean(xs):
 xs=[float(x) for x in xs if x is not None and math.isfinite(float(x))]
 return sum(xs)/len(xs) if xs else None
def audit(rows,target_route):
 rows=sorted(rows,key=lambda x:int(x["rank"])); target=next(x for x in rows if x["route_id"]==target_route); tr=int(target["rank"])
 groups=defaultdict(list)
 for r in rows: groups[_backend(r)].append(r)
 summaries=[]
 for b,rr in sorted(groups.items()):
  summaries.append({"backend_family":b,"n":len(rr),"mean_rank":_mean([x["rank"] for x in rr]),"mean_score":_mean([x.get("coverage_adjusted_score") for x in rr]),"top50_fraction":sum(int(x["rank"])<=50 for x in rr)/len(rr),"feature_means":{f:_mean([x.get(f) for x in rr]) for f in FEATURES},"feature_observation_fraction":{f:sum(x.get(f) is not None for x in rr)/len(rr) for f in FEATURES}})
 above=[x for x in rows if int(x["rank"])<tr]
 tb=_backend(target)
 return {"target_route":target_route,"target_rank":tr,"target_backend_family":tb,"outrankers_n":len(above),"outranker_backend_counts":dict(sorted((b,sum(_backend(x)==b for x in above)) for b in groups)),"backend_summaries":summaries}
