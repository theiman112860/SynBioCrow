# SynBioCrow AI development operating contract

This document governs AI-assisted work on this repository. Read it before making changes.

## Mission
First establish that all seven designated generator engines are independently installable, callable, and produce genuine target-specific reactions within their supported domains. Only then prioritize reaction-level ensemble integration, pathway closure, ranking, and downstream scientific validation.

## Non-negotiable rules
1. Every task must specify Goal, Context, Constraints, and Done-when.
2. Work on a task-specific branch; propose changes by pull request. Do not directly edit main, develop/2.3, frozen release tags, or sealed benchmark artifacts.
3. Do not assume the latest Colab experiments are committed to this repository. Reconcile provenance and source commit before modifying an engine.
4. Never claim engine success from importability, synthetic fixtures, mock reactions, or exit code alone. Distinguish install, import, native call, target-specific output, provenance, and scientific validation.
5. Keep Candidate, Mature, and Certified statuses separate. Never fabricate chemistry, kinetics, thermodynamics, sequence evidence, or experimental validation.
6. Do not tune on the frozen 65-path Galaxy held-out benchmark or rescore historical prospective results as new prospective successes.
7. Preserve biosynthesis, chemical, and hybrid modes and the explicitly chosen similarity policy for each version. Do not silently change frozen ranking behavior.
8. Reuse established adapters, notebooks, environments, and working oxDNA/other scientific runtimes where relevant. Do not create unrelated audits or redesign architecture.
9. Consult docs/AI_FAILURE_LEDGER.md before proposing a repair; record unsuccessful approaches and evidence after each attempt.
10. Make bounded, testable changes. At most three substantially similar repair attempts before escalation to the architect.
11. Keep dependency installs isolated by engine when required. Never commit credentials, tokens, large dependency environments, or unlicensed third-party code.
12. Prefer one primary Colab notebook per integrated workflow; notebook name and output ZIP stem must match. Supply a rescue-download cell for Colab outputs when a notebook is requested.
13. Report PASS, FAIL, or INCONCLUSIVE with concrete evidence and exact commit SHA. Missing evidence means INCONCLUSIVE, not PASS.

## Required task handoff
- Task ID and baseline commit SHA
- Goal / Context / Constraints / Done-when
- Files in scope and files forbidden to change
- Reproduction commands and evidence requirements
- Expected output artifacts and bounded time/compute budget

## Review gate
The coding agent opens a PR with a concise change summary, tests executed and results, native engine evidence if applicable, known limitations, and any failure-ledger updates. The reviewer independently inspects diffs and evidence. Passing unit tests alone never certifies scientific validity.

## Current authority warning
The default main branch documents 2.2; develop/2.4 contains later release work. Recent seven-engine Colab experiments may exist outside GitHub. This coordination branch is NOT the authoritative latest scientific source. Resolve the canonical source snapshot before scientific code changes.
