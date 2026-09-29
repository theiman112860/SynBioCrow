from __future__ import annotations
from .models import ProteinEvidence, CDSEvidence, SequenceValidation

_CODON_TABLE = {
"TTT":"F","TTC":"F","TTA":"L","TTG":"L","TCT":"S","TCC":"S","TCA":"S","TCG":"S",
"TAT":"Y","TAC":"Y","TAA":"*","TAG":"*","TGT":"C","TGC":"C","TGA":"*","TGG":"W",
"CTT":"L","CTC":"L","CTA":"L","CTG":"L","CCT":"P","CCC":"P","CCA":"P","CCG":"P",
"CAT":"H","CAC":"H","CAA":"Q","CAG":"Q","CGT":"R","CGC":"R","CGA":"R","CGG":"R",
"ATT":"I","ATC":"I","ATA":"I","ATG":"M","ACT":"T","ACC":"T","ACA":"T","ACG":"T",
"AAT":"N","AAC":"N","AAA":"K","AAG":"K","AGT":"S","AGC":"S","AGA":"R","AGG":"R",
"GTT":"V","GTC":"V","GTA":"V","GTG":"V","GCT":"A","GCC":"A","GCA":"A","GCG":"A",
"GAT":"D","GAC":"D","GAA":"E","GAG":"E","GGT":"G","GGC":"G","GGA":"G","GGG":"G",
}

def translate_dna(dna: str) -> str:
    seq = "".join(dna.upper().split()).replace("U","T")
    if len(seq) % 3:
        raise ValueError("CDS length is not divisible by 3")
    try:
        return "".join(_CODON_TABLE[seq[i:i+3]] for i in range(0,len(seq),3))
    except KeyError as exc:
        raise ValueError(f"Invalid/ambiguous codon: {exc.args[0]}") from exc

def validate_cds_against_protein(cds: CDSEvidence, protein: ProteinEvidence) -> SequenceValidation:
    if not cds.cds_sequence:
        return SequenceValidation(False,None,protein.sequence,False,False,"CDS sequence missing")
    if not protein.sequence:
        return SequenceValidation(False,None,None,False,False,"Protein sequence missing")
    try:
        translated = translate_dna(cds.cds_sequence)
    except ValueError as exc:
        return SequenceValidation(False,None,protein.sequence,False,False,str(exc))
    removed = translated.endswith("*")
    clean = translated[:-1] if removed else translated
    target = "".join(protein.sequence.split()).upper().rstrip("*")
    exact = clean == target
    return SequenceValidation(
        valid=exact,
        translated_sequence=clean,
        protein_sequence=target,
        exact_match=exact,
        terminal_stop_removed=removed,
        reason="Exact amino-acid match" if exact else "Translated CDS does not match selected protein sequence",
    )
