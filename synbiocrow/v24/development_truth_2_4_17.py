"""2.4.17 development-only literature anchor evaluation."""
from __future__ import annotations
from pathlib import Path
from typing import Mapping,Any
import json,urllib.parse,urllib.request
from rdkit import Chem

def canonical(s):
    if not s:return None
    m=Chem.MolFromSmiles(str(s))
    return Chem.MolToSmiles(m,canonical=True,isomericSmiles=True) if m else None

def resolve_pubchem_name(name:str,timeout=30)->str|None:
    q=urllib.parse.quote(name,safe="")
    url=f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/property/CanonicalSMILES,IsomericSMILES/JSON"
    try:
        with urllib.request.urlopen(url,timeout=timeout) as fh: obj=json.load(fh)
        p=obj["PropertyTable"]["Properties"][0]
        return canonical(p.get("SMILES") or p.get("ConnectivitySMILES") or p.get("CanonicalSMILES") or p.get("IsomericSMILES"))
    except Exception:return None

def resolve_truth(truth:Mapping[str,Any],cache:dict|None=None)->dict:
    cache={} if cache is None else cache
    out=json.loads(json.dumps(truth))
    for r in out["records"]:
        rr=[]
        for name in r["anchor_names"]:
            if name not in cache:cache[name]=resolve_pubchem_name(name)
            rr.append({"name":name,"canonical_smiles":cache[name]})
        r["anchors"]=rr
    return out

def reaction_molecules(reaction:str)->set[str]:
    out=set()
    for side in str(reaction or "").replace(">>",">>").split(">"):
        for token in side.split("."):
            c=canonical(token.strip())
            if c:out.add(c)
    return out

def score_candidate(candidate:Mapping[str,Any],anchors:list[Mapping[str,Any]])->dict:
    mols=set()
    for s in candidate.get("steps") or []:mols |= reaction_molecules(s.get("reaction",""))
    usable=[a for a in anchors if a.get("canonical_smiles")]
    hit=[a["name"] for a in usable if a["canonical_smiles"] in mols]
    return {
      "candidate_id":str(candidate.get("candidate_id") or candidate.get("id") or ""),
      "anchor_count":len(usable),"anchor_hit_count":len(hit),
      "anchor_recall":len(hit)/len(usable) if usable else None,
      "anchor_hits":hit,
    }

def evaluate_record(artifact:Mapping[str,Any],truth_record:Mapping[str,Any],ranked_rows:list[Mapping[str,Any]])->dict:
    if artifact.get("split")!="development":raise ValueError("2.4.17 refuses non-development artifact")
    rank={str(x["route_id"]).removeprefix("candidate:"):int(x["rank"]) for x in ranked_rows}
    candidates=(artifact.get("result") or {}).get("candidates") or []
    scores=[score_candidate(c,truth_record["anchors"]) for c in candidates]
    for x in scores:x["rank_2_4_16"]=rank.get(x["candidate_id"])
    scores.sort(key=lambda x:(-(x["anchor_recall"] if x["anchor_recall"] is not None else -1),x["rank_2_4_16"] or 10**9,x["candidate_id"]))
    best=scores[0] if scores else None
    top={}
    for k in (1,5,10,50,100):
        rr=[x for x in scores if x["rank_2_4_16"] and x["rank_2_4_16"]<=k]
        top[str(k)]=max((x["anchor_recall"] for x in rr if x["anchor_recall"] is not None),default=None)
    return {
      "record_id":artifact["record_id"],"target_name":artifact["target_name"],
      "doi":truth_record["doi"],"usable_anchor_count":sum(bool(a.get("canonical_smiles")) for a in truth_record["anchors"]),
      "best_anchor_recall":best["anchor_recall"] if best else None,
      "best_anchor_candidate":best["candidate_id"] if best else None,
      "best_anchor_candidate_rank_2_4_16":best["rank_2_4_16"] if best else None,
      "topk_max_anchor_recall":top,"candidate_scores":scores,
    }
