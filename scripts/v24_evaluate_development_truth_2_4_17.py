#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from synbiocrow.v24.development_truth_2_4_17 import resolve_truth,evaluate_record

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--input-dir",required=True);ap.add_argument("--ranked-json",required=True)
 ap.add_argument("--truth",required=True);ap.add_argument("--split-manifest",required=True)
 ap.add_argument("--cache");ap.add_argument("--out-dir",required=True)
 a=ap.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"}
 sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 truth=json.loads(Path(a.truth).read_text())
 if {r["record_id"] for r in truth["records"]} != dev:raise ValueError("truth file must contain development records only")
 cache={}
 if a.cache and Path(a.cache).is_file():cache=json.loads(Path(a.cache).read_text())
 truth=resolve_truth(truth,cache)
 unresolved=[(r["record_id"],x["name"]) for r in truth["records"] for x in r["anchors"] if not x["canonical_smiles"]]
 (out/"resolved_development_truth_anchors.json").write_text(json.dumps(truth,indent=2,sort_keys=True)+"\n")
 (out/"pubchem_anchor_cache.json").write_text(json.dumps(cache,indent=2,sort_keys=True)+"\n")
 if unresolved:raise RuntimeError("unresolved PubChem anchors: "+repr(unresolved))
 ranked=json.loads(Path(a.ranked_json).read_text())
 by={}
 for x in ranked:by.setdefault(x["record_id"],[]).append(x)
 results=[]
 for tr in truth["records"]:
  rid=tr["record_id"]; p=Path(a.input_dir)/(rid+".json")
  obj=json.loads(p.read_text())
  if obj.get("split")!="development":raise ValueError("sealed split encountered")
  results.append(evaluate_record(obj,tr,by.get(rid,[])))
 summary={
   "schema":"synbiocrow.v24.development-anchor-evaluation.v1","version":"2.4.17",
   "records":[{k:v for k,v in r.items() if k!="candidate_scores"} for r in results],
   "development_record_ids":sorted(dev),"sealed_nondevelopment_record_ids":sorted(sealed),
   "validation_truth_accessed":False,"evaluation_truth_accessed":False,
   "ranking_weights_fit":False,"truth_type":"literature-supported pathway anchors; not exact reaction gold"
 }
 (out/"development_anchor_evaluation.json").write_text(json.dumps(results,indent=2,sort_keys=True)+"\n")
 (out/"development_anchor_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
