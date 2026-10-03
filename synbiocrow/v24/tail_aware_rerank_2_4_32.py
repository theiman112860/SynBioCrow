"""SynBioCrow 2.4.32 tail-aware nonlinear reranking diagnostic.

Development-only. Converts corrected internal-anchor similarity into a within-target
high-similarity tail label and evaluates out-of-fold classifiers as ranking scores.
No production reranking and no sealed truth.
"""
from __future__ import annotations
import math
FEATURES=("rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length")
def num(x):
 try:
  x=float(x);return x if math.isfinite(x) else None
 except:return None
def matrix(rows):
 X=[];y=[];ids=[]
 for r in rows:
  yy=num(r.get("similarity"))
  if yy is None:continue
  X.append([0.0 if num(r.get(f)) is None else num(r.get(f)) for f in FEATURES])
  y.append(yy);ids.append(r.get("route_id"))
 return X,y,ids
