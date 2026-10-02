#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from synbiocrow.v24.evidence_enrichment_2_4_15 import enrich_artifact

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",required=True); ap.add_argument("--split-manifest",required=True)
    ap.add_argument("--cache",required=True); ap.add_argument("--out-dir",required=True)
    ap.add_argument("--max-new-edges",type=int,default=750)
    a=ap.parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    man=json.loads(Path(a.split_manifest).read_text())
    dev=[r for r in man["records"] if r["split"]=="development"]
    sealed=[r["record_id"] for r in man["records"] if r["split"]!="development"]
    results=[]; rows=[]
    for i,r in enumerate(dev,1):
        p=Path(a.input_dir)/(r["record_id"]+".json")
        if not p.is_file(): raise FileNotFoundError(p)
        res=enrich_artifact(p,Path(a.cache),max_new_edges=a.max_new_edges)
        results.append(res); rows.extend(res["candidate_rows"])
        (out/(r["record_id"]+"_evidence.json")).write_text(json.dumps(res,indent=2,sort_keys=True)+"\n")
        print(f"[2.4.15] target {i}/{len(dev)} {r['target_name']}: candidates={len(res['candidate_rows'])} unique_edges={res['unique_edge_count']} new_queries={res['new_edge_queries']}",flush=True)
    # transparent evidence ranking: connectivity/context first, then shorter route.
    by={}
    for x in rows: by.setdefault(x["record_id"],[]).append(x)
    ranked=[]
    for rid,rr in by.items():
        rr.sort(key=lambda x:(-x["rhea_connectivity_fraction"],-x["ec_context_fraction"],
                              -x["reviewed_ec_context_fraction"],x["route_length"],x["route_id"]))
        for rank,x in enumerate(rr,1):
            y=dict(x); y["rank"]=rank; ranked.append(y)
    (out/"enriched_candidate_rows.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (out/"enriched_ranked_routes.json").write_text(json.dumps(ranked,indent=2,sort_keys=True)+"\n")
    with (out/"enriched_ranked_routes.csv").open("w",newline="",encoding="utf-8") as fh:
        cols=["record_id","target_name","route_id","rank","rhea_connectivity_fraction",
              "ec_context_fraction","reviewed_ec_context_fraction","evidence_query_coverage",
              "unqueried_edge_count","route_length"]
        w=csv.DictWriter(fh,fieldnames=cols);w.writeheader()
        for x in ranked:w.writerow({k:x.get(k) for k in cols})
    summary={"schema":"synbiocrow.v24.evidence-enrichment-run.v1","version":"2.4.15",
      "development_record_ids":[r["record_id"] for r in dev],"sealed_nondevelopment_record_ids":sealed,
      "generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,
      "candidate_count":len(rows),"targets":results,
      "ranking_semantics":"context evidence is used for discrimination only and is not exact reaction proof or certification"}
    (out/"evidence_enrichment_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"candidate_count":len(rows),"sealed":sealed},indent=2))
if __name__=="__main__":main()
