from __future__ import annotations

import argparse, json, math, os
from dataclasses import asdict
from pathlib import Path

from synbiocrow import DesignRequest, SynBioCrowEngine
from synbiocrow.execution.runner import _candidate_from_dict, _run_id
from synbiocrow.execution.state import RunStateStore
from synbiocrow.ensemble import resolve_compound
from synbiocrow.learning import (
    LearningPolicy, TestOutcome, evidence_aware_route_feature_vector,
)

TARGETS={
    "commodity_butanediol":{
        "target_name":"1,4-butanediol",
        "target_smiles":"OCCCCO",
    },
    "commodity_3hp":{
        "target_name":"3-hydroxypropionic acid",
        "target_smiles":"O=C(O)CCO",
    },
}

def load_panel(path:Path):
    payload=json.loads(path.read_text())
    return {x["target_id"]:x for x in payload["targets"]}

def arm_request(target,backend_id,max_steps,max_routes):
    return DesignRequest(
        target_smiles=target["target_smiles"],
        mode="biosynthesis",
        backend_ids=(backend_id,),
        sink_smiles=tuple(target.get("sink_smiles") or ()),
        max_route_steps=max_steps,
        max_routes=max_routes,
    )

def cached_candidates(target,backend_id,state_root,max_steps,max_routes):
    req=arm_request(target,backend_id,max_steps,max_routes)
    store=RunStateStore(str(state_root))
    payload=store.read_stage(_run_id(req),"candidates")
    if not payload:
        return []
    return [_candidate_from_dict(x) for x in payload.get("candidates",[])]

def build_graph_from_state(target,state_root,max_steps,max_routes):
    engine=SynBioCrowEngine()
    all_candidates=[]
    per_backend={}
    for bid in ("doranet","retrobiocat2","retropath_standalone"):
        found=cached_candidates(target,bid,state_root,max_steps,max_routes)
        per_backend[bid]=len(found)
        all_candidates.extend(found)
    graph=engine.build_ensemble(all_candidates)
    tk=resolve_compound(target["target_smiles"],source="request").key
    sk={resolve_compound(x,source="request").key for x in target.get("sink_smiles",[])}
    routes=graph.find_routes(tk,sk,max_steps=max_steps,max_routes=max_routes) if sk else []
    return engine,graph,routes,per_backend

def evidence_features(engine,graph,route):
    try:
        report=engine.evaluate_route(graph,route)
        features=evidence_aware_route_feature_vector(graph,list(route),report)
        return report,features,None
    except Exception as exc:
        features=evidence_aware_route_feature_vector(graph,list(route),None)
        return None,features,f"{type(exc).__name__}: {exc}"

def reward_from_features(features):
    # Test-stage reward is bounded and evidence-derived.
    # Positive evidence raises priority; FAIL evidence lowers it; abstention is neutral.
    pos=(features.get("closure_pass_fraction",0)+
         features.get("rhea_pass_fraction",0)+
         features.get("thermo_pass_fraction",0)+
         features.get("enzyme_pass_fraction",0))/4.0
    neg=features.get("evidence_fail_fraction",0)
    return max(-1.0,min(1.0,pos-neg))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",required=True)
    ap.add_argument("--state-root",required=True)
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--max-route-steps",type=int,default=8)
    ap.add_argument("--max-routes",type=int,default=100)
    ap.add_argument("--learn-route-limit",type=int,default=20)
    args=ap.parse_args()

    panel=load_panel(Path(args.panel))
    state_root=Path(args.state_root)
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)

    result={
        "schema":"synbiocrow.dbtl_case_study.v1",
        "truth_accessed":False,
        "state_root":str(state_root),
        "design":{},
        "test":{},
        "build":{},
        "learn":{},
    }

    # ---- DESIGN + TEST: 1,4-butanediol ----
    bdo=panel["commodity_butanediol"]
    engine,g,routes,counts=build_graph_from_state(
        bdo,state_root,args.max_route_steps,args.max_routes
    )
    if not routes:
        raise RuntimeError("No cached complete 1,4-butanediol route found")
    chosen=routes[0]
    result["design"]["commodity_butanediol"]={
        "target_name":bdo["target_name"],
        "candidate_counts_by_backend":counts,
        "ensemble_route_count":len(routes),
        "selected_route_edge_ids":list(chosen),
        "selected_route_reactions":[g.edges[e].reaction for e in chosen],
        "selected_route_sources":[list(g.edges[e].source_backends) for e in chosen],
    }
    report,features,err=evidence_features(engine,g,chosen)
    result["test"]["commodity_butanediol"]={
        "feature_vector":features,
        "evaluation_error":err,
        "route_overall":getattr(getattr(report,"overall",None),"value",None) if report else "ABSTAIN",
        "edge_reports":[asdict(x) for x in getattr(report,"edge_reports",())] if report else [],
    }

    # Build stage: intentionally no fabricated sequence evidence.
    result["build"]["commodity_butanediol"]={
        "status":"ABSTAIN_MISSING_VERIFIED_SEQUENCE_INPUTS",
        "reason":"No provenance-backed protein/CDS/regulatory sequences are embedded in the benchmark route artifact. SynBioCrow design_expression_construct is enabled, but this case study does not fabricate sequence evidence.",
        "api_enabled":True,
        "required_inputs":[
            "ProteinEvidence with sequence and provenance",
            "CDSEvidence with nucleotide sequence and matching protein",
            "verified promoter sequence",
            "verified RBS sequence",
            "verified terminator sequence",
        ],
    }

    # ---- LEARN: 3HP alternative routes ----
    hp=panel["commodity_3hp"]
    engine2,g2,routes2,counts2=build_graph_from_state(
        hp,state_root,args.max_route_steps,args.max_routes
    )
    routes2=routes2[:args.learn_route_limit]
    if not routes2:
        raise RuntimeError("No cached complete 3HP routes found")

    before_policy=LearningPolicy(
        route_feature_weights={
            "route_length":-0.10,
            "backend_diversity":0.05,
            "composite_edges":0.05,
            "closure_pass_fraction":0.25,
            "rhea_pass_fraction":0.50,
            "thermo_pass_fraction":0.35,
            "enzyme_pass_fraction":0.50,
            "evidence_fail_fraction":-0.75,
        }
    )
    route_features={}
    outcomes=[]
    test_rows=[]
    for i,route in enumerate(routes2):
        rid=f"3hp-route-{i:03d}"
        rep,feat,err=evidence_features(engine2,g2,route)
        route_features[rid]=feat
        reward=reward_from_features(feat)
        outcomes.append(TestOutcome(
            outcome_id=f"3hp-test-{i:03d}",
            kind="route",
            subject_id=rid,
            reward=reward,
            features=feat,
            source="synbiocrow_evidence_test",
            notes=err,
        ))
        test_rows.append({
            "route_id":rid,
            "edge_ids":list(route),
            "reactions":[g2.edges[e].reaction for e in route],
            "source_backends":[list(g2.edges[e].source_backends) for e in route],
            "features":feat,
            "reward":reward,
            "evidence_error":err,
        })

    before_rank=engine2.rank_routes(route_features,before_policy)
    after_policy,update=engine2.learn(before_policy,outcomes,learning_rate=0.10)
    after_rank=engine2.rank_routes(route_features,after_policy)

    result["design"]["commodity_3hp"]={
        "target_name":hp["target_name"],
        "candidate_counts_by_backend":counts2,
        "ensemble_route_count_total":len(build_graph_from_state(hp,state_root,args.max_route_steps,args.max_routes)[2]),
        "routes_evaluated_for_learning":len(routes2),
    }
    result["test"]["commodity_3hp"]={"routes":test_rows}
    result["learn"]={
        "policy_before":asdict(before_policy),
        "policy_after":asdict(after_policy),
        "update":asdict(update),
        "ranking_before":before_rank,
        "ranking_after":after_rank,
        "top_route_changed":bool(before_rank and after_rank and before_rank[0][0]!=after_rank[0][0]),
        "learning_constraints":{
            "lifecycle_effect":"NONE",
            "missing_evidence_cannot_become_positive_evidence":True,
            "candidate_promotion_not_permitted":True,
        },
    }

    (out/"dbtl_case_study.json").write_text(json.dumps(result,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps({
        "butanediol_routes":result["design"]["commodity_butanediol"]["ensemble_route_count"],
        "butanediol_test":result["test"]["commodity_butanediol"]["route_overall"],
        "build_status":result["build"]["commodity_butanediol"]["status"],
        "3hp_routes_tested":len(routes2),
        "top_before":before_rank[0] if before_rank else None,
        "top_after":after_rank[0] if after_rank else None,
        "top_route_changed":result["learn"]["top_route_changed"],
        "policy_update_digest":result["learn"]["update"]["audit_digest"],
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
