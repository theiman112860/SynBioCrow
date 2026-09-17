# SynBioCrow V2.0 Alpha90.1.4.3.2.5

Corrected Reference Reconnection + Predicted-Product Parser Certification.

This release reconnects the immutable Alpha90.1.4.3 sealed predictions to the reconciled 20/20, 70-step Golden reference from Alpha90.1.4.3.2.4 and certifies the predicted-product parser before any metrics are recomputed.

Parser certification is explicit: every serialized predicted product is classified either as a concrete molecular identity or as an explicit wildcard abstraction. In the real-input dry run, 1,389/1,408 products parsed to molecular InChIKeys, 19/1,408 were explicit `*` wildcard abstractions, and 0 were unclassified failures.

Two exact identity criteria are reported separately. `full` requires full InChIKey identity for every step. `source-aware` is identical except that the terminal target in the 8 Golden cases independently certified as source-stereo-unspecified may match by the 14-character InChIKey connectivity block; all earlier steps still require full identity. Partial/LCS concordance remains diagnostic and cannot be promoted to exact success.

The real-input dry run preserves route-positive coverage at 18/20 and gives full-identity S@10 = 0, source-aware S@10 = 0, mean best-route LCS fraction ≈0.148 (full) and ≈0.249 (source-aware). No new route generation, engine calls, prediction rewriting, aliases, benchmark tuning, or post-hoc bridge edits occur.

Packaged verification: 11/11 tests passed; all notebook code cells compile after fresh extraction.