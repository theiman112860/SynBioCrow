# SynBioCrow 2.2.0-rc1

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22999039.svg)](https://doi.org/10.5281/zenodo.22999039)

**SynBioCrow** is a computational synthetic-biology design framework for moving from a target molecule to evidence-aware biosynthetic pathway Candidates and provenance-backed DNA construct Candidates.

> **Release-candidate status:** 2.2.0-rc1 is the consolidated engine release candidate. Candidate pathways and constructs are computational designs, not experimental certifications. The DOI above is the archived 2.1.1 record; a new archival version should be minted when 2.2 is formally released.

## What changed in 2.2

SynBioCrow 2.2 consolidates the development lineage into one engine: DORAnet, RetroBioCat2, RetroPath2/RetroRules, BioPKS/RetroTide, reaction-level cross-engine graph union, evidence/thermodynamics, sequence/construct design, unified execution, Test/reproducibility, and bounded auditable Learn/DBTL.

The frozen Paper-1/v0.21 baseline and benchmark-v2 truth boundary remain unchanged.

## Install the release-candidate core

```bash
pip install -e .
```

This installs **SynBioCrow core plus RDKit**. It does **not** silently install every generator runtime.

Optional extras:

```bash
pip install -e ".[doranet]"
pip install -e ".[thermo]"
```

### Generator/runtime requirements

| Component | Current upstream location | Installation/runtime notes |
|---|---|---|
| **DORAnet** | https://github.com/wsprague-nu/doranet | Optional SynBioCrow extra pins the validated 0.5.7a1 API. |
| **RetroBioCat2** | https://github.com/willfinnigan/RetroBioCat-2 | Separate pinned research runtime; RBC2 scientific data assets are required for real searches. |
| **RetroPath2 wrapper** | https://github.com/brsynth/retropath2-wrapper | Python wrapper plus KNIME runtime. |
| **rp2paths** | https://github.com/brsynth/rp2paths | Enumerates complete pathways from RetroPath2 scope output. |
| **RetroRules** | https://retrorules.org | Reaction-rule resource used by RetroPath2; rules/sink remain explicit inputs. |
| **RetroTide** | https://github.com/JBEI/RetroTide | Specialized PKS generator; installed separately. |
| **BioPKS Pipeline** | https://github.com/JBEI/BioPKS-Pipeline | External specialized runtime. Review/accept upstream license before use. SynBioCrow does not vendor it. |
| **KNIME** | https://www.knime.com/ | Required by the current RetroPath2 workflow. |
| **eQuilibrator** | https://github.com/equilibrator/equilibrator-api | Optional thermodynamics via `.[thermo]`. |

Check readiness:

```bash
synbiocrow readiness
synbiocrow bootstrap
```

## All-generators Jupyter/Colab notebook

Reference notebook:

`notebooks/SynBioCrow_2_2_RC1_ALL_GENERATORS.ipynb`

It installs/imports SynBioCrow, DORAnet, RetroBioCat2, RetroPath2 wrapper, rp2paths, RetroTide, BioPKS Pipeline (after explicit license acknowledgement), and eQuilibrator. It distinguishes **importable**, **configured**, and **execution-ready**.

## Quick API

```python
from synbiocrow import DesignRequest, design
result = design(
    DesignRequest(
        target_smiles="CCO",
        mode="biosynthesis",
        backend_ids=("doranet", "retrobiocat2"),
        sink_smiles=("CC",),
    ),
    state_root=".synbiocrow_runs",
)
```

## CLI

```bash
synbiocrow readiness
synbiocrow bootstrap
synbiocrow design "CCO" --backend doranet --sink "CC"
synbiocrow learn --outcomes outcomes.json --output learned_policy.json --audit-log learning_audit.jsonl
```

## Design-Build-Test-Learn

- **Design:** multi-generator pathway discovery and cross-engine graph assembly
- **Build:** verified CDS selection, synonymous nucleotide optimization, cassette assembly
- **Test:** evidence gates, thermodynamics, reproducibility, runtime/construct validation
- **Learn:** bounded versioned ranking-policy updates with append-only audit

Learning changes prioritization only; it cannot create evidence or promote Candidate → Mature → Certified.

## Release-candidate verification

```bash
python -m unittest discover -s tests -v
python scripts/m7_release_readiness.py
python scripts/build_m9_release.py --check
python scripts/build_m9_release.py --output-dir dist_m9
```

See [M9 release candidate](docs/M9_RELEASE_CANDIDATE.md), [M7 Test](docs/M7_TEST_REPRODUCIBILITY.md), [M8 Learn](docs/M8_LEARN_DBTL.md), and [limitations](docs/LIMITATIONS.md).

## Historical release and citation

The sealed 2.1 scientific release remains under `release/2.1.0/`.

Archived 2.1.1 DOI: **10.5281/zenodo.22999039**

Until the final 2.2 Zenodo record is minted, cite:

**Heiman, Thomas J. (2026). SynBioCrow 2.1.1: computational synthetic-biology pathway and construct design framework. Zenodo. https://doi.org/10.5281/zenodo.22999039**
