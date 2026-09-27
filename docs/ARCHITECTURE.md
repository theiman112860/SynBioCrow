# Architecture

SynBioCrow 2.1 uses layered DBTL-oriented computational contracts:

1. Core biosynthesis generators and reaction-graph ensemble.
2. Evidence/closure/thermodynamic gates separated from raw generation.
3. Sequence/CDS provenance and cassette/construct generation.
4. Specialized bounded PKS generation through RetroTide/BioPKS.
5. Candidate -> Mature -> Certified lifecycle with fail-closed promotion.
6. Release API exposing sealed manifests and provenance.

Specialized generators never bypass the ordinary evidence gates. Rhea is evidence/closure infrastructure, not counted as an independent generator.
