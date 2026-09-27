import unittest

from synbiocrow.sequence import (
    ProteinEvidence, CDSEvidence, validate_cds_against_protein,
    optimize_protein_sequence, translate_dna,
)
from synbiocrow.cassette import RegulatoryPart, build_expression_cassette
from synbiocrow.design import design_expression_construct
from synbiocrow.core.models import LifecycleState

class M4ConstructTests(unittest.TestCase):
    def setUp(self):
        self.protein=ProteinEvidence(
            accession="PTEST", source="fixture", sequence="MKT", reviewed=True
        )
        self.cds=CDSEvidence(
            nucleotide_accession="NTEST",
            source="fixture",
            cds_sequence="ATGAAAACC",
            protein_accession="PTEST",
        )
        self.promoter=RegulatoryPart("P1","promoter","TTGACA","fixture")
        self.rbs=RegulatoryPart("R1","rbs","AGGAGG","fixture")
        self.terminator=RegulatoryPart("T1","terminator","TTTTGC","fixture")

    def test_cds_translation_must_match_selected_protein(self):
        v=validate_cds_against_protein(self.cds,self.protein)
        self.assertTrue(v.valid)
        bad=CDSEvidence("BAD","fixture",cds_sequence="ATGAAAAGC")
        self.assertFalse(validate_cds_against_protein(bad,self.protein).valid)

    def test_codon_optimization_preserves_amino_acid_sequence(self):
        result=optimize_protein_sequence("MKT")
        self.assertEqual(translate_dna(result.dna_sequence).rstrip("*"),"MKT")

    def test_construct_pipeline_stays_candidate(self):
        result=design_expression_construct(
            pathway_id="route-1",
            protein=self.protein,
            cds=self.cds,
            promoter=self.promoter,
            rbs=self.rbs,
            terminator=self.terminator,
        )
        self.assertTrue(result.validation.valid)
        self.assertEqual(
            translate_dna(result.optimization.dna_sequence).rstrip("*"),
            self.protein.sequence,
        )
        self.assertEqual(
            result.cassette.candidate.lifecycle,
            LifecycleState.CANDIDATE,
        )
        roles=[p.role for p in result.cassette.candidate.parts]
        self.assertEqual(roles,["promoter","rbs","cds","terminator"])

    def test_unverified_regulatory_sequence_blocks_build(self):
        missing=RegulatoryPart("P1","promoter",None,"fixture")
        with self.assertRaises(ValueError):
            build_expression_cassette(
                pathway_id="route-1",
                cds_sequence=self.cds.cds_sequence,
                promoter=missing,
                rbs=self.rbs,
                terminator=self.terminator,
            )

if __name__=="__main__":
    unittest.main()
