"""SynBioCrow 2.4.27.1 bounded multivariate route-space diagnostic.

Repairs the 2.4.27 O(n^2) timeout by keeping PCA exact on all development
candidates while bounding MDS and distance-concordance calculations to a
deterministic representative subset / pair sample.
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
  x=float(x);return x if math.isfinite(x) else None
 except Exception:return None

def zscore_matrix(rows:list[Mapping[str,Any]],features=EVIDENCE_FEATURES):
 cols={}
 for f in features:
  vals=[_num(r.get(f)) for r in rows];obs=[v for v in vals if v is not None]
  mean=sum(obs)/len(obs) if obs else 0.0
  sd=(sum((v-mean)**2 for v in obs)/len(obs))**0.5 if obs else 1.0
  if sd==0:sd=1.0
  cols[f]=(vals,mean,sd)
 X=[]
 for i in range(len(rows)):
  X.append([0.0 if cols[f][0][i] is None else (cols[f][0][i]-cols[f][1])/cols[f][2] for f in features])
 return X,{f:{"mean":m,"sd":s} for f,(_,m,s) in cols.items()}

def pathway_profiles(rows:list[Mapping[str,Any]]):
 prof=[]
 for r in rows:
  vals=[_num(a.get("best_similarity")) for a in (r.get("anchor_near_misses") or [])]
  prof.append([0.0 if v is None else v for v in vals])
 width=max((len(x) for x in prof),default=0)
 return [x+[0.0]*(width-len(x)) for x in prof]

def dist(a,b):return sum((x-y)**2 for x,y in zip(a,b))**0.5

def pca(X,dims=2):
 import numpy as np
 A=np.array(X,float)
 if len(A)==0:return [],[],[]
 A=A-A.mean(axis=0,keepdims=True)
 U,S,Vt=np.linalg.svd(A,full_matrices=False)
 coords=(U[:,:dims]*S[:dims]).tolist()
 var=S**2;evr=(var/var.sum()).tolist() if var.sum()>0 else [0.0]*len(var)
 return coords,evr,Vt[:dims].tolist()

def deterministic_subset(rows:list[Mapping[str,Any]],max_n=300,seed=241271):
 n=len(rows)
 if n<=max_n:return list(range(n))
 # preserve top ranks + highest internal-anchor candidates + deterministic spread
 chosen=set()
 rank_order=sorted(range(n),key=lambda i:int(rows[i].get("rank") or 10**9))
 chosen.update(rank_order[:min(50,max_n//4)])
 sim_order=sorted(range(n),key=lambda i:-(_num(rows[i].get("internal_anchor_similarity_mean")) or -1))
 chosen.update(sim_order[:min(50,max_n//4)])
 remain=[i for i in range(n) if i not in chosen]
 rng=random.Random(seed+n);rng.shuffle(remain)
 chosen.update(remain[:max(0,max_n-len(chosen))])
 return sorted(chosen)

def distance_matrix(X,idx):
 import numpy as np
 A=np.asarray([X[i] for i in idx],float)
 sq=np.sum(A*A,axis=1,keepdims=True)
 D2=np.maximum(sq+sq.T-2*A@A.T,0.0)
 return np.sqrt(D2)

def classical_mds_from_matrix(D,dims=2):
 import numpy as np
 A=np.asarray(D,float);n=A.shape[0]
 H=np.eye(n)-np.ones((n,n))/n;B=-0.5*H@(A**2)@H
 vals,vecs=np.linalg.eigh(B);order=np.argsort(vals)[::-1];vals=vals[order];vecs=vecs[:,order]
 k=min(dims,int(np.sum(vals>0)));X=vecs[:,:k]*np.sqrt(np.maximum(vals[:k],0))
 if k<dims:X=np.pad(X,((0,0),(0,dims-k)))
 return X.tolist(),vals.tolist()

def pearson(x,y):
 if len(x)<3 or len(x)!=len(y):return None
 mx=sum(x)/len(x);my=sum(y)/len(y)
 a=sum((u-mx)*(v-my) for u,v in zip(x,y));b=sum((u-mx)**2 for u in x);c=sum((v-my)**2 for v in y)
 return a/(b*c)**0.5 if b>0 and c>0 else None

def sampled_concordance(Xe,Xp,max_pairs=50000,permutations=100,seed=241272):
 n=len(Xe)
 if n<3:return {"correlation":None,"pair_count":0,"permutations":0,"p_value":None}
 rng=random.Random(seed+n)
 total=n*(n-1)//2
 if total<=max_pairs:
  pairs=[(i,j) for i in range(n) for j in range(i)]
 else:
  pairs=set()
  while len(pairs)<max_pairs:
   i=rng.randrange(n);j=rng.randrange(n)
   if i==j:continue
   if i<j:i,j=j,i
   pairs.add((i,j))
  pairs=list(pairs)
 de=[dist(Xe[i],Xe[j]) for i,j in pairs];dp=[dist(Xp[i],Xp[j]) for i,j in pairs]
 obs=pearson(de,dp)
 if obs is None:return {"correlation":None,"pair_count":len(pairs),"permutations":0,"p_value":None}
 extreme=0;base=list(range(n))
 for _ in range(permutations):
  perm=base[:];rng.shuffle(perm)
  yp=[dist(Xp[perm[i]],Xp[perm[j]]) for i,j in pairs]
  r=pearson(de,yp)
  if r is not None and abs(r)>=abs(obs):extreme+=1
 return {"correlation":obs,"pair_count":len(pairs),"permutations":permutations,"p_value":(extreme+1)/(permutations+1)}
