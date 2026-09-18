# SynBioCrow V2.0 Alpha90.1.6.1

Parent-Preserving Recursive Assembly + Dominance Filtering.

This release addresses the Alpha90.1.6 regression in which recursive expansion preserved 20/20 route-positive coverage but reduced mean strict Golden concordance relative to the shallower recovered route set. Alpha90.1.6.1 protects the original C-branch routes as fallbacks and allows recursive descendants into the final D route set only when they pass a fixed benchmark-blind intrinsic dominance rule.

A descendant must demonstrably resolve its recorded parent precursor, may not reduce molecular completeness or adjacency, may not increase abstract products, may add at most four steps, and must improve the generic assembly score by at least 0.02. Golden identities, Golden case labels, benchmark scores, and benchmark-derived thresholds are not inputs to this rule.

The D branch can retain up to 30 routes so all protected C routes remain available while qualifying recursive descendants are added. Per-case state is atomically persisted to Drive. Final packaging reads the durable Drive checkpoint when available, avoiding the Alpha90.1.6 local-checkpoint FileNotFoundError.

Packaged verification: 7/7 tests passed and all 9 executable notebook code cells compile after fresh generation.