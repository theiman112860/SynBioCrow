"""SynBioCrow 2.4.29 metadata-block collapse counterfactual.

Development-only counterfactual. Collapses three exactly identical metadata
features into one block while preserving their combined frozen weight (0.50).
No production policy change.
"""
from __future__ import annotations
import math
BASE_WEIGHTS={
"rhea_connectivity_fraction":1.0,"ec_context_fraction":0.5,"reviewed_ec_context_fraction":0.3,
"step_feasibility_mean":0.8,"step_feasibility_min":0.6,"filter_score_mean":0.55,"filter_score_min":0.35,
"precedent_step_fraction":0.75,"rule_coverage_fraction":0.2,"metadata_block":0.5,"route_length_penalty":-0.25}
BLOCK=("template_metadata_fraction","reaction_domain_fraction","reaction_type_fraction")
def n(x):
 try:
  x=float(x);return x if math.isfinite(x) else None
 except:return None
def score(r):
 x=dict(r);vals=[n(x.get(k)) for k in BLOCK];obs=[v for v in vals if v is not None]
 x["metadata_block"]=sum(obs)/len(obs) if obs else None
 x["route_length_penalty"]=min(int(x.get("route_length") or 0),12)/12
 num=den=0.0;count=0
 for k,w in BASE_WEIGHTS.items():
  v=n(x.get(k))
  if v is None:continue
  if k!="route_length_penalty":v=max(0,min(1,v))
  num+=w*v;den+=abs(w);count+=1
 raw=num/den if den else None
 return raw*(count/len(BASE_WEIGHTS)) if raw is not None else None
