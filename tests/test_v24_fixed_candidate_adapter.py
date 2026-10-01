import csv, json
from pathlib import Path
from synbiocrow.v24.adapters import adapt_route, load_fixed_candidates
from synbiocrow.v24.feature_matrix import feature_rows

def test_nested_route_adapter_preserves_fixed_candidates():
    r=adapt_route({"route_id":"r1","similarity_2d":0.8,"reactions":[
      {"reaction_smiles":"A>>B","engine":"retrobiocat2","rhea_id":"RHEA:1","mapping_confidence":0.9},
      {"reaction_smiles":"B>>C","engine":"retropath2"},
    ]})
    assert r.route_id=="r1"
    assert len(r.reactions)==2
    assert r.features.route_length==2
    assert r.features.engine_count==2
    assert r.features.reaction_evidence_fraction==0.5
    assert r.features.structural_2d==0.8

def test_missing_reaction_fails_closed():
    try: adapt_route({"route_id":"bad","reactions":[{"foo":"bar"}]})
    except ValueError as e: assert "identifier" in str(e)
    else: raise AssertionError("expected failure")

def test_json_loader_and_matrix(tmp_path):
    p=tmp_path/"routes.json"
    p.write_text(json.dumps({"routes":[{"route_id":"x","reactions":[{"id":"rx1","uniprot":"P1"}]}]}))
    routes=load_fixed_candidates(str(p))
    rows=feature_rows(routes)
    assert len(rows)==1
    assert rows[0]["reviewed_enzyme_fraction"]==1.0

def test_csv_groups_rows_by_route(tmp_path):
    p=tmp_path/"routes.csv"
    with p.open("w",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["route_id","reaction_smiles","engine"])
        w.writeheader(); w.writerow({"route_id":"r","reaction_smiles":"A>>B","engine":"a"})
        w.writerow({"route_id":"r","reaction_smiles":"B>>C","engine":"b"})
    routes=load_fixed_candidates(str(p))
    assert len(routes)==1 and len(routes[0].reactions)==2


def test_observed_vnext_0_3_51_7_schema():
    r=adapt_route({
      "candidate_pathway_id":"BIOPKS-98ad0b2ff61121ed",
      "backend":"BioPKS+DORAnet",
      "benchmark_v2_truth_accessed":False,
      "net_feasibility":0.26669833,
      "state":"CANDIDATE",
      "enzyme_evidence_status":"NO_DIRECT_ENZYME_IDENTITY_FOR_THIS_EXACT_REACTION",
      "thermo_status":"NOT_QUANTIFIED_NO_FABRICATION",
      "reactions":[{"raw":"O=C(O)C(O)Cc1ccccc1 = O=C=O + OCCc1ccccc1","parse_status":"PASS"}]
    },source_format="vnext_0_3_51_7")
    assert r.route_id=="BIOPKS-98ad0b2ff61121ed"
    assert r.reactions[0].reaction_id.startswith("O=C(O)")
    assert r.reactions[0].engines==("BioPKS+DORAnet",)
    assert r.features.reaction_evidence_fraction==0.0
    assert r.features.reviewed_enzyme_fraction==0.0
    assert r.features.thermo_coverage_fraction==0.0
