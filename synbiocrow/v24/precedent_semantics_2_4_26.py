"""SynBioCrow 2.4.26 generator-precedent semantics audit.

Development-only diagnostic. Inspects the raw generator metadata underlying
precedent_step_fraction without converting metadata presence into biochemical proof.
"""
from __future__ import annotations
from collections import Counter
from typing import Any,Mapping

def _items(x:Any)->list:
 if x is None:return []
 if isinstance(x,Mapping):return [x]
 if isinstance(x,(list,tuple,set)):return list(x)
 return [x]

def _classify(x:Any)->str:
 if isinstance(x,Mapping):
  keys={str(k).lower() for k in x}
  if any(k in keys for k in ("reaction","reaction_smiles","rxn_smiles","smarts","reaction_smarts")):return "structured_reaction"
  if any(k in keys for k in ("id","reaction_id","rule_id","template_id","name","doi","reference","source")):return "structured_identifier"
  return "structured_other"
 if isinstance(x,str):
  s=x.strip()
  if not s:return "empty"
  if ">>" in s:return "reaction_string"
  if any(t in s.lower() for t in ("doi","rhea","rule","template","reaction")):return "identifier_string"
  return "opaque_string"
 if isinstance(x,(int,float,bool)):return "scalar"
 return type(x).__name__

def candidate_precedent_audit(candidate:Mapping[str,Any])->dict:
 steps=candidate.get("steps") or [];classes=Counter();bearing=0;items=0;examples=[]
 for i,s in enumerate(steps):
  md=(s or {}).get("metadata") or {};p=md.get("precedents");vals=_items(p)
  if vals:bearing+=1
  for v in vals:
   c=_classify(v);classes[c]+=1;items+=1
   if len(examples)<12:
    examples.append({"step_index":i,"class":c,"value":v})
 return {"candidate_id":candidate.get("candidate_id") or candidate.get("id"),"step_count":len(steps),
 "precedent_bearing_steps":bearing,"precedent_step_fraction":bearing/len(steps) if steps else 0.0,
 "precedent_item_count":items,"precedent_classes":dict(classes),"examples":examples}

def audit_record(obj:Mapping[str,Any],route_ids:list[str])->dict:
 cands={str(c.get("candidate_id") or c.get("id")):c for c in (obj.get("result") or {}).get("candidates",[]) if isinstance(c,Mapping)}
 out=[]
 for route_id in route_ids:
  cid=route_id.split("candidate:",1)[-1];c=cands.get(cid)
  if c is not None:out.append(candidate_precedent_audit(c))
 return {"record_id":obj.get("record_id"),"target_name":obj.get("target_name"),"candidates":out}
