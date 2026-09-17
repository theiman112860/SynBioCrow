# SynBioCrow V2.0 Alpha90.1.4.3.2.3.1

Bootstrap-only repair for Alpha90.1.4.3.2.3 Native Golden Compound-Node Path Reconstruction.

The scientific module and frozen contracts are unchanged. This patch fixes Colab SOURCE extraction/root discovery: the notebook now resolves the package root as `module_path.parent.parent`, so imports target `<package>/src/alpha90_1_4_3_2_3.py` rather than the invalid `<package>/src/src/alpha90_1_4_3_2_3.py`.

A regression test reproduces the extracted layout and verifies the project root, preventing recurrence of the double-`src` import path. Packaged verification: 8/8 tests passed and all 8 notebook code cells compile after fresh re-extraction.