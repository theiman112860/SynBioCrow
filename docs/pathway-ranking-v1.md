# Candidate graph route ranking v1

Ranking is deterministic and explicitly **not** a biochemical feasibility score. Only graph-reachable routes with at least one provenance-bearing reaction are ranked.

Ordering: fewer reaction steps, then more distinct contributing engines, then reaction ID. Engine diversity is a tie-breaker for traceability, not independent scientific corroboration. Thermodynamics, enzyme support, cofactor balance, host feasibility, and experimental validation remain NOT_EVALUATED.

This is a first-stage triage heuristic. A future evidence-based ranking layer must only use verified per-reaction measurements or cited biochemical evidence. Never convert this order to a success probability.
