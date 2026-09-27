from dataclasses import dataclass,field
from collections.abc import Iterable
from synbiocrow.generators.registry import BackendRegistry,default_registry
from synbiocrow.lifecycle.policy import PromotionPolicy
from synbiocrow.core.models import PathwayCandidate
from synbiocrow.ensemble import build_reaction_graph, EnsembleGraph

@dataclass
class SynBioCrowEngine:
    """2.2 consolidation engine shell."""
    backends:BackendRegistry=field(default_factory=default_registry)
    promotion_policy:PromotionPolicy=field(default_factory=PromotionPolicy)

    def backend_ids(self)->tuple[str,...]:
        return self.backends.ids()

    def backend_readiness(self)->dict[str,dict]:
        out={}
        for backend_id in self.backends.ids():
            backend=self.backends.get(backend_id)
            info=getattr(backend,"runtime_info",None)
            if callable(info):
                try:
                    out[backend_id]=dict(info())
                except Exception as exc:
                    out[backend_id]={"available":False,"error":f"{type(exc).__name__}: {exc}"}
            else:
                available=getattr(backend,"available",lambda:False)
                try: state=bool(available())
                except Exception: state=False
                out[backend_id]={"available":state}
        return out

    def build_ensemble(self,candidates:Iterable[PathwayCandidate])->EnsembleGraph:
        return build_reaction_graph(candidates)
