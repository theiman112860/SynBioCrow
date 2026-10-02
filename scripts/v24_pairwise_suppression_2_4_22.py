#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.pairwise_suppression_2_4_22 import audit_target,compare_failed_policy
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--decomposition",required=True);ap.add_argument("--failed-policy-summary",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());dec=json.loads(Path(a.decomposition).read_text());failed=json.loads(Path(a.failed_policy_summary).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 ids={r["record_id"] for r in dec["records"] if r["failure_mode"]=="RANKING_LIMITED"}
 aby={r["record_id"]:r["candidate_audit"] for r in aud};rby={}
 for r in ranked:rby.setdefault(r["record_id"],[]).append(r)
 records=[]
 for rid in sorted(ids):
  best=max(aby[rid],key=lambda x:(x["internal_anchor_similarity_mean"] if x["internal_anchor_similarity_mean"] is not None else -1))
  records.append({"record_id":rid,**audit_target(rby[rid],best)})
 fp=compare_failed_policy(failed)
 if not fp["all_worsened"]:raise ValueError("2.4.21 failure premise not satisfied")
 summary={"schema":"synbiocrow.v24.pairwise-suppression-audit.v1","version":"2.4.22",
 "failed_2_4_21_policy":fp,"records":records,"development_record_ids":sorted(dev),
 "sealed_nondevelopment_record_ids":sorted(sealed),"ranking_changed":False,"generation_invoked":False,
 "validation_truth_accessed":False,"evaluation_truth_accessed":False}
 (out/"pairwise_suppression_audit.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
