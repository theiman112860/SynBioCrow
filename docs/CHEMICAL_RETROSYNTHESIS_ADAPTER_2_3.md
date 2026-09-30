# Chemical retrosynthesis as a SynBioCrow proposal backend

## Purpose

Conventional organic-synthesis planners such as AiZynthFinder or ASKCOS can
suggest chemically plausible disconnections that are outside the search spaces
of biosynthesis-specific engines. SynBioCrow may use such planners as an
**additional proposal source**, but their routes must not be relabeled as
biosynthetic routes without biochemical validation.

## Conversion contract

A chemical retrosynthesis route enters SynBioCrow in the state
`CHEMICAL_PROPOSAL`. Each reaction is normalized and evaluated through:

1. **Structure/reaction normalization**
   - canonical compound identity
   - atom-mapped or canonical reaction representation where available
   - explicit reagents/catalysts/conditions retained as provenance

2. **Biochemical transform matching**
   - exact/near match to Rhea and curated enzymatic transformations
   - RetroRules/RetroBioCat/DORAnet rule compatibility
   - EC/enzyme precedent where available

3. **Biological-context filtering**
   - reject or flag protecting-group chemistry
   - reject steps requiring non-biological stoichiometric reagents or extreme
     conditions unless a documented enzymatic analogue exists
   - identify cofactor requirements and regenerate balanced biochemical forms

4. **Evidence and feasibility**
   - stoichiometric closure
   - thermodynamic evaluation
   - enzyme evidence / substrate-context evidence
   - chassis precursor availability

5. **Lifecycle outcome**
   - `CHEMICAL_PROPOSAL`: chemistry only
   - `BIOCONVERTIBLE_CANDIDATE`: every retained step has a plausible
     biochemical analogue, but evidence may be incomplete
   - normal SynBioCrow Candidate/Mature/Certified lifecycle thereafter

A conventional route that fails biochemical conversion remains useful as a
search hint or missing-transformation hypothesis, but is not counted as a
biosynthetic pathway.

## Candidate initial backends

- **AiZynthFinder**: open-source tree-search retrosynthesis using learned
  expansion policies and purchasable precursor stocks.
- **ASKCOS**: computer-aided synthesis planning with learned/template-based
  retrosynthesis and forward plausibility/context tools.

## Why this may help

Chemical planners explore a much larger reaction space than dedicated
retrobiosynthesis tools. Their value to SynBioCrow is therefore not that they
are biological, but that they may expose useful disconnections that can be
mapped to enzyme chemistry, reveal missing enzymatic transformations, or
suggest hybrid chemoenzymatic routes.

## Manuscript policy

For the current paper this capability should be described as a planned/adapter
architecture unless and until a chemical-planner backend is integrated and
benchmarked. It must not be included in current performance claims.
