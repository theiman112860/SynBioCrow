# M5 BioPKS / RetroTide integration

M5 migrates the proven specialized PKS boundary into the shared SynBioCrow 2.2
engine.

## Upstream projects

- BioPKS Pipeline: https://github.com/JBEI/BioPKS-Pipeline
- RetroTide: https://github.com/JBEI/RetroTide

BioPKS Pipeline currently carries an upstream copyright/license notice with
distribution restrictions. SynBioCrow therefore **does not vendor or
redistribute the BioPKS Pipeline source**.

## External bridge

A separately installed/authorized BioPKS environment communicates with
SynBioCrow through the JSON schema:

`synbiocrow.biopks.external.v1`

Configure:

```bash
export SYNBIOCROW_BIOPKS_RUNNER=/path/to/bridge.py
export SYNBIOCROW_BIOPKS_ACK_LICENSE=1
export SYNBIOCROW_BIOPKS_PYTHON=/path/to/biopks/python   # optional
```

A bridge template is provided in `scripts/biopks_external_bridge_template.py`.

## Candidate normalization

BioPKS/RetroTide routes are normalized into ordinary SynBioCrow
`PathwayCandidate` objects with backend ID `biopks_retrotide`.

The following are retained as provenance where available:

- PKS route class
- route score
- predicted product
- PKS design/module architecture
- sequence assets
- specialist sequence-completeness state
- experimental-validation claim state
- per-step evidence identifiers

All specialized routes default to **Candidate**.

## Graph integration

Only steps carrying explicit reaction chemistry enter the reaction-level
ensemble graph.

A PKS architecture-only step is **not** converted into an invented chemical
reaction. Its module/domain design remains Candidate provenance until an
explicit chemical transformation is available.

This means BioPKS/RetroTide can now contribute genuine reaction edges to the
same DORAnet + RetroBioCat2 + RetroPath2 graph without weakening identity or
evidence contracts.

## Execution semantics

- bridge status COMPLETE/PASS with routes → Candidate pathways
- COMPLETE/NO_HIT with zero routes → successful bounded no-hit
- bridge runtime or malformed JSON/schema → BackendExecutionError
- missing bridge/license acknowledgement → BackendUnavailableError

The historical 2.1 evidence abstention remains conceptually preserved: a
specialized candidate is not Mature or Certified merely because BioPKS or
RetroTide generated it.
