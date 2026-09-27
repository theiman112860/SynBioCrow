from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from synbiocrow.core.models import PathwayCandidate
from synbiocrow.core.errors import BackendUnavailableError

@dataclass(frozen=True)
class BackendInfo:
    backend_id:str; family:str; role:str; optional_dependency:str|None=None

class OptionalBackend:
    info: BackendInfo
    @property
    def backend_id(self)->str: return self.info.backend_id
    def available(self)->bool: return False
    def generate(self,target_smiles:str,*,options:Mapping[str,Any]|None=None)->Sequence[PathwayCandidate]:
        raise BackendUnavailableError(f"{self.backend_id} adapter contract is present, but the live backend has not yet been migrated into the 2.2 package.")
