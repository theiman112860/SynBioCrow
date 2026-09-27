# Evidence and closure layer

Status: **M3 foundation implemented on the 2.2 consolidation branch**.

This layer evaluates ensemble reaction edges without allowing database hits or
scores to silently promote lifecycle state.

## Current evidence gates

### 1. Stoichiometric closure

Each normalized reaction is checked for explicit atom balance and formal-charge
balance using RDKit.

Results:
- `PASS`: explicit atoms and charge balance.
- `FAIL`: explicit imbalance.
- `ABSTAIN`: a participant cannot be parsed as a molecular structure.

This is structural closure only. It is not thermodynamic evidence.

### 2. Rhea reaction evidence

SynBioCrow queries Rhea by canonical participant InChIKeys.

A participant co-occurrence hit is **contextual evidence only** and remains
`ABSTAIN`. An edge reaches `PASS` only when it already carries an explicit
Rhea identifier and the Rhea search confirms that mapping.

This prevents a nearby or compositionally similar Rhea reaction from being
misreported as direct evidence.

### 3. Reviewed UniProt enzyme evidence

Reviewed UniProtKB enzyme records are queried only for an **exact Rhea reaction
mapping**.

- exact Rhea + reviewed UniProt record(s): `PASS`
- no exact Rhea mapping: `ABSTAIN`
- no reviewed record for exact Rhea: `ABSTAIN`
- service/query failure: `ABSTAIN`

No protein sequence is invented and contextual family hits are not promoted to
exact enzyme identity.

### 4. RetroPath identifier resolution

RetroPath / rp2paths may emit internal compound identifiers rather than
canonical structures.

The M3 mapping layer accepts explicit `identifier,smiles` mappings and rebuilds
the ensemble graph with canonical structure identities. Unmapped identifiers
remain source-scoped and cannot form cross-engine joins accidentally.

## Route evidence report

`SynBioCrowEngine.evaluate_route(...)` returns a structured
`RouteEvidenceReport` containing edge-level:

- stoichiometric closure
- Rhea reaction evidence
- exact-Rhea reviewed UniProt enzyme evidence
- exact Rhea IDs
- reviewed UniProt accessions

Even if every currently implemented evidence gate passes, the report remains
`LifecycleState.CANDIDATE`. Lifecycle promotion remains a separate explicit
policy decision.

## Still pending in M3

- quantitative thermodynamics
- richer exact reaction-direction/stoichiometry matching against Rhea
- enzyme-family/context evidence distinct from exact-enzyme evidence
- route-level evidence weighting/ranking
