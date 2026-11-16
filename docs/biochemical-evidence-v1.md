# Biochemical evidence annotations v1

This layer accepts curated, reaction-ID-keyed evidence. For each reaction, four dimensions are tracked: enzyme support, thermodynamics, cofactor balance, and host feasibility. Each is SUPPORTED, CONTRADICTED or NOT_EVALUATED. A positive or negative assertion requires a citation; absent evidence remains NOT_EVALUATED.

Route-level status is CONTRADICTED if any reaction contradicts the dimension, SUPPORTED only when every reaction has support, and NOT_EVALUATED otherwise. This is evidence bookkeeping, **not** an automated biochemical feasibility model. No empirical measurements, enzyme assignments or thermodynamic calculations are fabricated. Even fully annotated routes remain NOT_CERTIFIED pending scientific review.

Future work: connect verified enzyme databases, thermodynamic calculations and cofactor inventories to these exact evidence fields, then add a calibrated ranking policy with explicit uncertainty.
