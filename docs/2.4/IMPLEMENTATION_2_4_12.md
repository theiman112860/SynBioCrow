# SynBioCrow 2.4.12 — evidence-first biochemical route discrimination

## Objective

2.4.12 introduces the first route-discrimination layer on the frozen 2.4 pilot
development set. It does not learn weights and does not access validation truth.

## Components

Each route can carry evidence for seven independent dimensions:

1. reaction compatibility;
2. enzyme precedent;
3. EC evidence;
4. cofactor feasibility;
5. thermodynamic support;
6. pathway context;
7. cross-engine agreement.

Every observed component must carry provenance IDs. A component with no evidence
is `null`, not zero. This prevents absence of evidence from becoming fabricated
negative evidence.

## Provisional score

2.4.12 intentionally uses no fitted weights.

`observed_mean = mean(observed component values)`

`evidence_coverage = observed_components / 7`

`coverage_adjusted_score = observed_mean * evidence_coverage`

Thus a route cannot receive a high provisional score from one or two favorable
facts while most biochemical dimensions remain unknown.

This score is infrastructure, not the final 2.4 ranking model.

## Firewall

Only these frozen development targets may enter 2.4.12:

- methyl isobutyl ketone;
- jasmonic acid;
- dammaradienol;
- curcumin.

The scorer rejects any route whose split is not `development`. In particular,
bakuchiol and D-allitol remain sealed validation targets.

## Next step

Populate route candidates for the four development targets from the existing
SynBioCrow generators, then attach real Rhea/EC/enzyme/cofactor/thermodynamic
and cross-engine evidence. Once evidence coverage is sufficient, compare
candidate ranking behavior on development only and freeze the ranking policy
before opening validation.
