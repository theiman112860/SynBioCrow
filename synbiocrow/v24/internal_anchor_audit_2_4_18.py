"""SynBioCrow 2.4.18 internal-anchor structural near-miss audit."""
from __future__ import annotations
from typing import Any,Mapping
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
from synbiocrow.v24.development_truth_2_4_17 import canonical,reaction_molecules

_MORGAN=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)

def fp(s):
 m=Chem.MolFromSmiles(str(s)) if s else None
 return _MORGAN.GetFingerprint(m) if m else None

def tanimoto(a,b):
 fa,fb=fp(a),fp(b)
 return float(DataStructs.TanimotoSimilarity(fa,fb)) if fa is not None and fb is not None else None

def candidate_molecules(candidate:Mapping[str,Any])->set[str]:
 out=set()
 for step in candidate.get("steps") or []:out |= reaction_molecules(step.get("reaction",""))
 return out

def audit_candidate(candidate:Mapping[str,Any],anchors:list[Mapping[str,Any]],target_smiles:str)->dict:
 target=canonical(target_smiles)
 mols={m for m in candidate_molecules(candidate) if m and m!=target}
 rows=[]
 for a in anchors:
  asm=a.get("canonical_smiles")
  if not asm or asm==target:continue
  vals=[(tanimoto(asm,m),m) for m in mols]
  vals=[x for x in vals if x[0] is not None]
  best=max(vals,key=lambda x:(x[0],x[1])) if vals else (None,None)
  rows.append({"anchor_name":a["name"],"anchor_smiles":asm,"best_similarity":best[0],"best_candidate_smiles":best[1]})
 sims=[x["best_similarity"] for x in rows if x["best_similarity"] is not None]
 return {"candidate_id":str(candidate.get("candidate_id") or candidate.get("id") or ""),
         "internal_anchor_count":len(rows),"internal_anchor_similarity_mean":sum(sims)/len(sims) if sims else None,
         "internal_anchor_similarity_max":max(sims) if sims else None,"anchor_near_misses":rows}
