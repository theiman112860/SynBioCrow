# RetroBioCat2 adapter

Status on the 2.2 consolidation branch: **native bounded MCTS adapter implemented**.

The adapter binds to the same upstream API used successfully in the prior SynBioCrow lineage:

```python
from rbc2.mcts.mcts import MCTS
from rbc2.expansion.expander_repository import get_expanders

mcts = MCTS(
    target_smi=target_smiles,
    expanders=get_expanders(["retrobiocat"]),
    config=config,
)
mcts.run()
solved = mcts.get_solved_pathways()
```

The currently pinned source revision for reproducibility is:

```text
willfinnigan/RetroBioCat-2
commit c5f32561b1ed99d0701a6dbb472dc448d6c082e8
package version observed in the proven SynBioCrow runtime: rbc2 2026.2.27
```

## Runtime installation

RetroBioCat2 is an upstream research package with a large dependency surface.
For the proven Colab-style runtime, SynBioCrow historically used a conservative
install rather than allowing RBC2 to replace the whole scientific environment:

```bash
python -m pip install PyYAML sqlalchemy tables gdown tqdm
python -m pip install --no-deps --no-build-isolation \
  "git+https://github.com/willfinnigan/RetroBioCat-2.git@c5f32561b1ed99d0701a6dbb472dc448d6c082e8"
python scripts/smoke_retrobiocat2.py
```

RDKit, NumPy/Pandas/SciPy/scikit-learn, TensorFlow and other upstream RBC2
requirements must still be available in the scientific runtime.

## SynBioCrow normalization

Each solved RBC2 `Pathway` is converted into a SynBioCrow
`PathwayCandidate`. Each RBC2 reaction contributes:

- product → substrates retrosynthetic reaction text
- reaction name
- reaction/domain type
- reaction score
- feasibility-filter scores
- template metadata
- precedent metadata when present

RBC2's random reaction UUID is **not** included in the SynBioCrow candidate ID,
so repeated normalization of the same chemistry is deterministic.

## Search semantics

The adapter explicitly distinguishes:

- **COMPLETE + one or more solved pathways** → Candidate pathways
- **COMPLETE + zero solved pathways** → bounded no-hit, returns `[]`
- **installed backend fails during MCTS/data evaluation** → `BackendExecutionError`
- **RBC2 not installed / native API cannot import** → `BackendUnavailableError`

This distinction is important because earlier RBC2 data-asset problems must not
be interpreted as evidence that no biochemical route exists.

All normalized routes remain **Candidate**. RBC2 precedent or route scores do
not bypass SynBioCrow evidence/lifecycle gates.
