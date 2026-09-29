from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from synbiocrow import DesignRequest, SynBioCrowEngine
from synbiocrow.execution.runner import _candidate_from_dict, _run_id
from synbiocrow.execution.state import RunStateStore
from synbiocrow.ensemble import resolve_compound

GENERAL_BACKENDS=("doranet","retrobiocat2","retropath_standalone")


def load_panel(path:Path)->list[dict]:
    payload=json.loads(path.read_text(encoding="utf-8"))
    return list(payload["targets"])


def load_candidates(stores:list[RunStateStore],target:dict,backend_id:str,max_steps:int,max_routes:int):
    req=DesignRequest(
        target_smiles=target["target_smiles"],
        mode="biosynthesis",
        backend_ids=(backend_id,),
        sink_smiles=tuple(target.get("sink_smiles") or ()),
        max_route_steps=max_steps,
        max_routes=max_routes,
    )
    run_id=_run_id(req)
    for store in stores:
        payload=store.read_stage(run_id,"candidates")
        if payload:
            return [_candidate_from_dict(x) for x in payload.get("candidates",[])],payload
    return [],None


def route_signature(graph,route):
    sig=[]
    for eid in route:
        e=graph.edges[eid]
        sig.append((e.parent_key,tuple(sorted(e.precursor_keys))))
    return tuple(sig)


def routes_for(engine,candidates,target,max_steps,max_routes):
    graph=engine.build_ensemble(candidates)
    target_key=resolve_compound(target["target_smiles"],source="request").key
    sink_keys={resolve_compound(x,source="request").key for x in target.get("sink_smiles",[])}
    routes=graph.find_routes(target_key,sink_keys,max_steps=max_steps,max_routes=max_routes)
    return graph,routes


def audit_target(engine,stores,target,max_steps,max_routes):
    by_backend={}
    union=[]
    for bid in GENERAL_BACKENDS:
        if bid not in set(target.get("applicable_backends") or GENERAL_BACKENDS):
            continue
        candidates,_=load_candidates(stores,target,bid,max_steps,max_routes)
        graph,routes=routes_for(engine,candidates,target,max_steps,max_routes) if candidates else (engine.build_ensemble([]),[])
        by_backend[bid]={
            "candidate_count":len(candidates),
            "graph":graph,
            "routes":routes,
            "route_signatures":{route_signature(graph,r) for r in routes},
        }
        union.extend(candidates)

    ensemble_graph,ensemble_routes=routes_for(engine,union,target,max_steps,max_routes)
    ensemble_sigs={route_signature(ensemble_graph,r) for r in ensemble_routes}
    rows=[]
    for bid,data in by_backend.items():
        for idx,route in enumerate(data["routes"],1):
            sig=route_signature(data["graph"],route)
            missing_edges=[]
            for parent,precursors in sig:
                matching=[
                    e.edge_id for e in ensemble_graph.edges.values()
                    if e.parent_key==parent and tuple(sorted(e.precursor_keys))==precursors
                ]
                if not matching:
                    missing_edges.append({"parent_key":parent,"precursor_keys":list(precursors)})
            rows.append({
                "backend":bid,
                "individual_route_index":idx,
                "individual_edge_count":len(route),
                "all_edges_present_in_ensemble":not missing_edges,
                "missing_edge_count":len(missing_edges),
                "missing_edges":missing_edges,
                "exact_route_returned_by_ensemble_enumerator":sig in ensemble_sigs,
            })

    graph_losses=[r for r in rows if not r["all_edges_present_in_ensemble"]]
    enumeration_losses=[
        r for r in rows
        if r["all_edges_present_in_ensemble"] and not r["exact_route_returned_by_ensemble_enumerator"]
    ]
    return {
        "target_id":target["target_id"],
        "target_name":target["target_name"],
        "backend_route_counts":{b:len(d["routes"]) for b,d in by_backend.items()},
        "ensemble_candidate_count":len(union),
        "ensemble_route_count_returned":len(ensemble_routes),
        "ensemble_route_cap":max_routes,
        "individual_route_audits":rows,
        "graph_monotonicity_violation_count":len(graph_losses),
        "enumeration_truncation_or_order_count":len(enumeration_losses),
        "graph_monotonicity_pass":len(graph_losses)==0,
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",required=True)
    ap.add_argument("--state-root",action="append",required=True,
                    help="State root to search; may be supplied multiple times in priority order")
    ap.add_argument("--output",required=True)
    ap.add_argument("--max-route-steps",type=int,default=8)
    ap.add_argument("--max-routes",type=int,default=100)
    args=ap.parse_args()

    panel=load_panel(Path(args.panel))
    stores=[RunStateStore(Path(x)) for x in args.state_root]
    engine=SynBioCrowEngine()

    results=[]
    for target in panel:
        rec=audit_target(engine,stores,target,args.max_route_steps,args.max_routes)
        if any(rec["backend_route_counts"].values()):
            results.append(rec)
            print(
                f"[AUDIT] {rec['target_id']} individual={rec['backend_route_counts']} "
                f"ensemble={rec['ensemble_route_count_returned']} "
                f"graph_losses={rec['graph_monotonicity_violation_count']} "
                f"enumeration_losses={rec['enumeration_truncation_or_order_count']}",
                flush=True,
            )

    report={
        "schema":"synbiocrow.route_preservation_audit.v1",
        "panel":str(Path(args.panel).resolve()),
        "state_roots":[str(Path(x).resolve()) for x in args.state_root],
        "max_route_steps":args.max_route_steps,
        "max_routes":args.max_routes,
        "targets_with_individual_routes":len(results),
        "targets":results,
        "total_graph_monotonicity_violations":sum(x["graph_monotonicity_violation_count"] for x in results),
        "total_enumeration_losses":sum(x["enumeration_truncation_or_order_count"] for x in results),
        "interpretation":{
            "graph_monotonicity_violation":"An individual route contains at least one normalized reaction edge absent from the union graph; this indicates a union/identity/direction defect.",
            "enumeration_loss":"All individual route edges remain in the union graph, but the exact route was not returned within the ensemble route enumeration cap/order. This is not loss of chemical graph reachability.",
        },
        "truth_accessed":False,
    }
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "targets_with_individual_routes":report["targets_with_individual_routes"],
        "total_graph_monotonicity_violations":report["total_graph_monotonicity_violations"],
        "total_enumeration_losses":report["total_enumeration_losses"],
        "output":str(out),
        "truth_accessed":False,
    },indent=2))
    return 1 if report["total_graph_monotonicity_violations"] else 0


if __name__=="__main__":
    raise SystemExit(main())
