#!/usr/bin/env python3
import argparse,json,pickle
from pathlib import Path
from collections import deque,Counter
from rdkit import Chem
from synbiocrow.ensemble.graph import build_reaction_graph
from synbiocrow.ensemble.identity import resolve_compound

def compound_smiles(graph,key):
    ci=graph.compounds.get(key)
    if ci is None: return None
    return getattr(ci,"canonical_smiles",None) or getattr(ci,"smiles",None) or getattr(ci,"raw",None)

def currency_keys(graph):
    keys=set(); rows=[]
    for key in graph.compounds:
        smi=compound_smiles(graph,key)
        mol=Chem.MolFromSmiles(str(smi)) if smi else None
        if mol is None: continue
        atoms=[a.GetSymbol() for a in mol.GetAtoms()]
        heavy=mol.GetNumHeavyAtoms(); p=atoms.count("P"); n=atoms.count("N")
        reason=None
        if smi=="O": reason="water"
        elif heavy<=2 and set(atoms).issubset({"H","O","N","P","S","C"}): reason="small_currency_species"
        elif p>=2 and n>=3 and heavy>=20: reason="nucleotide_cofactor_like"
        if reason:
            keys.add(key); rows.append({"compound_key":key,"compound_smiles":smi,"reason":reason})
    return keys,rows

def mixed_closure(graph,target_key,sink_keys,currency,max_steps=8,max_routes=100):
    terminal=set(sink_keys)|set(currency)
    q=deque([(frozenset([target_key]),tuple())]); seen=set(); admissible=[]; currency_only=[]
    while q and (len(admissible)+len(currency_only))<max_routes:
        frontier,used=q.popleft(); state=(frontier,used)
        if state in seen: continue
        seen.add(state)
        unresolved=frontier-terminal
        if not unresolved:
            rec={"reaction_ids":list(used),
                 "terminal_strict_sink_keys":sorted(frontier & set(sink_keys)),
                 "terminal_currency_keys":sorted(frontier & set(currency))}
            (admissible if rec["terminal_strict_sink_keys"] else currency_only).append(rec)
            continue
        if len(used)>=max_steps: continue
        key=sorted(unresolved)[0]
        for eid in graph.by_parent.get(key,()):
            edge=graph.edges[eid]; nf=set(frontier); nf.remove(key); nf.update(edge.precursor_keys)
            q.append((frozenset(nf),used+(eid,)))
    return {"admissible_route_count":len(admissible),"currency_only_route_count":len(currency_only),
            "admissible_routes_preview":admissible[:10],"currency_only_routes_preview":currency_only[:10]}

def near_miss(graph,target_key,sink_keys,currency,max_steps=8,max_states=25000):
    sinks=set(sink_keys); currency=set(currency)
    q=deque([(frozenset([target_key]),tuple(),frozenset())]); seen=set()
    best_n=None; counts=Counter(); previews=[]; states=0
    while q and states<max_states:
        frontier,used,used_edges=q.popleft(); state=(frontier,used_edges)
        if state in seen: continue
        seen.add(state); states+=1
        strict=frontier & sinks; unresolved=set(frontier)-sinks-currency
        if strict and unresolved:
            n=len(unresolved)
            if best_n is None or n<best_n:
                best_n=n; counts=Counter(); previews=[]
            if n==best_n:
                counts.update(unresolved)
                if len(previews)<20:
                    previews.append({"reaction_ids":list(used),
                                     "unresolved_noncurrency":[{"compound_key":k,
                                         "compound_smiles":compound_smiles(graph,k),
                                         "has_outgoing_edge":bool(graph.by_parent.get(k,()))}
                                         for k in sorted(unresolved)]})
        if len(used)>=max_steps: continue
        expandable=sorted(k for k in unresolved if graph.by_parent.get(k,()))
        if not expandable: continue
        key=expandable[0]
        for eid in graph.by_parent.get(key,()):
            if eid in used_edges: continue
            edge=graph.edges[eid]; nf=set(frontier); nf.remove(key); nf.update(edge.precursor_keys)
            q.append((frozenset(nf),used+(eid,),used_edges|frozenset([eid])))
    ranked=[]
    for k,n in counts.most_common(50):
        ranked.append({"compound_key":k,"compound_smiles":compound_smiles(graph,k),
                       "near_miss_state_count":n,"has_outgoing_edge":bool(graph.by_parent.get(k,()))})
    return {"states_examined":states,"state_limit_hit":bool(q),
            "minimum_unresolved_noncurrency_leaf_count":best_n,
            "ranked_minimum_blockers":ranked,"preview":previews}

ap=argparse.ArgumentParser()
ap.add_argument("--target",required=True)
ap.add_argument("--sink-panel",required=True)
ap.add_argument("--candidate-pickle",action="append",default=[])
ap.add_argument("--out",required=True)
a=ap.parse_args()
panel=json.loads(Path(a.sink_panel).read_text())
sinks=[x["smiles"] for x in panel["sinks"]]
candidates=[]
source_files=[]
for p in a.candidate_pickle:
    with open(p,"rb") as fh: part=pickle.load(fh)
    candidates.extend(part); source_files.append({"path":p,"count":len(part)})
graph=build_reaction_graph(candidates)
target_key=resolve_compound(a.target,source="request").key
sink_keys={resolve_compound(x,source="request").key for x in sinks}
curr,curr_rows=currency_keys(graph)
strict_routes=graph.find_routes(target_key,sink_keys,max_steps=8,max_routes=100)
mixed=mixed_closure(graph,target_key,sink_keys,curr)
miss=near_miss(graph,target_key,sink_keys,curr)
payload={
 "schema":"synbiocrow.v24.mibk-isolated-evaluation.v1",
 "version":"2.4.13.15",
 "target":a.target,
 "candidate_sources":source_files,
 "candidate_count":len(candidates),
 "graph_summary":{"compound_count":len(graph.compounds),"edge_count":len(graph.edges),
                  "backends":list(graph.backend_set()),"composite_edge_count":graph.composite_edge_count()},
 "strict_route_count":len(strict_routes),
 "mixed_boundary":mixed,
 "near_miss":miss,
 "currency_species_count":len(curr_rows),
 "frozen_sink_panel_unchanged":True,
 "validation_truth_accessed":False,
 "tuning_performed":False,
}
Path(a.out).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
print(json.dumps(payload,indent=2),flush=True)
