# SBC-SOURCE-002 — RetroBioCat2 interface reconciliation

## Source interfaces (static inspection, not runtime certification)

| Contract | V14 `native_adapter_v13_3.py` | Canonical V2 `SynBioCrow_Seven_Engine_Canonical_V2.ipynb` |
|---|---|---|
| Python import | `rbc2.mcts.mcts.MCTS` | `rbc2.RetroBioCatExpander` |
| Native entrypoint | Construct MCTS with `target_smi` and configured expander, then attempt `run/search/run_search` | `RetroBioCatExpander(search_literature_precedent=...).get_reactions(target_smiles)` |
| Setup | External engine source dir and explicit `SYNBIOCROW_RBC2_EXPANDER` / kwargs | Isolated uv/Python 3.11, upstream source pinned to `c5f32561b1ed99d0701a6dbb472dc448d6c082e8` |
| Target | CLI `--target`, default `CC(=O)O` | `targets.json` list of `[name, SMILES]` |
| Output | `retrobiocat2.worker.json`, `native_execution_report.json`; native result represented as type/repr | `results/results.json` with per-target `reactions[]`; optional `synbiocrow_candidate_reactions.csv` |
| Error handling | `CONTRACT_UNRESOLVED`, worker exception, timeout; `NATIVE_CALL_RETURNED_UNVERIFIED` does not prove reaction | `TARGET_FAILED`, `ENGINE_FAILED`, `PARTIAL_FAILURE`, nonzero process exit |
| Reaction provenance | No exported reaction records in current RBC2 path | `engine`, `source_commit`, `target_smiles`, `reaction_smiles`, `candidate_only`, `reaction_smiles_parseable` |
| Acceptance | **INCONCLUSIVE**: no target-specific reaction records | **PENDING NATIVE RUN**: supports auditable records, but static inspection is not proof of successful generation |

## Important constraints

- These are **different native APIs**, not interchangeable adapters. Do not replace one with the other based on imports alone.
- Canonical V2's `reaction_smiles_parseable` flag is a parser result, **not** stoichiometric balance, pathway closure, or biochemical feasibility.
- A target with `NATIVE_EXECUTED` and **zero reactions** is a successful invocation but **not** target-specific generation PASS.
- Both the expected target and the pinned source commit must match evidence; missing or mismatched provenance fails the evidence gate.
- No source ZIP, frozen 2.3 artifacts, or 65-path benchmark was modified.

## Native Colab reproduction

1. Open the uploaded `SynBioCrow_Seven_Engine_Canonical_V2.ipynb` in Google Colab.
2. Run its cells in order; retain the isolated uv-based Python environment and pinned upstream RBC2 commit.
3. Use the included smoke targets: `O=C(O)CCO` (3-hydroxypropionic acid), `CCCC=O` (butanal).
4. Download `SynBioCrow_SEVEN_ENGINE_CANONICAL_V2_ALL_OUTPUTS.zip`.
5. Validate the contained `results/results.json` against the evidence contract. **PASS requires at least one genuine native reaction for each target being claimed as passed**.

## Acceptance gate

- Static interface reconciliation: **PASS**.
- Stdlib contract validator self-tests: run in CI or locally before relying on it.
- Native target-specific RBC2 generation: **INCONCLUSIVE** until new Colab evidence is provided.
- Seven-engine native ensemble: **NOT CERTIFIED**.

Next scientific step: one native RBC2 Colab run, inspect actual reaction rows, and then integrate its export schema into the seven-engine controller without changing engine chemistry.
