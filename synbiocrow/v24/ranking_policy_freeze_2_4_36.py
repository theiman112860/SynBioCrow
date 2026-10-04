"""SynBioCrow 2.4.36 development ranking policy freeze candidate.

Freezes the target-relative linear pairwise representation selected from 2.4.35
development-only leave-one-target-out transfer. No validation/evaluation truth is
accessed here. This module provides deterministic feature normalization and
pairwise linear scoring suitable for reproducibility packaging.
"""
from __future__ import annotations
import math

FEATURES=(
"rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length"
)

def num(x):
    try:
        x=float(x)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def matrix(rows):
    X=[]; y=[]; ids=[]
    for r in rows:
        yy=num(r.get("similarity"))
        if yy is None:
            continue
        X.append([0.0 if num(r.get(f)) is None else num(r.get(f)) for f in FEATURES])
        y.append(yy)
        ids.append(r.get("route_id"))
    return X,y,ids

def percentile_transform(X):
    import numpy as np
    A=np.asarray(X,float)
    n,p=A.shape
    R=np.zeros_like(A,float)
    for j in range(p):
        order=np.argsort(A[:,j],kind="mergesort")
        rank=np.empty(n,float)
        k=0
        while k<n:
            m=k+1
            while m<n and A[order[m],j]==A[order[k],j]:
                m+=1
            avg=(k+m-1)/2
            for t in range(k,m):
                rank[order[t]]=avg
            k=m
        R[:,j]=0.5 if n==1 else rank/(n-1)
    return R

def max_equivalent_ids(ids,y,tol=1e-12):
    if not y:
        return []
    m=max(y)
    return [rid for rid,v in zip(ids,y) if abs(v-m)<=tol]
