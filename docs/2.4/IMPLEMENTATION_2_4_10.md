# SynBioCrow 2.4.10 — exact target-identity blacklist recovery

## Purpose

2.4.10 completes the machinery needed to recover the exact target identities
behind the 65 frozen SynBioCrow 2.3 Galaxy held-out pathways.

## Source

Galaxy-SynBioCAD Supplementary Dataset 2 is the original source used by the
released 2.3 ingest/normalization notebooks.

The publication states that Dataset 2 contains:
- 77 literature pathways;
- 60 expressed compounds;
- substrate/product structures and EC annotations used for literature benchmarking.

## Recovery modes

The recovery runner accepts either:
1. the original Supplementary Dataset 2 XLSX; or
2. the previously normalized SynBioCrow 2.3 Galaxy benchmark JSON.

For XLSX input it reproduces the released 2.3 logic:
- identify the literature-pathway sheet;
- read `pathway_lit_ID`, target name, and target InChI;
- convert InChI to canonical isomeric SMILES with RDKit;
- reconstruct the released deterministic 12-development/65-heldout split;
- select exactly the 65 held-out pathway records.

Any source with other than 77 literature pathways fails closed.

## Target blacklist

The output records:
- all 65 held-out pathway IDs;
- target names;
- source InChI;
- canonical target SMILES;
- number of unique held-out targets;
- source SHA-256;
- target-blacklist SHA-256.

## Tranche resolution

Each 2.4 source-tranche target is RDKit-canonicalized and compared with the
held-out blacklist.

Resolution policy:
- exact canonical structure match → `blocked_historical_23`;
- name match without structure match → `pending` for manual mapping review;
- no structure or name match → `verified_excluded`.

The 2.4 split may be frozen only if `pending_count == 0`.

## Colab runner

`notebooks/SynBioCrow_2_4_10_TARGET_BLACKLIST_RECOVERY.ipynb`

The notebook:
- mounts Google Drive;
- clones `develop/2.4`;
- installs RDKit/openpyxl;
- tries the exact public publisher URLs used by the released 2.3 notebook;
- if blocked, asks for only the ~55 KB Supplementary Dataset 2 XLSX;
- reconstructs and validates the blacklist;
- resolves the tranche;
- persists outputs to Drive;
- produces a rescue-download ZIP.

## Current environment limitation

The current ChatGPT execution environment can verify that the public article
still exposes Supplementary Dataset 2 as a 55 KB XLSX, but cannot retrieve the
binary supplement bytes from Springer Nature/PMC.

Therefore the code and Colab recovery workflow are complete, while the final
resolved blacklist artifact remains pending one successful Colab download or
single-file upload.

No benchmark split is frozen until the exact recovery passes.
