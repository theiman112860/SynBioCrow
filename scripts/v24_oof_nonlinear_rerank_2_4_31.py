#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
from synbiocrow.v24.oof_nonlinear_rerank_2_4_31 import matrix

def folds(n,k=5,seed=2431):
 rng=np.random.default_rng(seed);idx=np.arange(n);rng.shuffle(idx);return np.array_split(idx,k)

def oof_predict(X,y,factory,k=5):
 X=np.asarray(X,float);y=np.asarray(y,float);pred=np.empty(len(y),float)
 for test in folds(len(y),min(k,len(y))):
  train=np.setdiff1d(np.arange(len(y)),test)
  if len(train)<3:pred[test]=y[train].mean() if len(train) else y.mean();continue
  m=factory();m.fit(X[train],y[train]);pred[test]=m.predict(X[test])
 return pred

def rank_of(ids,pred,target_id):
 order=sorted(range(len(ids)),key=lambda i:(-float(pred[i]),ids[i]))
 return 1+order.index(ids.index(target_id))

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 aby={r["record_id"]:r["candidate_audit"] for r in aud};rby={}
 for r in ranked:rby.setdefault(r["record_id"],[]).append(r)
 from sklearn.ensemble import RandomForestRegressor,GradientBoostingRegressor
 records=[]
 for rid in sorted(dev):
  aa={x["candidate_id"]:x for x in aby[rid]};rows=[]
  for r in rby[rid]:
   cid=str(r["route_id"]).removeprefix("candidate:")
   if cid in aa:
    x=dict(r);x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");rows.append(x)
  X,y,ids=matrix(rows)
  best_idx=max(range(len(y)),key=lambda i:y[i]);best_id=ids[best_idx];best_sim=y[best_idx]
  frozen_rank=int(next(r["rank"] for r in rows if r["route_id"]==best_id))
  rf=lambda:RandomForestRegressor(n_estimators=300,max_depth=8,min_samples_leaf=5,random_state=2431,n_jobs=-1)
  gb=lambda:GradientBoostingRegressor(n_estimators=220,max_depth=3,learning_rate=0.03,subsample=0.8,random_state=2431)
  prf=oof_predict(X,y,rf,5);pgb=oof_predict(X,y,gb,5);pens=(prf+pgb)/2
  records.append({"record_id":rid,"candidate_count":len(y),"best_internal_anchor_route_id":best_id,"best_internal_anchor_similarity":best_sim,
  "frozen_rank":frozen_rank,"oof_random_forest_rank":rank_of(ids,prf,best_id),"oof_gradient_boosting_rank":rank_of(ids,pgb,best_id),
  "oof_ensemble_rank":rank_of(ids,pens,best_id),
  "rank_improvement":{"random_forest":frozen_rank-rank_of(ids,prf,best_id),"gradient_boosting":frozen_rank-rank_of(ids,pgb,best_id),"ensemble":frozen_rank-rank_of(ids,pens,best_id)}})
 summary={"schema":"synbiocrow.v24.oof-nonlinear-rerank.v1","version":"2.4.31","records":records,
 "method":"5-fold out-of-fold random forest, gradient boosting, and mean ensemble on development-only corrected internal-anchor similarity",
 "production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"oof_nonlinear_rerank_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
