# Integrated candidate pathway report v1

The integrated CLI connects existing archived reaction records to the graph tracer, citation-required biochemical annotations and initial route ranking. It requires no native generator installation.

```bash
python scripts/build_integrated_pathway_report.py SynBioCrow_AiZynth_Seven_Engine_Combined_RESULTS.zip --target 'CCCCCC(=O)O' --seed 'CCCCCCO' --output pathway_report.json
```

Optionally pass `--evidence curated_evidence.json`, a JSON mapping from reaction IDs to dimension states and citations. Unknowns remain NOT_EVALUATED. A single candidate's rank is descriptive; comparing alternatives requires generating multiple independent witnesses.

No scientific certification, thermodynamic calculation, enzyme lookup, atom-balance validation or experimental verification is implied.
