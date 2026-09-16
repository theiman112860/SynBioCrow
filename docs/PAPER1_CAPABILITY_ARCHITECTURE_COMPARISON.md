# Paper 1 capability/architecture comparison note

Position SynBioCrow as an **agentic, evidence-aware orchestration layer** that can call, reconcile, audit, and rank outputs from established retrosynthesis and synthetic-biology tools, rather than as a drop-in replacement for each specialized engine.

| System | Core role / architecture | Relationship to SynBioCrow |
|---|---|---|
| Galaxy-SynBioCAD | Galaxy-based end-to-end synthetic-biology workflows spanning retrosynthesis (RetroRules/RetroPath2.0/RP2Paths/rpCompletion), pathway evaluation/ranking (rpThermo/rpFBA/rpScore), and genetic design. | Strongest integration target. SynBioCrow should be framed as an agentic orchestration/evidence layer that can invoke Galaxy-SynBioCAD capabilities and combine them with additional engines/evidence. Direct integration belongs on Alpha91 roadmap. |
| BioNavi-NP | Transformer single-step model plus AND-OR-tree multistep planning for natural-product biosynthesis. | Complementary learned route generator; useful as one proposal engine whose outputs SynBioCrow can audit and reconcile. |
| RetroPathRL | Monte Carlo Tree Search reinforcement-learning bioretrosynthesis guided by biochemical/chemical scores. | Complementary long-horizon search engine and source of the LASER/Golden benchmark lineage. |
| RetroPath2.0 | Generalized reaction-rule retrosynthesis workflow linking source targets to chassis sink compounds. | Established rule-based engine already conceptually aligned with SynBioCrow's multi-engine design. |
| RetroBioCat | Expert-encoded biocatalytic reaction rules plus literature/enzyme precedent for cascade planning. | High-value specialist engine for enzyme/biocatalysis-aware branches and evidence enrichment. |
| SynBioCrow | Agentic orchestration of heterogeneous retrosynthesis engines, evidence sources, semantic audits, confidence/provenance tracking, pathway closure, and downstream DBTL reasoning. | Integrator/meta-system: emphasize traceability, tool selection, evidence reconciliation, and workflow automation rather than claiming novelty for every underlying retrosynthesis primitive. |

Primary sources to cite in manuscript: Galaxy-SynBioCAD, Nature Communications 2022 (10.1038/s41467-022-32661-x); BioNavi-NP, Nature Communications 2022 (10.1038/s41467-022-30970-9); RetroPathRL, ACS Synthetic Biology 2020 (10.1021/acssynbio.9b00447); RetroPath2.0, Metabolic Engineering 2018 (10.1016/j.ymben.2017.12.002); RetroBioCat, Nature Catalysis 2021 (10.1038/s41929-020-00556-z).
