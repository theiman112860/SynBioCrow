# SynBioCrow 2.4.13.5 — cross-engine partial-path closure

2.4.13.4 established that RetroBioCat2 is genuinely exploring reaction space but
finding zero solved routes to the frozen sink panel. This is not an adapter
conversion failure.

Observed native MCTS behavior included:
- methyl isobutyl ketone: 103 reactions, 78 molecules, 104 iterations;
- jasmonic acid: 2,526 reactions, 1,734 molecules, 230 iterations;
- dammaradienol: 145 reactions, 106 molecules, 147 iterations;
- curcumin: 1,938 reactions, 1,528 molecules, 50 iterations;
- solved pathways: 0 for all four targets.

2.4.13.5 tests the ensemble hypothesis directly. RetroBioCat2 now exposes
`get_all_pathways()` when explicitly requested. These outputs are marked
`PARTIAL_EXPLORED` unless they are also in the solved set; they are never
misrepresented as solved RBC2 routes.

The runner merges:
- DORAnet candidates;
- RBC2 solved candidates, if any;
- RBC2 explored partial candidates;

then performs the normal SynBioCrow cross-engine graph merge and bounded route
closure against the frozen central-metabolite sink panel.

A route found only after graph merging would be evidence for complementary
cross-engine closure. Validation targets remain sealed and no ranking weights
are tuned.
