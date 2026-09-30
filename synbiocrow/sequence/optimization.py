from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

from .validation import translate_dna

AA_CODONS = {
"A":("GCT","GCC","GCA","GCG"),"R":("CGT","CGC","CGA","CGG","AGA","AGG"),
"N":("AAT","AAC"),"D":("GAT","GAC"),"C":("TGT","TGC"),"Q":("CAA","CAG"),
"E":("GAA","GAG"),"G":("GGT","GGC","GGA","GGG"),"H":("CAT","CAC"),
"I":("ATT","ATC","ATA"),"L":("TTA","TTG","CTT","CTC","CTA","CTG"),
"K":("AAA","AAG"),"M":("ATG",),"F":("TTT","TTC"),"P":("CCT","CCC","CCA","CCG"),
"S":("TCT","TCC","TCA","TCG","AGT","AGC"),"T":("ACT","ACC","ACA","ACG"),
"W":("TGG",),"Y":("TAT","TAC"),"V":("GTT","GTC","GTA","GTG"),"*":("TAA","TAG","TGA"),
}

ECOLI_K12_PREFERRED = {
"A":"GCC","R":"CGT","N":"AAC","D":"GAT","C":"TGC","Q":"CAG","E":"GAA",
"G":"GGT","H":"CAC","I":"ATC","L":"CTG","K":"AAA","M":"ATG","F":"TTC",
"P":"CCG","S":"AGC","T":"ACC","W":"TGG","Y":"TAC","V":"GTG","*":"TAA",
}

@dataclass(frozen=True)
class CodonOptimizationResult:
    dna_sequence: str
    protein_sequence: str
    profile_name: str
    substitutions: int
    original_dna: str | None = None

def optimize_protein_sequence(
    protein_sequence: str,
    *,
    preferred_codons: Mapping[str,str] | None = None,
    profile_name: str = "ecoli_k12_simple_preferred",
    include_stop: bool = True,
) -> CodonOptimizationResult:
    table=dict(preferred_codons or ECOLI_K12_PREFERRED)
    protein="".join(protein_sequence.split()).upper().rstrip("*")
    unknown=sorted(set(protein)-set(AA_CODONS))
    if unknown:
        raise ValueError(f"Unsupported amino-acid symbols: {unknown}")
    dna="".join(table[aa] for aa in protein)
    if include_stop:
        dna += table.get("*","TAA")
    translated=translate_dna(dna).rstrip("*")
    if translated != protein:
        raise AssertionError("Codon optimization changed the amino-acid sequence")
    return CodonOptimizationResult(dna,protein,profile_name,len(protein))

def reoptimize_cds(
    original_dna: str,
    protein_sequence: str,
    *,
    preferred_codons: Mapping[str,str] | None = None,
    profile_name: str = "ecoli_k12_simple_preferred",
) -> CodonOptimizationResult:
    result=optimize_protein_sequence(
        protein_sequence,
        preferred_codons=preferred_codons,
        profile_name=profile_name,
        include_stop=True,
    )
    original="".join(original_dna.upper().split()).replace("U","T")
    old_codons=[original[i:i+3] for i in range(0,len(original),3)]
    new_codons=[result.dna_sequence[i:i+3] for i in range(0,len(result.dna_sequence),3)]
    subs=sum(1 for a,b in zip(old_codons,new_codons) if a!=b)+abs(len(old_codons)-len(new_codons))
    return CodonOptimizationResult(
        result.dna_sequence,result.protein_sequence,result.profile_name,subs,original
    )


def repair_synonymous_forbidden_motifs(
    dna_sequence: str,
    protein_sequence: str,
    *,
    forbidden_motifs: tuple[str,...] = (
        "GAATTC","GGATCC","AAGCTT","GGTCTC","CGTCTC",
    ),
    preferred_codons: Mapping[str,str] | None = None,
    max_passes: int = 50,
) -> CodonOptimizationResult:
    """Remove forbidden DNA motifs by synonymous codon substitution.

    The amino-acid sequence is invariant. Candidate substitutions are accepted
    only when they reduce the number of forbidden-motif occurrences.
    """
    table=dict(preferred_codons or ECOLI_K12_PREFERRED)
    protein="".join(protein_sequence.split()).upper().rstrip("*")
    seq="".join(dna_sequence.upper().split()).replace("U","T")
    if translate_dna(seq).rstrip("*") != protein:
        raise ValueError("Input DNA does not translate to the supplied protein")

    def motif_count(s: str) -> int:
        return sum(s.count(m) for m in forbidden_motifs if m)

    current=motif_count(seq)
    substitutions=0
    passes=0

    while current > 0 and passes < max_passes:
        passes += 1
        improved=False
        for motif in forbidden_motifs:
            start=seq.find(motif)
            if start < 0:
                continue
            end=start+len(motif)-1
            first_codon=start//3
            last_codon=end//3
            for ci in range(first_codon,last_codon+1):
                aa=protein[ci] if ci < len(protein) else "*"
                original=seq[ci*3:ci*3+3]
                alternatives=[c for c in AA_CODONS[aa] if c != original]
                preferred=table.get(aa)
                alternatives=sorted(
                    alternatives,
                    key=lambda c:(0 if c==preferred else 1,c)
                )
                for codon in alternatives:
                    trial=seq[:ci*3]+codon+seq[ci*3+3:]
                    if translate_dna(trial).rstrip("*") != protein:
                        continue
                    score=motif_count(trial)
                    if score < current:
                        seq=trial
                        current=score
                        substitutions += 1
                        improved=True
                        break
                if improved:
                    break
            if improved:
                break
        if not improved:
            break

    if current:
        raise ValueError(
            f"Could not remove all forbidden motifs synonymously; remaining={current}"
        )
    if translate_dna(seq).rstrip("*") != protein:
        raise AssertionError("Synonymous motif repair changed the protein sequence")

    return CodonOptimizationResult(
        dna_sequence=seq,
        protein_sequence=protein,
        profile_name="synonymous_forbidden_motif_repair",
        substitutions=substitutions,
        original_dna=dna_sequence,
    )
