# M6 unified execution layer

M6 turns the consolidated 2.2 modules into one user-facing execution surface.

## Python API

```python
from synbiocrow import DesignRequest, design

result = design(
    DesignRequest(
        target_smiles="CCO",
        backend_ids=("doranet", "retrobiocat2"),
        sink_smiles=("CC",),
    ),
    state_root=".synbiocrow_runs",
)
```

The result contains:

- normalized Candidate pathways
- per-backend COMPLETE / ERROR / SKIPPED_UNAVAILABLE status
- shared reaction-graph summary
- bounded composite routes when sinks are supplied
- run diagnostics
- deterministic run ID

Unavailable backends are recorded rather than silently substituted with a
different scientific method.

## CLI

```bash
synbiocrow readiness
synbiocrow readiness --json

synbiocrow design "CCO" \
  --backend doranet \
  --backend retrobiocat2 \
  --sink "CC" \
  --state-dir .synbiocrow_runs \
  --output result.json
```

## Resume

Each request receives a deterministic run ID derived from its complete design
request. Stage files are written atomically under:

```text
<state-dir>/<run-id>/
  candidates.json
  graph_summary.json
  routes.json
  result.json
  manifest.json
```

On resume, completed Candidate generation can be restored without rerunning
backends. Resume does not alter the request or promote lifecycle state.

## Backend bootstrap/readiness

`SynBioCrowEngine.backend_readiness()` reports runtime state.

`synbiocrow.bootstrap.bootstrap_advice()` adds installation/configuration
guidance without auto-installing heavy or externally licensed backends.

SynBioCrow deliberately does not silently install KNIME, RetroRules data,
RetroBioCat2 data assets, or BioPKS.

## Colab

`notebooks/SynBioCrow_2_2_DEV_COLAB.ipynb`:

- clones the active 2.2 consolidation branch
- installs core + DORAnet optional dependency
- mounts Google Drive
- stores resumable run state under `MyDrive/SynBioCrow/2_2_runs`
- prints backend readiness
- runs a configurable design request
- persists the JSON result
- creates a rescue ZIP for browser download

The notebook does not pretend that separately configured RBC2, RetroPath2, or
BioPKS runtimes are present when they are not.

## Scientific state

M6 is orchestration only. It does not change the Candidate/Mature/Certified
contracts established earlier.
