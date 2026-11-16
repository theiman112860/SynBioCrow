# Pathway evidence v1

This is a **candidate graph witness** feature, not a scientific certification engine. It does not call or reinstall native generators.

Input: Reaction objects with stable IDs, all reactants/products, engine and evidence reference; explicit seed set and target.

Output: target reachability, a dependency-complete reaction witness, provenance and direct target-producing precursor gaps. A target already supplied as a seed has zero reaction evidence and must not be counted as a newly discovered pathway.

The implementation does not infer reaction direction, cofactor balance, carbon balance, enzymatic support, thermodynamics, host feasibility, or experimental validation. Those require separate gates. PKS design records must not be fed as chemical reaction edges without a verified release transformation.

Run regression tests with `python -m unittest discover -s tests -p 'test_pathway_evidence.py'`.
