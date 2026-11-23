# Failure and attempted-method ledger

| Issue | Prior evidence | Avoid repeating | Next allowed action |
|---|---|---|---|
| AiZynth route trees absent from prior outputs | Historical acetone trees later recovered; 55 target-specific route trees exported for 3-HP, butanal, hexanoic acid | Do not repeat broad Drive searches or reinstall AiZynthFinder to recover these artifacts | Reuse the native route-tree archive and regression-test extractor |
| Native engine contract probe incomplete | Earlier probe marked AiZynthFinder and RetroPath2 contracts not implemented; later separate AiZynth evidence exists | Do not call a notebook exit a native chemistry PASS | Repair only the specific failing contract, retaining newer evidence |
| RetroPath2 directionality | Source-to-product expansion can be misread as product-to-target synthesis | Do not reverse edges implicitly | Assert reaction direction with native fixture |
| PKS designs | BioPKS and RetroTide return designs/carrier intermediates | Do not count designs as ordinary balanced reactions | Validate release chemistry before linking |
| Incomplete routes to butanal/hexanoic acid | Graph search from assumed seeds did not find complete routes | Do not rerun identical search without new chemistry or seeds | Address precursor gaps with documented native evidence |

Each new failure must include: date, engine, exact artifact/hash, attempted method, error, root cause if known, smallest repair, and acceptance test.

## M1.20.7 bounded review, November 22, 2026

| Engine or gate | Artifact and failure | Repair tested and exit criterion |
|---|---|---|
| ChemEnzyRetroPlanner hosted | M1.16 archive SHA256 `adb0a3ea2cd381caffcad1a3b3341e6450548bb2907d521adbdeff8d9a100078`. Prior job resume and fresh submissions returned HTTP 502. | Preserve the archive and use local native inference. Reopen hosted retries only with new service-health evidence. |
| ChemEnzyRetroPlanner import lineage | M1.20.6 SOURCE SHA256 `9129fa66c11fd9795572814501857aa8ac78bbcfd7b45cd530dbadc3c18f9752`. M1.20.4 skipped a namespace project. M1.20.5 fixed the condition predictor but missed EASIFA. M1.20.6 included all vendored roots. | Reuse the upstream Git pin and all vendored roots. Do not repeat root-discovery fixes for the numerical error. |
| ChemEnzyRetroPlanner scientific stack | M1.20.6 evidence SHA256 `0cfc0693e0f7841b6b0e03f2e1ba1222982185e66c33d1b7c62f1ec07932c024`. DGL-LifeSci imported scikit-learn 0.23.1, where `np.float` raised. An earlier SciPy extension emitted a binary-size warning. The upstream declared pair NumPy 1.23.5/SciPy 1.7.3 failed a clean wheel solve because SciPy requires NumPy below 1.23. | Python 3.8 with NumPy 1.23.5, SciPy 1.10.1, scikit-learn 0.23.1, joblib 1.3.2 and threadpoolctl 3.2.0 passed `pip check`, strict ABI-warning imports, and a nearest-neighbor calculation in an isolated environment. Full RSPlanner import and two matching inference runs are separate gates. No global alias shim. |
| DORAnet save path | GitHub base `5126061bee9781e703e19e82f869c3525614c84b`, live 0.5.7a1. Native 26-reaction ethanol generation raised `FileNotFoundError: ./tmp/synbiocrow_doranet_…/direct_rule_probe__retro_saved_network.pgnet.tmp` during save. | Use the known-good basename in an isolated subprocess working directory. New native runs via the public design API yielded matching rule/reaction multisets in two runs per target, 75 butanal and 98 3-HP. Keep these outputs and hashes for regression. |
| Execution recovery | At the same GitHub base, candidate checkpoints cached an errored backend as terminal on resume. | Resume now retains completed results and retries failed or unavailable backends. The regression test verifies one failed backend recovers without rerunning a completed backend. |
