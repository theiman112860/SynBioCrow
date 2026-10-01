# SynBioCrow 2.3.0 release notes

## Release status

SynBioCrow 2.3 is scientifically frozen. This release packages the frozen scientific state without post-holdout tuning.

## Scientific freeze

- Scientific freeze commit: `39b3b21d8a5018001746a1ad783859cba75f9ad5`
- Freeze package SHA-256: `67bea03543b60f4299aace5e1de674357e9ffed88e1a2d2fc21dc47c83cfcaf6`
- Sealed predictions: `68fbf9440eecf3103ca70734bc7d71514978fbeab008ba0ab1734cab030f1200`
- Scored Galaxy benchmark: `4ccfb292295e9017098c061b36baacf1fcacf8ff95182a114b66ee4d7977d809`
- Error analysis: `c7c960a866e3347e7355773648fc875243778a6e6f8ecbc8f2f7937ebefdd764`
- Frozen 2D-primary policy: `7448c031189a1c42a13f16c1856efef30c95de19a0059f5c87166b4ddcced7e4`
- Frozen manuscript hash: `b25abe53beb07511e2ff375a6f37e4bb9f51381ccbbf76a5044f49b0bc6d9539`

## Held-out Galaxy benchmark

The denominator is 65 pathways; 64 were runnable and `literature_10` (3-methylbutanol) was mapping-limited.

Connectivity-level partial recovery:
- ensemble: 19/65
- RetroBioCat2: 13/65
- RetroPath standalone: 9/65
- DORAnet: 0/65

RetroPath recovered p-hydroxystyrene and phenol exactly at rank 12. The ensemble preserved both routes but the frozen 2D reranking placed them at ranks 46 and 31. SynBioCrow 2.3 therefore does not claim improved exact Top-K ranking.

Failure classification: 42/65 complete predicted routes with zero literature-reaction overlap; 17/65 partial recovery; 2/65 exact recovery; 3/65 backend runtime failure; 1/65 mapping-limited.

## Similarity policy

Development-set leave-one-pathway-out ranking favored Morgan/Tanimoto 2D over USRCAT 3D-first/3D-only. Version 2.3 therefore freezes 2D as the primary signal and retains 3D only as an optional secondary feature.

## Computational DBTL

The release includes provenance-aware Design, sequence-backed Build, evidence/QC Test, and bounded Learn. Learn can change prioritization weights only; it cannot create evidence, alter evidence gates, access protected benchmark truth, or promote Candidate/Mature/Certified lifecycle state.

The sabinene Build example resolves reviewed sabinene synthase A6XH06, designs a 1,746-nt E. coli-preferred CDS with exact translation preservation, repairs one BamHI motif synonymously, and passes sequence QC at 54.58% GC. Full cassette assembly abstains because verified promoter/RBS/terminator sequences were not supplied.

## Scope and limitations

All claims are computational. The release does not establish experimental pathway activity, enzyme productivity, titer, yield, or construct function. Literature-route recovery is not equivalent to chemical feasibility, and connectivity-level matching is less stringent than stereochemical reaction identity.

## Next research line

SynBioCrow 2.4 will focus on biochemical discrimination and route ranking using a fresh untouched evaluation set. The 65-path 2.3 held-out benchmark remains frozen and must not become a tuning set.
