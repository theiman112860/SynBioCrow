# SynBioCrow 2.4.13.4 — RBC2 native MCTS diagnostics

The 2.4.13.3.1 run successfully removed the external RBC2 source-database
dependency and executed both DORAnet and RetroBioCat2 on all four frozen
development targets.

Observed result:

- DORAnet: 889 candidates total across the four targets;
- RetroBioCat2: status COMPLETE for all four targets;
- RetroBioCat2 candidates: 0 for all four targets;
- sink-connected ensemble routes: 0 for all four targets;
- validation truth accessed: false;
- tuning performed: false.

A zero-candidate COMPLETE result is ambiguous without MCTS internals. 2.4.13.4
therefore persists RetroBioCat2's native `last_run_stats` for every target,
including iterations, run time, reaction/molecule counts, positive
backpropagations, solved count, template applications, expander calls, and
selection metrics where available.

The runner classifies each no-hit into one of:

- `MCTS_EXPLORED_NO_SOLVED_PATHWAYS`
- `SOLVED_PATHWAYS_NOT_CONVERTED`
- `NO_EXPANSION_OR_NO_HIT`
- `CANDIDATES_RETURNED`

No search bound is increased in this checkpoint. The purpose is to distinguish
coverage/closure failure from adapter-conversion failure before any tuning.
