#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
from synbiocrow import SynBioCrowEngine
from synbiocrow.execution import json_safe
from synbiocrow.ensemble import resolve_compound
from rdkit import Chem

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class FrozenSinkEvaluator:
    """RBC2 StartingMaterialEvaluator-compatible closure over the frozen sink panel."""
    def __init__(self, sinks):
        self.target_always_not_buyable=True
        self._sink_canon={self._canon(x) for x in sinks}
    def _canon(self,smi):
        mol=Chem.MolFromSmiles(str(smi))
        if mol is None:
            return str(smi)
        return Chem.MolToSmiles(mol,canonical=True,isomericSmiles=True)
    def eval(self,smi):
        c=self._canon(smi)
        return (c in self._sink_canon, {"source":"synbiocrow_frozen_sink_panel","canonical_smiles":c})
    def is_mol_chiral(self,smi):
        mol=Chem.MolFromSmiles(str(smi))
        if mol is None:
            return False
        return bool(Chem.FindMolChiralCenters(mol,includeUnassigned=True))

def main():
    ap=argparse.ArgumentParser()
    for x in ("tranche","split_manifest","sink_panel","out_dir","state_dir"):
        ap.add_argument("--"+x.replace("_","-"),required=True)
    ap.add_argument("--max-route-steps",type=int,default=8)
    ap.add_argument("--max-routes",type=int,default=100)
    a=ap.parse_args()
    tranche=json.loads(Path(a.tranche).read_text())
    manifest=json.loads(Path(a.split_manifest).read_text())
    panel=json.loads(Path(a.sink_panel).read_text())
    sinks=tuple(x["smiles"] for x in panel["sinks"])
    if not sinks: raise ValueError("sink panel cannot be empty")
    sink_evaluator=FrozenSinkEvaluator(sinks)
    recs={r["record_id"]:r for r in tranche["records"]}
    dev=[x for x in manifest["records"] if x["split"]=="development"]
    sealed={x["record_id"] for x in manifest["records"] if x["split"]!="development"}
    engine=SynBioCrowEngine(); readiness=engine.backend_readiness()
    available=tuple(k for k,v in readiness.items() if v.get("available"))
    required={"doranet","retrobiocat2"}
    missing=sorted(required-set(available))
    if missing: raise RuntimeError("required 2.4.13.3 backends unavailable: "+", ".join(missing))
    selected=tuple(x for x in ("doranet","retrobiocat2","retropath_standalone","retropath2","biopks_retrotide") if x in available)
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"backend_readiness.json").write_text(json.dumps(readiness,indent=2,sort_keys=True)+"\n")
    results=[]
    for i,item in enumerate(dev,1):
        rid=item["record_id"]
        if rid in sealed: raise RuntimeError("validation firewall violation")
        r=recs[rid]
        print(f"[2.4.13.3] target {i}/4 | {r['target_name']} | backends={selected}",flush=True)
        target=r["normalized_target"]
        candidates=[]
        backend_status={}
        for bid in selected:
            backend=engine.backends.get(bid)
            try:
                opts={}
                if bid=="retrobiocat2":
                    opts={
                        "max_search_time":30.0,
                        "max_iterations":750,
                        "max_length":6,
                        "starting_material_evaluator":sink_evaluator,
                    }
                found=list(backend.generate(target,options=opts))
                candidates.extend(found)
                backend_status[bid]={"status":"COMPLETE","candidate_count":len(found)}
            except Exception as exc:
                backend_status[bid]={
                    "status":"ERROR",
                    "error_type":type(exc).__name__,
                    "error":str(exc),
                }

        graph=engine.build_ensemble(candidates)
        target_key=resolve_compound(target,source="request").key
        sink_keys={resolve_compound(x,source="request").key for x in sinks}
        routes=graph.find_routes(
            target_key,sink_keys,
            max_steps=a.max_route_steps,
            max_routes=a.max_routes,
        )
        payload={
            "request":{
                "target_smiles":target,
                "mode":"biosynthesis",
                "backend_ids":list(selected),
                "sink_smiles":list(sinks),
                "max_route_steps":a.max_route_steps,
                "max_routes":a.max_routes,
                "retrobiocat2_policy":"frozen_sink_panel_custom_evaluator",
            },
            "candidates":json_safe(candidates),
            "routes":routes,
            "backend_status":backend_status,
            "graph_summary":{
                "compound_count":len(graph.compounds),
                "edge_count":len(graph.edges),
                "backends":list(graph.backend_set()),
                "composite_edge_count":graph.composite_edge_count(),
            },
            "diagnostics":{
                "mode":"biosynthesis",
                "selected_backends":list(selected),
                "scientific_state":"CANDIDATE_ONLY",
                "commercial_source_database_used":False,
            },
        }
        row={"record_id":rid,"target_name":r["target_name"],"split":"development","result":payload}
        (out/f"{rid}.json").write_text(json.dumps(row,indent=2,sort_keys=True)+"\n")
        results.append({"record_id":rid,"target_name":r["target_name"],
            "candidate_count":len(payload["candidates"]),"route_count":len(payload["routes"]),
            "backend_status":payload["backend_status"],"graph_summary":payload["graph_summary"]})
    summary={"schema":"synbiocrow.v24.development-generation.v3","version":"2.4.13.3",
      "split_manifest_sha256":manifest.get("manifest_sha256"),"sink_panel_sha256":panel["panel_sha256"],
      "sink_count":len(sinks),"selected_backends":list(selected),"sealed_validation_record_ids":sorted(sealed),
      "targets":results,
      "rbc2_starting_material_policy":"frozen_sink_panel_custom_evaluator",
      "commercial_source_database_used":False,
      "validation_truth_accessed":False,"tuning_performed":False}
    (out/"generation_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
