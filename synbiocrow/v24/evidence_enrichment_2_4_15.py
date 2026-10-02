"""SynBioCrow 2.4.15 bounded evidence enrichment.

Enriches persisted DEVELOPMENT candidate pathways only. Rhea participant matches
are connectivity/context evidence, never exact-reaction proof. Reviewed UniProt
entries found through EC classes are contextual enzyme-family evidence only.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from typing import Any, Mapping
import hashlib,json,time

from synbiocrow.core.models import PathwayCandidate,ReactionStep
from synbiocrow.ensemble.graph import build_reaction_graph
from synbiocrow.evidence.rhea import RheaClient
from synbiocrow.evidence.uniprot import UniProtRheaClient

def candidate_from_dict(d:Mapping[str,Any])->PathwayCandidate:
    return PathwayCandidate(
        candidate_id=str(d.get("candidate_id") or d.get("id") or "candidate"),
        target_smiles=str(d.get("target_smiles") or ""),
        steps=tuple(ReactionStep(
            reaction=str(x.get("reaction") or ""),
            rule_id=x.get("rule_id"),source_backend=x.get("source_backend"),
            feasibility=x.get("feasibility"),metadata=dict(x.get("metadata") or {})
        ) for x in (d.get("steps") or []) if isinstance(x,Mapping)),
        source_backends=tuple(str(x) for x in (d.get("source_backends") or ())),
        provenance=dict(d.get("provenance") or {}),evidence=dict(d.get("evidence") or {}),
    )

def edge_signature(graph,eid:str)->str:
    e=graph.edges[eid]
    keys=[e.parent_key,*e.precursor_keys]
    return hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest()

def audit_metadata(candidates:list[PathwayCandidate])->dict:
    step_keys=Counter(); prov_keys=Counter(); evidence_keys=Counter(); feas=[]
    for c in candidates:
        prov_keys.update(map(str,c.provenance.keys()))
        evidence_keys.update(map(str,c.evidence.keys()))
        for s in c.steps:
            step_keys.update(map(str,(s.metadata or {}).keys()))
            if s.feasibility is not None:
                try: feas.append(float(s.feasibility))
                except Exception: pass
    return {
      "candidate_count":len(candidates),
      "step_metadata_keys":dict(step_keys.most_common()),
      "candidate_provenance_keys":dict(prov_keys.most_common()),
      "candidate_evidence_keys":dict(evidence_keys.most_common()),
      "feasibility_count":len(feas),
      "feasibility_min":min(feas) if feas else None,
      "feasibility_max":max(feas) if feas else None,
    }

def load_cache(path:Path)->dict:
    if not path.is_file(): return {"schema":"synbiocrow.v24.evidence-cache.v1","edges":{},"ec_uniprot":{}}
    return json.loads(path.read_text())

def save_cache(path:Path,cache:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache,indent=2,sort_keys=True)+"\n")
    tmp.replace(path)

def enrich_artifact(path:Path,cache_path:Path,*,max_new_edges:int=750,sleep_s:float=0.05)->dict:
    obj=json.loads(path.read_text())
    if obj.get("split")!="development":
        raise ValueError("2.4.15 refuses non-development artifacts")
    candidates=[candidate_from_dict(x) for x in obj["result"].get("candidates",[]) if isinstance(x,Mapping)]
    graph=build_reaction_graph(candidates)
    usage=Counter()
    candidate_edges={}
    for c in candidates:
        g=build_reaction_graph([c]); ids=sorted(g.edges)
        sigs=[]
        for eid in ids:
            sig=edge_signature(g,eid); usage[sig]+=1; sigs.append((sig,g,eid))
        candidate_edges[c.candidate_id]=sigs

    representatives={}
    for sigs in candidate_edges.values():
        for sig,g,eid in sigs: representatives.setdefault(sig,(g,eid))
    cache=load_cache(cache_path); ecache=cache.setdefault("edges",{})
    rhea=RheaClient(timeout=20,user_agent="SynBioCrow/2.4.15")
    uni=UniProtRheaClient(timeout=20,user_agent="SynBioCrow/2.4.15")
    queried=0
    for sig,_freq in usage.most_common():
        if sig in ecache: continue
        if queried>=max_new_edges: break
        g,eid=representatives[sig]; e=g.edges[eid]
        ids=[g.compounds[k].inchikey for k in [e.parent_key,*e.precursor_keys] if k in g.compounds]
        rec={"status":"abstain","rhea_connectivity":None,"rhea_ids":[],"ec_numbers":[],
             "reviewed_ec_context":[],"query_error":None}
        if len(ids)==1+len(e.precursor_keys) and all(ids):
            try:
                hits=rhea.search_inchikeys(ids,limit=50)
                if hits:
                    rec["status"]="database_context"
                    rec["rhea_connectivity"]=True
                    rec["rhea_ids"]=sorted({h.rhea_id for h in hits if h.rhea_id})
                    ecs=sorted({ec for h in hits for ec in h.ec})
                    rec["ec_numbers"]=ecs
                    accessions=set()
                    for ec in ecs[:6]:
                        try:
                            accessions.update(h.accession for h in uni.reviewed_for_ec(ec,size=10) if h.accession)
                        except Exception:
                            pass
                    rec["reviewed_ec_context"]=sorted(accessions)
                else:
                    rec["status"]="no_participant_match"
                    rec["rhea_connectivity"]=False
            except Exception as exc:
                rec["query_error"]=f"{type(exc).__name__}: {exc}"
        else:
            rec["status"]="unmapped_participants"
        ecache[sig]=rec; queried+=1
        if queried%25==0: save_cache(cache_path,cache)
        if sleep_s: time.sleep(sleep_s)
    save_cache(cache_path,cache)

    rows=[]
    for c in candidates:
        sigs=candidate_edges[c.candidate_id]
        recs=[ecache.get(sig) for sig,_,_ in sigs]
        known=[r for r in recs if r is not None]
        n=max(1,len(sigs))
        rows.append({
          "record_id":obj["record_id"],"target_name":obj["target_name"],
          "route_id":"candidate:"+c.candidate_id,"route_length":len(sigs),
          "source_backends":list(c.source_backends),
          "rhea_connectivity_fraction":sum(r.get("rhea_connectivity") is True for r in known)/n,
          "ec_context_fraction":sum(bool(r.get("ec_numbers")) for r in known)/n,
          "reviewed_ec_context_fraction":sum(bool(r.get("reviewed_ec_context")) for r in known)/n,
          "evidence_query_coverage":len(known)/n,
          "unqueried_edge_count":len(sigs)-len(known),
        })
    return {
      "record_id":obj["record_id"],"target_name":obj["target_name"],
      "metadata_audit":audit_metadata(candidates),
      "candidate_rows":rows,
      "unique_edge_count":len(usage),"cached_edge_count":sum(sig in ecache for sig in usage),
      "new_edge_queries":queried,
      "rhea_semantics":"participant-set match is connectivity/context evidence only; exact reaction proof is not claimed",
      "uniprot_semantics":"reviewed EC matches are enzyme-family/context evidence only; exact reaction-enzyme proof is not claimed",
    }
