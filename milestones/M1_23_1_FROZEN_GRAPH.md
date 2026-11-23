# M1.23.1 — Frozen evidence graph, independent scientific layer

The verified M1.22.4 engine implementations remain unchanged. This development branch derives a graph from the frozen `outputs/integration/normalized_admissible.json` within `SynBioCrow_M1_22_4_UNIFIED_LIVE_SEVEN_ENGINE_FINAL_ALL_OUTPUTS.zip`.

Source archive SHA-256: `bdd6fcd30ae6dbb0cd22dbcffe3380ec57896db47ba5ebbf20b630a4536e1c93`.

## Locally executed result

- Input admissible reaction occurrences: **367**
- Reaction edges after removing one identity/reordering edge: **366**
- Exact intermediate two-step candidates across distinct engines: **12**
- Certified multistep pathways: **0**
- No native engines rerun; no hosted jobs submitted.

Graph rule: for a reaction `A.B>>C.D`, record component SMILES and link two reactions when a product component of the first exactly equals a reactant component of the second, the engines differ, and neither reaction is an identity/reordering. This is a **structural-only** check: co-reactant supply, atom balance, cofactors, enzymes, and thermodynamics are not verified. The older 50 structural witnesses included an identity step; those are not scientific pathway proof.

## Acceptance gates

- Operational baseline: inherited from frozen M1.22.4, **PASS**.
- Reaction graph construction: **PASS** on saved evidence.
- Cross-engine structural two-step matching: **12 candidates**.
- Chemically complete/biochemically supported pathway: **NOT CERTIFIED**.

## Artifact archival status

The exact M1.22.4 notebook, SOURCE ZIP, and ALL_OUTPUTS ZIP are still local conversation artifacts, not committed GitHub blobs. GitHub archival is **incomplete**. Do not tag this as a fully reproducible archive until their bytes are committed and hashes reverified.

## Next scientific step

Review the 12 candidates for reaction direction, required co-reactants, atom balance, enzyme support, and whether either engine independently found the full two-step route. No changes to the frozen engine adapters.
