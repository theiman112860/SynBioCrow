"""SynBioCrow 2.4.34 leave-one-target-out pairwise transfer diagnostic.

Development-only hard generalization test. For each development target, train the
pairwise ranker only on the other development targets and score the held-out
target. Tie-aware evaluation uses the full max-similarity equivalence set.
"""
from __future__ import annotations
import math
FEATURES=("rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length")
def num(x):
 try:
  x=float(x); return x if math.isfinite(x) else None
 except Exception:return None
def matrix(rows):
 X=[];y=[];ids=[]
 for r in rows:
  yy=num(r.get("similarity"))
  if yy is None:continue
  X.append([0.0 if num(r.get(f)) is None else num(r.get(f)) for f in FEATURES])
  y.append(yy);ids.append(r.get("route_id"))
 return X,y,ids
def max_equivalent_ids(ids,y,tol=1e-12):
 if not y:return []
 m=max(y)
 return [rid for rid,v in zip(ids,y) if abs(v-m)<=tol]
