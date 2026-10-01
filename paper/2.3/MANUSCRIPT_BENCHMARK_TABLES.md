# SynBioCrow 2.3 manuscript benchmark tables

## Held-out Galaxy benchmark

| Backend | Connectivity-level partial recovery | Exact Top-50 connectivity routes | Exact Top-10 |
|---|---:|---:|---:|
| Ensemble | 19/65 | 2/65 | 0/65 |
| RetroBioCat2 | 13/65 | 0/65 | 0/65 |
| RetroPath standalone | 9/65 | 2/65 | 0/65 |
| DORAnet | 0/65 | 0/65 | 0/65 |

RetroPath recovered p-hydroxystyrene and phenol exactly at rank 12. The ensemble preserved both but the frozen 2D-primary ranking placed them at ranks 46 and 31, respectively.

## Held-out failure analysis

| Failure class | Count |
|---|---:|
| Complete predicted route, zero literature-reaction overlap | 42 |
| Partial literature-route recovery | 17 |
| Exact connectivity-level route recovery | 2 |
| Backend runtime failure | 3 |
| Mapping-limited | 1 |

Denominator: 65 pathways. Runnable: 64. Mapping-limited: `literature_10` (3-methylbutanol).

## Similarity-policy ablation

| Policy | Exact Top-1 | Exact Top-5 | Exact-route MRR | EC-neighbor Top-1 | EC-neighbor MRR |
|---|---:|---:|---:|---:|---:|
| 2D Morgan/Tanimoto | 1/12 | 2/12 | 0.7500 | 9/10 | 0.925 |
| 3D-first USRCAT | 1/12 | 1/12 | 0.5294 | 8/10 | 0.900 |
| 3D-only USRCAT | 1/12 | 1/12 | 0.5294 | 8/10 | 0.900 |

3D changed the top-ranked route on 10/12 development targets but did not improve validated outcomes.
