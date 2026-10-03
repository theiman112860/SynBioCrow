"""SynBioCrow 2.4.27 multivariate route-space diagnostic.

Development-only analysis comparing evidence/metadata geometry with
chemical/pathway proximity geometry. No production reranking or generation.
"""
from __future__ import annotations
from typing import Any,Mapping
import math,random

EVIDENCE_FEATURES=(
 "rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
 "step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
 "precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
 "reaction_domain_fraction","reaction_type_fraction","route_length"
)

def _num(x):
 try:
  x=float(x); return x if math.isfinite(x) else None
 except Exception:return None

def zscore_matrix(rows:list[Mapping[str,Any]],features=EVIDENCE_FEATURES):
    cols={}
    for f in features:
        vals=[_num(r.get(f)) for r in rows]
        obs=[v for v in vals if v is not None]
        mean=sum(obs)/len(obs) if obs else 0.0
        sd=(sum((v-mean)**2 for v in obs)/len(obs))**0.5 if obs else 1.0
        if sd==0:sd=1.0
        cols[f]=(vals,mean,sd)
    X=[]
    for i in range(len(rows)):
        x=[]
        for f in features:
            vals,mean,sd=cols[f]
            v=vals[i]
            x.append(0.0 if v is None else (v-mean)/sd)
        X.append(x)
    return X,{f:{"mean":m,"sd":s} for f,(_,m,s) in cols.items()}

def euclidean_distance_matrix(X):
    n=len(X);D=[[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i):
            d=sum((a-b)**2 for a,b in zip(X[i],X[j]))**0.5
            D[i][j]=D[j][i]=d
    return D

def pathway_distance_matrix(audit_rows:list[Mapping[str,Any]]):
    # Distance defined from corrected internal-anchor similarity:
    # closer means more similar literature/pathway proximity profile.
    prof=[]
    for r in audit_rows:
        vals=[]
        for a in r.get("anchor_near_misses") or []:
            v=_num(a.get("best_similarity"))
            vals.append(0.0 if v is None else v)
        prof.append(vals)
    width=max((len(x) for x in prof),default=0)
    X=[x+[0.0]*(width-len(x)) for x in prof]
    return euclidean_distance_matrix(X),X

def upper_triangle(D):
    return [D[i][j] for i in range(len(D)) for j in range(i)]

def pearson(x,y):
    if len(x)<3 or len(x)!=len(y):return None
    mx=sum(x)/len(x);my=sum(y)/len(y)
    a=sum((u-mx)*(v-my) for u,v in zip(x,y))
    b=sum((u-mx)**2 for u in x);c=sum((v-my)**2 for v in y)
    return a/(b*c)**0.5 if b>0 and c>0 else None

def mantel_style(D1,D2,permutations=250,seed=24127):
    obs=pearson(upper_triangle(D1),upper_triangle(D2))
    if obs is None:return {"correlation":None,"permutations":0,"p_value":None}
    rng=random.Random(seed);n=len(D2);extreme=0
    idx=list(range(n))
    for _ in range(permutations):
        rng.shuffle(idx)
        P=[[D2[idx[i]][idx[j]] for j in range(n)] for i in range(n)]
        r=pearson(upper_triangle(D1),upper_triangle(P))
        if r is not None and abs(r)>=abs(obs):extreme+=1
    return {"correlation":obs,"permutations":permutations,"p_value":(extreme+1)/(permutations+1)}

def classical_mds(D,dims=2):
    # Pure-Python fallback using numpy if available.
    import numpy as np
    A=np.array(D,float);n=A.shape[0]
    H=np.eye(n)-np.ones((n,n))/n
    B=-0.5*H@(A**2)@H
    vals,vecs=np.linalg.eigh(B);order=np.argsort(vals)[::-1]
    vals=vals[order];vecs=vecs[:,order]
    k=min(dims,sum(vals>0))
    X=vecs[:,:k]*np.sqrt(np.maximum(vals[:k],0))
    if k<dims:X=np.pad(X,((0,0),(0,dims-k)))
    return X.tolist(),vals.tolist()

def pca(X,dims=2):
    import numpy as np
    A=np.array(X,float)
    if len(A)==0:return [],[],[]
    A=A-A.mean(axis=0,keepdims=True)
    U,S,Vt=np.linalg.svd(A,full_matrices=False)
    coords=(U[:,:dims]*S[:dims]).tolist()
    var=(S**2);evr=(var/var.sum()).tolist() if var.sum()>0 else [0.0]*len(var)
    loadings=Vt[:dims].tolist()
    return coords,evr,loadings
