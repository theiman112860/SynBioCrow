#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.ranking_attribution_2_4_20 import attribute
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--decomposition",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);ranked=json.loads(Path(a.ranked).read_text());audit=json.loads(Path(a.audit).read_text());dec=json.loads(Path(a.decomposition).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 ranking_ids={r["record_id"] for r in dec["records"] if r["failure_mode"]=="RANKING_LIMITED"};generation_ids={r["record_id"] for r in dec["records"] if "GENERATION" in r["failure_mode"]}
 aby={r["record_id"]:r["candidate_audit"] for r in audit}
 rows=[attribute(ranked,aby[rid],rid) for rid in sorted(ranking_ids)]
 summary={"schema":"synbiocrow.v24.ranking-feature-attribution.v1","version":"2.4.20","ranking_limited_record_ids":sorted(ranking_ids),"generation_repair_record_ids":sorted(generation_ids),"records":rows,"development_record_ids":sorted(dev),"sealed_nondevelopment_record_ids":sorted(sealed),"ranking_weights_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"truth_use":"development-only target-excluded internal-anchor similarity"}
 (out/"ranking_feature_attribution.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
