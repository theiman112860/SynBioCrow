import json
from pathlib import Path

def test_frozen_split_keeps_validation_sealed():
    p=Path("benchmarks/2.4/split_manifest_2_4_11.json")
    m=json.loads(p.read_text())
    dev={x["record_id"] for x in m["records"] if x["split"]=="development"}
    val={x["record_id"] for x in m["records"] if x["split"]=="validation"}
    assert dev=={
        "post2022-mibk-2025",
        "post2022-jasmonic-acid-2023",
        "post2022-dammaradienol-2024",
        "post2022-curcumin-2024",
    }
    assert val=={"post2022-bakuchiol-2024","post2022-allitol-2025"}
    assert dev.isdisjoint(val)
