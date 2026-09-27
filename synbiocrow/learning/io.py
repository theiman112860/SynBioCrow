from __future__ import annotations
import json
from pathlib import Path
from .models import LearningPolicy, TestOutcome

def load_policy(path:str|Path)->LearningPolicy:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    return LearningPolicy(
        version=int(data.get("version",1)),
        backend_weights=data.get("backend_weights") or {},
        route_feature_weights=data.get("route_feature_weights") or {},
        construct_feature_weights=data.get("construct_feature_weights") or {},
        min_weight=float(data.get("min_weight",0.25)),
        max_weight=float(data.get("max_weight",4.0)),
        max_delta_per_update=float(data.get("max_delta_per_update",0.20)),
    )

def load_outcomes(path:str|Path)->tuple[TestOutcome,...]:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data,dict):
        data=data.get("outcomes",[])
    return tuple(
        TestOutcome(
            outcome_id=str(x["outcome_id"]),
            kind=str(x["kind"]),
            subject_id=str(x["subject_id"]),
            reward=float(x["reward"]),
            backend_id=x.get("backend_id"),
            features=x.get("features") or {},
            source=str(x.get("source","computational_test")),
            notes=x.get("notes"),
        )
        for x in data
    )
