#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
from synbiocrow.v24.multivariate_interaction_2_4_30 import design
def ridge(X,y,lam=1.0):
 X=np.asarray(X,float);y=np.asarray(y,float);mu=X.mean(0);sd=X.std(0);sd[sd==0]=1;Z=(X-mu)/sd
 A=Z.T@Z+lam*np.eye(Z.shape[1]);b=Z.T@y;coef=np.linalg.solve(A,b);pred=Z@coef+y.mean()
 ssr=((y-pred)**2).sum();sst=((y-y.mean())**2).sum();r2=1-ssr/sst if sst>0 else None
 return coef.tolist(),r2
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"};aby={r["record_id"]:r["candidate_audit"] for r in aud};rby={}
 for r in ranked:rby.setdefault(r["record_id"],[]).append(r)
 rec=[]
 for rid in sorted(dev):
  aa={x["candidate_id"]:x for x in aby[rid]};rows=[]
  for r in rby[rid]:
   cid=str(r["route_id"]).removeprefix("candidate:")
   if cid in aa:
    x=dict(r);x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");rows.append(x)
  X,y,ids,names=design(rows);coef,r2=ridge(X,y,1.0);order=sorted(range(len(coef)),key=lambda i:-abs(coef[i]))
  rec.append({"record_id":rid,"candidate_count":len(y),"ridge_r2_in_sample":r2,"top_coefficients":[{"term":names[i],"standardized_coefficient":coef[i]} for i in order[:12]]})
 summary={"schema":"synbiocrow.v24.multivariate-interaction-audit.v1","version":"2.4.30","records":rec,"method":"ridge regression on frozen evidence variables plus selected pairwise interactions; development diagnostic only","production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"multivariate_interaction_audit.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
