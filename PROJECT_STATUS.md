# SynBioCrow authoritative project status
Updated: 2026-11-08
Status: M1 BLOCKED ON CANONICAL SOURCE RECOVERY; governance installed.

## Verified repository facts
- Repository: theiman112860/SynBioCrow.
- main README describes SynBioCrow 2.2.0, most recent main history found dated 2026-09-29.
- develop/2.4 pyproject.toml declares version 2.4.0, but its README is an older 2.3 release-candidate narrative: documentation and package metadata are not synchronized.
- Branch listing includes develop/2.3, develop/2.4, main, and governance/m1-baseline-20261108; no develop/2.6 branch was returned.
- GitHub governance files were committed and read back. GitHub Actions execution is NOT verified.
- Search for named latest seven-engine source/result ZIPs in conversation/library index returned no results. This is not proof that artifacts do not exist.

## Milestone status
| Milestone | State | Evidence |
|---|---|---|
| M1 Baseline recovery | BLOCKED | GitHub metadata and 2.4 manifest inspected; authoritative 2.6 source not found |
| M2 Seven-engine native readiness | NOT VERIFIED | Native reaction outputs needed per engine |
| M3 Reaction output normalization | NOT VERIFIED | Requires canonical source |
| M4 Reaction graph and hybrid closure | NOT VERIFIED | Requires canonical source |
| M5 Ranking and held-out evaluation | NOT VERIFIED | Historical evaluations are not a fresh pass |
| M6 Usable end-to-end application | NOT VERIFIED | Clean-install test not run |

## Task M1.1
Goal: identify canonical 2.6 source and seven-engine roster.
Context: GitHub 2.2/2.4 code, historical Colab run artifacts.
Constraints: no architecture changes, no new engine installation, no benchmark mutation.
Done-when: SHA-256 source manifest; seven native entry points; latest outputs mapped; provenance and dependencies documented.
Result: BLOCKED; no authoritative 2.6 SOURCE ZIP in accessible searched materials.

## Immediate single next action
Obtain the latest 2.6 seven-engine SOURCE ZIP or a direct Git commit/branch containing that source. Prefer the most recent seven-engine canonical notebook plus its SOURCE package. Inspect the source before any repairs.

## Immutable boundaries
Frozen 2.3 artifacts and sealed 65-path Galaxy benchmark remain untouched. Historical prospective failures remain failures.

## M1.2 uploaded artifact inspection — 2026-11-08
- SOURCE ZIP SHA256 e6cd9b76c7a239feb64df42639818fff90d86fa823c956711aa9cde6ac3e6873 contains canonical notebook, RBC2 reference notebook, README only.
- ALL_OUTPUTS ZIP SHA256 c2dc7da0ee4538ccc392e3c5328459548bf1a461e66deadee249d9adf774bb0f.
- RBC2 native archive records 9 target-conditioned candidate reactions for 3-hydroxypropionic acid and 7 for butanal; 16 CSV rows and JSON counts consistent; source commit c5f32561b1ed99d0701a6dbb472dc448d6c082e8. Archived evidence verified, execution not repeated in this environment.
- DORAnet, RetroPath2, ChemEnzyRetroPlanner, BioPKS, RetroTide NOT_CONFIGURED in this notebook. Seventh slot UNRESOLVED_SEVENTH_ENGINE. Do not count RetroRules resource or legacy wrappers as a seventh engine without explicit canonical evidence.
- M1.2 PARTIAL PASS (artifact integrity/roster), M1 overall BLOCKED until full source lineage and seventh engine identity recovered.
- Next single action: recover and integrate previously working native DORAnet implementation, preserving RBC2 and its output contract; concurrently identify seventh engine from historical source rather than guessing.

## M1.4 source recovery — 2026-11-08
- Recovered V9, V12 fixed, V14 source archives from targeted Drive retrieval.
- Exact historical seven-engine roster confirmed by V9 engine_registry.json: DORAnet, RetroBioCat2, RetroPath2, RetroTide, BioPKS, AiZynthFinder, ChemEnzyRetroPlanner.
- V9 first three entries CACHED_EXPORT; remaining four NO_VERIFIED_OUTPUT_IN_V8. All V9 run_command values null.
- V12 README explicitly says four native engines not executed; V14 README says BioPKS target-specific contract blocked, ChemEnzy remote opt-in, RetroPath2 example different target.
- M1.4 source/roster recovery PASS; seven-engine native science NOT VERIFIED. V14 most advanced recovered orchestration, not automatically canonical current 2.6.
- Next task M2.1: preserve verified RBC2 and test genuine target-specific DORAnet native output with exact logs.

## M2.1 bounded DORAnet probe built — 2026-11-08
- SOURCE ZIP and one Colab notebook produced locally. Python and notebook code compiled successfully; native Colab run NOT EXECUTED.
- Probe installs DORAnet 0.5.7a1 in isolated venv, calls historical target-conditioned native API, captures logs and raw native identifiers.
- No chemical-side reaction exporter certified. Explicit fail-closed state NATIVE_RETURNED_EXPORT_UNVERIFIED is expected until native reaction mapping is verified. This is diagnostic, not M2 scientific PASS.
- RBC2 implementation and historical outputs untouched.
- Next action: execute M2.1 Colab notebook and inspect output ZIP for native API signature, reaction identifiers, and failures before narrow repair.

## M2.1.1 Python 3.13 venv bootstrap repair — 2026-11-08
- Observed Colab failure: venv.EnvBuilder(with_pip=True) -> ensurepip CalledProcessError under Python 3.13, before native DORAnet execution.
- Narrow repair: uv-managed Python 3.11 isolated venv, uv pip install doranet==0.5.7a1 and rdkit; no native probe or RBC2 code changed.
- Local notebook code syntax checks PASS. Colab runtime, native chemistry, and reaction export NOT VERIFIED.
- Next single action: run M2.1.1 notebook and inspect ALL_OUTPUTS ZIP; do not retry Python 3.13 ensurepip bootstrap.

## M2.1.1 observed run and M2.1.2 exporter — 2026-11-08
- Uploaded ALL_OUTPUTS verified: Python 3.11.17, doranet 0.5.7a1 installed; native reverse expansion on O=C(O)CCO returned ChemNetworkBasic, 98 native reactions, 126 molecules, 3571 operators, 1 generation, 1.54 min.
- M2.1.1 status NATIVE_RETURNED_EXPORT_UNVERIFIED: 98 native reaction identifiers, zero verified chemical-side reaction exports; warnings include invalid valence/kekulization; not a scientific export PASS.
- M2.1.2 notebook and SOURCE ZIP built: introspects native molecule container, maps native molecule IDs to RDKit-valid SMILES where possible, exports native reactant/product sides and operator IDs, otherwise retains fail-closed schema evidence.
- Local syntax checks PASS; M2.1.2 Colab native execution PENDING. RBC2 untouched.
- Next action: run M2.1.2 and inspect ALL_OUTPUTS; no new broad engine audit.

## M2.4.1 RetroPath2 source schema repair — 2026-11-08
- M2.4 Colab failed before native execution: upstream source headers ['Name','InChI']; notebook erroneously asserted one SMILES column. This is an input-contract error, not native chemistry failure.
- M2.4.1 patch derives InChI from O=C(O)CCO via isolated RDKit, writes one row preserving exact Name/InChI schema, leaves rules/sink and native CLI unchanged, retains native row logs and fail-closed target matching.
- Notebook AST and nbformat validation PASS; native target run PENDING. No claims of target-specific RetroPath2 success until outputs inspected.
- Next action: execute M2.4.1 and inspect target-native outputs; do not repeat M2.3 installation or example preflight unless needed for smoke baseline.

## M2.4.2 RetroPath2 source/sink collision — 2026-11-08
- Uploaded M2.4.1 output: input Name/InChI correct; native rules 17 and source fingerprints calculated, then process failed with ArgumentException duplicate key InChI=1S/C3H6O3/c4-2-1-3(5)6/h4H,1-2H2,(H,5,6) in SinkAndSourceDivider.Divide. Native target reaction count 0.
- Built M2.4.2: preserve original sink/rules and native executable, remove exact target InChI from run-local sink copy, record original and filtered hashes and removed rows; retain fail-closed native target reaction acceptance.
- Local syntax PASS; Colab execution pending. Do not count pinocembrin smoke rows as target-specific evidence.
- Next action: run M2.4.2, upload outputs, inspect actual target-specific reaction SMILES.

## M2.4.3 conditional sink and governance notification correction — 2026-11-08
- User observed all-failed 'Governance contract' GitHub Actions notifications. Unverified workflow `.github/workflows/governance.yml` removed from governance branch (commit cdecb60b683c95159cbc1307d8e03967e734759d). Documentation and checker retained. Existing failed runs may remain visible; no claim that all failures were diagnosed.
- M2.4.2 Colab observed source Name/InChI correct; 963 sink rows; zero exact target matches. Hard assertion len(removed)>0 was incorrect and stopped execution before native run.
- M2.4.3: when target absent from sink, use original sink unchanged; if present, filter only exact target in a run-local copy. Record duplicate InChI keys within sink to investigate prior duplicate-key exception. Preserve native logs, source and rules. Local notebook AST PASS; Colab run PENDING.
- Next action: run M2.4.3 and inspect target-specific native output or duplicate-key traceback. Avoid additional GitHub workflow creation until validated locally.
