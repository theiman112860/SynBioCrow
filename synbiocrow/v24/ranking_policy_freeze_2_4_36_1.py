"""SynBioCrow 2.4.36.1 deterministic within-target pairwise freeze.

Fixes two issues in 2.4.36:
1) stochastic pair sampling;
2) invalid cross-target pair labels on target-specific similarity scales.

All pairwise preference examples are generated deterministically within target,
then pooled across development targets. Validation/evaluation truth remains sealed.
"""
from __future__ import annotations
import math
FEATURES=(
"rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length"
)
OFFSETS=(1,2,4,8,16,32,64,128,256,512,1024)

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

def percentile_transform(X):
    import numpy as np
    A=np.asarray(X,float);n,p=A.shape;R=np.zeros_like(A,float)
    for j in range(p):
        order=np.argsort(A[:,j],kind="mergesort");rank=np.empty(n,float);k=0
        while k<n:
            m=k+1
            while m<n and A[order[m],j]==A[order[k],j]:m+=1
            avg=(k+m-1)/2
            for t in range(k,m):rank[order[t]]=avg
            k=m
        R[:,j]=0.5 if n==1 else rank/(n-1)
    return R

def deterministic_within_target_pairs(X,y,ids):
    import numpy as np
    X=np.asarray(X,float);y=np.asarray(y,float)
    order=sorted(range(len(ids)),key=lambda i:(y[i],ids[i]))
    P=[];L=[]
    for off in OFFSETS:
        if off>=len(order):continue
        for k in range(len(order)-off):
            i=order[k];j=order[k+off]
            d=y[j]-y[i]
            if abs(d)<=1e-12:continue
            z=X[j]-X[i]
            P.append(z);L.append(1)
            P.append(-z);L.append(0)
    if not P:return np.empty((0,X.shape[1])),np.empty((0,),int)
    return np.asarray(P,float),np.asarray(L,int)

def max_equivalent_ids(ids,y,tol=1e-12):
    if not y:return []
    m=max(y);return [rid for rid,v in zip(ids,y) if abs(v-m)<=tol]
