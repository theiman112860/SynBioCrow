# SynBioCrow V2.0 Alpha90.1.4.3.1

Frozen Golden Bridge + Sealed Prediction Exact-Path Scoring.

This release performs no route generation and makes no engine calls. It verifies the immutable Alpha90.1.4.3 prediction seal `8641cbc9a1494ddb9e4e1f14555475f1121d4f31b8519e165ef5c50d648f37c4`, the frozen Alpha90.1.4.4.2.2 bridge manifest `ae1e483a8b9becf86b643e43296e395742bcfc3ba8c49eb6b08c09813fe07690`, and the certified Golden source SHA before scoring.

Exact pathway is defined narrowly as exact equality of the ordered Golden source-native product InChIKey sequence. Predicted route-step products are converted to InChIKeys; route length and every ordered product identity must match. This authorizes ordered product-identity S@1/S@3/S@5/S@10 and MRR, but does not claim full stoichiometric reaction equality.

No post-hoc aliases, bridge edits, prediction rewriting, chemistry/search tuning, or Alpha90.2 authorization are permitted. Packaged verification: 5/5 tests passed; all notebook code cells compile.