# RetroPath2 M2.4.8 RR02 restoration — native target-specific evidence

Input: user-uploaded `SynBioCrow_M2_4_8_RETROPATH_RR02_RESTORE_ALL_OUTPUTS.zip`.

## Runtime
- TraceLD native executable: successful for both targets, `NATIVE_COMPLETED`.
- Rule source: RetroRules rr02, Zenodo DOI 10.5281/zenodo.5828017.
- Converted rules: 4,500, diameter 2 only in this capped pilot (`rule_manifest.json` reports `counts_by_diameter: {"2":4500}`, truncated true).
- Previous M2.4.7 used only 17 example rules and generated zero rows. M2.4.8 restored real rule coverage.

## Independent RDKit audit
Parsed `runs/<target>/results/results.csv` in the supplied ZIP and canonicalized the left-hand side of every `Reaction SMILES` using RDKit 2025.09.4, removing explicit H before canonicalization. Compared each reaction's left-side components with the canonical requested target SMILES.

| Target | Native rows | Unique reaction SMILES | Rows matching target on LHS | Parse failures |
| --- | ---: | ---: | ---: | ---: |
| 3-hydroxypropionic acid (`O=C(O)CCO`) | 973 | 486 | 973 | 0 |
| Butanal (`CCCC=O`) | 426 | 238 | 426 | 0 |
| Total | 1,399 | 724 | 1,399 | 0 |

## Gate
**PASS** native engine callable and genuine target-specific *rule-generated candidate reactions* for both targets. This is a computational candidate-generation gate only, not evidence of biochemical feasibility, mass balance, full pathway closure, or experimental validation.

Note: original notebook `summary.json` sets `target_specific_reactions_verified: false`; the independent audit above supplies that previously missing check. Do not change the historical summary retroactively. Further integration should deduplicate reaction SMILES and preserve rule IDs, provenance, and native evidence.
