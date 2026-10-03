"""SynBioCrow 2.4.35 target-relative LOTO pairwise transfer.

Development-only hard transfer diagnostic. Features are converted to within-target
percentiles using unlabeled candidate distributions before leave-one-target-out
pairwise ranking. Held-out target contributes no labels.
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
 except Exception:return None
def matrix(rows):
 X=[];y=[];ids=[]
 for r in rows:
  yy=num(r.get("similarity"))
  if yy is None:continue
  X.append([0.0 if num(r.get(f)) is None else num(r.get(f)) for f in FEATURES])
  y.append(yy);ids.append(r.get("route_id"))
 return X,y,ids
def percentile_transform(X):
 import numpy as np
 A=np.asarray(X,float);n,p=A.shape;R=np.zeros_like(A,float)
 for j in range(p):
  order=np.argsort(A[:,j],kind="mergesort");r=np.empty(n,float);k=0
  while k<n:
   m=k+1
   while m<n and A[order[m],j]==A[order[k],j]:m+=1
   avg=(k+m-1)/2
   for t in range(k,m):r[order[t]]=avg
   k=m
  R[:,j]=0.5 if n==1 else r/(n-1)
 return R
def max_equivalent_ids(ids,y,tol=1e-12):
 if not y:return []
 m=max(y);return [rid for rid,v in zip(ids,y) if abs(v-m)<=tol]
