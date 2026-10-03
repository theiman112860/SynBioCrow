"""SynBioCrow 2.4.30 nonlinear multivariate interaction audit.

Development-only diagnostic comparing linear and nonlinear models for predicting
corrected internal-anchor pathway proximity from frozen evidence features.
No production reranking, generation, or sealed-truth access.
"""
from __future__ import annotations
import math
FEATURES=("rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length")
INTERACTIONS=(
 ("precedent_step_fraction","step_feasibility_mean"),
 ("precedent_step_fraction","route_length"),
 ("step_feasibility_mean","route_length"),
 ("rhea_connectivity_fraction","ec_context_fraction"),
 ("rhea_connectivity_fraction","precedent_step_fraction"),
)
def n(x):
 try:
  x=float(x);return x if math.isfinite(x) else None
 except:return None
def design(rows,with_interactions=False):
 X=[];y=[];ids=[]
 idx={f:i for i,f in enumerate(FEATURES)}
 for r in rows:
  yy=n(r.get("similarity"))
  if yy is None:continue
  vals=[0.0 if n(r.get(f)) is None else n(r.get(f)) for f in FEATURES]
  if with_interactions:
   vals=vals+[vals[idx[a]]*vals[idx[b]] for a,b in INTERACTIONS]
  X.append(vals);y.append(yy);ids.append(r.get("route_id"))
 names=list(FEATURES)
 if with_interactions:names += [a+"*"+b for a,b in INTERACTIONS]
 return X,y,ids,names
