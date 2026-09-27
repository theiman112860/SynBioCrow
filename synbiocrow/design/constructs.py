from __future__ import annotations
from dataclasses import dataclass

from synbiocrow.sequence import (
    ProteinEvidence, CDSEvidence, SequenceValidation,
    CodonOptimizationResult, validate_cds_against_protein,
    reoptimize_cds, sequence_qc, SequenceQC,
)
from synbiocrow.cassette import (
    RegulatoryPart, CassetteBuildResult, build_expression_cassette,
)

@dataclass(frozen=True)
class ConstructDesignResult:
    validation: SequenceValidation
    optimization: CodonOptimizationResult
    optimized_cds_qc: SequenceQC
    cassette: CassetteBuildResult

def design_expression_construct(
    *,
    pathway_id: str,
    protein: ProteinEvidence,
    cds: CDSEvidence,
    promoter: RegulatoryPart,
    rbs: RegulatoryPart,
    terminator: RegulatoryPart,
    preferred_codons=None,
    profile_name: str = "ecoli_k12_simple_preferred",
) -> ConstructDesignResult:
    validation=validate_cds_against_protein(cds,protein)
    if not validation.valid:
        raise ValueError(
            "Cannot design construct: CDS/protein validation failed: "
            + validation.reason
        )
    if not cds.cds_sequence or not protein.sequence:
        raise ValueError("Validated CDS/protein sequences are required")

    optimized=reoptimize_cds(
        cds.cds_sequence,
        protein.sequence,
        preferred_codons=preferred_codons,
        profile_name=profile_name,
    )
    optimized_qc=sequence_qc(optimized.dna_sequence)
    cassette=build_expression_cassette(
        pathway_id=pathway_id,
        cds_sequence=optimized.dna_sequence,
        promoter=promoter,
        rbs=rbs,
        terminator=terminator,
        cds_identifier=cds.nucleotide_accession,
        cds_source=cds.source,
    )
    return ConstructDesignResult(
        validation=validation,
        optimization=optimized,
        optimized_cds_qc=optimized_qc,
        cassette=cassette,
    )
