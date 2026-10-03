#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.multivariate_route_space_2_4_27 import (
 EVIDENCE_FEATURES,zscore_matrix,euclidean_distance_matrix,pathway_distance_matrix,
 mantel_style,classical_mds,pca
)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--decomposition",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());dec=json.loads(Path(a.decomposition).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 rby={};[rby.setdefault(r["record_id"],[]).append(r) for r in ranked]
 aby={r["record_id"]:r["candidate_audit"] for r in aud}
 records=[]
 for rid in sorted(dev):
  rr=rby[rid]; aa={x["candidate_id"]:x for x in aby[rid]}
  joined=[]
  for r in rr:
   cid=str(r["route_id"]).removeprefix("candidate:")
   if cid in aa:
    x=dict(r);x["candidate_id"]=cid;x["internal_anchor_similarity_mean"]=aa[cid].get("internal_anchor_similarity_mean");x["anchor_near_misses"]=aa[cid].get("anchor_near_misses") or [];joined.append(x)
  X,stats=zscore_matrix(joined)
  De=euclidean_distance_matrix(X)
  Dp,pathX=pathway_distance_matrix(joined)
  pc,evr,load=pca(X,2)
  mds_e,_=classical_mds(De,2);mds_p,_=classical_mds(Dp,2)
  concord=mantel_style(De,Dp,permutations=250)
  points=[]
  for i,x in enumerate(joined):
   points.append({"route_id":x["route_id"],"rank_2_4_16":x["rank"],"score":x.get("coverage_adjusted_score"),
    "source_backends":x.get("source_backends"),"internal_anchor_similarity_mean":x.get("internal_anchor_similarity_mean"),
    "evidence_pc1":pc[i][0],"evidence_pc2":pc[i][1],"evidence_mds1":mds_e[i][0],"evidence_mds2":mds_e[i][1],
    "pathway_mds1":mds_p[i][0],"pathway_mds2":mds_p[i][1]})
  records.append({"record_id":rid,"candidate_count":len(joined),"feature_stats":stats,"pca_explained_variance_ratio":evr[:2],
    "pca_loadings":{"pc1":dict(zip(EVIDENCE_FEATURES,load[0])) if load else {},"pc2":dict(zip(EVIDENCE_FEATURES,load[1])) if len(load)>1 else {}},
    "evidence_vs_pathway_distance_concordance":concord,"points":points})
 summary={"schema":"synbiocrow.v24.multivariate-route-space.v1","version":"2.4.27","records":records,
 "development_record_ids":sorted(dev),"sealed_nondevelopment_record_ids":sorted(sealed),
 "analysis":["z-scored evidence feature PCA","classical MDS of evidence distance","classical MDS of corrected pathway-proximity distance","Mantel-style permutation concordance"],
 "production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False}
 (out/"multivariate_route_space_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps({k:v for k,v in summary.items() if k!="records"}|{"records":[{"record_id":r["record_id"],"candidate_count":r["candidate_count"],"concordance":r["evidence_vs_pathway_distance_concordance"],"pca_evr":r["pca_explained_variance_ratio"]} for r in records]},indent=2))
if __name__=="__main__":main()
