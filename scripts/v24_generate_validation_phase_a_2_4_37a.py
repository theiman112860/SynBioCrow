#!/usr/bin/env python3
"""SynBioCrow 2.4.37A truth-blind validation generator wrapper.

Reuses the tested 2.4.13.14.1 generator implementation verbatim except for
narrow split/output-label substitutions required to run the validation records.
No validation literature anchors/truth are read by this wrapper.
"""
from pathlib import Path

SRC=Path(__file__).with_name("v24_generate_development_routes_2_4_13_14_1.py")
text=SRC.read_text()

patches={
'dev=[x for x in manifest["records"] if x["split"]=="development"]':
'dev=[x for x in manifest["records"] if x["split"]=="validation"]',
'sealed={x["record_id"] for x in manifest["records"] if x["split"]!="development"}':
'sealed={x["record_id"] for x in manifest["records"] if x["split"]!="validation"}',
'if rid in sealed: raise RuntimeError("validation firewall violation")':
'if rid in sealed: raise RuntimeError("validation Phase A split firewall violation")',
'"split":"development"':'"split":"validation"',
'"development_only":True':'"validation_phase_a_truth_blind":True',
'"schema":"synbiocrow.v24.development-generation.v14_1"':
'"schema":"synbiocrow.v24.validation-phase-a-generation.v1"',
'"version":"2.4.13.14.1"':'"version":"2.4.37A"',
'"sealed_validation_record_ids":sorted(sealed)':'"sealed_development_record_ids":sorted(sealed)',
'"tuning_performed":False':'"tuning_performed":False,"validation_phase_a_truth_blind":True'
}
for old,new in patches.items():
    if old not in text:
        raise RuntimeError("expected generator patch target missing: "+old)
    text=text.replace(old,new)

g={"__name__":"__main__","__file__":str(SRC)}
exec(compile(text,str(SRC)+"[2.4.37A validation patch]","exec"),g,g)
