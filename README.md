# SynBioCrow 2.3.0

**SynBioCrow** is a computational synthetic-biology design framework for moving from a target molecule to evidence-aware biosynthetic pathway Candidates and provenance-backed DNA construct Candidates.

> **Release status:** SynBioCrow 2.3.0 is released. The scientific state is frozen and the 2.3 held-out benchmark and ranking policy remain immutable. GitHub release: `v2.3.0`. Zenodo DOI: [10.5281/zenodo.23083426](https://doi.org/10.5281/zenodo.23083426). Candidate pathways and constructs are computational designs, not experimental certifications.

## What changed in 2.3

SynBioCrow 2.3 freezes the first literature-grounded evaluation of the consolidated multi-generator engine. On the 65-path held-out Galaxy benchmark, connectivity-level partial recovery was 19/65 for the ensemble, 13/65 for RetroBioCat2, 9/65 for RetroPath standalone, and 0/65 for DORAnet. RetroPath recovered two exact connectivity-level pathways at rank 12; the ensemble preserved both but reranked them to ranks 46 and 31. The release therefore claims broader aggregate reaction recovery and route preservation, **not** improved exact Top-K ranking.

A non-tuning failure analysis classified 42/65 targets as complete predicted routes with no literature-reaction overlap, 17/65 as partial recovery, 2/65 as exact recovery, 3/65 as backend runtime failure, and 1/65 as mapping-limited. This identifies biochemical discrimination and ranking as the principal research problem reserved for 2.4.

The 2.3 similarity policy is Morgan/Tanimoto **2D-primary**. USRCAT 3D remains optional/secondary because development-set leave-one-pathway-out ranking favored 2D and 3D changed route ordering without improving validated outcomes.

The computational DBTL workflow is retained: Design uses multi-generator graph integration; Build requires provenance-backed sequence evidence; Test keeps evidence, thermodynamics, closure and QC explicit; Learn may update bounded prioritization weights but cannot fabricate evidence or promote lifecycle state.

## Frozen 2.3 scientific state

- scientific freeze commit: `39b3b21d8a5018001746a1ad783859cba75f9ad5`
- freeze package SHA-256: `67bea03543b60f4299aace5e1de674357e9ffed88e1a2d2fc21dc47c83cfcaf6`
- held-out denominator: 65; runnable: 64; mapping-limited: `literature_10`
- benchmark truth used for learning: false
- post-holdout ranking tuning: false
- default similarity: 2D Morgan/Tanimoto
- 3D USRCAT: optional secondary signal

See `paper/2.3/MANUSCRIPT_DRAFT.md` for the frozen study narrative and limitations.

## Install the release core

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
| **RetroPath standalone** | https://github.com/TraceLD/retropath | Primary KNIME-free RetroPath2.0-compatible runtime for SynBioCrow 2.2; validated against the historical r20220104 lycopene fixture at exact compound-transition level (34/34). |
| **RetroPath2 wrapper (legacy/reference)** | https://github.com/brsynth/retropath2-wrapper | Retained for historical/reference compatibility checks; KNIME is not required for the primary 2.2 runtime path. |
| **rp2paths** | https://github.com/brsynth/rp2paths | Enumerates complete pathways from RetroPath2 scope output. |
| **RetroRules** | https://retrorules.org | Reaction-rule resource used by RetroPath2; rules/sink remain explicit inputs. |
| **RetroTide** | https://github.com/JBEI/RetroTide | Specialized PKS generator; installed separately. |
| **BioPKS Pipeline** | https://github.com/JBEI/BioPKS-Pipeline | External specialized runtime. Review/accept upstream license before use. SynBioCrow does not vendor it. |
| **KNIME** | https://www.knime.com/ | Optional legacy/reference dependency only; not required by the primary 2.2 RetroPath standalone path. |
| **eQuilibrator** | https://github.com/equilibrator/equilibrator-api | Optional thermodynamics via `.[thermo]`. |

Check readiness:

```bash
synbiocrow readiness
synbiocrow bootstrap
```

## All-generators Jupyter/Colab notebook

Reference notebook:

`notebooks/SynBioCrow_2_2_RC1_ALL_GENERATORS.ipynb`

It installs/imports SynBioCrow, DORAnet, RetroBioCat2, KNIME-free RetroPath standalone, RetroTide, BioPKS Pipeline (after explicit license acknowledgement), and eQuilibrator. The legacy RetroPath2-wrapper/KNIME path remains available for reference but is not required for primary release readiness. It distinguishes **importable**, **configured**, **execution-ready**, and RetroPath standalone **certification-ready** states.

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

## RetroPath standalone certification evidence

For the archived r20220104 lycopene fixture (`results.7325.csv`), the KNIME-free standalone engine reproduces the historical **compound-transition multiset exactly**: 34/34 transitions, precision=1.0, recall=1.0, Jaccard=1.0, with 0 missing and 0 novel transitions. Rule/evidence serialization differs and is retained as an implementation-level difference rather than treated as chemical equivalence.

## Release verification

```bash
python -m unittest discover -s tests -v
python scripts/m7_release_readiness.py
python scripts/build_m9_release.py --check
python scripts/build_m9_release.py --output-dir dist_m9
```

See [M9 release candidate](docs/M9_RELEASE_CANDIDATE.md), [M7 Test](docs/M7_TEST_REPRODUCIBILITY.md), [M8 Learn](docs/M8_LEARN_DBTL.md), and [limitations](docs/LIMITATIONS.md).

## Historical releases and citation

SynBioCrow 2.2.0 remains archived at DOI **10.5281/zenodo.23027052**. The sealed 2.1 scientific release remains under `release/2.1.0/` (DOI **10.5281/zenodo.22999039**).

SynBioCrow 2.3.0 is publicly released as GitHub tag `v2.3.0` and archived on Zenodo at DOI **10.5281/zenodo.23083426**. The frozen scientific state is anchored at commit `39b3b21d8a5018001746a1ad783859cba75f9ad5`; subsequent documentation and citation updates do not alter that scientific freeze.
