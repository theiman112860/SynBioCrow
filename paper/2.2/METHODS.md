# SynBioCrow 2.2 paper draft — Methods

## System architecture
SynBioCrow separates generator proposal, graph integration, evidence, construct design, testing, and learning into explicit contracts.

## Generator ensemble
DORAnet, RetroBioCat2, RetroPath2/RetroRules, and external BioPKS/RetroTide are normalized to Candidate records. Runtime failure is distinct from a bounded no-hit.

## Reaction-level graph union
Normalized reactions become retrosynthetic hyperedges merged on canonical molecular identity when structures are available, retaining per-engine provenance.

## Evidence
Evidence includes atom/formal-charge closure, exact Rhea identifier/equation confirmation, reviewed UniProt exact/context evidence, and optional eQuilibrator thermodynamics. Missing evidence yields ABSTAIN.

## Sequence/construct design
Verified CDS coordinates must translate exactly to selected protein. Synonymous redesign preserves amino-acid sequence by default. Regulatory sequences require explicit provenance.

## Test and Learn
M7 verifies frozen policies/hermetic reproducibility. M8 performs bounded versioned prioritization updates and cannot alter evidence or lifecycle.

## Reproducibility
The sealed 2.1 state is a read-only regression anchor. The M9 package builder records per-file SHA-256 hashes and the release commit.
