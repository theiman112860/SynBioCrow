from dataclasses import dataclass,field
from collections.abc import Iterable
from synbiocrow.generators.registry import BackendRegistry,default_registry
from synbiocrow.lifecycle.policy import PromotionPolicy
from synbiocrow.core.models import PathwayCandidate
from synbiocrow.ensemble import build_reaction_graph, EnsembleGraph
from synbiocrow.evidence import evaluate_route_evidence, RouteEvidenceReport
from synbiocrow.design import design_expression_construct, ConstructDesignResult
from synbiocrow.learning import (
    LearningPolicy, TestOutcome, PolicyUpdate,
    apply_test_outcomes, rank_routes, rank_constructs, LearningAuditLog,
)

@dataclass
class SynBioCrowEngine:
    """2.2 consolidated engine."""
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

    def evaluate_route(self, graph:EnsembleGraph, edge_ids:Iterable[str], **kwargs)->RouteEvidenceReport:
        return evaluate_route_evidence(graph, edge_ids, **kwargs)

    def design_construct(self, **kwargs)->ConstructDesignResult:
        return design_expression_construct(**kwargs)

    def learn(
        self,
        policy:LearningPolicy,
        outcomes:Iterable[TestOutcome],
        *,
        learning_rate:float=0.10,
        audit_log:str|None=None,
    )->tuple[LearningPolicy,PolicyUpdate]:
        outcomes=tuple(outcomes)
        new_policy,update=apply_test_outcomes(
            policy,outcomes,learning_rate=learning_rate
        )
        if audit_log:
            LearningAuditLog(audit_log).append(
                policy_before=policy,
                policy_after=new_policy,
                update=update,
                outcomes=outcomes,
            )
        return new_policy,update

    def rank_routes(
        self,
        route_features:dict[str,dict[str,float]],
        policy:LearningPolicy,
    )->list[tuple[str,float]]:
        return rank_routes(route_features,policy)

    def rank_constructs(
        self,
        construct_features:dict[str,dict[str,float]],
        policy:LearningPolicy,
    )->list[tuple[str,float]]:
        return rank_constructs(construct_features,policy)
