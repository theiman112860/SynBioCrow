# SynBioCrow seven-engine review

M1.20.7 review candidate. The release and scientific acceptance gates remain open.

The implementation starts from GitHub `5126061bee9781e703e19e82f869c3525614c84b`, the attached M1.20.6 source and logs, and the M1.16 master notebook's embedded source. The attached exploratory and third-engine notebooks are earlier recovery evidence. Each pair of copies was byte-identical. The recovered master notebook that provided the adapter sources has SHA256 `b297e267ed68493e8796ca3ea3695f315b8450706d57e727ee2f3d2ce2e97214`.

## Engine acceptance

| Engine | Verified evidence | Remaining acceptance gate |
|---|---|---|
| DORAnet | `PASS_REPRODUCED` for one-generation candidate output. 0.5.7a1, JN3604IMT, Linux CPython 3.12. Both runs for each target matched: 75 butanal candidates and 98 3-hydroxypropionic acid candidates. | The evidence contains normalized native output and the native network file hashes. Full restoration from the recorded wheel lock has a separate reproducibility gate. Candidate reachability and biochemical validity require independent checks. |
| AiZynthFinder | `PASS_HISTORICAL_EVIDENCE` for M1.16. 4.4.1, NumPy 1.26.4, PyArrow 17.0.0, USPTO policy, ZINC stock. Archived native trees and exported reactions matched for 15 3-HP and 16 butanal reactions. | Fresh model and stock restore and two native runs. The attachment carries outputs, with no original weight files or weight hashes. |
| ChemEnzyRetroPlanner | `PASS_REPRODUCED`. The repaired RSPlanner produced 66 butanal and 28 3-HP routes in each of two runs. The master driver and standalone runner matched on 31 hexanoic acid routes. | Annotation modes have their own dependency and scientific gates. The verified scope is CPU, BioNav stock and 12 iterations. |
| RetroBioCat2 | `PASS_REPRODUCED` for native reaction expansion. Source `c5f32561b1ed99d0701a6dbb472dc448d6c082e8`, Python 3.11. Two runs matched at 9 3-HP and 7 butanal raw records. | Full MCTS route and biochemical validation remain separate. |
| RetroPath2 | `PASS_REPRODUCED` for standalone compound transitions. Two runs matched 973 3-HP and 426 butanal transitions using one step and the pinned RR02 input. | Rule attributions varied. Verify target synthesis direction before admitting the records to closure. |
| BioPKS | `PASS_HISTORICAL_EVIDENCE` for 113 native design/release calls. Source `372cbfe9caf452fdf83976e6d0f32511dd28fccb`. One exact released hexanoic-acid match. | Verify repeatable target-specific design and balance for any proposed carrier-release graph edge. The archived edge is quarantined. |
| RetroTide | `PASS_HISTORICAL_EVIDENCE` for 113 direct `designPKS` designs via the same upstream commit as BioPKS. | Restore and reproduce the target-directed designs. The archived run executed zero native release calls and recorded zero exact released target matches. |

The fresh three-engine regression combined ChemEnzy, DORAnet and RetroBioCat2. It matched each normalized ChemEnzy reaction to its raw route pointer, quarantined 115 placeholder records, and retained 402 graph edges, including five with provenance from multiple engines.

The M1.16 regression checked 941 exported records, 708 distinct RDKit-parseable species, and referenced raw member hashes. It retained 216 direction-admitted candidates and 725 quarantined records. The archived source recorded a butanal witness for its assumed seed set and no complete multi-engine target pathway.

## Reproduce the review

From a repository checkout on Linux x86-64 with CPython 3.12:

```sh
python -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r notebooks/seven_engine/doranet-linux-cp312.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/verify_core_governance.py
.venv/bin/python notebooks/seven_engine/check_m116_archive.py /path/to/M1.16_ALL_OUTPUTS.zip
.venv/bin/python notebooks/seven_engine/check_native_integration.py evidence/m1_20_7
python scripts/build_seven_engine_review.py --output-dir dist_seven_engine
```

The ChemEnzy runner uses the checksum-addressed native environment and three inference assets in `scripts/chemenzy/assets.json`. Use a dedicated upstream checkout, a persistent cache and a new output path for each attempt. If the cache already has the archived environment and models, `--fetch` reuses the files after checking SHA256 and downloads only missing files. The separate wheel overlay leaves the base restore intact. Colab defaults to its existing Drive cache.

```sh
python scripts/chemenzy/runner.py --cache /path/to/cache \
  --upstream /path/to/ChemEnzyRetroPlanner --out /path/to/probe --fetch --probe-only
python scripts/chemenzy/runner.py --cache /path/to/cache \
  --upstream /path/to/ChemEnzyRetroPlanner --out /path/to/run-1 \
  --stock BioNav-stock --iterations 12 --target 'CCCC=O' --target 'O=C(O)CCO'
```

Run the same inference command under a second new output path. Compare per-target reaction identities and retain the original trees, config, status and logs for both runs. The runner defaults to the checkpoint's Zinc stock and BioNav model. CPU is the default device, and `--gpu 0` selects the first GPU. The selected stock alone is prepared to avoid warming unused stocks.

Open `notebooks/SynBioCrow_SEVEN_ENGINE_REVIEW.ipynb` in Colab and set the SOURCE ZIP and cache paths. Use the SHA256-matched M1.4 seed archive or the M1.16 evidence archive with its recorded seed provenance. Engine logs and evidence are persisted separately. The complete Colab acceptance run remains pending. The SOURCE ZIP, EVIDENCE ZIP and manifest are review artifacts awaiting human approval. GitHub CI attaches all three to the source-package job.
