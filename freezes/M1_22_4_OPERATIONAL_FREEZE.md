# SynBioCrow M1.22.4 — Operational freeze record

Status: **OPERATIONAL SOFTWARE BASELINE APPROVED BY USER (2026-11-23)**.

This branch is based on `review/seven-engine-evidence` and must not be used to rewrite the working engine implementations.

## Verified live execution

Source: `SynBioCrow_M1_22_4_UNIFIED_LIVE_SEVEN_ENGINE_FINAL_ALL_OUTPUTS.zip`, checked locally with ZIP integrity test and inspected `outputs/acceptance.json`.

- `seven_engine_live_operational: PASS`
- Six native execution slots: DORAnet 173 reaction records; AiZynthFinder 31; RetroBioCat2 16; RetroPath2 1,399 candidate transitions; BioPKS 113 designs; RetroTide 113 designs.
- Hosted ChemEnzyRetroPlanner: 88 routes, job `178bb451-8619-47f2-85ac-dc442e0f1a36`.
- 1,619 native reaction/transition records; 147 hosted reaction occurrences; 367 admitted reaction occurrences; 50 structural cross-engine candidates.
- `scientific_pathway_certification: NOT_CERTIFIED`.
- RetroPath2 direction is unverified; PKS design records are not counted as reaction edges; cross-engine witnesses are structural candidates only.

## Immutable artifact SHA-256 inventory

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `SynBioCrow_M1_22_4_UNIFIED_LIVE_SEVEN_ENGINE.ipynb` | `0c60b71e5f45a397abd4e54481ce4d75df9791c4a656b1d108709134e4c81e04` | 15141 |
| `SynBioCrow_M1_22_4_SOURCE.zip` | `0eae1f7d230e73471eb836611db40c158cd17746b3c38ba3bad664e07814c783` | 6200 |
| `SynBioCrow_M1_22_4_UNIFIED_LIVE_SEVEN_ENGINE_FINAL_ALL_OUTPUTS.zip` | `bdd6fcd30ae6dbb0cd22dbcffe3380ec57896db47ba5ebbf20b630a4536e1c93` | 289963 |
| `outputs/hosted/routes.json` | `aab22366457e30556ef5dea4f39db134b81b0b6b16d96246006ab58ef8c42e42` | — |

**Artifact storage caveat:** This GitHub record contains the exact verified hashes, but the three named files have not yet been uploaded to GitHub. Do not claim a fully archived/reproducible GitHub freeze until the files are committed or attached to a release and reverified.

## Change control

1. No edits to pinned native engine implementations or hosted POST retrieval in this frozen baseline.
2. New scientific integration work happens on separate development branches.
3. Preserve evidence and failure logs; scientific certification remains independent of operational software acceptance.
