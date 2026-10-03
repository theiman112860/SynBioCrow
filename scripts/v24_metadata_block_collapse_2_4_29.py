#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.metadata_block_collapse_2_4_29 import score
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"};aby={r["record_id"]:r["candidate_audit"] for r in aud};rby={}
 for r in ranked:rby.setdefault(r["record_id"],[]).append(r)
 records=[]
 for rid in sorted(dev):
  aa={x["candidate_id"]:x for x in aby[rid]};rows=[]
  for r in rby[rid]:
   cid=str(r["route_id"]).removeprefix("candidate:")
   if cid in aa:
    x=dict(r);x["candidate_id"]=cid;x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");x["collapsed_score"]=score(x);rows.append(x)
  rows.sort(key=lambda x:(-(x["collapsed_score"] if x["collapsed_score"] is not None else -1e99),int(x.get("rank") or 10**9),x["route_id"]))
  for i,x in enumerate(rows,1):x["collapsed_rank"]=i
  best=max(rows,key=lambda x:x["similarity"] if x["similarity"] is not None else -1)
  records.append({"record_id":rid,"candidate_count":len(rows),"best_internal_anchor_candidate_id":best["candidate_id"],"similarity":best["similarity"],"frozen_rank":int(best["rank"]),"collapsed_rank":best["collapsed_rank"],"rank_change":int(best["rank"])-best["collapsed_rank"],"frozen_score":best.get("coverage_adjusted_score"),"collapsed_score":best["collapsed_score"]})
 summary={"schema":"synbiocrow.v24.metadata-block-collapse.v1","version":"2.4.29","counterfactual":"collapse template/domain/type into one metadata block while preserving combined frozen weight 0.50","records":records,"production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"metadata_block_collapse_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
