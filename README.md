# SynBioCrow 2.1.0

SynBioCrow is a computational synthetic-biology pathway-design framework built around a DBTL-oriented workflow, multiple biosynthesis/bioretrosynthesis generators, evidence-aware reaction-graph integration, sequence/CDS provenance, and explicit Candidate -> Mature -> Certified lifecycle gates.

## SynBioCrow 2.1 scientific state

- 19 unique provenance-backed **Candidate** DNA constructs are retained from final computational validation.
- 6 normalized BioPKS/RetroTide specialized-generator pathways are retained as **Candidate**.
- 0 specialized pathways are Mature or Certified.
- `rule0024_21` is frozen as an explicit evidence abstention: stoichiometric closure passes, but direct reaction evidence, verified enzyme identity, and quantitative thermodynamics are not established.
- The Paper-1 v0.21 baseline remains frozen.
- Benchmark-v2 truth remains isolated and was not accessed during this release.

## Stable Python API

```python
from synbiocrow import SynBioCrowRelease

r = SynBioCrowRelease("/path/to/release_bundle")
print(r.status())
print(r.policies())
print(r.specialized_summary())
```

The 2.1 API is deliberately read-only. It exposes sealed release status, provenance, policy, and evidence-abstention records without silently promoting scientific states.

## Release gates

SynBioCrow 2.1.0 passed the integrated regression, API packaging, documentation, and GitHub assembly gates. See `RELEASE_NOTES.md`, `docs/`, `integrated_regression.json`, and `release_manifest.json`.

## Repository history

The earlier notebook-era SynBioCrow files are intentionally preserved in this repository as historical material. The `synbiocrow/` package and 2.1 documentation are the current release surface.
