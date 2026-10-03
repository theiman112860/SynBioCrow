#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.multivariate_route_space_2_4_27_1 import *
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 rby={};[rby.setdefault(r["record_id"],[]).append(r) for r in ranked];aby={r["record_id"]:r["candidate_audit"] for r in aud}
 records=[]
 for rid in sorted(dev):
  aa={x["candidate_id"]:x for x in aby[rid]};joined=[]
  for r in rby[rid]:
   cid=str(r["route_id"]).removeprefix("candidate:")
   if cid in aa:
    x=dict(r);x["internal_anchor_similarity_mean"]=aa[cid].get("internal_anchor_similarity_mean");x["anchor_near_misses"]=aa[cid].get("anchor_near_misses") or [];joined.append(x)
  Xe,stats=zscore_matrix(joined);Xp=pathway_profiles(joined);pc,evr,load=pca(Xe,2)
  subset=deterministic_subset(joined,max_n=300)
  De=distance_matrix(Xe,subset);Dp=distance_matrix(Xp,subset)
  mde,_=classical_mds_from_matrix(De,2);mdp,_=classical_mds_from_matrix(Dp,2)
  conc=sampled_concordance(Xe,Xp,max_pairs=50000,permutations=100)
  smap={idx:k for k,idx in enumerate(subset)}
  pts=[]
  for i,x in enumerate(joined):
   k=smap.get(i)
   pts.append({"route_id":x["route_id"],"rank_2_4_16":x["rank"],"score":x.get("coverage_adjusted_score"),"source_backends":x.get("source_backends"),"internal_anchor_similarity_mean":x.get("internal_anchor_similarity_mean"),"evidence_pc1":pc[i][0],"evidence_pc2":pc[i][1],"evidence_mds1":None if k is None else mde[k][0],"evidence_mds2":None if k is None else mde[k][1],"pathway_mds1":None if k is None else mdp[k][0],"pathway_mds2":None if k is None else mdp[k][1],"in_mds_subset":k is not None})
  records.append({"record_id":rid,"candidate_count":len(joined),"mds_subset_count":len(subset),"feature_stats":stats,"pca_explained_variance_ratio":evr[:2],"pca_loadings":{"pc1":dict(zip(EVIDENCE_FEATURES,load[0])) if load else {},"pc2":dict(zip(EVIDENCE_FEATURES,load[1])) if len(load)>1 else {}},"evidence_vs_pathway_distance_concordance":conc,"points":pts})
 summary={"schema":"synbiocrow.v24.multivariate-route-space.v1","version":"2.4.27.1","repair":"bounded pair sampling and deterministic MDS subset; PCA exact on all candidates","records":records,"development_record_ids":sorted(dev),"sealed_nondevelopment_record_ids":sorted(sealed),"production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False}
 (out/"multivariate_route_space_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"version":"2.4.27.1","records":[{"record_id":r["record_id"],"n":r["candidate_count"],"mds_n":r["mds_subset_count"],"pca_evr":r["pca_explained_variance_ratio"],"concordance":r["evidence_vs_pathway_distance_concordance"]} for r in records]},indent=2))
if __name__=="__main__":main()
