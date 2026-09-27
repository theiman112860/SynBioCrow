from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Tuple

class LifecycleState(str, Enum):
    CANDIDATE="CANDIDATE"; MATURE="MATURE"; CERTIFIED="CERTIFIED"

@dataclass(frozen=True)
class ReactionStep:
    reaction: str
    rule_id: str|None=None
    source_backend: str|None=None
    feasibility: float|None=None
    metadata: Mapping[str,Any]=field(default_factory=dict)

@dataclass(frozen=True)
class PathwayCandidate:
    candidate_id: str
    target_smiles: str
    steps: Tuple[ReactionStep,...]
    source_backends: Tuple[str,...]
    lifecycle: LifecycleState=LifecycleState.CANDIDATE
    provenance: Mapping[str,Any]=field(default_factory=dict)
    evidence: Mapping[str,Any]=field(default_factory=dict)

@dataclass(frozen=True)
class ConstructCandidate:
    construct_id: str
    pathway_id: str
    sequence: str|None=None
    lifecycle: LifecycleState=LifecycleState.CANDIDATE
    provenance: Mapping[str,Any]=field(default_factory=dict)
