# BioPKS M2.4.9.3 native chain transition evidence — 2026-11-09

Source: user-uploaded `SynBioCrow_M2_4_9_3_BIOPKS_MODULE_REACTION_TRACE_ALL_OUTPUTS (1).zip`.

## Native result
Upstream pinned commit: `372cbfe9caf452fdf83976e6d0f32511dd28fccb`. Native `biopks_pipeline.retrotide.retrotide.designPKS` completed for both requested targets.

| Target | Designs | Unique product SMILES | Chain transitions | Unique (reactant, product) pairs |
|---|---:|---:|---:|---:|
| 3-hydroxypropionic acid | 36 | 32 | 5 | 5 |
| Butanal | 41 | 31 | 15 | 4 |
| Total | 77 | 63 within-target | 20 | 9 |

These counts were computed directly from `native_designs.json` and `native_chain_transitions.json`. They are not free-product reactions. Each row's `target_specific_reaction_verified` and `balanced_reaction_verified` is false; both native probe summaries record zero verified reaction records.

Example native chain-state change for butanal-directed design: `CC(=O)[S]` to `CCCC(=O)[S]`.

## Decision
- Native installation and PKS design API: **PASS**.
- Native PKS-bound chemical chain-state generation: **PASS**.
- Genuine target-specific reaction record gate: **NOT YET PASSED**.
- Do not conflate a design conditioned on a target with a reaction involving or yielding that target.

## Next bounded microtask
Recover exact domain-by-domain chemical transformations from upstream `bcs.py` operations (AT/KS condensation, KR, DH, ER, TE) on selected native designs, with module and domain provenance. Explicitly record native reaction SMARTS, before/after chain states, extender and cofactors where supported. Do not fabricate stoichiometry, release products, or target matching. Check at least one chemically appropriate PKS target if both smoke targets are outside supported synthesis domain. Keep candidate and certified statuses separate.
