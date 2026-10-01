"""Evidence-first biochemical route discrimination for SynBioCrow 2.4.

2.4.12 deliberately does not learn weights and does not access validation truth.
It converts supplied route evidence into transparent component scores plus an
evidence-coverage ceiling. Missing evidence is not treated as negative evidence.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping, Optional, Sequence
import hashlib, json

COMPONENTS=(
    "reaction_compatibility",
    "enzyme_precedent",
    "ec_evidence",
    "cofactor_feasibility",
    "thermodynamic_support",
    "pathway_context",
    "cross_engine_agreement",
)

@dataclass(frozen=True)
class EvidenceValue:
    value: Optional[float]
    source_ids: tuple[str,...]=()
    note: str=""

    def validate(self):
        if self.value is not None and not (0.0 <= float(self.value) <= 1.0):
            raise ValueError("evidence value must be in [0,1] or None")
        if self.value is not None and not self.source_ids:
            raise ValueError("observed evidence requires provenance source_ids")

@dataclass(frozen=True)
class RouteEvidence:
    route_id: str
    target_record_id: str
    split: str
    components: Mapping[str,EvidenceValue]
    route_length: Optional[int]=None

@dataclass(frozen=True)
class RouteDiscrimination:
    route_id: str
    target_record_id: str
    component_scores: Mapping[str,Optional[float]]
    observed_components: int
    total_components: int
    evidence_coverage: float
    observed_mean: Optional[float]
    coverage_adjusted_score: Optional[float]
    missing_components: tuple[str,...]
    provenance_sha256: str

def score_route(route: RouteEvidence) -> RouteDiscrimination:
    if route.split!="development":
        raise ValueError(
            f"2.4.12 scoring is development-only; refused split={route.split!r}"
        )
    unknown=set(route.components)-set(COMPONENTS)
    if unknown:
        raise ValueError(f"unknown evidence components: {sorted(unknown)}")
    values={}
    provenance=[]
    missing=[]
    for name in COMPONENTS:
        ev=route.components.get(name,EvidenceValue(None))
        ev.validate()
        values[name]=None if ev.value is None else float(ev.value)
        if ev.value is None:
            missing.append(name)
        else:
            provenance.append({
                "component":name,
                "value":float(ev.value),
                "source_ids":sorted(ev.source_ids),
                "note":ev.note,
            })
    observed=[x for x in values.values() if x is not None]
    coverage=len(observed)/len(COMPONENTS)
    mean=(sum(observed)/len(observed)) if observed else None
    # Conservative provisional score: evidence quality cannot outrun coverage.
    adjusted=(mean*coverage) if mean is not None else None
    digest=hashlib.sha256(json.dumps(
        provenance,sort_keys=True,separators=(",",":")
    ).encode()).hexdigest()
    return RouteDiscrimination(
        route_id=route.route_id,
        target_record_id=route.target_record_id,
        component_scores=values,
        observed_components=len(observed),
        total_components=len(COMPONENTS),
        evidence_coverage=coverage,
        observed_mean=mean,
        coverage_adjusted_score=adjusted,
        missing_components=tuple(missing),
        provenance_sha256=digest,
    )

def rank_development_routes(routes: Sequence[RouteEvidence]) -> list[RouteDiscrimination]:
    scored=[score_route(r) for r in routes]
    return sorted(
        scored,
        key=lambda x:(
            -(x.coverage_adjusted_score if x.coverage_adjusted_score is not None else -1.0),
            -x.evidence_coverage,
            x.route_id,
        ),
    )

def result_dict(x: RouteDiscrimination) -> dict:
    return asdict(x)
