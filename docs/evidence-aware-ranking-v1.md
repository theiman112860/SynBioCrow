# Evidence-aware route triage v1

This module compares candidate graph routes using per-reaction, citation-required evidence annotations. Routes with contradicted checks are placed last for review. Among routes without contradictions, those with fewer unknown checks rank earlier, followed by shorter reaction chains and deterministic IDs.

It does not claim quantitative probabilities, experimentally validated routes, enzyme assignments, thermodynamic predictions or organism-level feasibility. A citation is required for a claim but is not independently verified by this module. A route with all checks annotated remains NOT_CERTIFIED.

The input is a list of distinct candidate graph witnesses plus curated evidence keyed by reaction ID. The current graph tracer may yield only one witness for a target; generating and comparing multiple independent pathways is a separate milestone.
