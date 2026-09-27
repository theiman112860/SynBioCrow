# SynBioCrow 2.2 engine consolidation

## Completed

- M0 release preservation and core contracts
- M1 DORAnet, RetroBioCat2, RetroPath2/RetroRules adapters
- M2 reaction-level cross-engine ensemble graph
- M3 evidence and closure

### M3 components now implemented
- RetroPath identifier→structure remapping
- atom/formal-charge closure
- Rhea participant search
- strict exact-Rhea identifier + equation/direction contract
- reviewed UniProt exact-Rhea enzyme evidence
- reviewed UniProt EC/context evidence
- quantitative eQuilibrator standard transformed Gibbs energy
- route-level evidence aggregation
- no automatic lifecycle promotion

See [EVIDENCE_LAYER.md](EVIDENCE_LAYER.md) and [M3_COMPLETION.md](M3_COMPLETION.md).

## Next: M4 — sequence + construct design optimization

- evidence-backed enzyme sequence selection
- verified CDS acquisition
- amino-acid/CDS consistency
- nucleotide optimization while preserving amino-acid sequence by default
- chassis-aware codon optimization
- motif/restriction/repeat/GC QC
- promoter/RBS/terminator selection
- cassette assembly
- construct scoring and provenance

## Later

- M5 BioPKS/RetroTide migration
- M6 public execution API, CLI, Colab, bootstrap/readiness, resume
- M7 computational Test layer
- M8 Learn/closed-loop DBTL
- M9 2.2 release candidate and paper package
