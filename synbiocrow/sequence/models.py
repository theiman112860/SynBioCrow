from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping, Any

@dataclass(frozen=True)
class ProteinEvidence:
    accession: str
    source: str
    sequence: str | None = None
    reviewed: bool | None = None
    organism: str | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class CDSEvidence:
    nucleotide_accession: str
    source: str
    cds_sequence: str | None = None
    protein_accession: str | None = None
    protein_sequence: str | None = None
    organism: str | None = None
    start: int | None = None
    end: int | None = None
    strand: int | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class SequenceValidation:
    valid: bool
    translated_sequence: str | None
    protein_sequence: str | None
    exact_match: bool
    terminal_stop_removed: bool
    reason: str
