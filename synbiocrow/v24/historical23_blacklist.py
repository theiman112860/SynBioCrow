"""Mechanical recovery of the frozen SynBioCrow 2.3 Galaxy pathway blacklist."""
from __future__ import annotations
import hashlib, json
from typing import List, Tuple

SOURCE_PATHWAY_COUNT = 77
DEVELOPMENT_COUNT = 12

def reconstruct_split() -> Tuple[List[str], List[str]]:
    ids=[f"literature_{i}" for i in range(1,SOURCE_PATHWAY_COUNT+1)]
    ranked=sorted(ids,key=lambda x:hashlib.sha256(x.encode()).hexdigest())
    development=set(ranked[:DEVELOPMENT_COUNT])
    dev=sorted(development,key=lambda x:int(x.split("_")[1]))
    held=sorted((x for x in ids if x not in development),key=lambda x:int(x.split("_")[1]))
    return dev,held

def heldout_id_sha256() -> str:
    _,held=reconstruct_split()
    payload=json.dumps(sorted(held),separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()

EXPECTED_HELDOUT_COUNT=65
EXPECTED_HELDOUT_SHA256="c7c43814c973e941172b18b8745ba7e79bcaa4e4e193bfde473b796415bbd58f"

def validate_reconstruction() -> None:
    dev,held=reconstruct_split()
    if len(dev)!=12 or len(held)!=EXPECTED_HELDOUT_COUNT:
        raise ValueError("unexpected reconstructed split size")
    if heldout_id_sha256()!=EXPECTED_HELDOUT_SHA256:
        raise ValueError("held-out pathway blacklist digest mismatch")
    if "literature_10" not in held:
        raise ValueError("expected mapping-limited literature_10 in holdout")
