from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib

class IdentityState(str, Enum):
    CANONICAL = "CANONICAL"
    RAW = "RAW"
    UNRESOLVED = "UNRESOLVED"

@dataclass(frozen=True)
class CompoundIdentity:
    key: str
    display: str
    state: IdentityState
    canonical_smiles: str | None = None
    inchikey: str | None = None
    source: str | None = None

def _raw_key(value: str, source: str | None = None) -> str:
    payload=f"{source or 'unknown'}\n{value.strip()}"
    return "raw:"+hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]

def resolve_compound(value: str, *, source: str | None = None) -> CompoundIdentity:
    raw=value.strip()
    if not raw:
        return CompoundIdentity(_raw_key(raw,source),raw,IdentityState.UNRESOLVED,source=source)
    try:
        from rdkit import Chem
        mol=Chem.MolFromSmiles(raw)
        if mol is not None:
            smi=Chem.MolToSmiles(mol,canonical=True)
            try:
                ik=Chem.InchiToInchiKey(Chem.MolToInchi(mol))
            except Exception:
                ik=None
            key=("inchikey:"+ik) if ik else ("smiles:"+smi)
            return CompoundIdentity(key,raw,IdentityState.CANONICAL,smi,ik,source)
    except Exception:
        pass
    return CompoundIdentity(_raw_key(raw,source),raw,IdentityState.RAW,source=source)
