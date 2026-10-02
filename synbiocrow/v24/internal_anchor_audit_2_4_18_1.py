"""SynBioCrow 2.4.18.1 corrected internal-anchor audit.

Repairs 2.4.18 target leakage and reports carrier-aware similarity for CoA-like
anchors. This is measurement-only: no generation or ranking changes.
"""
from __future__ import annotations
from typing import Any,Mapping
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
from synbiocrow.v24.development_truth_2_4_17 import canonical,reaction_molecules
_M=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)
def fp(s):
 m=Chem.MolFromSmiles(str(s)) if s else None
 return _M.GetFingerprint(m) if m else None
def sim(a,b):
 fa,fb=fp(a),fp(b)
 return float(DataStructs.TanimotoSimilarity(fa,fb)) if fa is not None and fb is not None else None
def mols(c):
 o=set()
 for s in c.get("steps") or []:o|=reaction_molecules(s.get("reaction",""))
 return o
def is_target_anchor(anchor,target_name,target_smiles):
 n=str(anchor.get("name") or "").strip().lower();t=str(target_name or "").strip().lower()
 return n==t or (canonical(anchor.get("canonical_smiles")) and canonical(anchor.get("canonical_smiles"))==canonical(target_smiles))
def carrier_adjust(anchor,candidate,carrier):
 raw=sim(anchor,candidate);base=sim(carrier,candidate);ab=sim(anchor,carrier)
 if raw is None:return None
 if base is None or ab is None or ab>=0.999:return raw
 return max(0.0,min(1.0,(raw-base)/(1.0-ab)))
def audit_candidate(candidate:Mapping[str,Any],anchors:list[Mapping[str,Any]],target_name:str,target_smiles:str,coa_smiles:str|None=None):
 cm={m for m in mols(candidate) if m and m!=canonical(target_smiles)}
 rows=[]
 for a in anchors:
  if is_target_anchor(a,target_name,target_smiles):continue
  asm=a.get("canonical_smiles")
  if not asm:continue
  coa_like="coa" in str(a.get("name") or "").lower()
  vals=[]
  for m in cm:
   raw=sim(asm,m)
   adj=carrier_adjust(asm,m,coa_smiles) if coa_like and coa_smiles else raw
   if adj is not None:vals.append((adj,raw,m))
  best=max(vals,key=lambda x:(x[0],x[1],x[2])) if vals else (None,None,None)
  rows.append({"anchor_name":a["name"],"anchor_smiles":asm,"carrier_aware":coa_like,
    "best_similarity":best[0],"best_raw_similarity":best[1],"best_candidate_smiles":best[2]})
 vals=[x["best_similarity"] for x in rows if x["best_similarity"] is not None]
 return {"candidate_id":str(candidate.get("candidate_id") or candidate.get("id") or ""),
  "internal_anchor_count":len(rows),"internal_anchor_similarity_mean":sum(vals)/len(vals) if vals else None,
  "internal_anchor_similarity_max":max(vals) if vals else None,"anchor_near_misses":rows}
