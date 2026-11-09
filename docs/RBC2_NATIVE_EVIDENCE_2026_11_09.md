# RetroBioCat2 native reaction generation — 2026-11-09

## Evidence source
User-supplied `SynBioCrow_SEVEN_ENGINE_CANONICAL_V2_ALL_OUTPUTS (2).zip`, inspected directly. This evidence file documents observed output, not a rerun in CI. Native upstream commit: `c5f32561b1ed99d0701a6dbb472dc448d6c082e8`.

## Observations
- `results/results.json`: top-level `status=COMPLETED`, `engine=RetroBioCat2`, `search_literature_precedent=false`.
- 3-hydroxypropionic acid, `O=C(O)CCO`: `NATIVE_EXECUTED`, 9 reaction candidates.
- Butanal, `CCCC=O`: `NATIVE_EXECUTED`, 7 reaction candidates.
- Every exported reaction is marked `candidate_only=true` and `reaction_smiles_parseable=true`. These are native exporter flags, not independent chemical certification.
- Example candidate: `CCCCO>>CCCC=O`, native reaction name `Primary alcohol oxidation`, native score string `0.259`.
- `logs/smoke.log`: `RBC2_NATIVE_IMPORT_PASS`; `logs/native_expansion.log`: completed with counts 9 and 7.
- CUDA/cuDNN/TensorRT warnings appear, but did not prevent CPU native execution.
- `engine_status.json`: the other six slots are `NOT_CONFIGURED`; seventh identity remains `UNRESOLVED_SEVENTH_ENGINE` in this notebook.

## Scientific gate
**PASS**: pinned RetroBioCat2 installed/imported and produced genuine target-specific native reaction candidates for both smoke targets.

**NOT CLAIMED**: independently balanced reactions, biochemical feasibility, route closure, certified pathways, seven-engine readiness, or success on the sealed Galaxy benchmark.

## Next priority
Keep this RBC2 capability intact. Integrate its native candidate exchange and prioritize independently callable, target-specific native reaction generation in the remaining engine slots. Do not divert into ranking, hypergraph closure, or unrelated audits.
