#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
from synbiocrow import SynBioCrowEngine
from synbiocrow.execution import json_safe
from synbiocrow.ensemble import resolve_compound
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

_morgan=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)

def _fp(smiles):
    mol=Chem.MolFromSmiles(str(smiles))
    return None if mol is None else _morgan.GetFingerprint(mol)

def _compound_smiles(graph,key):
    ci=graph.compounds.get(key)
    if ci is None:
        return None
    return getattr(ci,"canonical_smiles",None) or getattr(ci,"smiles",None) or getattr(ci,"raw",None)

def _compound_sets(graph):
    by={"doranet":set(),"retrobiocat2":set()}
    for edge in graph.edges.values():
        keys={edge.parent_key,*edge.precursor_keys}
        for backend in by:
            if backend in edge.source_backends:
                by[backend].update(keys)
    return by

def _bridge_diagnostics(graph,sinks):
    by=_compound_sets(graph)
    overlap=by["doranet"] & by["retrobiocat2"]

    def items(keys):
        out=[]
        for key in sorted(keys):
            smi=_compound_smiles(graph,key)
            fp=_fp(smi) if smi else None
            if fp is not None:
                out.append((key,smi,fp))
        return out

    d_items=items(by["doranet"])
    r_items=items(by["retrobiocat2"])
    cross=[]

    if d_items and r_items:
        r_fps=[x[2] for x in r_items]
        scored=[]
        for dkey,dsmi,dfp in d_items:
            sims=DataStructs.BulkTanimotoSimilarity(dfp,r_fps)
            for j,sim in enumerate(sims):
                rkey,rsmi,_=r_items[j]
                if dkey!=rkey:
                    scored.append((float(sim),dkey,dsmi,rkey,rsmi))
        for sim,dkey,dsmi,rkey,rsmi in sorted(scored,reverse=True)[:20]:
            cross.append({
                "tanimoto":sim,
                "doranet_key":dkey,
                "doranet_smiles":dsmi,
                "retrobiocat2_key":rkey,
                "retrobiocat2_smiles":rsmi,
            })

    sink_rows=[]
    for sink in sinks:
        sfp=_fp(sink)
        row={"sink_smiles":sink}
        if sfp is not None:
            for backend,vals in (("doranet",d_items),("retrobiocat2",r_items)):
                scored=[
                    (float(DataStructs.TanimotoSimilarity(sfp,fp)),key,smi)
                    for key,smi,fp in vals
                ]
                if scored:
                    sim,key,smi=max(scored)
                    row[backend]={
                        "tanimoto":sim,
                        "compound_key":key,
                        "compound_smiles":smi,
                    }
        sink_rows.append(row)

    return {
        "doranet_compound_count":len(by["doranet"]),
        "retrobiocat2_compound_count":len(by["retrobiocat2"]),
        "exact_compound_overlap_count":len(overlap),
        "exact_compound_overlap_keys":sorted(overlap)[:100],
        "top_cross_engine_near_pairs":cross,
        "nearest_compound_to_each_sink":sink_rows,
    }

def _connectivity_key(smiles):
    mol=Chem.MolFromSmiles(str(smiles))
    if mol is None:
        return None
    Chem.RemoveStereochemistry(mol)
    return Chem.MolToSmiles(mol,canonical=True,isomericSmiles=False)

def _reachability_diagnostics(graph,target_key,sink_keys):
    # OR reachability: follows any precursor edge from a target-reachable parent.
    # This does not claim route closure; it only localizes where sink nodes occur.
    reachable={target_key}
    depth={target_key:0}
    frontier=[target_key]
    while frontier:
        parent=frontier.pop(0)
        for eid in graph.by_parent.get(parent,()):
            edge=graph.edges[eid]
            for key in edge.precursor_keys:
                if key not in reachable:
                    reachable.add(key)
                    depth[key]=depth[parent]+1
                    frontier.append(key)
    reached_sinks=sorted(reachable & sink_keys)
    global_sinks=sorted(set(graph.compounds) & sink_keys)
    return {
        "global_sink_keys_present":global_sinks,
        "target_reachable_sink_keys":reached_sinks,
        "target_reachable_sink_depths":{k:depth[k] for k in reached_sinks},
        "target_reachable_compound_count":len(reachable),
        "note":"OR reachability is diagnostic only; full route closure still requires all precursor branches to terminate in sinks.",
    }

def _connectivity_relaxed_diagnostics(graph,target_smiles,sinks,max_steps,max_routes):
    # Collapse only identity granularity (stereochemistry); do not add reactions.
    key_to_conn={}
    for key in graph.compounds:
        smi=_compound_smiles(graph,key)
        ck=_connectivity_key(smi) if smi else None
        if ck: key_to_conn[key]=ck
    tconn=_connectivity_key(target_smiles)
    sconn={x for x in (_connectivity_key(s) for s in sinks) if x}

    by_parent={}
    collapsed_edges={}
    for eid,edge in graph.edges.items():
        pk=key_to_conn.get(edge.parent_key)
        prec=tuple(sorted(key_to_conn.get(k,k) for k in edge.precursor_keys))
        if not pk: continue
        ceid=(pk,prec)
        collapsed_edges.setdefault(ceid,set()).update(edge.source_backends)
        by_parent.setdefault(pk,[]).append(prec)

    exact_alias_groups={}
    for strict,conn in key_to_conn.items():
        exact_alias_groups.setdefault(conn,[]).append(strict)
    merged_groups={k:sorted(v) for k,v in exact_alias_groups.items() if len(v)>1}

    # Same AND semantics as EnsembleGraph.find_routes, but over connectivity keys.
    from collections import deque
    routes=[]
    q=deque([(frozenset([tconn]),tuple())]) if tconn else deque()
    seen=set()
    while q and len(routes)<max_routes:
        frontier,used=q.popleft()
        if frontier.issubset(sconn):
            routes.append(list(used)); continue
        if len(used)>=max_steps: continue
        state=(frontier,used)
        if state in seen: continue
        seen.add(state)
        unresolved=sorted(frontier-sconn)[0]
        for prec in by_parent.get(unresolved,()):
            nf=set(frontier); nf.remove(unresolved); nf.update(prec)
            q.append((frozenset(nf),used+((unresolved,prec),)))

    cross_engine_collapses=0
    for conn,stricts in merged_groups.items():
        backends=set()
        for edge in graph.edges.values():
            if edge.parent_key in stricts or any(k in stricts for k in edge.precursor_keys):
                backends.update(edge.source_backends)
        if {"doranet","retrobiocat2"}.issubset(backends):
            cross_engine_collapses+=1
    return {
        "strict_compound_count":len(graph.compounds),
        "connectivity_compound_count":len(set(key_to_conn.values())),
        "strict_nodes_collapsed":len(graph.compounds)-len(set(key_to_conn.values())),
        "multi_strict_identity_groups":len(merged_groups),
        "cross_engine_connectivity_alias_groups":cross_engine_collapses,
        "connectivity_level_route_count":len(routes),
        "connectivity_level_routes_preview":routes[:10],
        "diagnostic_only":True,
        "no_reactions_added":True,
    }

def _frontier_blocker_audit(graph,target_key,sink_keys,sinks,max_steps=8,max_states=50000):
    # Diagnose why strict AND closure fails. No reactions are added.
    from collections import deque, Counter
    q=deque([(frozenset([target_key]),0)])
    seen=set()
    dead=Counter()
    examples={}
    terminal_states=[]
    while q and len(seen)<max_states:
        frontier,depth=q.popleft()
        state=frontier
        if state in seen:
            continue
        seen.add(state)
        unresolved=sorted(frontier-sink_keys)
        if not unresolved:
            terminal_states.append(sorted(frontier))
            continue
        if depth>=max_steps:
            for key in unresolved:
                dead[(key,"DEPTH_LIMIT")]+=1
                examples.setdefault((key,"DEPTH_LIMIT"),sorted(frontier))
            continue
        key=unresolved[0]
        eids=list(graph.by_parent.get(key,()))
        if not eids:
            dead[(key,"NO_OUTGOING_EDGE")]+=1
            examples.setdefault((key,"NO_OUTGOING_EDGE"),sorted(frontier))
            continue
        advanced=False
        for eid in eids:
            edge=graph.edges[eid]
            nf=set(frontier); nf.remove(key); nf.update(edge.precursor_keys)
            q.append((frozenset(nf),depth+1)); advanced=True
        if not advanced:
            dead[(key,"NO_EXPANSION")]+=1
            examples.setdefault((key,"NO_EXPANSION"),sorted(frontier))

    by=_compound_sets(graph)
    sink_fps=[(s,_fp(s)) for s in sinks if _fp(s) is not None]
    rows=[]
    for (key,reason),count in dead.most_common(50):
        smi=_compound_smiles(graph,key)
        fp=_fp(smi) if smi else None
        nearest=None
        if fp is not None and sink_fps:
            sim,ss=max((float(DataStructs.TanimotoSimilarity(fp,sfp)),ss) for ss,sfp in sink_fps)
            nearest={"sink_smiles":ss,"tanimoto":sim}
        present=[b for b,keys in by.items() if key in keys]
        rows.append({
            "compound_key":key,
            "compound_smiles":smi,
            "reason":reason,
            "blocking_state_count":count,
            "present_in_backends":present,
            "has_outgoing_edge":bool(graph.by_parent.get(key)),
            "nearest_frozen_sink":nearest,
            "example_frontier":examples[(key,reason)][:25],
        })
    return {
        "states_examined":len(seen),
        "state_limit_hit":len(seen)>=max_states,
        "closed_terminal_state_count":len(terminal_states),
        "blocking_compound_count":len(dead),
        "top_blocking_compounds":rows,
        "interpretation":"NO_OUTGOING_EDGE identifies unresolved precursor leaves under the current generated graph; DEPTH_LIMIT identifies branches still expandable beyond the frozen search depth.",
        "diagnostic_only":True,
        "no_reactions_added":True,
    }

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
    if missing: raise RuntimeError("required 2.4.13.9 backends unavailable: "+", ".join(missing))
    selected=tuple(x for x in ("doranet","retrobiocat2","retropath_standalone","retropath2","biopks_retrotide") if x in available)
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"backend_readiness.json").write_text(json.dumps(readiness,indent=2,sort_keys=True)+"\n")
    results=[]
    for i,item in enumerate(dev,1):
        rid=item["record_id"]
        if rid in sealed: raise RuntimeError("validation firewall violation")
        r=recs[rid]
        print(f"[2.4.13.9] target {i}/4 | {r['target_name']} | backends={selected}",flush=True)
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
                        "include_explored_pathways":True,
                    }
                found=list(backend.generate(target,options=opts))
                candidates.extend(found)
                status={"status":"COMPLETE","candidate_count":len(found)}
                if bid=="retrobiocat2":
                    status["mcts_run_stats"]=json_safe(getattr(backend,"last_run_stats",{}))
                    stats=status["mcts_run_stats"] or {}
                    solved=int(stats.get("solved_pathways",stats.get("solved",0)) or 0)
                    reactions=int(stats.get("reactions",0) or 0)
                    molecules=int(stats.get("molecules",0) or 0)
                    iterations=int(stats.get("iterations",0) or 0)
                    if len(found)==0 and solved==0 and (reactions>0 or molecules>1 or iterations>0):
                        status["interpretation"]="MCTS_EXPLORED_NO_SOLVED_PATHWAYS"
                    elif len(found)==0 and solved>0:
                        status["interpretation"]="SOLVED_PATHWAYS_NOT_CONVERTED"
                    elif len(found)==0:
                        status["interpretation"]="NO_EXPANSION_OR_NO_HIT"
                    else:
                        status["interpretation"]="CANDIDATES_RETURNED"
                backend_status[bid]=status
            except Exception as exc:
                backend_status[bid]={
                    "status":"ERROR",
                    "error_type":type(exc).__name__,
                    "error":str(exc),
                }

        graph=engine.build_ensemble(candidates)
        target_key=resolve_compound(target,source="request").key
        sink_keys={resolve_compound(x,source="request").key for x in sinks}

        # Bounded cross-engine frontier handoff. Development targets only.
        # We expand only unresolved organic leaves seen by exactly one engine,
        # and ask the *other* engine to continue them. This adds no inferred
        # reactions: every added edge must be returned by a real backend.
        pre_frontier=_frontier_blocker_audit(graph,target_key,sink_keys,sinks,a.max_route_steps,max_states=10000)
        handoff=[]
        handoff_candidates=[]
        for row in pre_frontier.get("top_blocking_compounds",[]):
            if len(handoff)>=4:
                break
            smi=row.get("compound_smiles")
            present=set(row.get("present_in_backends") or [])
            mol=Chem.MolFromSmiles(str(smi)) if smi else None
            if mol is None:
                continue
            heavy=mol.GetNumHeavyAtoms()
            if heavy < 4 or heavy > 80:
                continue
            if present=={"doranet"}:
                dest="retrobiocat2"
            elif present=={"retrobiocat2"}:
                dest="doranet"
            else:
                continue
            backend=engine.backends.get(dest)
            opts={}
            if dest=="retrobiocat2":
                opts={
                    "max_search_time":15.0,
                    "max_iterations":300,
                    "max_length":4,
                    "starting_material_evaluator":sink_evaluator,
                    "include_explored_pathways":True,
                }
            try:
                found=list(backend.generate(smi,options=opts))
                handoff_candidates.extend(found)
                handoff.append({
                    "frontier_smiles":smi,
                    "from_backends":sorted(present),
                    "to_backend":dest,
                    "reason":row.get("reason"),
                    "candidate_count":len(found),
                    "status":"COMPLETE",
                })
            except Exception as exc:
                handoff.append({
                    "frontier_smiles":smi,
                    "from_backends":sorted(present),
                    "to_backend":dest,
                    "reason":row.get("reason"),
                    "candidate_count":0,
                    "status":"ERROR",
                    "error_type":type(exc).__name__,
                    "error":str(exc),
                })
        if handoff_candidates:
            candidates.extend(handoff_candidates)
            graph=engine.build_ensemble(candidates)

        routes=graph.find_routes(
            target_key,sink_keys,
            max_steps=a.max_route_steps,
            max_routes=a.max_routes,
        )
        bridge_diag=_bridge_diagnostics(graph,sinks)
        reach_diag=_reachability_diagnostics(graph,target_key,sink_keys)
        connectivity_diag=_connectivity_relaxed_diagnostics(graph,target,sinks,a.max_route_steps,a.max_routes)
        frontier_diag=_frontier_blocker_audit(graph,target_key,sink_keys,sinks,a.max_route_steps)
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
            "bridge_diagnostics":bridge_diag,
            "reachability_diagnostics":reach_diag,
            "connectivity_relaxed_diagnostics":connectivity_diag,
            "frontier_blocker_audit":frontier_diag,
            "cross_engine_frontier_handoff":{"attempts":handoff,"added_candidate_count":len(handoff_candidates),"max_handoffs":4,"development_only":True,"validation_truth_accessed":False},
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
    summary={"schema":"synbiocrow.v24.development-generation.v9","version":"2.4.13.9",
      "split_manifest_sha256":manifest.get("manifest_sha256"),"sink_panel_sha256":panel["panel_sha256"],
      "sink_count":len(sinks),"selected_backends":list(selected),"sealed_validation_record_ids":sorted(sealed),
      "targets":results,
      "rbc2_candidate_policy":"all_explored_pathways_marked_partial_unless_solved",
      "rbc2_starting_material_policy":"frozen_sink_panel_custom_evaluator",
      "commercial_source_database_used":False,
      "validation_truth_accessed":False,"tuning_performed":False}
    (out/"generation_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
