#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.backend_bias_audit_2_4_26 import audit
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--anchor-audit",required=True);ap.add_argument("--decomposition",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 ranked=json.loads(Path(a.ranked).read_text());anc=json.loads(Path(a.anchor_audit).read_text());dec=json.loads(Path(a.decomposition).read_text());man=json.loads(Path(a.split_manifest).read_text());out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ids={r["record_id"] for r in dec["records"] if r["failure_mode"]=="RANKING_LIMITED"};rby={};[rby.setdefault(x["record_id"],[]).append(x) for x in ranked];aby={x["record_id"]:x["candidate_audit"] for x in anc}
 rec=[]
 for rid in sorted(ids):
  best=max(aby[rid],key=lambda x:x["internal_anchor_similarity_mean"] if x["internal_anchor_similarity_mean"] is not None else -1)
  rec.append({"record_id":rid,**audit(rby[rid],"candidate:"+best["candidate_id"])})
 s={"schema":"synbiocrow.v24.backend-bias-audit.v1","version":"2.4.26","records":rec,"ranking_policy_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False}
 (out/"backend_bias_audit_summary.json").write_text(json.dumps(s,indent=2,sort_keys=True)+"\n");print(json.dumps(s,indent=2))
if __name__=="__main__":main()
