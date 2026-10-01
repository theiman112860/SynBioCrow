"""Evidence contracts for SynBioCrow 2.4.

These objects contain evidence ABOUT generated routes.  They do not generate
routes and they do not promote Candidate/Mature/Certified lifecycle state.
Unknown evidence remains unknown rather than being converted to support.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple


class EvidenceLevel(str, Enum):
    UNKNOWN = "unknown"
    INFERRED = "inferred"
    CALCULATED = "calculated"
    DATABASE = "database"
    LITERATURE = "literature"
    REVIEWED = "reviewed"


@dataclass(frozen=True)
class ReactionEvidence:
    reaction_id: str
    engines: Tuple[str, ...] = ()
    rhea_exact: Optional[bool] = None
    rhea_connectivity: Optional[bool] = None
    ec_numbers: Tuple[str, ...] = ()
    reviewed_uniprot: Tuple[str, ...] = ()
    literature_ids: Tuple[str, ...] = ()
    thermo_dg: Optional[float] = None
    thermo_units: Optional[str] = None
    cofactors: Tuple[str, ...] = ()
    mapping_confidence: Optional[float] = None
    evidence_level: EvidenceLevel = EvidenceLevel.UNKNOWN
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.mapping_confidence is not None and not 0.0 <= self.mapping_confidence <= 1.0:
            raise ValueError("mapping_confidence must be in [0,1]")
        if self.thermo_dg is not None and not self.thermo_units:
            raise ValueError("thermo_units required when thermo_dg is present")


@dataclass(frozen=True)
class RouteEvidence:
    route_id: str
    reaction_count: int
    independent_engines: Tuple[str, ...]
    supported_reactions: int
    reviewed_enzyme_reactions: int
    rhea_exact_reactions: int
    rhea_connectivity_reactions: int
    thermo_covered_reactions: int
    unknown_evidence_reactions: int
    evidence_bottleneck: EvidenceLevel

    def __post_init__(self) -> None:
        if self.reaction_count < 0:
            raise ValueError("reaction_count cannot be negative")
        for name in (
            "supported_reactions", "reviewed_enzyme_reactions",
            "rhea_exact_reactions", "rhea_connectivity_reactions",
            "thermo_covered_reactions", "unknown_evidence_reactions",
        ):
            value = getattr(self, name)
            if not 0 <= value <= self.reaction_count:
                raise ValueError(f"{name} must be between 0 and reaction_count")


@dataclass(frozen=True)
class RankingFeatureVector:
    route_id: str
    structural_2d: Optional[float] = None
    structural_3d: Optional[float] = None
    reaction_evidence_fraction: Optional[float] = None
    reviewed_enzyme_fraction: Optional[float] = None
    rhea_exact_fraction: Optional[float] = None
    thermo_coverage_fraction: Optional[float] = None
    engine_count: int = 0
    route_length: int = 0
    unsupported_edge_count: int = 0
    mapping_confidence_mean: Optional[float] = None
    extra: Dict[str, Optional[float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "structural_2d", "structural_3d", "reaction_evidence_fraction",
            "reviewed_enzyme_fraction", "rhea_exact_fraction",
            "thermo_coverage_fraction", "mapping_confidence_mean",
        ):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0,1]")
        if min(self.engine_count, self.route_length, self.unsupported_edge_count) < 0:
            raise ValueError("count features cannot be negative")


_LEVEL_ORDER = {
    EvidenceLevel.UNKNOWN: 0,
    EvidenceLevel.INFERRED: 1,
    EvidenceLevel.CALCULATED: 2,
    EvidenceLevel.DATABASE: 3,
    EvidenceLevel.LITERATURE: 4,
    EvidenceLevel.REVIEWED: 5,
}


def aggregate_route_evidence(route_id: str, reactions: Sequence[ReactionEvidence]) -> RouteEvidence:
    """Aggregate without inventing evidence.

    A reaction is supported only when at least one explicit evidence field is
    positive/present.  Missing values are not treated as negative evidence.
    """
    engines = sorted({e for r in reactions for e in r.engines})
    supported = sum(bool(
        r.rhea_exact is True or r.rhea_connectivity is True or r.ec_numbers
        or r.reviewed_uniprot or r.literature_ids or r.thermo_dg is not None
    ) for r in reactions)
    levels = [r.evidence_level for r in reactions]
    bottleneck = min(levels, key=_LEVEL_ORDER.get) if levels else EvidenceLevel.UNKNOWN
    return RouteEvidence(
        route_id=route_id,
        reaction_count=len(reactions),
        independent_engines=tuple(engines),
        supported_reactions=supported,
        reviewed_enzyme_reactions=sum(bool(r.reviewed_uniprot) for r in reactions),
        rhea_exact_reactions=sum(r.rhea_exact is True for r in reactions),
        rhea_connectivity_reactions=sum(r.rhea_connectivity is True for r in reactions),
        thermo_covered_reactions=sum(r.thermo_dg is not None for r in reactions),
        unknown_evidence_reactions=sum(r.evidence_level == EvidenceLevel.UNKNOWN for r in reactions),
        evidence_bottleneck=bottleneck,
    )
