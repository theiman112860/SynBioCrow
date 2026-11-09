# DORAnet native two-target evidence — 2026-11-09

Source: user-uploaded `SynBioCrow_DORANET_NATIVE_TWO_TARGET_ALL_OUTPUTS (1).zip`, containing `results.json` and `run.log`. Inspected directly; no CI-native rerun.

- Engine: DORAnet `0.5.7a1`
- Direction: `retro`; generations: `1`; ruleset: `JN3604IMT`.
- 3-hydroxypropionic acid `O=C(O)CCO`: `NATIVE_EXECUTED`, **98** candidate reactions.
- Butanal `CCCC=O`: `NATIVE_EXECUTED`, **75** candidate reactions.
- Total: **173** exported candidate records, each with reaction, rule ID, metadata, provenance and candidate-only flag.
- `run.log` contains clone startup text only; scientific evidence is in `results.json`.

**Gate:** native DORAnet reaction generation on two requested targets PASS. No claim of independent stoichiometric/thermodynamic validation, biosynthetic feasibility, pathway closure, or prospective benchmark success.

**Next:** retain working DORAnet and RBC2 native implementations; integrate conservative exchange formats, then pursue remaining engines. Do not repeat smoke tests without a concrete reason.
