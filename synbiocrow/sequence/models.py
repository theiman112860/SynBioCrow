from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping,Any

@dataclass(frozen=True)
class ProteinEvidence:
    accession:str; source:str; sequence:str|None=None; provenance:Mapping[str,Any]|None=None

@dataclass(frozen=True)
class CDSEvidence:
    nucleotide_accession:str; source:str; cds_sequence:str|None=None; protein_accession:str|None=None
