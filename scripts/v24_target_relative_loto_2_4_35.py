#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
from synbiocrow.v24.target_relative_loto_2_4_35 import matrix,percentile_transform,max_equivalent_ids

def pair_training(X,y,max_pairs=60000,seed=2435):
 rng=np.random.default_rng(seed);X=np.asarray(X,float);y=np.asarray(y,float);n=len(y);P=[];L=[];tries=0
 while len(L)<max_pairs and tries<max_pairs*20:
  i,j=rng.integers(0,n,2);tries+=1
  if i==j:continue
  d=y[i]-y[j]
  if abs(d)<=1e-12:continue
  z=X[i]-X[j];lab=1 if d>0 else 0
  P.append(z);L.append(lab);P.append(-z);L.append(1-lab)
 return np.asarray(P,float),np.asarray(L,int)

def ranks(ids,scores):
 order=sorted(range(len(ids)),key=lambda i:(-float(scores[i]),ids[i]))
 return {ids[i]:r+1 for r,i in enumerate(order)}

def score_linear(Xtr,ytr,Xte):
 from sklearn.linear_model import LogisticRegression
 P,L=pair_training(Xtr,ytr,60000,2435)
 m=LogisticRegression(C=1.0,max_iter=2500,solver="lbfgs").fit(P,L)
 return np.asarray(Xte,float)@m.coef_.ravel()

def score_nonlinear(Xtr,ytr,Xte,refs=160):
 from sklearn.ensemble import HistGradientBoostingClassifier
 P,L=pair_training(Xtr,ytr,50000,2436)
 m=HistGradientBoostingClassifier(max_iter=220,max_depth=5,learning_rate=0.04,l2_regularization=1.0,random_state=2435).fit(P,L)
 rng=np.random.default_rng(2437);Xtr=np.asarray(Xtr,float);Xte=np.asarray(Xte,float)
 ref=np.arange(len(Xtr))
 if len(ref)>refs:ref=rng.choice(ref,refs,replace=False)
 out=np.empty(len(Xte))
 for i,x in enumerate(Xte):out[i]=m.predict_proba(x[None,:]-Xtr[ref])[:,1].mean()
 return out

def summarize(eq,rankmap):
 vals=[rankmap[x] for x in eq]
 return {"best_equivalent_rank":min(vals),"median_equivalent_rank":float(np.median(vals)),"worst_equivalent_rank":max(vals)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 aby={r["record_id"]:r["candidate_audit"] for r in aud};rby={}
 for r in ranked:rby.setdefault(r["record_id"],[]).append(r)
 by={}
 for rid in sorted(dev):
  aa={x["candidate_id"]:x for x in aby[rid]};rows=[]
  for r in rby[rid]:
   cid=str(r["route_id"]).removeprefix("candidate:")
   if cid in aa:
    x=dict(r);x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");rows.append(x)
  X,y,ids=matrix(rows);by[rid]=(rows,percentile_transform(X),y,ids)
 rec=[]
 for hold in sorted(dev):
  rows_h,Xh,yh,idsh=by[hold];Xtr=[];ytr=[];train=[]
  for rid,(rows,X,y,ids) in by.items():
   if rid==hold:continue
   Xtr.extend(X.tolist());ytr.extend(y);train.append(rid)
  eq=max_equivalent_ids(idsh,yh);frozen={r["route_id"]:int(r["rank"]) for r in rows_h}
  sl=score_linear(Xtr,ytr,Xh);sn=score_nonlinear(Xtr,ytr,Xh)
  zl=(sl-sl.mean())/(sl.std() or 1);zn=(sn-sn.mean())/(sn.std() or 1);se=zl+zn
  rl=ranks(idsh,sl);rn=ranks(idsh,sn);re=ranks(idsh,se);fv=[frozen[x] for x in eq]
  rec.append({"record_id":hold,"train_targets":sorted(train),"candidate_count":len(idsh),"max_similarity":float(max(yh)),"max_equivalent_count":len(eq),
  "frozen":{"best_equivalent_rank":min(fv),"median_equivalent_rank":float(np.median(fv)),"worst_equivalent_rank":max(fv)},
  "relative_loto_linear":summarize(eq,rl),"relative_loto_nonlinear":summarize(eq,rn),"relative_loto_ensemble":summarize(eq,re)})
 summary={"schema":"synbiocrow.v24.target-relative-loto.v1","version":"2.4.35","records":rec,
 "method":"within-target percentile normalization from unlabeled features followed by leave-one-target-out pairwise transfer",
 "production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"target_relative_loto_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
