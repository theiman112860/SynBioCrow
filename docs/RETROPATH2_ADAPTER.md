# RetroPath2 / RetroRules adapter

Status on the 2.2 consolidation branch: **live two-stage adapter implemented**.

The adapter uses the current upstream RetroPath2 Python wrapper to generate a
metabolic scope and then uses **rp2paths** to enumerate complete pathways.
SynBioCrow does not treat arbitrary reactions in the RetroPath2 scope as
complete routes.

## Runtime contract

1. Convert the target SMILES to a standard InChI with RDKit.
2. Run `retropath2_wrapper.retropath2(...)` with a configured sink and
   RetroRules/RetroPath2-ready rules file.
3. Interpret RetroPath2 return codes explicitly.
4. For successful scope generation, run:
   `python -m rp2paths all results.csv --outdir ...`
5. Parse `out_paths.csv` into Candidate pathways.

Current upstream wrapper revision inspected during migration:
`brsynth/retropath2-wrapper@d9948aa1672873d1e3c1905a355f62f714946e67`.

A full RetroRules rr02 RetroPath2-ready corpus can be supplied externally; the
large rules resource is intentionally not vendored into SynBioCrow.

## Result semantics

- RetroPath code **0**: scope completed; enumerate pathways.
- code **10**: source already belongs to sink; successful bounded terminal case,
  represented as no generated pathway.
- code **11**: no solution found; successful bounded no-hit, returns `[]`.
- other codes / KNIME failure / missing results / rp2paths failure:
  `BackendExecutionError`.

## Identity policy

`rp2paths/out_paths.csv` represents compounds using RetroPath identifiers.
During this migration those identifiers are preserved exactly and labeled
`RETROPATH_IDENTIFIER_PENDING_GRAPH_RESOLUTION`.

They are **not** silently treated as canonical SMILES/InChIKey identities.
The next reaction-graph ensemble milestone will resolve these identifiers before
cross-engine graph joining.

All RetroPath2 routes remain **Candidate** and cannot bypass evidence gates.
