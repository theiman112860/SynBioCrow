from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import Iterable

from synbiocrow.core.models import LifecycleState
from synbiocrow.sequence.qc import SequenceQC, sequence_qc
from .models import CassettePart, CassetteCandidate
from .parts import RegulatoryPart

@dataclass(frozen=True)
class CassetteBuildResult:
    candidate: CassetteCandidate
    qc: SequenceQC

def _part(role: str, sequence: str, source: str, identifier: str | None = None) -> CassettePart:
    seq="".join(sequence.upper().split()).replace("U","T")
    if not seq or any(b not in "ACGT" for b in seq):
        raise ValueError(f"{role} sequence must contain only A/C/G/T")
    return CassettePart(role=role, sequence=seq, source=source, identifier=identifier)

def build_expression_cassette(
    *,
    pathway_id: str,
    cds_sequence: str,
    promoter: RegulatoryPart,
    rbs: RegulatoryPart,
    terminator: RegulatoryPart,
    cds_identifier: str | None = None,
    cds_source: str = "verified_cds",
) -> CassetteBuildResult:
    for p, role in ((promoter,"promoter"),(rbs,"rbs"),(terminator,"terminator")):
        if p.sequence is None:
            raise ValueError(f"{p.identifier} has no verified sequence")
        if p.role != role:
            raise ValueError(f"Expected {role}, got {p.role}")

    parts=(
        _part("promoter",promoter.sequence,promoter.source,promoter.identifier),
        _part("rbs",rbs.sequence,rbs.source,rbs.identifier),
        _part("cds",cds_sequence,cds_source,cds_identifier),
        _part("terminator",terminator.sequence,terminator.source,terminator.identifier),
    )
    full="".join(p.sequence for p in parts)
    qc=sequence_qc(full)
    payload="|".join([
        pathway_id,
        promoter.identifier,
        rbs.identifier,
        cds_identifier or hashlib.sha256(parts[2].sequence.encode("utf-8")).hexdigest()[:12],
        terminator.identifier,
        hashlib.sha256(full.encode("utf-8")).hexdigest(),
    ])
    cid="CASSETTE-"+hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    candidate=CassetteCandidate(
        cassette_id=cid,
        parts=parts,
        lifecycle=LifecycleState.CANDIDATE,
        provenance={
            "pathway_id":pathway_id,
            "assembly_order":["promoter","rbs","cds","terminator"],
            "sequence_sha256":hashlib.sha256(full.encode("utf-8")).hexdigest(),
            "qc_pass":qc.pass_qc,
        },
    )
    return CassetteBuildResult(candidate,qc)

def assemble_multigene_construct(
    cassettes: Iterable[CassetteCandidate],
    *,
    construct_id: str | None = None,
) -> CassetteCandidate:
    cassettes=tuple(cassettes)
    if not cassettes:
        raise ValueError("At least one cassette is required")
    parts=tuple(p for c in cassettes for p in c.parts)
    full="".join(p.sequence for p in parts)
    if construct_id is None:
        construct_id="OPERON-"+hashlib.sha256(full.encode("utf-8")).hexdigest()[:16]
    return CassetteCandidate(
        cassette_id=construct_id,
        parts=parts,
        lifecycle=LifecycleState.CANDIDATE,
        provenance={
            "source_cassettes":[c.cassette_id for c in cassettes],
            "sequence_sha256":hashlib.sha256(full.encode("utf-8")).hexdigest(),
            "multi_gene":len(cassettes)>1,
        },
    )
