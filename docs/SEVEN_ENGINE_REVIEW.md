# SynBioCrow seven-engine review

M1.20.7 review candidate. The release and scientific acceptance gates remain open.

The implementation starts from GitHub `5126061bee9781e703e19e82f869c3525614c84b`, the attached M1.20.6 source and logs, and the M1.16 master notebook's embedded source. The attached exploratory and third-engine notebooks are earlier recovery evidence. Each pair of copies was byte-identical. The recovered master notebook that provided the adapter sources has SHA256 `b297e267ed68493e8796ca3ea3695f315b8450706d57e727ee2f3d2ce2e97214`.

## Engine acceptance

| Engine | Verified evidence | Remaining acceptance gate |
|---|---|---|
| DORAnet | `PASS_REPRODUCED` for one-generation candidate output. 0.5.7a1, JN3604IMT, Linux CPython 3.12. Both runs for each target matched: 75 butanal candidates and 98 3-hydroxypropionic acid candidates. | The evidence contains normalized native output and the native network file hashes. A new environment restored from the recorded wheel lock and passed all 90 core tests. Candidate reachability and biochemical validity require independent checks. |
| AiZynthFinder | `PASS_REPRODUCED`. 4.4.1, NumPy 1.26.4, PyArrow 17.0.0, USPTO policy and ZINC stock. Two runs matched 15 3-HP and 16 butanal solved tree identities. | Route list order varied. Biochemical feasibility requires independent evidence. |
| ChemEnzyRetroPlanner | `PASS_REPRODUCED`. The repaired RSPlanner produced 66 butanal and 28 3-HP routes in each of two runs. The master driver and standalone runner matched on 31 hexanoic acid routes. | Annotation modes have their own dependency and scientific gates. The verified scope is CPU, BioNav stock and 12 iterations. |
| RetroBioCat2 | `PASS_REPRODUCED` for native reaction expansion. Source `c5f32561b1ed99d0701a6dbb472dc448d6c082e8`, Python 3.11. Two runs matched at 9 3-HP and 7 butanal raw records. | Full MCTS route and biochemical validation remain separate. |
| RetroPath2 | `PASS_REPRODUCED` for standalone compound transitions. Two runs matched 973 3-HP and 426 butanal transitions using one step and the pinned RR02 input. | Rule attributions varied. Verify target synthesis direction before admitting the records to closure. |
| BioPKS | `PASS_REPRODUCED` for 113 target-conditioned design and release calls with a fixed Python hash seed. Source `372cbfe9caf452fdf83976e6d0f32511dd28fccb`. Both runs recorded one exact hexanoic acid release. | Determine the carrier and cofactor chemistry before admitting a release into the reaction graph. |
| RetroTide | `PASS_REPRODUCED` for 113 target-conditioned `designPKS` designs with a fixed Python hash seed. Same upstream commit as BioPKS, direct design adapter. | Release steps remain outside this adapter's tested scope. |

The fresh integration regression combined AiZynthFinder, ChemEnzy, DORAnet and RetroBioCat2. It matched each normalized ChemEnzy reaction to its raw route pointer, quarantined 115 placeholder records, and retained 429 graph edges, including seven with provenance from multiple engines. The explicit atom and charge balance audit recorded 138 DORAnet and 31 ChemEnzy balanced records in this subset. Some native candidate reactions omit reaction participants. See the evidence report for the full per-engine counts.

A local run of the recovered master used its seven notebook adapters with paths redirected to the workspace. The first pass completed six engines. RetroBioCat2 failed during creation of an existing environment. Restoring the cache guard from the M1.16 native script allowed that engine to pass on its own. The combined campaign retained 1,961 native reaction records and checked their raw artifact hashes. The canonical notebook's analysis cells confirmed the butanal candidate witness through AiZynthFinder alone. The documented seeds yielded no complete multi-engine target witness in this campaign.

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

The other Python environments have version-pinned requirements snapshots under `notebooks/seven_engine/`. Exact acquisition and runtime asset hashes are listed in the evidence bundle. The snapshots use upstream Git commits for local packages and do not encode all wheel hashes.

The ChemEnzy runner uses the checksum-addressed native environment and three inference assets in `scripts/chemenzy/assets.json`. Use a dedicated upstream checkout, a persistent cache and a new output path for each attempt. If the cache already has the archived environment and models, `--fetch` reuses the files after checking SHA256 and downloads only missing files. The separate wheel overlay leaves the base restore intact. Colab defaults to its existing Drive cache.

```sh
python scripts/chemenzy/runner.py --cache /path/to/cache \
  --upstream /path/to/ChemEnzyRetroPlanner --out /path/to/probe --fetch --probe-only
python scripts/chemenzy/runner.py --cache /path/to/cache \
  --upstream /path/to/ChemEnzyRetroPlanner --out /path/to/run-1 \
  --stock BioNav-stock --iterations 12 --target 'CCCC=O' --target 'O=C(O)CCO'
```

Run the same inference command under a second new output path. Compare per-target reaction identities and retain the original trees, config, status and logs for both runs. The runner defaults to the checkpoint's Zinc stock and BioNav model. CPU is the default device, and `--gpu 0` selects the first GPU. The selected stock alone is prepared to avoid warming unused stocks.

Open `notebooks/SynBioCrow_SEVEN_ENGINE_REVIEW.ipynb` in Colab and set the SOURCE ZIP and cache paths. Use the SHA256-matched M1.4 seed archive or the M1.16 evidence archive with its recorded seed provenance. Engine logs and evidence are persisted separately. The controller and analysis ran locally with cached assets. Colab's Drive mount and execution from a fresh Colab session remain unverified. The SOURCE ZIP, EVIDENCE ZIP and manifest are review artifacts awaiting human approval. GitHub CI attaches all three to the source-package job.
