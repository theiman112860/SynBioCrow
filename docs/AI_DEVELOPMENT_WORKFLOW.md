# Browser-based ChatGPT + coding-agent + GitHub + Colab workflow

## Purpose
Use ChatGPT to define bounded scientific/engineering tasks and evaluate evidence; a browser-based coding agent to implement tasks; GitHub as the durable source of truth; and Google Colab for heavy scientific execution.

## Roles
- Architect/reviewer (ChatGPT): specify Goal, Context, Constraints, Done-when; inspect commits, tests and native outputs; decide PASS/FAIL/INCONCLUSIVE.
- Coding agent (browser): read AGENTS.md and task contract, edit only permitted files, run local/CI checks, open PR, report failures honestly.
- Human owner: approve milestone changes, external licensing/credentials and merges; run Colab when browser agent cannot.
- GitHub Actions: run bounded deterministic tests; not long-running scientific workloads.
- Colab: run native generator experiments, store concise evidence and reproducibility metadata.

## Per-task loop
1. Architect writes tasks/CURRENT_TASK.md on a dedicated branch.
2. Coding agent reads AGENTS.md, task, current files, and AI_FAILURE_LEDGER.md.
3. Agent implements the smallest testable change and opens a PR against the agreed development baseline.
4. CI runs existing unit/contract checks. Scientific jobs run in Colab as needed.
5. Evidence includes source SHA, environment/package versions, target SMILES, actual native engine command, reaction records with provenance, exit status and logs.
6. Reviewer returns PASS, FAIL or INCONCLUSIVE with reasons. FAIL triggers a narrowly scoped repair; after three similar attempts, escalate rather than loop.
7. Owner approves merge. Architect writes next task.

## Budget discipline
Prefer free GitHub/Colab allowances; verify actual coding-agent entitlement before choosing a vendor. Do not rely on unlimited free Claude Code or Copilot agent access. No paid API keys are required for the protocol. Keep CI light and cap Colab runtime/outputs.

## Canonical source reconciliation
Before coding scientific features, identify: (a) repository branch + commit; (b) newest successful seven-engine SOURCE ZIP and notebook; (c) differences between notebook source and GitHub; (d) frozen historical versions; (e) engine-specific proven capabilities and failures. Never overwrite a working native engine integration based on an older repository snapshot.

## Evidence rubric
- INSTALL: isolated environment installs dependencies.
- IMPORT: native package imports.
- CALL: actual engine native entrypoint executes.
- TARGET: output includes reactions genuinely generated for the requested target and native engine metadata.
- VALIDATE: reaction mapping, chemistry and provenance checked separately.
- ENSEMBLE: independent reaction graphs combined without invented edges.
A stage can PASS only with recorded evidence; later stages cannot be inferred from earlier stages.

## Output naming
For a notebook named NAME.ipynb, its outputs must be named NAME_ALL_OUTPUTS.zip (or NAME_RESULTS.zip if the task contract explicitly specifies). Include a small manifest and rescue-download mechanism when Colab is involved.
