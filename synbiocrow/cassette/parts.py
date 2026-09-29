from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RegulatoryPart:
    identifier: str
    role: str
    sequence: str | None
    source: str
    provenance_url: str | None = None

STANDARD_PART_REFERENCES = {
    "J23119": RegulatoryPart(
        "J23119","promoter",None,"iGEM Registry",
        "https://parts.igem.org/Part:BBa_J23119",
    ),
    "B0034": RegulatoryPart(
        "B0034","rbs",None,"iGEM Registry",
        "https://parts.igem.org/Part:BBa_B0034",
    ),
    "B0015": RegulatoryPart(
        "B0015","terminator",None,"iGEM Registry",
        "https://parts.igem.org/Part:BBa_B0015",
    ),
}

def with_verified_sequence(part: RegulatoryPart, sequence: str) -> RegulatoryPart:
    seq="".join(sequence.upper().split()).replace("U","T")
    if not seq or any(b not in "ACGT" for b in seq):
        raise ValueError("Verified regulatory-part sequence must contain only A/C/G/T")
    return RegulatoryPart(
        identifier=part.identifier,
        role=part.role,
        sequence=seq,
        source=part.source,
        provenance_url=part.provenance_url,
    )
