"""SynBioCrow 2.4.30 development-only multivariate interaction audit.

Fits transparent regularized linear and tree-free interaction models to explain
corrected internal-anchor similarity from frozen evidence features. Diagnostic
only: no production reranking, no validation/evaluation truth.
"""
from __future__ import annotations
import math
FEATURES=("rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length")
def n(x):
 try:
  x=float(x);return x if math.isfinite(x) else None
 except:return None
def design(rows):
 X=[];y=[];ids=[]
 for r in rows:
  yy=n(r.get("similarity"))
  if yy is None:continue
  vals=[]
  for f in FEATURES:
   v=n(r.get(f));vals.append(0.0 if v is None else v)
  # selected pairwise interactions among unsaturated/decision-relevant signals
  idx={f:i for i,f in enumerate(FEATURES)}
  pairs=[("precedent_step_fraction","step_feasibility_mean"),
         ("precedent_step_fraction","route_length"),
         ("step_feasibility_mean","route_length"),
         ("rhea_connectivity_fraction","ec_context_fraction"),
         ("rhea_connectivity_fraction","precedent_step_fraction")]
  inter=[vals[idx[a]]*vals[idx[b]] for a,b in pairs]
  X.append(vals+inter);y.append(yy);ids.append(r.get("route_id"))
 names=list(FEATURES)+[a+"*"+b for a,b in pairs]
 return X,y,ids,names
