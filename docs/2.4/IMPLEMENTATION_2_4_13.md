# SynBioCrow 2.4.13 — development route generation

2.4.13 runs the accumulated SynBioCrow design API on the four frozen
development targets only. It preserves raw candidate and route outputs before
any 2.4.12 biochemical discrimination is applied.

Development targets:
- methyl isobutyl ketone;
- jasmonic acid;
- dammaradienol;
- curcumin.

Sealed validation targets:
- bakuchiol;
- D-allitol.

The runner records backend readiness, selects only backends reporting available,
runs biosynthesis mode, persists one raw JSON result per target, and emits a
generation summary. Per-target backend failures are retained as evidence rather
than silently replaced with synthetic routes.

No validation truth is accessed and no ranking weights are learned.

The Colab launcher persists the complete output bundle to Google Drive before
browser download and provides a rescue-download cell.
