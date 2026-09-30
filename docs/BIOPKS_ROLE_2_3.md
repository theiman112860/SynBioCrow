# BioPKS/RetroTide role in SynBioCrow 2.3

## Decision

BioPKS/RetroTide remains integrated as a **specialized PKS generator** but is not treated as a general-purpose peer of DORAnet, RetroBioCat2, or RetroPath across the full manuscript benchmark.

## Evidence

- PKS-only generation completed successfully for naringenin and pinocembrin.
- Naringenin: 25 PKS designs, 17.8 s.
- Pinocembrin: 25 PKS designs, 11.3 s.
- The upstream combined PKS+bio workflow exceeded bounded runtime during DORAnet post-PKS expansion.
- Direct one-step JN1224MIN screening completed in 35.1 s and 29.2 s, generated 3,409 and 2,717 unique products, and found no exact target hit.
- A resumable direct beam search completed three depths with beam width 12 and found no exact target.
- Best 2D similarity by depth:
  - naringenin: 0.227 -> 0.300 -> 0.351
  - pinocembrin: 0.263 -> 0.389 -> 0.526

## Policy

1. Include BioPKS/RetroTide only on PKS-relevant targets.
2. Report PKS design success separately from downstream enzymatic completion.
3. Do not count post-PKS timeout as a biochemical no-hit.
4. Do not let BioPKS runtime failure change the general-ensemble denominator.
5. Preserve generated PKS candidates and provenance even when downstream completion is unresolved.
6. For manuscript comparisons, treat bounded direct post-PKS search as a specialist follow-on analysis rather than part of the general retrosynthesis benchmark.
7. Revisit broader BioPKS integration only if a future version provides tractable post-PKS expansion or a validated specialized continuation method.

## Current status

BioPKS/RetroTide is **integrated and operational for PKS candidate generation**, but **not benchmark-stable as an unrestricted combined PKS+post-PKS engine** in the current Colab environment.
