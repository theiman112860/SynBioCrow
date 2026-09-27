# SynBioCrow 2.2 engine consolidation

## Completed

- M0 release preservation/core contracts
- M1 generator adapters
- M2 reaction-level cross-engine ensemble graph
- M3 evidence/thermodynamics
- M4 sequence/construct optimization
- M5 BioPKS/RetroTide integration
- M6 unified execution API/CLI/Jupyter/Colab/resume
- M7 computational Test/reproducibility/release-readiness
- M8 Learn/closed-loop DBTL
- M9 2.2 release-candidate packaging

### M9 components

- package version 2.2.0rc1
- finalized README/backend installation matrix
- all-generators Jupyter/Colab setup notebook
- source/reproducibility ZIP builder
- generated per-file SHA-256 release manifest
- package summary with ZIP SHA-256
- RC release notes
- Methods/Results paper draft skeleton
- M9 CI package-smoke gate

## Remaining release actions

1. Require green CI on final M9 commit.
2. Build/inspect M9 package.
3. Tag `v2.2.0-rc1`.
4. Publish GitHub prerelease with package.
5. After acceptance, promote to `v2.2.0`.
6. Archive final 2.2 release with Zenodo and update citation metadata.

No further feature milestone is required before the RC.
