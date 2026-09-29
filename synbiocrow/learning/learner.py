from __future__ import annotations
import hashlib, json
from dataclasses import asdict, replace
from typing import Iterable

from .models import TestOutcome, LearningPolicy, PolicyUpdate

_ALLOWED_KINDS={"backend","route","construct"}

def _clip(value: float, lo: float, hi: float)->float:
    return max(lo,min(hi,value))

def _stable_digest(payload)->str:
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def apply_test_outcomes(
    policy: LearningPolicy,
    outcomes: Iterable[TestOutcome],
    *,
    learning_rate: float = 0.10,
) -> tuple[LearningPolicy, PolicyUpdate]:
    outcomes=tuple(sorted(outcomes,key=lambda x:x.outcome_id))
    if learning_rate <= 0:
        raise ValueError("learning_rate must be > 0")

    back=dict(policy.backend_weights)
    route=dict(policy.route_feature_weights)
    construct=dict(policy.construct_feature_weights)
    bd={}; rd={}; cd={}

    for outcome in outcomes:
        if outcome.kind not in _ALLOWED_KINDS:
            raise ValueError(f"Unsupported TestOutcome kind: {outcome.kind}")
        reward=_clip(float(outcome.reward),-1.0,1.0)
        delta=_clip(
            learning_rate*reward,
            -policy.max_delta_per_update,
            policy.max_delta_per_update,
        )
        if outcome.kind=="backend":
            if not outcome.backend_id:
                raise ValueError("backend outcome requires backend_id")
            old=float(back.get(outcome.backend_id,1.0))
            new=_clip(old+delta,policy.min_weight,policy.max_weight)
            back[outcome.backend_id]=new
            bd[outcome.backend_id]=bd.get(outcome.backend_id,0.0)+(new-old)
        else:
            target=route if outcome.kind=="route" else construct
            deltas=rd if outcome.kind=="route" else cd
            for feature,value in sorted(outcome.features.items()):
                contrib=_clip(
                    delta*float(value),
                    -policy.max_delta_per_update,
                    policy.max_delta_per_update,
                )
                old=float(target.get(feature,0.0))
                new=_clip(old+contrib,-policy.max_weight,policy.max_weight)
                target[feature]=new
                deltas[feature]=deltas.get(feature,0.0)+(new-old)

    payload={
        "previous_version":policy.version,
        "new_version":policy.version+1,
        "backend_deltas":bd,
        "route_feature_deltas":rd,
        "construct_feature_deltas":cd,
        "outcome_ids":[o.outcome_id for o in outcomes],
    }
    digest=_stable_digest(payload)
    new_policy=LearningPolicy(
        version=policy.version+1,
        backend_weights=back,
        route_feature_weights=route,
        construct_feature_weights=construct,
        min_weight=policy.min_weight,
        max_weight=policy.max_weight,
        max_delta_per_update=policy.max_delta_per_update,
    )
    update=PolicyUpdate(
        previous_version=policy.version,
        new_version=new_policy.version,
        backend_deltas=bd,
        route_feature_deltas=rd,
        construct_feature_deltas=cd,
        outcome_ids=tuple(o.outcome_id for o in outcomes),
        audit_digest=digest,
    )
    return new_policy,update
