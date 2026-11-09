# SBC-WF-001 — Browser-based AI development workflow bootstrap

## Goal
Establish a reproducible GitHub-centered AI development protocol without modifying scientific behavior.

## Context
main documents 2.2.0; develop/2.4 includes later 2.4 work and GitHub Actions. Recent seven-engine Colab notebooks and source ZIPs may not yet be committed. The priority is native target-specific reaction generation across seven engines, not new unrelated audits.

## Constraints
- Coordination branch only; no scientific source edits, package version changes, benchmark changes, or releases.
- Do not modify frozen 2.3 artifacts or the 65-path held-out benchmark.
- No paid service or API key required.
- No claims that an engine works without native target-specific evidence.

## Done when
- AGENTS.md, docs/AI_DEVELOPMENT_WORKFLOW.md, docs/AI_FAILURE_LEDGER.md, and this task are present and readable on a coordination branch.
- A draft PR exists for human review, without merging.
- Existing CI is left unchanged; if CI runs, record its result rather than assuming success.
- The next scientific task is explicitly blocked pending canonical-source reconciliation.

## Evidence
PR URL; branch name; file diff; GitHub CI status if available; exact head SHA.

## Next task (not yet authorized)
SBC-SOURCE-001: reconcile latest seven-engine Colab SOURCE ZIP/notebook with repository commit history, then define one native target-specific engine acceptance test.
