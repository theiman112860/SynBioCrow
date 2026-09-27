from __future__ import annotations
import hashlib
from collections.abc import Iterable
from synbiocrow.core.models import PathwayCandidate

def pathway_fingerprint(candidate:PathwayCandidate)->str:
    payload="\n".join(step.reaction.strip() for step in candidate.steps)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def union_candidates(candidates:Iterable[PathwayCandidate])->list[PathwayCandidate]:
    """Deterministic exact-path union; does not rank or promote."""
    by_fp={}
    for candidate in candidates: by_fp.setdefault(pathway_fingerprint(candidate),candidate)
    return [by_fp[k] for k in sorted(by_fp)]
