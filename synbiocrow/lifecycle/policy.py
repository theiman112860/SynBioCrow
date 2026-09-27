from dataclasses import dataclass
from synbiocrow.core.models import LifecycleState
from synbiocrow.core.errors import ContractViolation
from synbiocrow.evidence.gates import GateDecision

@dataclass(frozen=True)
class PromotionPolicy:
    def promote(self,current:LifecycleState,gate:GateDecision)->LifecycleState:
        if current is LifecycleState.CERTIFIED:return current
        if gate is not GateDecision.PASS:return current
        if current is LifecycleState.CANDIDATE:return LifecycleState.MATURE
        if current is LifecycleState.MATURE:return LifecycleState.CERTIFIED
        raise ContractViolation(f"unsupported lifecycle state: {current}")
