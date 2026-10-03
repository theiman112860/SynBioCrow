#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.precedent_semantics_2_4_26 import audit_record
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input-dir",required=True);ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--decomposition",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);ranked=json.loads(Path(a.ranked).read_text());near=json.loads(Path(a.audit).read_text());dec=json.loads(Path(a.decomposition).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"};ids={r["record_id"] for r in dec["records"] if r["failure_mode"]=="RANKING_LIMITED"}
 aby={r["record_id"]:r["candidate_audit"] for r in near};rby={}
 for r in ranked:rby.setdefault(r["record_id"],[]).append(r)
 records=[]
 for rid in sorted(ids):
  p=Path(a.input_dir)/(rid+".json");obj=json.loads(p.read_text());assert obj["split"]=="development"
  best=max(aby[rid],key=lambda x:x["internal_anchor_similarity_mean"] if x["internal_anchor_similarity_mean"] is not None else -1);target="candidate:"+best["candidate_id"];tr=next(r for r in rby[rid] if r["route_id"]==target);rank=int(tr["rank"])
  above=sorted([r for r in rby[rid] if int(r["rank"])<rank],key=lambda x:int(x["rank"]))
  picks=[] if not above else [above[i]["route_id"] for i in sorted(set([0,len(above)//4,len(above)//2,3*len(above)//4,len(above)-1]))]
  rec=audit_record(obj,[target]+picks);rec["near_miss_route_id"]=target;rec["near_miss_rank"]=rank;rec["representative_outranker_route_ids"]=picks;records.append(rec)
 summary={"schema":"synbiocrow.v24.precedent-semantics-audit.v1","version":"2.4.26","records":records,"interpretation_contract":"generator precedent metadata is audited as metadata provenance only; presence is not biochemical or literature-path proof","production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"precedent_semantics_audit.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
