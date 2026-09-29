# M9 — SynBioCrow 2.2 release candidate

M9 packages the consolidated engine without adding new scientific capability.

## RC contents

- finalized 2.2 README/backend installation matrix
- all-generators Jupyter/Colab notebook
- source/reproducibility bundle builder
- generated SHA-256 inventory
- Methods/Results paper draft skeleton
- CI package-smoke gate

## Release procedure

1. Require green CI for the final RC commit.
2. Run `python scripts/m7_release_readiness.py`.
3. Run `python scripts/build_m9_release.py --output-dir dist_m9`.
4. Inspect the generated release manifest and hashes.
5. Create tag `v2.2.0-rc1`.
6. Create GitHub prerelease and attach the generated ZIP.
7. After RC acceptance, create `v2.2.0` and archive the final release with Zenodo.
8. Update CITATION.cff/README/paper with the final 2.2 DOI.

## Packaging exclusions

The release builder excludes Git metadata, caches, run-state/build directories, development-history material, and non-public truth/holdout-named paths. It never searches for or opens protected benchmark truth.

## All-generators notebook

`notebooks/SynBioCrow_2_2_RC1_ALL_GENERATORS.ipynb` distinguishes:

- **IMPORTABLE**
- **CONFIGURED**
- **EXECUTION_READY**

This distinction is essential for RBC2 data assets, RetroPath2 KNIME/rules/sink resources, and the authorized BioPKS external bridge.
