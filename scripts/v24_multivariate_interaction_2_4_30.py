#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
from synbiocrow.v24.multivariate_interaction_2_4_30 import design

def r2(y,p):
 y=np.asarray(y,float);p=np.asarray(p,float);ssr=((y-p)**2).sum();sst=((y-y.mean())**2).sum()
 return float(1-ssr/sst) if sst>0 else None

def rmse(y,p):
 y=np.asarray(y,float);p=np.asarray(p,float);return float(np.sqrt(np.mean((y-p)**2)))

def corr(x,y):
 x=np.asarray(x,float);y=np.asarray(y,float)
 if len(x)<3 or np.std(x)==0 or np.std(y)==0:return None
 return float(np.corrcoef(x,y)[0,1])

def folds(n,k=5,seed=2430):
 rng=np.random.default_rng(seed);idx=np.arange(n);rng.shuffle(idx);return np.array_split(idx,k)

def eval_cv(X,y,factory,k=5):
 X=np.asarray(X,float);y=np.asarray(y,float);pred=np.empty(len(y),float)
 for test in folds(len(y),min(k,len(y))):
  train=np.setdiff1d(np.arange(len(y)),test)
  if len(train)<3:
   pred[test]=y[train].mean() if len(train) else y.mean();continue
  m=factory();m.fit(X[train],y[train]);pred[test]=m.predict(X[test])
 return {"cv_r2":r2(y,pred),"cv_rmse":rmse(y,pred),"cv_pearson":corr(y,pred)}

def perm_importance(model,X,y,n_repeats=5,seed=2431):
 X=np.asarray(X,float);y=np.asarray(y,float);base=rmse(y,model.predict(X));rng=np.random.default_rng(seed);out=[]
 for j in range(X.shape[1]):
  vals=[]
  for _ in range(n_repeats):
   Xp=X.copy();Xp[:,j]=rng.permutation(Xp[:,j]);vals.append(rmse(y,model.predict(Xp))-base)
  out.append(float(np.mean(vals)))
 return out

def interaction_surface(model,X,names,a,b,grid_n=7):
 X=np.asarray(X,float);ia=names.index(a);ib=names.index(b);base=np.median(X,axis=0)
 qa=np.quantile(X[:,ia],np.linspace(.05,.95,grid_n));qb=np.quantile(X[:,ib],np.linspace(.05,.95,grid_n))
 grid=[]
 for va in qa:
  for vb in qb:
   z=base.copy();z[ia]=va;z[ib]=vb
   grid.append({"a":float(va),"b":float(vb),"prediction":float(model.predict(z.reshape(1,-1))[0])})
 return {"feature_a":a,"feature_b":b,"grid":grid}

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True)
 a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"}
 sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 aby={r["record_id"]:r["candidate_audit"] for r in aud};rby={}
 for r in ranked:rby.setdefault(r["record_id"],[]).append(r)

 from sklearn.linear_model import Ridge
 from sklearn.ensemble import RandomForestRegressor,GradientBoostingRegressor

 rec=[]
 for rid in sorted(dev):
  aa={x["candidate_id"]:x for x in aby[rid]};rows=[]
  for r in rby[rid]:
   cid=str(r["route_id"]).removeprefix("candidate:")
   if cid in aa:
    x=dict(r);x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");rows.append(x)

  X0,y,ids,names0=design(rows,False)
  Xi,yi,idsi,namesi=design(rows,True)
  frozen=[next(r.get("coverage_adjusted_score") for r in rows if r["route_id"]==rid2) for rid2 in ids]
  frozen_metrics={"pearson_vs_similarity":corr(frozen,y),"r2_direct":r2(y,frozen),"rmse_direct":rmse(y,frozen)}

  models={
   "ridge_linear":(X0,names0,lambda:Ridge(alpha=1.0)),
   "ridge_interactions":(Xi,namesi,lambda:Ridge(alpha=1.0)),
   "random_forest":(X0,names0,lambda:RandomForestRegressor(n_estimators=250,max_depth=8,min_samples_leaf=5,random_state=2430,n_jobs=-1)),
   "gradient_boosting":(X0,names0,lambda:GradientBoostingRegressor(n_estimators=180,max_depth=3,learning_rate=0.03,subsample=0.8,random_state=2430)),
  }
  mres={};fitted={}
  for name,(X,names,factory) in models.items():
   cv=eval_cv(X,y,factory,5)
   m=factory();m.fit(np.asarray(X,float),np.asarray(y,float));fitted[name]=(m,np.asarray(X,float),names)
   imp=perm_importance(m,X,y,5);order=np.argsort(np.abs(imp))[::-1][:12]
   mres[name]={**cv,"top_permutation_importance":[{"term":names[i],"delta_rmse":imp[i]} for i in order]}
  gb,gbX,gbnames=fitted["gradient_boosting"]
  surfaces=[
   interaction_surface(gb,gbX,gbnames,"precedent_step_fraction","step_feasibility_mean"),
   interaction_surface(gb,gbX,gbnames,"precedent_step_fraction","route_length"),
   interaction_surface(gb,gbX,gbnames,"step_feasibility_mean","route_length"),
  ]
  rec.append({"record_id":rid,"candidate_count":len(y),"frozen_score_baseline":frozen_metrics,"models":mres,"gradient_boosting_interaction_surfaces":surfaces})

 summary={"schema":"synbiocrow.v24.nonlinear-multivariate-interaction-audit.v1","version":"2.4.30","records":rec,
 "models":["ridge_linear","ridge_interactions","random_forest","gradient_boosting"],
 "evaluation":"5-fold development-only cross-validation; permutation importance; gradient-boosting interaction surfaces",
 "production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,
 "sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"nonlinear_multivariate_interaction_audit.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
