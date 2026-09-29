import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_benchmark_2_3 import load_panel, summarize


class Benchmark23Tests(unittest.TestCase):
    def test_load_panel_requires_unique_ids(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"panel.json"
            p.write_text(json.dumps({"targets":[
                {"target_id":"x","target_name":"A","target_smiles":"CCO","chemical_class":"a"},
                {"target_id":"x","target_name":"B","target_smiles":"CCC","chemical_class":"b"},
            ]}))
            with self.assertRaises(ValueError):
                load_panel(p)

    def test_summary_detects_ensemble_only_route(self):
        records=[{
            "target_id":"x","target_name":"x","chemical_class":"a",
            "arms":{
                "doranet":{"status":"COMPLETE","elapsed_seconds":1,"candidate_count":1,"route_count":0},
                "retrobiocat2":{"status":"NO_HIT","elapsed_seconds":1,"candidate_count":0,"route_count":0},
                "retropath_standalone":{"status":"COMPLETE","elapsed_seconds":1,"candidate_count":1,"route_count":0},
                "biopks_retrotide":{"status":"SKIPPED_UNAVAILABLE","elapsed_seconds":0,"candidate_count":0,"route_count":0},
                "ensemble":{"status":"COMPLETE","elapsed_seconds":2,"candidate_count":2,"route_count":1},
            }
        }]
        s=summarize(records)
        self.assertEqual(s["ensemble_only_route_targets"],["x"])
        self.assertEqual(s["arms"]["ensemble"]["route_coverage_count"],1)


if __name__=="__main__":
    unittest.main()
