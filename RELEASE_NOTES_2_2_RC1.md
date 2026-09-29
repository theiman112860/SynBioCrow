# SynBioCrow 2.2.0-rc1 release notes

SynBioCrow 2.2.0-rc1 is the first release candidate of the consolidated engine.

## Major additions since 2.1.1

- DORAnet, RetroBioCat2, RetroPath2/rp2paths, and BioPKS/RetroTide adapters
- reaction-level cross-engine ensemble graph
- conservative molecular identity resolution
- Rhea, reviewed UniProt, and eQuilibrator evidence layers
- protein/CDS validation and amino-acid-preserving nucleotide optimization
- sequence QC and cassette assembly
- unified API, CLI, notebooks, checkpoint/resume
- M7 Test/reproducibility gate
- M8 bounded/auditable Learn layer
- M9 source/reproducibility package builder and all-generators notebook

## Scientific invariants

2.2.0-rc1 does not reopen protected benchmark-v2 truth, modify the frozen Paper-1/v0.21 baseline, or collapse Candidate/Mature/Certified states.

The RC should be tagged/released only after the final GitHub Actions matrix and M9 package-smoke job are green.
