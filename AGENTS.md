# SynBioCrow development contract

## Goal
Deliver an evidence-backed, usable multi-engine biosynthesis design platform. Do not turn installation diagnostics into the product roadmap.

## Mandatory task format
Before code changes state: Goal, Context, Constraints, Done-when. Use the smallest testable change and provide an evidence artifact or a precise blocker.

## Seven native engines
DORAnet, AiZynthFinder, ChemEnzyRetroPlanner, RetroBioCat2, RetroPath2, BioPKS, RetroTide.
Keep engine-specific pinned environments and existing known-good runners. Never rebuild all environments to fix one engine. A successful notebook exit is not proof of native chemistry. PKS designs are not ordinary reaction edges.

## Evidence and scientific integrity
Distinguish NOT_VERIFIED, FAIL, PASS_HISTORICAL_EVIDENCE and PASS_REPRODUCED. Native execution requires target-specific artifacts, no swallowed errors, hashes, and parser provenance. Reaction direction, all reactants, and stock/seed assumptions must survive normalization. Route reachability is not biochemical validation. A negative route finding is acceptable.

## Anti-drift
Consult FAILURE_LEDGER.md before retrying. Record attempted approach, exact failure, repair and exit criterion. Never rerun a known passing step without a changed dependency, input, or explicit regression purpose. Reuse previous outputs; run only missing gates. Do not invent source files, download links, reaction steps, or claims of certification.

## Exit to product development
Certification follows ACCEPTANCE.md and is machine-checked. A pending core certification does not block independent product features. After acceptance, prioritize multi-engine route joining, thermodynamics/cofactors/enzyme evidence, ranking, experimental feedback, and user-facing reports.

## Merge policy
Changes to governance or core must pass the governance-contract CI check and receive human review. No AI agent may self-certify scientific claims or merge without human approval.
