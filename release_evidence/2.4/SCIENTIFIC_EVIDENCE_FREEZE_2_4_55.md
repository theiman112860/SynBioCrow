# SynBioCrow 2.4 Scientific Evidence Freeze

## Release conclusion

SynBioCrow 2.4 is frozen as a **Candidate-stage generator/representation milestone**.

It is **not certified as a validated complete-pathway recovery system** and no production ranking policy is certified.

## Prospective external evaluation

The prospective cohort was locked before evaluation truth was defined. Phase A was hashed and locked before Phase B scoring. The repaired Phase-B scorer verified the Phase-A lock and did not regenerate predictions.

### 1,3-propanediol
- DORAnet: 30 candidates; exact predeclared truth-intermediate recall 0%.
- RetroBioCat2: 1,373 candidates; 3 internally `SOLVED`, 1,370 partial; exact predeclared truth-intermediate recall 0%.

### 1,4-butanediol
- DORAnet: 33 candidates; exact predeclared truth-intermediate recall 0%.
- RetroBioCat2: 1,466 candidates; 2 internally `SOLVED`, 1,464 partial; exact predeclared truth-intermediate recall 0%.

The RBC2 `SOLVED` statuses are backend-internal search outcomes. Because the predeclared external pathway intermediates were not recovered, they must not be presented as external pathway-validation successes.

## What 2.4 establishes

2.4 repairs the reaction representation and target-connected Candidate generation architecture and demonstrates that the system can generate non-collapsed chemistry hypotheses. It also establishes a reproducible prospective evaluation protocol and, importantly, records a negative prospective result without tuning after truth reveal.

## What 2.4 does not establish

2.4 does not establish validated complete-pathway recovery, validated ranking, or Certified/Mature pathway status.

## Frozen identities

- Phase-A lock SHA256: `0f557e08e870f4823278d641b06ca038057600be61806a57d781ab92d55540cc`
- Phase-A hash-manifest SHA256: `6ac9e8c9b06b4f55d5c8183584490162ab830efef3f465894b4aadd7974ad3f8`
- Phase-B truth-contract SHA256: `ad967a66e7899be54bd19a29bd406206743f764f76e18892a5d048d0c1321c97`
- Repaired Phase-B results SHA256: `9c2a8be5102739406dd264f5d5091a44da261ad32870f7b10c9d53b73941d2b2`
