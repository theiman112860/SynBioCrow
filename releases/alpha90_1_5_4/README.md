# SynBioCrow V2.0 Alpha90.1.5.4

Zero-Candidate Identity-Boundary Proposal Recovery + Evidence-Preserving Orchestration.

Alpha90.1.5.3 demonstrated a real benchmark-blind orchestration signal: route-positive coverage was unchanged at 17/20 and exact top-10 remained 0, but mean full-identity ordered LCS increased from 0.1350 to 0.18083 and the source-aware B score was 0.2825, with 24 routes rescued from 351 raw candidates. Three cases produced zero raw candidates, which means downstream orchestration cannot help them.

Alpha90.1.5.4 therefore moves one boundary upstream. The frozen Alpha87.11 execution is still the A branch. B first applies the validated evidence-preserving recovery to the same raw pool. Only when the original raw pool is empty, a fixed benchmark-independent identity-boundary fallback generates deterministic equivalent molecular serializations (original, canonical isomeric SMILES, canonical non-isomeric SMILES, Kekule SMILES, and bounded rooted noncanonical SMILES) and retries proposal generation. Candidate pools are unioned and deduplicated before the recovery orchestrator. The zero-candidate trigger and serialization policy are fixed independently of Golden outcomes.

The source package is self-contained for predecessor bootstrap: it embeds the validated Alpha87.11/Alpha90.1.5.2 overlay plus slim, hash-traceable frozen target/reference manifests, so the notebook does not ask the user to re-upload predecessor artifacts. It uses bounded Drive discovery, per-target checkpointing, progress/elapsed/ETA, Drive-first output persistence, and rescue download.