# M1.23.3 — Historical Rhea evidence recovery and bounded integration

Recovered and inspected the prior Alpha89 notebook contract from the user's Library: frozen `rhea-reaction-smiles.tsv`, exact snapshot hash checking, and `rhea-directions.tsv` use in later Alpha89 work. The original historical SOURCE ZIP and its full multi-resource implementation were **not recovered**, so claiming to reuse that executable implementation would be incorrect.

Built `SynBioCrow_M1_23_3_RHEA_REUSE.ipynb` to take the exact 12 saved M1.23.2 candidates, require SHA-verified input, and optionally match complete reaction SMILES against a supplied Rhea TSV. The notebook never reruns engines, never silently substitutes a newer Rhea snapshot, and reports exact forward/reverse matches separately. Its explicit opt-in switch can download a **new**, distinctly identified Rhea snapshot.

Local dry-run: 12 candidates loaded, notebook syntax checked, **BLOCKED_RHEA_SNAPSHOT_MISSING** because the historic TSV was not available in the current runtime. Zero matches were **not** asserted; zero scientific pathways certified.

This is a partial bridge, not yet the full historic Rhea/UniProt/KEGG/MetaCyc/MetaNetX/eQuilibrator integration. Next: supply verified frozen Rhea TSV and historic source artifacts, run screen, then reconnect mapping and enzyme/direction evidence with independent provenance.
