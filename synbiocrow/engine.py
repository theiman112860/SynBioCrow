from dataclasses import dataclass,field
from synbiocrow.generators.registry import BackendRegistry,default_registry
from synbiocrow.lifecycle.policy import PromotionPolicy

@dataclass
class SynBioCrowEngine:
    """2.2 consolidation shell; live adapters are migrated incrementally."""
    backends:BackendRegistry=field(default_factory=default_registry)
    promotion_policy:PromotionPolicy=field(default_factory=PromotionPolicy)
    def backend_ids(self)->tuple[str,...]: return self.backends.ids()
