#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
from synbiocrow.v24.loto_pairwise_transfer_2_4_34 import matrix,max_equivalent_ids

def pair_training(X,y,max_pairs=60000,seed=2434):
 rng=np.random.default_rng(seed);X=np.asarray(X,float);y=np.asarray(y,float);n=len(y)
 P=[];L=[];tries=0
 while len(L)<max_pairs and tries<max_pairs*20:
  i,j=rng.integers(0,n,2);tries+=1
  if i==j:continue
  d=y[i]-y[j]
  if abs(d)<=1e-12:continue
  z=X[i]-X[j];lab=1 if d>0 else 0
  P.append(z);L.append(lab);P.append(-z);L.append(1-lab)
 if not L:return np.empty((0,X.shape[1])),np.empty((0,),int)
 return np.asarray(P,float),np.asarray(L,int)

def ranks(ids,scores):
 order=sorted(range(len(ids)),key=lambda i:(-float(scores[i]),ids[i]))
 return {ids[i]:r+1 for r,i in enumerate(order)}

def score_linear(Xtrain,ytrain,Xtest):
 from sklearn.linear_model import LogisticRegression
 P,L=pair_training(Xtrain,ytrain,60000,2434)
 if len(np.unique(L))<2:return np.zeros(len(Xtest))
 m=LogisticRegression(C=1.0,max_iter=2500,solver="lbfgs").fit(P,L)
 return np.asarray(Xtest,float)@m.coef_.ravel()

def score_nonlinear(Xtrain,ytrain,Xtest,refs=160):
 from sklearn.ensemble import HistGradientBoostingClassifier
 P,L=pair_training(Xtrain,ytrain,50000,2435)
 if len(np.unique(L))<2:return np.zeros(len(Xtest))
 m=HistGradientBoostingClassifier(max_iter=220,max_depth=5,learning_rate=0.04,l2_regularization=1.0,random_state=2434).fit(P,L)
 rng=np.random.default_rng(2436)
 Xtr=np.asarray(Xtrain,float);Xte=np.asarray(Xtest,float)
 ref=np.arange(len(Xtr))
 if len(ref)>refs:ref=rng.choice(ref,refs,replace=False)
 out=np.empty(len(Xte),float)
 for i,x in enumerate(Xte):
  D=x[None,:]-Xtr[ref]
  out[i]=float(m.predict_proba(D)[:,1].mean())
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

 bytarget={}
 for rid in sorted(dev):
  aa={x["candidate_id"]:x for x in aby[rid]};rows=[]
  for r in rby[rid]:
   cid=str(r["route_id"]).removeprefix("candidate:")
   if cid in aa:
    x=dict(r);x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");rows.append(x)
  bytarget[rid]=(rows,*matrix(rows))

 records=[]
 for hold in sorted(dev):
  rows_h,Xh,yh,idsh=bytarget[hold]
  Xtr=[];ytr=[];train_targets=[]
  for rid,(rows,X,y,ids) in bytarget.items():
   if rid==hold:continue
   Xtr.extend(X);ytr.extend(y);train_targets.append(rid)
  eq=max_equivalent_ids(idsh,yh)
  frozen={r["route_id"]:int(r["rank"]) for r in rows_h}
  sl=score_linear(Xtr,ytr,Xh);sn=score_nonlinear(Xtr,ytr,Xh)
  zl=(sl-sl.mean())/(sl.std() or 1);zn=(sn-sn.mean())/(sn.std() or 1);se=zl+zn
  rl=ranks(idsh,sl);rn=ranks(idsh,sn);re=ranks(idsh,se)
  fv=[frozen[x] for x in eq]
  records.append({"record_id":hold,"train_targets":sorted(train_targets),"candidate_count":len(idsh),"max_similarity":float(max(yh)),"max_equivalent_count":len(eq),
   "frozen":{"best_equivalent_rank":min(fv),"median_equivalent_rank":float(np.median(fv)),"worst_equivalent_rank":max(fv)},
   "loto_pairwise_linear":summarize(eq,rl),"loto_pairwise_nonlinear":summarize(eq,rn),"loto_pairwise_ensemble":summarize(eq,re)})
 summary={"schema":"synbiocrow.v24.loto-pairwise-transfer.v1","version":"2.4.34","records":records,
 "method":"leave-one-development-target-out pairwise transfer; held-out target contributes no labels to model training; tie-aware max-equivalence evaluation",
 "production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"loto_pairwise_transfer_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
