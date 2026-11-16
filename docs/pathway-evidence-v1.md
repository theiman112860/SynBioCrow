# Pathway evidence v1

This feature produces a **candidate graph witness**, not scientific certification, and does not reinstall or run any native generator.

## Existing historical archive adapter

The adapter accepts two previously inspected SynBioCrow archive layouts:
- `SynBioCrow_AiZynth_Seven_Engine_Combined_RESULTS.zip` with `combined_reaction_candidates.json`
- `SynBioCrow_AIZYNTH_TARGET_BIDIRECTIONAL_INTEGRATION.zip` with `synbiocrow_target_integration/combined_reactions.json`

Records must have `id`, `engine`, `substrates`, `products`, `direction`, `source_file` and `source_sha256`. Missing evidence is quarantined. The historical source's explicit substrate-to-product orientation is preserved; no reverse chemistry is inferred. SMILES are treated as exact strings, not canonicalized.

Example:
```bash
python scripts/trace_legacy_archive.py SynBioCrow_AiZynth_Seven_Engine_Combined_RESULTS.zip --target 'CCCCCC(=O)O' --seed 'CCCCCCO' --output hexanoic_graph_evidence.json
```

This example reports a candidate graph connection only. The source's native direction and chemical feasibility still require independent validation.

For a custom normalized JSON input use `python scripts/trace_pathway_evidence.py INPUT.json`.

## Safety boundary

The tracer requires all substrates, records reaction IDs and source hashes, and separates graph reachability from biochemical validity. It does not evaluate carbon/atom balance, enzyme support, cofactor availability, thermodynamics, organism constraints, or experimental validation. BioPKS/RetroTide designs must not be treated as chemical edges without verified release chemistry.

Tests: `python -m unittest discover -s tests -p 'test_*pathway_evidence.py'` and `python -m unittest discover -s tests -p 'test_legacy_adapter.py'`.
