# SynBioCrow 2.4.35 — Target-Relative Leave-One-Target-Out Transfer

2.4.34 failed to generalize consistently across unseen development targets: jasmonic acid improved strongly, while curcumin, dammaradienol, and MIBK worsened. This indicates substantial target-level feature-domain shift.

2.4.35 tests whether the transferable signal is relative rather than absolute. Each evidence feature is converted to its within-target percentile using only the unlabeled candidate feature distribution. Pairwise models are then trained on the other development targets and transferred to the held-out target.

The held-out target contributes no similarity labels to training. Percentile normalization uses only unlabeled evidence values, preserving the target-level truth firewall.

This is diagnostic only; production ranking is unchanged and validation/evaluation truth remains sealed.
