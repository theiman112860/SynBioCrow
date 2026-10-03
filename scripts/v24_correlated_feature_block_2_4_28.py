#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.correlated_feature_block_2_4_28 import *
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
    x=dict(r);x["sim"]=aa[cid].get("internal_anchor_similarity_mean");x["collapsed_metadata_block"]=collapsed_block_score(x);rows.append(x)
  st=block_stats(rows);st["record_id"]=rid;st["candidate_count"]=len(rows)
  st["correlation_with_pathway_similarity"]={"frozen_score":pearson([r.get("coverage_adjusted_score") for r in rows],[r.get("sim") for r in rows]),"template":pearson([r.get("template_metadata_fraction") for r in rows],[r.get("sim") for r in rows]),"domain":pearson([r.get("reaction_domain_fraction") for r in rows],[r.get("sim") for r in rows]),"type":pearson([r.get("reaction_type_fraction") for r in rows],[r.get("sim") for r in rows]),"collapsed_metadata_block":pearson([r.get("collapsed_metadata_block") for r in rows],[r.get("sim") for r in rows])}
  records.append(st)
 summary={"schema":"synbiocrow.v24.correlated-feature-block-audit.v1","version":"2.4.28","hypothesis":"template/domain/type coverage form a highly redundant metadata block and should not be interpreted as three independent biochemical evidence dimensions","records":records,"production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"correlated_feature_block_audit.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
