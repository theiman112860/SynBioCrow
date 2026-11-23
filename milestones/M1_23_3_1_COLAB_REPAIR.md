# M1.23.3.1 Colab repair

Two observed failures in M1.23.3:
1. `ModuleNotFoundError: No module named 'rdkit'` because RDKit was imported before installation.
2. `AssertionError: Input evidence SHA mismatch` for a user-uploaded M1.23.2 ZIP (reported 2614 bytes vs local reference 2616 bytes).

The revised notebook installs RDKit if absent and records the exact observed archive SHA. It validates the input ZIP integrity, expected three JSON members, M1.23.2 milestone, 12 unique candidate IDs, 12 summary entries, reaction fields, and the frozen M1.22.4 archive SHA lineage `bdd6fcd30ae6dbb0cd22dbcffe3380ec57896db47ba5ebbf20b630a4536e1c93`.

The original reference archive SHA is `e948efd13081f4baa8a3f7e3eec062e7e77f3ff24714953e328d8d867be5e722`. A nonidentical upload is allowed **only if its scientific evidence contract passes** and the difference is recorded. The user's actual 2614-byte upload has not been inspected locally, so acceptance is not preclaimed.

Static notebook syntax verification passed. No Colab execution or Rhea data match was performed. Original frozen seven-engine engines untouched.
