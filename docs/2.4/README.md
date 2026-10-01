# SynBioCrow 2.4 research line

## Purpose

SynBioCrow 2.4 focuses on **biochemical discrimination and route ranking**. Version 2.3 established that graph-level integration broadens aggregate reaction recovery and preserves constituent routes, but does not yet improve exact Top-K ranking. Version 2.4 must address that limitation without converting the frozen 2.3 held-out benchmark into a tuning set.

## Lineage

- branch: `develop/2.4`
- parent release: `v2.3.0`
- parent release commit: `3ee772026f8cf8cd4b81395b461147cc1543be50`
- frozen 2.3 scientific commit: `39b3b21d8a5018001746a1ad783859cba75f9ad5`
- 2.3 Galaxy held-out denominator: 65 pathways
- 2.3 held-out benchmark may be used only as historical evidence, regression context, or non-tuning retrospective reporting.

## Primary research question

Can SynBioCrow rank biologically meaningful routes more effectively by combining structural similarity with explicit biochemical evidence, while preserving truth-independent generation and avoiding benchmark leakage?

## Major 2.4 milestones

1. Freeze a new benchmark protocol and benchmark firewall.
2. Assemble a new development set and untouched evaluation set.
3. Implement evidence-aware reaction and route features.
4. Add confidence/calibration and abstention behavior.
5. Add engine-agreement/disagreement features.
6. Train/tune only on development data.
7. Seal predictions before opening untouched evaluation truth.
8. Report Top-K exact recovery, partial recovery, MRR, calibration, runtime, and failure modes.
9. Keep hybrid chemical-route transformation and sustainability work behind an experimental interface for later validation.

## Non-negotiable constraints

- no tuning against the 65-path SynBioCrow 2.3 held-out benchmark;
- no fabrication of reaction, enzyme, thermodynamic, cofactor, kinetics, sequence, or process evidence;
- Candidate / Mature / Certified remain distinct computational lifecycle states;
- generation, evidence, ranking, and lifecycle promotion remain separate operations;
- 2.4 evaluation truth is inaccessible during prediction generation and model selection;
- all ranking-policy changes must be versioned and auditable.

See:
- `EXPERIMENTAL_SPEC.md`
- `BENCHMARK_PROTOCOL.md`
- `HYBRID_SUSTAINABILITY_ARCHITECTURE.md`
