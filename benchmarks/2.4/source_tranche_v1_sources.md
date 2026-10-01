# SynBioCrow 2.4 source tranche v1 — provenance notes

This tranche contains real post-2022 biosynthetic pathway targets selected for
development/validation curation. It is **not yet a frozen benchmark split**.

A record may enter development/validation only after its
`historical_exclusion_status` is `verified_excluded`.

## Records

### Curcumin
- Primary pathway paper: Rainha et al., ACS Synthetic Biology (2024).
- DOI: 10.1021/acssynbio.4c00059
- Structure source: PubChem CID 969516.
- Paper reports the first successful de novo production of curcumin in S. cerevisiae.

### Bakuchiol
- Primary pathway paper: Zheng et al., ACS Synthetic Biology (2024).
- DOI: 10.1021/acssynbio.4c00416
- Structure source: PubChem CID 5468522.
- Engineered S. cerevisiae produced bakuchiol from glucose.

### Dammaradienol
- Primary pathway paper: Gan et al., ACS Synthetic Biology (2024).
- DOI: 10.1021/acssynbio.4c00396
- Structure source: PubChem CID 13893946.
- Heterologous yeast biosynthesis of a polyene-type ginsenoside precursor.

### Methyl isobutyl ketone
- Primary pathway paper: ACS Synthetic Biology (2025).
- DOI: 10.1021/acssynbio.5c00527
- Structure source: PubChem CID 7909.
- The paper reports a novel de novo biosynthetic pathway and states there had
  been no previous report of biosynthesis directly from glucose.

### Jasmonic acid
- Primary pathway paper: Tang et al., Nature Synthesis (2023/2024 issue).
- DOI: 10.1038/s44160-023-00429-w
- Structure source: PubChem CID 5281166.
- Engineered yeast produced jasmonic acid and jasmonate derivatives from glucose.

### D-Allitol
- Primary pathway paper: Journal of Agricultural and Food Chemistry (2025).
- DOI: 10.1021/acs.jafc.5c03615
- Structure source: PubChem CID 120700.
- De novo production from sucrose via engineered modular pathways.

## Cross-check policy

Publication after the Galaxy-SynBioCAD paper is **not by itself sufficient** to
prove that the target compound was absent from the frozen 2.3 holdout.

Therefore five of the six records remain `pending`.

MIBK is provisionally marked `verified_excluded` because the 2025 primary paper
describes the pathway as a first de novo biosynthesis from glucose and the
target/pathway therefore could not have been represented as that biosynthetic
route in the 2022 Galaxy benchmark lineage. This status should still be
rechecked if the exact 65-target frozen list is recovered.
