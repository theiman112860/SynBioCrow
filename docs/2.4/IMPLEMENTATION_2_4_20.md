# SynBioCrow 2.4.20 — Development Ranking Feature Attribution

2.4.19 cleanly separates the development targets: jasmonic acid and curcumin are ranking-limited, whereas MIBK and dammaradienol are generation-coverage-limited.

2.4.20 does not change weights. For the two ranking-limited targets only, it joins the frozen 2.4.16 feature table to the corrected 2.4.18.1 target-excluded internal-anchor similarity and reports per-feature Spearman association and coverage. This identifies which existing signals align or conflict with literature-related chemical proximity before any development-only calibration is attempted.

MIBK and dammaradienol are reserved for a separate generation repair. Validation/evaluation records remain sealed.
