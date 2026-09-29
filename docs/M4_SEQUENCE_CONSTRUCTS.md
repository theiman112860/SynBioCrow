# M4 sequence and construct optimization

M4 implements SynBioCrow's first explicit **digital Build** layer.

## Evidence-backed sequence acquisition

- UniProt sequence retrieval requires an explicit protein accession.
- NCBI nucleotide retrieval requires an explicit accession **plus CDS coordinates and strand**.
- A whole nucleotide record is never silently relabeled as a CDS.
- The selected CDS must translate exactly to the selected protein sequence before construct design proceeds.

## Nucleotide optimization

By default, SynBioCrow preserves the selected amino-acid sequence and changes
only synonymous codons.

The current optimizer is deterministic and auditable. It accepts a user-supplied
preferred-codon mapping and includes a simple E. coli K-12-oriented preferred
codon profile for reproducible baseline tests. It is not presented as a full
CAI/tAI or expression model.

Protein engineering is intentionally outside this default path.

## Sequence QC

Current deterministic checks include:

- GC percentage
- selected forbidden restriction motifs
- long homopolymers
- DNA alphabet validation

A QC failure does not fabricate a repaired sequence; it remains visible in the
result for later optimization iterations.

## Regulatory parts

SynBioCrow ships provenance references for the standard iGEM parts already used
in the 2.1 lineage (J23119, B0034, B0015), but does **not** hard-code a regulatory
DNA sequence unless that sequence has been explicitly verified and supplied.

This preserves the evidence policy: a part identifier is not treated as a
verified sequence.

## Cassette assembly

A single-gene expression cassette is assembled in the order:

```text
promoter -> RBS -> CDS -> terminator
```

Each resulting cassette retains:

- part identifiers and sources
- pathway ID
- optimized CDS accession
- deterministic sequence SHA-256
- whole-cassette QC result
- Candidate lifecycle state

Multiple expression cassettes can also be combined into a deterministic
multi-gene construct.

## Lifecycle

M4 produces **Candidate** constructs. Passing translation validation and sequence
QC does not imply successful expression, flux, toxicity, manufacturability, or
experimental validation.
