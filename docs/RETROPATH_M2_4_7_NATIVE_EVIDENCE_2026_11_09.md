# M2.4.7 RetroPath2 native two-target result — 2026-11-09

Source: user-uploaded `SynBioCrow_M2_4_7_RETROPATH_TWO_TARGET_NATIVE_GATE_ALL_OUTPUTS.zip`, inspected directly.

## Native results
- TraceLD RetroPath alpha executable ran with exit code 0 on both 3-hydroxypropionic acid (`O=C(O)CCO`) and butanal (`CCCC=O`) at pathway lengths 1 and 4.
- Every run exported a CSV header and **zero reaction rows**; summary status `NO_VERIFIED_TARGET_REACTIONS` for both targets.
- Each native stdout log reports **Rules: 17**, using `native/retropath_1.0.0-alpha_linux-x64/example_data/rules.csv`.
- Both targets were treated as source molecules not present in the sink. Input manifests report 963 original and 807 effective sink entries after filtering.
- Two RDKit sanitization warnings concern nitrogen-containing molecules, not an identified target-specific failure; native process continued.
- Increasing pathway length from 1 to 4 did not change the zero-row outcome.

## Scientific decision
**FAIL** third-engine target-specific native reaction generation gate. Successful process exit is not scientific success.

## Bounded next experiment
Do not repeat protonation changes or merely increase iteration count. Determine whether the installed TraceLD distribution has a non-example, supported reaction-rule corpus, or whether an authentic documented rule file must be supplied. Verify rule schema and provenance before running the same two targets. If no supported production rule corpus is available, mark RetroPath2 as blocked on rules and move to another engine rather than fabricating chemistry or repeating empty runs.
