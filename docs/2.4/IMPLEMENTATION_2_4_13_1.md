# SynBioCrow 2.4.13.1 — route-closure and backend repair

The 2.4.13 run completed for all four development targets and produced 889
DORAnet candidates across 1,200 reaction edges, but zero routes. Inspection
showed two independent causes:

1. only DORAnet was execution-available in the Colab runtime;
2. the runner supplied an empty `sink_smiles` tuple, and the engine intentionally
   skips route reconstruction when no sinks are supplied.

2.4.13.1 therefore freezes a truth-independent central-metabolite sink panel
before validation and requires both DORAnet and RetroBioCat2 to be available.
The sink panel is not derived from any literature route truth.

RetroPath and BioPKS remain optional in this repair unless genuinely
execution-ready. They are not marked ready using validation fixtures or an
unacknowledged external license.

The two validation targets remain sealed.
