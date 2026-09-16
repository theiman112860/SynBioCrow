# SynBioCrow testing strategy

SynBioCrow treats automated testing as part of scientific reproducibility.

## Test layers

- `tests/unit/`: fast isolated behavior such as normalization, parsing, hashing, scoring helpers, provenance utilities, and route operations.
- `tests/contracts/`: frozen scientific and software invariants. A refactor may change implementation but must not silently change these contracts.
- `tests/integration/`: small end-to-end workflows using bounded fixtures and no expensive external campaigns.
- `tests/adapters/`: added as full engine adapters are migrated. External tools should normally be mocked or exercised with tiny smoke fixtures in CI.
- `tests/scientific_validation/`: expensive explicitly invoked campaigns; never part of routine CI.

## Alpha90 frozen contract

The current harness encodes the following invariants:

1. Frozen engine identifier is Alpha87.11.
2. Canonical expected populations are LASER=152, Golden=20, building blocks=437.
3. Certification fails closed.
4. Exact counts without provenance cannot pass.
5. Golden certification requires pathway/reference semantics.
6. Alpha90.2 cannot be enabled unless all required gates pass.
7. Routine certification does not execute SynBioCrow predictions and does not tune against the external benchmark.

## Running locally

```bash
python -m pip install -r requirements-dev.txt
pytest -m "not scientific_validation"
```

Fast layers can also be run independently:

```bash
pytest tests/unit
pytest tests/contracts
pytest tests/integration
```

## Migration rule

As Alpha81-90 functionality is recovered into the canonical engine, each component should receive unit tests and at least one contract or regression test before substantial refactoring. The goal is to preserve scientific behavior while modernizing the repository structure.
