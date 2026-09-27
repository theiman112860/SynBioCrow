from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SequenceQC:
    length_bp: int
    gc_percent: float
    forbidden_motif_hits: tuple[str,...]
    homopolymer_hits: tuple[str,...]
    pass_qc: bool

DEFAULT_FORBIDDEN_MOTIFS = (
    "GAATTC",  # EcoRI
    "GGATCC",  # BamHI
    "AAGCTT",  # HindIII
    "GGTCTC",  # BsaI
    "CGTCTC",  # BsmBI/Esp3I family recognition motif orientation
)

def sequence_qc(
    dna: str,
    *,
    forbidden_motifs: tuple[str,...] = DEFAULT_FORBIDDEN_MOTIFS,
    max_homopolymer: int = 6,
    min_gc: float = 30.0,
    max_gc: float = 70.0,
) -> SequenceQC:
    seq="".join(dna.upper().split()).replace("U","T")
    if not seq or any(b not in "ACGT" for b in seq):
        raise ValueError("DNA sequence must contain only A/C/G/T")
    gc=100.0*(seq.count("G")+seq.count("C"))/len(seq)
    motifs=tuple(sorted({m for m in forbidden_motifs if m and m in seq}))
    homo=[]
    for base in "ACGT":
        motif=base*(max_homopolymer+1)
        if motif in seq:
            homo.append(motif)
    passed=(not motifs and not homo and min_gc <= gc <= max_gc)
    return SequenceQC(len(seq),gc,motifs,tuple(homo),passed)
