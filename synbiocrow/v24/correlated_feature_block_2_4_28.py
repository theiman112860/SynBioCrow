"""SynBioCrow 2.4.28 correlated-feature block audit.

Development-only diagnostic testing whether highly redundant metadata variables
(template/domain/type coverage) are effectively triple-counted in the frozen
2.4.16 scalar score. No production ranking change.
"""
from __future__ import annotations
import math
from typing import Any,Mapping

BLOCK=("template_metadata_fraction","reaction_domain_fraction","reaction_type_fraction")
def _n(x):
 try:
  x=float(x);return x if math.isfinite(x) else None
 except:return None
def pearson(xs,ys):
 z=[(x,y) for x,y in zip(xs,ys) if _n(x) is not None and _n(y) is not None]
 if len(z)<3:return None
 x=[float(a) for a,b in z];y=[float(b) for a,b in z];mx=sum(x)/len(x);my=sum(y)/len(y)
 a=sum((u-mx)*(v-my) for u,v in zip(x,y));b=sum((u-mx)**2 for u in x);c=sum((v-my)**2 for v in y)
 return a/(b*c)**0.5 if b and c else None
def block_stats(rows:list[Mapping[str,Any]]):
 corr={}
 for i,a in enumerate(BLOCK):
  for b in BLOCK[i+1:]:corr[f"{a}__{b}"]=pearson([r.get(a) for r in rows],[r.get(b) for r in rows])
 identical=sum(1 for r in rows if len({_n(r.get(f)) for f in BLOCK})==1)
 return {"pairwise_pearson":corr,"identical_within_route_fraction":identical/len(rows) if rows else None}
def collapsed_block_score(r:Mapping[str,Any]):
 vals=[_n(r.get(f)) for f in BLOCK];obs=[v for v in vals if v is not None]
 return sum(obs)/len(obs) if obs else None
