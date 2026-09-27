# Reproducibility and provenance

The final builder consumes only the sealed 0.3.53.0 ALL_OUTPUTS scientific handoff. It does not rerun BioPKS, RetroTide, literature searches, Rhea, thermodynamics, or benchmark truth.

The release manifest records SHA-256 provenance. The specialized-generator abstention ledger is linked by its content SHA-256. Re-running final packaging should preserve scientific counts and policy decisions; timestamp and archive byte hashes may differ.
