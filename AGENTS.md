# SynBioCrow development contract
This file is mandatory for AI-assisted and human development.

## Mission
Deliver a reproducible multi-engine pathway discovery application that invokes genuine native engines, preserves reaction provenance, combines compatible reaction graphs, reports candidate/closed routes, and distinguishes scientific evidence levels.

## Every task MUST declare
- Goal: one narrow deliverable.
- Context: exact repository ref/commit, relevant source and evidence.
- Constraints: architecture, chemistry, environment, immutable baselines.
- Done-when: named executable tests and expected evidence artifacts.

## Non-negotiable rules
1. Read PROJECT_STATUS.md, ENGINE_REGISTRY.yaml, FAILURE_LEDGER.md, and ACCEPTANCE_TESTS.md before modifying code.
2. Plan the smallest bounded change before implementation; do not expand scope without a documented decision.
3. Never treat installation/import, native execution, reaction generation, route closure, or scientific validation as equivalent.
4. Never fabricate chemistry, enzyme assignments, thermodynamics, kinetics, provenance, or experimental certification.
5. Preserve frozen 2.3 and historical prospective results, including the sealed 65-path Galaxy benchmark; do not tune on held-out data.
6. Keep Candidate, Mature, Certified distinct. Failure remains failure; no retrospective promotion.
7. Use isolated environments when upstream engines have conflicting dependencies.
8. Prefer one primary Colab entry point and modular, testable source. No new notebook unless existing entry point cannot serve the task.
9. Log every failed approach with exact signature and new evidence needed for retry.
10. After every microtask update PROJECT_STATUS.md with evidence, blocker, and exactly one next action.
11. Do not declare a milestone PASS without linked machine-readable evidence and a reproducible command.
12. Do not overwrite a frozen branch, sealed benchmark, or prior release.

## Session protocol
1. Read status and failure ledger.
2. Confirm exact source SHA and relevant evidence.
3. State Goal/Context/Constraints/Done-when.
4. Execute one microtask.
5. Run targeted test and relevant regression tests.
6. Record PASS, FAIL, or BLOCKED; attach commands and output paths.
7. Update status and choose only the next unblocked task.

## Stop conditions
Stop and report BLOCKED if source lineage is uncertain, native assets are missing, evidence is insufficient, or an acceptance gate fails. Do not replace real native outputs with fixtures and call that scientific success.

## Completion
Milestones M1-M6 in ACCEPTANCE_TESTS.md must each be PASS, with linked evidence. An exception must be explicit and cannot silently count as PASS.
