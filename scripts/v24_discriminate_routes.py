#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from synbiocrow.v24.discrimination import EvidenceValue, RouteEvidence, rank_development_routes, result_dict

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--evidence-json",required=True)
    ap.add_argument("--split-manifest",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    manifest=json.loads(Path(args.split_manifest).read_text())
    split_by_id={x["record_id"]:x["split"] for x in manifest["records"]}
    raw=json.loads(Path(args.evidence_json).read_text())
    routes=[]
    for r in raw.get("routes",[]):
        rid=r["target_record_id"]
        split=split_by_id.get(rid)
        if split is None:
            raise ValueError(f"target absent from frozen split manifest: {rid}")
        comps={
            k:EvidenceValue(
                v.get("value"),
                tuple(v.get("source_ids",[])),
                str(v.get("note","")),
            )
            for k,v in r.get("components",{}).items()
        }
        routes.append(RouteEvidence(
            route_id=r["route_id"],target_record_id=rid,split=split,
            components=comps,route_length=r.get("route_length"),
        ))
    scored=rank_development_routes(routes)
    out={
        "schema":"synbiocrow.v24.discrimination.v1",
        "policy":"2.4.12 evidence-first equal-component provisional score; coverage-adjusted; development-only",
        "split_manifest_sha256":manifest.get("manifest_sha256"),
        "routes":[result_dict(x) for x in scored],
    }
    Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "route_count":len(scored),
        "targets":sorted(set(x.target_record_id for x in scored)),
        "output":args.out,
    },indent=2))

if __name__=="__main__":
    main()
