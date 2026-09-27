# DORAnet adapter

Status on the 2.2 consolidation branch: **live bounded adapter implemented**.

The adapter targets the DORAnet 0.5.x enzymatic API:

```python
doranet.modules.enzymatic.generate_network(
    starters=[target_smiles],
    gen=1,
    direction="retro",
    ruleset="JN3604IMT",
)
```

SynBioCrow intentionally exposes this first migration as a **one-generation direct-rule probe**. Returned DORAnet reactions are normalized into immutable `PathwayCandidate` records with:

- deterministic candidate IDs
- raw reactant/product indices
- rule name and SMARTS provenance when available
- DORAnet version
- ruleset and direction
- Candidate lifecycle state

Multi-generation DORAnet expansion is currently rejected with `ContractViolation` rather than misrepresenting arbitrary network reactions as complete pathways. Multi-generation support will be enabled only after reaction-graph path reconstruction is migrated.

## Optional runtime

Current upstream PyPI release used for the smoke target:

```bash
pip install doranet==0.5.7a1
python scripts/smoke_doranet.py
```

The DORAnet package remains an optional external scientific dependency and is not vendored into SynBioCrow.
