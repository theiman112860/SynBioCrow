import json
from pathlib import Path
import pytest
from synbiocrow.v24.evidence_enrichment_2_4_15 import load_cache,save_cache

def test_cache_roundtrip(tmp_path):
    p=tmp_path/"cache.json"; x={"schema":"x","edges":{"a":{"status":"abstain"}}}
    save_cache(p,x); assert load_cache(p)==x

def test_cache_default(tmp_path):
    x=load_cache(tmp_path/"none.json")
    assert x["edges"]=={} and x["ec_uniprot"]=={}
