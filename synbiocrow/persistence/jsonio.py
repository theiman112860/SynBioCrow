from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def dump_json(data:Any,path:str|Path)->None:
    Path(path).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def load_json(path:str|Path)->Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
