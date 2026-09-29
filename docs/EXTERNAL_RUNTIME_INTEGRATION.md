# Final external-runtime integration

SynBioCrow 2.2 RC uses explicit runtime boundaries for the two backends that
cannot safely share the main Python environment.

## BioPKS / RetroTide

BioPKS Pipeline is installed in an isolated Python 3.10 environment. The
reference notebook applies one transparent compatibility patch to the temporary
checkout: it removes the obsolete `umap==0.1.1` requirement while retaining
the upstream `umap_learn==0.5.2` dependency.

`scripts/biopks_synbiocrow_bridge.py` is the real JSON bridge consumed by
`BioPKSBackend`.

The bridge:
- imports the upstream BioPKS Pipeline and DORA-XGB model,
- supports bounded PKS / PKS+biology execution,
- normalizes explicit post-PKS reaction SMILES into the SynBioCrow bridge schema,
- retains architecture-only PKS output as provenance rather than inventing
  reaction chemistry,
- keeps BioPKS stdout away from the JSON protocol,
- supports a lightweight `smoke_only` request used by the RC notebook.

## RetroPath2 / RetroRules

`RetroPathSettings` now accepts an explicit `knime_install` directory.

The reference notebook calls the upstream-supported KNIME 4.7.0 bootstrap and
downloads the RetroPath2 wrapper's published functional-test resources:

- `rules_d12_7325.csv.gz` (decompressed locally)
- `lycopene/in/sink.csv`
- `lycopene/in/source.csv`

Those files are used **only for runtime validation**. They are not declared to
be SynBioCrow's production RetroRules/sink corpus.

Environment variables configure the default engine registry:

- `SYNBIOCROW_RETROPATH_RULES`
- `SYNBIOCROW_RETROPATH_SINK`
- `SYNBIOCROW_RETROPATH_KNIME`
- `SYNBIOCROW_BIOPKS_RUNNER`
- `SYNBIOCROW_BIOPKS_PYTHON`
- `SYNBIOCROW_BIOPKS_ACK_LICENSE`

The RC notebook runs real bridge/runtime smoke tests before M7/M9 verification.

## RetroPath workflow compatibility pin

For the 2.2 RC Colab runtime, SynBioCrow pins the RetroPath2 KNIME workflow to `r20220104` with KNIME `4.6.4`. This is the wrapper repository's functional-test lineage and avoids coupling the release candidate to the wrapper's moving default workflow (`r20260212` as of RC integration), whose node/flow-variable contract is not compatible with the distributed KNIME 4.6.4 runtime. This is an explicit reproducibility/compatibility pin, not a claim that the older workflow is scientifically superior.
