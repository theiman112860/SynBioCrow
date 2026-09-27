"""Template external bridge for BioPKS Pipeline / RetroTide.

This file is a protocol example only. It intentionally does not import or
redistribute BioPKS Pipeline.

stdin:
  {"schema":"synbiocrow.biopks.external.v1",
   "target_smiles":"...",
   "options":{...}}

stdout:
  {"schema":"synbiocrow.biopks.external.v1",
   "status":"COMPLETE",
   "routes":[...]}
"""
import json, sys

request=json.load(sys.stdin)
assert request["schema"]=="synbiocrow.biopks.external.v1"
target=request["target_smiles"]

# In your separately installed BioPKS runtime:
# 1. run the bounded RetroTide/BioPKS workflow;
# 2. emit route dictionaries with explicit reaction chemistry where available;
# 3. retain architecture-only PKS steps as metadata;
# 4. do not claim sequence completeness or experimental validation unless proven.

response={
    "schema":"synbiocrow.biopks.external.v1",
    "status":"NO_HIT",
    "routes":[],
}
print(json.dumps(response))
