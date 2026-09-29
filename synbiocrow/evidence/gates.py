from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from collections.abc import Iterable

class GateDecision(str,Enum):
    PASS="PASS"; FAIL="FAIL"; ABSTAIN="ABSTAIN"

@dataclass(frozen=True)
class GateResult:
    gate_id:str
    decision:GateDecision
    reason:str
    evidence:tuple[str,...]=()

def require_all(results:Iterable[GateResult|GateDecision])->GateDecision:
    values=[]
    for item in results:
        values.append(item if isinstance(item,GateDecision) else item.decision)
    if GateDecision.FAIL in values:return GateDecision.FAIL
    if GateDecision.ABSTAIN in values:return GateDecision.ABSTAIN
    return GateDecision.PASS
