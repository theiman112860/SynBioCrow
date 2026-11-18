# Persistent project checkpoint protocol

This repository is the authority for project continuity; chat summaries are leads, not proof. Read `PROJECT_CHECKPOINT.json`, `DEVELOPMENT_HISTORY.md`, `AGENTS.md`, and any existing failure ledger before starting work.

## Task contract
State **Goal, Context, Constraints, Done-when** before editing or running experiments. Reuse pinned environments, known-good runners and prior artifacts. Do not rerun completed work without a changed input or a regression reason.

## At every completed notebook run
1. Write an immutable evidence bundle with input/output paths, SHA256 hashes, native logs, versions, parameters, and explicit status.
2. Append a dated entry to `DEVELOPMENT_HISTORY.md` recording attempted method, result, failure if any, and next action.
3. Atomically update `PROJECT_CHECKPOINT.json` on a working branch with the latest verified commit, notebook path, evidence hashes, blockers, and next action. Mark missing fields null; never invent them.
4. Open a pull request for human review. No autonomous merge or scientific certification.

## Colab integration
Use the canonical notebook's final evidence/export cell to generate a checkpoint *proposal* alongside the SOURCE ZIP and ALL_OUTPUTS ZIP. The proposal must not claim GitHub was updated unless a verified commit exists. Push only with explicit authenticated repository access and human review. Output ZIP basename must match notebook basename.

## Resume prompt
Continue SynBioCrow from GitHub. Read PROJECT_CHECKPOINT.json, DEVELOPMENT_HISTORY.md, AGENTS.md, and the failure ledger. Verify referenced SHA256 evidence and commit before coding. State Goal, Context, Constraints, Done-when and execute only the next unfinished gate.
