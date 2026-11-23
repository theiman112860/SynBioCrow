# M1.23.2 — Evidence-only chemical validation

Computed locally using RDKit 2025.09.4 from the 12 candidate records in M1.23.1. No engines were rerun and no hosted jobs were submitted.

## Results

- 12/12 candidate reaction SMILES parsed successfully.
- 4/12 two-step candidates have explicit heavy-atom balance in **both** steps.
- 6/12 have formal-charge balance in **both** steps.
- 6/12 have additional second-step reactants beyond the matched intermediate.
- 0/12 have independently verified reaction direction in this evidence.
- 0/12 have independently established enzyme support.
- 0/12 are certified biochemical pathways.

These are **explicit-reaction balance** checks, not proofs of chemistry. Missing water, cofactors, protons, and incomplete engine records can explain imbalances. Implicit hydrogen balance was not checked. Route novelty versus individual engines is not established.

Input: `SynBioCrow_M1_23_1_GRAPH_ALL_OUTPUTS.zip`.
Reproducible local notebook: `SynBioCrow_M1_23_2_CHEMICAL_VALIDATION.ipynb`.
Detailed results: `SynBioCrow_M1_23_2_CHEMICAL_VALIDATION_ALL_OUTPUTS.zip`.

**Gate:** M1.23.2 screening complete; scientific pathway certification **NOT CERTIFIED**. Next work: reaction-level provenance, cofactor-normalized balance, direction and enzyme mapping against external reaction databases, and comparison to full single-engine routes. The frozen seven-engine baseline must not be modified.
