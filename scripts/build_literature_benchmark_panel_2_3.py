from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--normalized-benchmark",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    src=Path(args.normalized_benchmark)
    payload=json.loads(src.read_text(encoding="utf-8"))
    targets=[]
    exclusions=[]
    benchmark_records=0

    for rec in payload.get("records",[]):
        if rec.get("split")!="benchmark":
            continue
        benchmark_records += 1
        base={
            "target_id":rec["pathway_id"],
            "target_name":rec["target_name"],
            "chemical_class":"literature_benchmark",
            "sink_smiles":list(rec.get("chassis",{}).get("source_metabolites") or []),
            "chassis":rec.get("chassis",{}).get("organism"),
            "applicable_backends":["doranet","retrobiocat2","retropath_standalone"],
        }
        if not rec.get("target_smiles"):
            exclusions.append({
                "target_id":rec["pathway_id"],
                "target_name":rec["target_name"],
                "status":"MAPPING_LIMITED",
                "reason":"Normalized benchmark record has no usable target_smiles; retained in 65-path denominator but excluded from prediction execution."
            })
            continue
        base["target_smiles"]=rec["target_smiles"]
        base["notes"]="Truth-stripped held-out benchmark input derived from Galaxy-SynBioCAD Supplementary Dataset 2."
        targets.append(base)

    out={
        "schema":"synbiocrow.literature_prediction_panel.v2",
        "panel_id":"galaxy_literature_benchmark_truth_stripped",
        "source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
        "truth_accessed_for_panel_construction":True,
        "truth_fields_in_output":False,
        "benchmark_record_count":benchmark_records,
        "runnable_target_count":len(targets),
        "excluded_target_count":len(exclusions),
        "excluded_targets":exclusions,
        "targets":targets,
    }
    Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "benchmark_record_count":benchmark_records,
        "runnable_target_count":len(targets),
        "excluded_target_count":len(exclusions),
        "excluded_targets":exclusions,
        "truth_fields_in_output":False,
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
