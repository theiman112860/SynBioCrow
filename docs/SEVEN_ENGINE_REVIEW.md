# SynBioCrow seven-engine review

M1.20.7 review candidate. The release and scientific acceptance gates remain open.

The implementation starts from GitHub `5126061bee9781e703e19e82f869c3525614c84b`, the attached M1.20.6 source and logs, and the M1.16 master notebook's embedded source. The attached exploratory and third-engine notebooks are earlier recovery evidence. Each pair of copies was byte-identical. The recovered master notebook that provided the adapter sources has SHA256 `b297e267ed68493e8796ca3ea3695f315b8450706d57e727ee2f3d2ce2e97214`.

## Engine acceptance

| Engine | Verified evidence | Remaining acceptance gate |
|---|---|---|
| DORAnet | `PASS_REPRODUCED` for one-generation candidate output. 0.5.7a1, JN3604IMT, Linux CPython 3.12. Both runs for each target matched: 75 butanal candidates and 98 3-hydroxypropionic acid candidates. | Raw archive retention and full restoration from the recorded wheel lock have separate evidence. Candidate reachability and biochemical validity require independent checks. |
| AiZynthFinder | `PASS_HISTORICAL_EVIDENCE` for M1.16. 4.4.1, NumPy 1.26.4, PyArrow 17.0.0, USPTO policy, ZINC stock. Archived native trees and exported reactions matched for 15 3-HP and 16 butanal reactions. | Fresh model and stock restore and two native runs. The attachment carries outputs, with no original weight files or weight hashes. |
| ChemEnzyRetroPlanner | M1.20.6 `FAIL`: native API import failed after vendored namespace repairs. The repaired scientific subset passed a native Python 3.8 check. | Full RSPlanner and model inference results are recorded separately. |
| RetroBioCat2 | `PASS_HISTORICAL_EVIDENCE` for M1.16 candidate generation. Source `c5f32561b1ed99d0701a6dbb472dc448d6c082e8`, Python 3.11. The archive has 9 3-HP and 7 butanal raw records, with 15 after export deduplication. | Restore native data and compare complete candidate identities from two independent runs. |
| RetroPath2 | `PASS_HISTORICAL_EVIDENCE` for standalone engine reaction expansion. M1.16 contains 724 export records across two native CSVs. | Reproduce the target runs and verify the synthesis direction before admitting the records to this closure graph. |
| BioPKS | `PASS_HISTORICAL_EVIDENCE` for 113 native design/release calls. Source `372cbfe9caf452fdf83976e6d0f32511dd28fccb`. One exact released hexanoic-acid match. | Verify repeatable target-specific design and balance for any proposed carrier-release graph edge. The archived edge is quarantined. |
| RetroTide | `PASS_HISTORICAL_EVIDENCE` for 113 direct `designPKS` designs via the same upstream commit as BioPKS. | Restore and reproduce the target-directed designs. The archived run executed zero native release calls and recorded zero exact released target matches. |

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
python scripts/build_seven_engine_review.py --output-dir dist_seven_engine
```

The ChemEnzy runner uses the checksum-addressed native environment and three inference assets in `scripts/chemenzy/assets.json`. Use a dedicated upstream checkout, a persistent cache and a new output path for each attempt. If the cache already has the archived environment and models, `--fetch` reuses the files after checking SHA256 and downloads only missing files. The separate wheel overlay leaves the base restore intact. Colab defaults to its existing Drive cache.

```sh
python scripts/chemenzy/runner.py --cache /path/to/cache \
  --upstream /path/to/ChemEnzyRetroPlanner --out /path/to/probe --fetch --probe-only
python scripts/chemenzy/runner.py --cache /path/to/cache \
  --upstream /path/to/ChemEnzyRetroPlanner --out /path/to/run-1 \
  --target 'CCCC=O' --target 'O=C(O)CCO'
```

Run the same inference command under a second new output path. Compare per-target reaction identities and retain the original trees, config, status and logs for both runs. The runner defaults to the checkpoint's Zinc stock and BioNav model. CPU is the default device, and `--gpu 0` selects the first GPU. The selected stock alone is prepared to avoid warming unused stocks.

Open `notebooks/SynBioCrow_SEVEN_ENGINE_REVIEW.ipynb` in Colab and set the SOURCE ZIP and cache paths. The notebook requires the original SHA256-matched M1.4 seed archive for closure. Engine logs and evidence are persisted separately. The complete Colab acceptance run remains pending. The SOURCE ZIP and its manifest are review artifacts awaiting human approval.
