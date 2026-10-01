# SynBioCrow 2.4.1 — Fixed-Candidate Evidence Adapter

## Scientific purpose

2.4.1 creates the controlled bridge between already-generated SynBioCrow candidate routes and the 2.4 evidence/ranking layer.

**Candidate generation is not invoked.**

This permits ranking experiments in which candidate availability is held fixed and only discrimination changes.

## Input compatibility

The adapter accepts JSON, JSONL and CSV artifacts and recognizes conservative aliases for:
- route IDs;
- reaction IDs / reaction SMILES;
- generator/backend;
- Rhea;
- EC;
- UniProt;
- literature identifiers;
- mapping confidence;
- 2D similarity;
- optional 3D similarity.

Unrecognized reaction records fail closed rather than being silently converted.

## Outputs

1. deterministic route-level feature CSV;
2. adapter manifest containing input/output SHA-256;
3. route and reaction counts;
4. explicit `generation_invoked: false`.

## 2.4.1 feature matrix

Current features:
- frozen structural 2D signal when present;
- optional 3D signal when present;
- reaction-evidence fraction;
- reviewed-enzyme fraction;
- exact-Rhea fraction;
- thermodynamic coverage;
- independent-engine count;
- route length;
- unsupported-edge count;
- mean mapping confidence.

Missing source evidence remains missing.

## Important limitation

Because historical 2.3 result bundles may contain multiple artifact schemas, the alias layer is deliberately narrow. A real 2.3 artifact should be run through the adapter next. Any newly observed schema should be added through a regression fixture, not by permissive guessing.

## Next checkpoint: 2.4.2

Run the adapter against a frozen real 2.3 candidate artifact, capture the exact schema as a regression fixture, and then implement the first interpretable fixed-candidate ranking baseline and ablation harness.
