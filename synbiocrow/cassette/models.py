from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping,Any,Tuple
from synbiocrow.core.models import LifecycleState

@dataclass(frozen=True)
class CassettePart:
    role:str; sequence:str; source:str; identifier:str|None=None

@dataclass(frozen=True)
class CassetteCandidate:
    cassette_id:str
    parts:Tuple[CassettePart,...]
    lifecycle:LifecycleState=LifecycleState.CANDIDATE
    provenance:Mapping[str,Any]|None=None
