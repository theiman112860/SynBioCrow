from __future__ import annotations
from typing import Protocol, Sequence, Mapping, Any
from .models import PathwayCandidate

class GeneratorBackend(Protocol):
    backend_id: str
    def generate(self,target_smiles:str,*,options:Mapping[str,Any]|None=None)->Sequence[PathwayCandidate]: ...

class EvidenceGate(Protocol):
    gate_id: str
    def evaluate(self,candidate:PathwayCandidate)->Mapping[str,Any]: ...
