# SynBioCrow V2.0 Alpha90.1.4.3.2.1

Automatic Predecessor Discovery Repair for the Frozen Golden Pathway Concordance Audit.

Scientific concordance logic is unchanged from Alpha90.1.4.3.2. This repair fixes notebook bootstrap behavior: it scans only the exact known predecessor Google Drive folders, inspects candidate ZIP contents through the existing scientific validators, and automatically selects the matching sealed prediction, frozen Golden bridge, and frozen exact-score packages. It no longer asks the user for a generic `ALL_OUTPUTS.zip`.

Manual upload is used only when a required predecessor is genuinely absent or fails validation, and the prompt names the exact expected package. The official exact metrics remain frozen at S@1/S@3/S@5/S@10 = 0/20 and MRR = 0.0; route-positive coverage remains 18/20. No new route generation, engine calls, bridge edits, aliases, or tuning occur.

Packaged verification: 6/6 tests passed; all notebook code cells compile; discovery cell validation passed.