from __future__ import annotations
from dataclasses import dataclass
from synbiocrow import SynBioCrowEngine

@dataclass(frozen=True)
class BootstrapAdvice:
    backend_id: str
    ready: bool
    install_hint: str
    external_requirements: tuple[str,...]=()

def bootstrap_advice(engine:SynBioCrowEngine|None=None)->tuple[BootstrapAdvice,...]:
    engine=engine or SynBioCrowEngine()
    readiness=engine.backend_readiness()
    hints={
        "doranet":(
            'pip install -e ".[doranet]"',
            (),
        ),
        "retrobiocat2":(
            "Install/configure the pinned RetroBioCat2 research runtime separately.",
            ("RetroBioCat2","RBC2 scientific data assets"),
        ),
        "retropath2":(
            "Legacy/reference backend: install retropath2-wrapper + rp2paths + KNIME only for historical compatibility checks.",
            ("RDKit","KNIME","RetroRules rules file","sink file"),
        ),
        "retropath_standalone":(
            "Use the KNIME-free TraceLD/retropath standalone runtime with explicit RetroRules rules + sink inputs.",
            ("TraceLD/retropath standalone CLI","RetroRules rules file","sink file"),
        ),
        "biopks_retrotide":(
            "Configure SYNBIOCROW_BIOPKS_RUNNER for an authorized BioPKS runtime.",
            ("BioPKS-Pipeline","RetroTide","upstream license acknowledgement"),
        ),
    }
    out=[]
    for bid in engine.backend_ids():
        hint,reqs=hints.get(bid,("Consult backend documentation.",()))
        out.append(BootstrapAdvice(
            backend_id=bid,
            ready=bool(readiness.get(bid,{}).get("available")),
            install_hint=hint,
            external_requirements=tuple(reqs),
        ))
    return tuple(out)
