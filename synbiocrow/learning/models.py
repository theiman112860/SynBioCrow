from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping

@dataclass(frozen=True)
class TestOutcome:
    outcome_id: str
    kind: str
    subject_id: str
    reward: float
    backend_id: str | None = None
    features: Mapping[str,float] = field(default_factory=dict)
    source: str = "computational_test"
    notes: str | None = None

@dataclass(frozen=True)
class LearningPolicy:
    version: int = 1
    backend_weights: Mapping[str,float] = field(default_factory=dict)
    route_feature_weights: Mapping[str,float] = field(default_factory=dict)
    construct_feature_weights: Mapping[str,float] = field(default_factory=dict)
    min_weight: float = 0.25
    max_weight: float = 4.0
    max_delta_per_update: float = 0.20

@dataclass(frozen=True)
class PolicyUpdate:
    previous_version: int
    new_version: int
    backend_deltas: Mapping[str,float]
    route_feature_deltas: Mapping[str,float]
    construct_feature_deltas: Mapping[str,float]
    outcome_ids: tuple[str,...]
    audit_digest: str
