# M3 completion: evidence, Rhea exactness, and thermodynamics

M3 is now structurally complete on the 2.2 consolidation branch.

## Exact Rhea policy

A Rhea participant search is contextual evidence only.

For exact reaction evidence, SynBioCrow now requires:

1. canonical participant structures are available;
2. an explicit Rhea identifier is attached to the edge;
3. Rhea confirms that identifier among participant-search hits; and
4. the exact Rhea equation/direction contract attached to the edge matches the
   Rhea equation returned by the service.

If any of these are missing, the Rhea gate ABSTAINS rather than inferring support.

## Quantitative thermodynamics

SynBioCrow now has a lazy eQuilibrator adapter using
`ComponentContribution.standard_dg_prime()`.

Thermodynamics are calculated only when provenance includes one unique
`equilibrator_formula` using database accessions recognized by eQuilibrator.
SynBioCrow does not guess accession mappings from arbitrary SMILES or names.

The result records:

- standard transformed Gibbs energy (kJ/mol)
- uncertainty when available
- pH
- ionic strength
- temperature
- exact accession formula used

A successfully quantified value means the **thermodynamics gate is quantified**.
It does not by itself certify the reaction or pathway.

The current eQuilibrator 0.8 line is exposed as optional extra `.[thermo]` on
Python 3.11+.

## Enzyme evidence

Two separate enzyme gates are now represented:

- **exact enzyme evidence** — reviewed UniProtKB entries explicitly annotated to
  an exact confirmed Rhea reaction;
- **enzyme context evidence** — reviewed UniProtKB proteins sharing associated
  EC classifications.

Context evidence is useful for ranking and follow-up but cannot substitute for
exact reaction-enzyme evidence.

## Lifecycle

Even when closure, exact Rhea, quantitative thermodynamics, and exact reviewed
UniProt evidence all pass, the route-level evidence report remains
`LifecycleState.CANDIDATE`.

Promotion remains an explicit downstream policy action.
