# M8 Learn / Closed-loop DBTL

M8 implements the **Learn** stage of SynBioCrow's Design-Build-Test-Learn loop.

The learning layer is intentionally **policy learning**, not autonomous
scientific truth modification.

## Structured Test outcomes

A `TestOutcome` records:

- unique outcome ID
- outcome kind: `backend`, `route`, or `construct`
- subject ID
- bounded reward in [-1, 1]
- optional backend ID
- numeric feature vector
- source and notes

Examples of future Test sources include:

- reproducibility-panel outcomes
- route evidence/closure results
- construct QC results
- benchmark results that are authorized for learning
- experimental results, when explicitly provided and provenance-backed

Protected holdout truth is not an authorized learning source.

## Learning policy

`LearningPolicy` contains only ranking/prioritization weights:

- backend weights
- route-feature weights
- construct-feature weights

Updates are bounded by:

- a learning rate
- `max_delta_per_update`
- minimum/maximum weight bounds

Outcome order is canonicalized before updating, so the same outcome set produces
the same audit digest.

## What learning can change

Learned policy may change:

- which successful backend results are prioritized for review
- route ranking among Candidate routes
- construct ranking among Candidate constructs
- future design/search prioritization

## What learning cannot change

M8 **cannot**:

- convert missing evidence into evidence
- change a Rhea/thermodynamic/enzyme gate result
- invent chemistry, proteins, CDS, or regulatory sequences
- access protected benchmark truth
- promote Candidate -> Mature -> Certified

Lifecycle promotion remains controlled exclusively by explicit evidence policy.

## Audit trail

Every policy update may be written to an append-only JSONL audit log containing:

- policy before
- policy after
- Test outcomes
- exact deltas
- deterministic audit digest
- `lifecycle_effect: NONE`

## CLI

Start from the default policy:

```bash
synbiocrow learn \
  --outcomes outcomes.json \
  --output learned_policy.json \
  --audit-log learning_audit.jsonl
```

Continue from an existing policy:

```bash
synbiocrow learn \
  --policy prior_policy.json \
  --outcomes new_outcomes.json \
  --output next_policy.json \
  --audit-log learning_audit.jsonl
```

The command writes both the new policy and the exact `PolicyUpdate`.

## DBTL mapping

- **Design**: generator ensemble, route graph, pathway/construct design
- **Build**: digital CDS optimization and cassette assembly
- **Test**: evidence gates, reproducibility, runtime/construct validation
- **Learn**: M8 bounded, versioned prioritization-policy updates

This completes the first computational DBTL loop while maintaining the frozen
scientific safety contracts.
