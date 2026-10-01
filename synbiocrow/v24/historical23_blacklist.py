"""Frozen SynBioCrow 2.3 Galaxy split helpers.

Important: the released split policy hashes the ACTUAL pathway IDs present in
Galaxy-SynBioCAD Supplementary Dataset 2.  It is invalid to synthesize a
literature_1..literature_77 sequence.
"""
from __future__ import annotations
import hashlib, json
from typing import Iterable, List, Sequence, Tuple

SOURCE_PATHWAY_COUNT = 77
DEVELOPMENT_COUNT = 12
EXPECTED_HELDOUT_COUNT = 65

def reconstruct_split(actual_ids: Sequence[str]) -> Tuple[List[str], List[str]]:
    ids=[str(x) for x in actual_ids]
    if len(ids)!=SOURCE_PATHWAY_COUNT:
        raise ValueError(f"expected {SOURCE_PATHWAY_COUNT} actual pathway IDs, found {len(ids)}")
    if len(set(ids))!=SOURCE_PATHWAY_COUNT:
        raise ValueError("duplicate pathway IDs in source")
    ranked=sorted(ids,key=lambda x:hashlib.sha256(x.encode()).hexdigest())
    development=set(ranked[:DEVELOPMENT_COUNT])
    dev=sorted(development)
    held=sorted(x for x in ids if x not in development)
    if len(dev)!=DEVELOPMENT_COUNT or len(held)!=EXPECTED_HELDOUT_COUNT:
        raise ValueError("unexpected reconstructed split size")
    return dev,held

def heldout_id_sha256(actual_ids: Sequence[str]) -> str:
    _,held=reconstruct_split(actual_ids)
    payload=json.dumps(sorted(held),separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()

def validate_reconstruction(actual_ids: Sequence[str]) -> None:
    dev,held=reconstruct_split(actual_ids)
    if set(dev) & set(held):
        raise ValueError("development/holdout overlap")
