# Development

Active branch: `develop/2.2-engine-consolidation`.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

The first consolidation milestone is intentionally dependency-light. Live scientific backends are optional and are migrated one at a time with backend-specific integration tests.

Do not weaken lifecycle or evidence gates to make an adapter test pass. Backend failures and missing evidence must remain distinguishable from negative scientific results.
