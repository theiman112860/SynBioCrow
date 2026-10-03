#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
from synbiocrow.v24.tie_aware_pairwise_rank_2_4_33 import matrix,max_equivalent_ids

def folds(n,k=5,seed=2433):
 rng=np.random.default_rng(seed);idx=np.arange(n);rng.shuffle(idx);return np.array_split(idx,k)

def pair_training(X,y,max_pairs=25000,seed=2433):
 rng=np.random.default_rng(seed);X=np.asarray(X,float);y=np.asarray(y,float);n=len(y)
 P=[];L=[];tries=0
 while len(L)<max_pairs and tries<max_pairs*20:
  i,j=rng.integers(0,n,2);tries+=1
  if i==j:continue
  d=y[i]-y[j]
  if abs(d)<=1e-12:continue
  z=X[i]-X[j];lab=1 if d>0 else 0
  P.append(z);L.append(lab)
  P.append(-z);L.append(1-lab)
 if not L:return np.empty((0,X.shape[1])),np.empty((0,),int)
 return np.asarray(P,float),np.asarray(L,int)

def oof_linear_scores(X,y,k=5):
 from sklearn.linear_model import LogisticRegression
 X=np.asarray(X,float);y=np.asarray(y,float);scores=np.empty(len(y),float)
 for fold,test in enumerate(folds(len(y),min(k,len(y)))):
  train=np.setdiff1d(np.arange(len(y)),test)
  P,L=pair_training(X[train],y[train],max_pairs=20000,seed=24330+fold)
  if len(np.unique(L))<2:
   scores[test]=0;continue
  m=LogisticRegression(C=1.0,max_iter=2000,solver="lbfgs").fit(P,L)
  scores[test]=X[test]@m.coef_.ravel()
 return scores

def oof_nonlinear_scores(X,y,k=5,refs=96):
 from sklearn.ensemble import HistGradientBoostingClassifier
 X=np.asarray(X,float);y=np.asarray(y,float);scores=np.empty(len(y),float)
 for fold,test in enumerate(folds(len(y),min(k,len(y)))):
  train=np.setdiff1d(np.arange(len(y)),test)
  P,L=pair_training(X[train],y[train],max_pairs=18000,seed=24400+fold)
  if len(np.unique(L))<2:
   scores[test]=0;continue
  m=HistGradientBoostingClassifier(max_iter=180,max_depth=5,learning_rate=0.05,l2_regularization=1.0,random_state=2433).fit(P,L)
  rng=np.random.default_rng(24500+fold)
  ref=train if len(train)<=refs else rng.choice(train,refs,replace=False)
  for i in test:
   D=X[i][None,:]-X[ref]
   scores[i]=float(m.predict_proba(D)[:,1].mean())
 return scores

def ranks(ids,scores):
 order=sorted(range(len(ids)),key=lambda i:(-float(scores[i]),ids[i]))
 return {ids[i]:r+1 for r,i in enumerate(order)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 aby={r["record_id"]:r["candidate_audit"] for r in aud};rby={}
 for r in ranked:rby.setdefault(r["record_id"],[]).append(r)
 records=[]
 for rid in sorted(dev):
  aa={x["candidate_id"]:x for x in aby[rid]};rows=[]
  for r in rby[rid]:
   cid=str(r["route_id"]).removeprefix("candidate:")
   if cid in aa:
    x=dict(r);x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");rows.append(x)
  X,y,ids=matrix(rows);eq=max_equivalent_ids(ids,y)
  frozen={r["route_id"]:int(r["rank"]) for r in rows if r["route_id"] in set(ids)}
  pl=oof_linear_scores(X,y,5);pn=oof_nonlinear_scores(X,y,5);pe=(pl-pl.mean())/(pl.std() or 1)+(pn-pn.mean())/(pn.std() or 1)
  rl=ranks(ids,pl);rn=ranks(ids,pn);re=ranks(ids,pe)
  def summarize(rankmap):
   vals=[rankmap[x] for x in eq]
   return {"best_equivalent_rank":min(vals),"median_equivalent_rank":float(np.median(vals)),"worst_equivalent_rank":max(vals)}
  frozen_vals=[frozen[x] for x in eq]
  records.append({"record_id":rid,"candidate_count":len(ids),"max_similarity":float(max(y)),"max_equivalent_count":len(eq),
   "frozen":{"best_equivalent_rank":min(frozen_vals),"median_equivalent_rank":float(np.median(frozen_vals)),"worst_equivalent_rank":max(frozen_vals)},
   "pairwise_linear":summarize(rl),"pairwise_nonlinear":summarize(rn),"pairwise_ensemble":summarize(re)})
 summary={"schema":"synbiocrow.v24.tie-aware-pairwise-rank.v1","version":"2.4.33","records":records,
 "method":"5-fold OOF pairwise ranking; zero-similarity-gap pairs excluded; evaluation uses full max-similarity equivalence set",
 "production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"tie_aware_pairwise_ranking_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
