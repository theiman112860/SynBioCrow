# SynBioCrow V2.0 Alpha90.1.4.3.2.3

Native Golden Compound-Node Path Reconstruction.

This reference-only diagnostic repairs the identity interpretation defect discovered in Alpha90.1.4.3.2.2. Molecular identities are derived only from actual Golden compound nodes (`InChIKey`, `InChI`, or `SMILES` -> InChIKey); InChIKey-looking prefixes embedded in reaction-node IDs are explicitly prohibited as molecule identities.

The release reuses the frozen Alpha90.1.4.4.2.2 reaction order and edge semantics (`compound_to_reaction_is_product`), maps Golden groups to the independently known Alpha90.1.4.3 target identities, reconstructs each ordered reaction's substrate/product compound nodes, and certifies a principal product-identity path only when adjacent native compound-node connectivity is unique and the terminal product equals the independently known target InChIKey.

No SynBioCrow prediction routes are read. No scoring, engine calls, route generation, aliases, bridge tuning, benchmark tuning, or Alpha90.2 authorization occurs.

Packaged verification: 6/6 tests passed; all notebook code cells compile.