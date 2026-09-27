from __future__ import annotations
from typing import Mapping, Iterable
from .models import LearningPolicy

def backend_priority(policy: LearningPolicy, backend_id: str)->float:
    return float(policy.backend_weights.get(backend_id,1.0))

def score_features(features: Mapping[str,float], weights: Mapping[str,float])->float:
    return sum(float(features.get(k,0.0))*float(w) for k,w in weights.items())

def rank_routes(
    route_features: Mapping[str,Mapping[str,float]],
    policy: LearningPolicy,
)->list[tuple[str,float]]:
    scored=[
        (rid,score_features(features,policy.route_feature_weights))
        for rid,features in route_features.items()
    ]
    return sorted(scored,key=lambda x:(-x[1],x[0]))

def rank_constructs(
    construct_features: Mapping[str,Mapping[str,float]],
    policy: LearningPolicy,
)->list[tuple[str,float]]:
    scored=[
        (cid,score_features(features,policy.construct_feature_weights))
        for cid,features in construct_features.items()
    ]
    return sorted(scored,key=lambda x:(-x[1],x[0]))
