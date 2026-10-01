# Hybrid Route Transformation & Sustainability Optimization

## Status

Experimental architecture for SynBioCrow 2.4/2.5.
Not part of the frozen 2.3 claims.
Not a 2.4 primary success criterion.

## Motivation

SynBioCrow should eventually accept a conventional chemical synthesis route, identify transformations that may be replaceable by enzymatic or biosynthetic alternatives, construct hybrid descendants, and compare route families using explicit sustainability and feasibility dimensions.

The system must not assume that biological equals environmentally preferable.

## Core object: Route Transformation Graph

A Route Transformation Graph records parent-child relationships among routes.

A parent route may be:
- conventional chemical;
- chemoenzymatic;
- biosynthetic;
- mixed/hybrid.

A child route is created only by an explicit transformation operation, for example:
- replace one chemical step with an enzymatic transformation;
- replace a multi-step chemical segment with an enzyme cascade;
- replace a route segment with a metabolic pathway;
- extend a synthetic intermediate backward to a renewable biological precursor;
- restore a chemical step where a biological alternative is infeasible.

Every child retains:
- parent route ID;
- transformation operation;
- affected reaction span;
- evidence used;
- generating engine/tool;
- uncertainty;
- provenance.

## Chemical-route ingestion

Define a neutral reaction-route schema that can ingest routes from conventional retrosynthesis planners.

Required fields:
- reactants/products;
- reagents/catalysts when available;
- solvent;
- temperature;
- pressure;
- time;
- yield;
- protecting-group operations;
- literature/source;
- confidence/missingness.

Unknown process conditions stay unknown.

## Biological substitution

For each chemical step or contiguous route segment:
1. normalize transformation;
2. search enzyme/rule precedent;
3. query SynBioCrow biological generators;
4. test whether biochemical replacement reconnects the same upstream/downstream compounds;
5. annotate enzyme, cofactor, thermo, and evidence;
6. generate child hybrid route.

No substitution is promoted solely because it is enzymatic.

## Sustainability feature vector

Maintain a vector, not a single opaque green score.

### Material efficiency
- atom economy;
- reaction mass efficiency;
- process mass intensity (PMI);
- E-factor;
- yield compounding;
- protecting-group burden.

### Energy/process intensity
- temperature;
- pressure;
- reaction duration;
- heating/cooling burden;
- distillation;
- evaporation;
- chromatography;
- concentration/dilution burden.

### Hazard
- flammability;
- toxicity;
- corrosivity;
- explosivity/reactivity;
- hazardous solvent/reagent classes.

### Environmental burden
- estimated cradle-to-gate CO2e where defensible;
- persistence/ecotoxicity;
- water demand;
- waste class;
- renewable versus fossil feedstock.

### Biological burden
- ATP requirement;
- NADH/NADPH demand;
- oxygen demand;
- cofactor regeneration;
- carbon loss;
- product toxicity;
- likely dilute-product/separation burden.

### Evidence quality
Every sustainability value carries:
- measured / literature / database / calculated / inferred / unknown;
- source;
- uncertainty;
- applicable system boundary.

## Ranking

Primary presentation should be multi-objective.

Use:
- Pareto frontier;
- dimension-specific leaders;
- configurable user preferences;
- uncertainty-aware comparison.

Examples:
- lowest energy;
- lowest hazard;
- lowest material intensity;
- highest biochemical evidence;
- lowest estimated carbon burden;
- best balanced compromise.

Avoid declaring a universal best route unless the user explicitly supplies weights and system boundaries.

## Validation program

Build a blinded benchmark of published route improvements.

For each case:
1. collect an original conventional synthesis;
2. collect a later published enzymatic, biosynthetic, or chemoenzymatic improvement;
3. expose only the original route to SynBioCrow;
4. hide the improved route during transformation generation;
5. test whether SynBioCrow rediscovers the same substitution class or a chemically equivalent improvement;
6. compare sustainability dimensions using only supported process data.

Primary metrics:
- substitution-site recall;
- route-family recovery;
- exact/near-equivalent hybrid recovery;
- evidence quality;
- Pareto position of known published improvement;
- false-positive substitution burden.

## Research firewall

The hidden published improvements must not be used to hand-code transformation rules for their own evaluation cases.

Development and evaluation cases must be source-separated where possible.

## Long-term objective

Given a desired molecule, SynBioCrow should enumerate credible chemical, enzymatic, biosynthetic, and hybrid manufacturing routes and expose the tradeoffs among feasibility, evidence, energy, environmental burden, hazard, material efficiency, and process complexity.
