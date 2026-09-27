from __future__ import annotations
import hashlib
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Iterable

from synbiocrow.core.models import PathwayCandidate, ReactionStep
from .identity import CompoundIdentity, resolve_compound

def pathway_fingerprint(candidate:PathwayCandidate)->str:
    payload="\n".join(step.reaction.strip() for step in candidate.steps)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def union_candidates(candidates:Iterable[PathwayCandidate])->list[PathwayCandidate]:
    by_fp={}
    for candidate in candidates:
        by_fp.setdefault(pathway_fingerprint(candidate),candidate)
    return [by_fp[k] for k in sorted(by_fp)]

@dataclass(frozen=True)
class ReactionEdge:
    edge_id: str
    parent_key: str
    precursor_keys: tuple[str,...]
    reaction: str
    rule_ids: tuple[str,...]
    source_backends: tuple[str,...]
    candidate_ids: tuple[str,...]
    provenance: tuple[dict,...]=()

@dataclass
class EnsembleGraph:
    compounds: dict[str,CompoundIdentity]=field(default_factory=dict)
    edges: dict[str,ReactionEdge]=field(default_factory=dict)
    by_parent: dict[str,list[str]]=field(default_factory=lambda: defaultdict(list))

    def add_edge(self, edge:ReactionEdge, compounds:Iterable[CompoundIdentity])->None:
        for c in compounds:
            self.compounds.setdefault(c.key,c)
        if edge.edge_id in self.edges:
            old=self.edges[edge.edge_id]
            self.edges[edge.edge_id]=ReactionEdge(
                edge_id=old.edge_id,
                parent_key=old.parent_key,
                precursor_keys=old.precursor_keys,
                reaction=old.reaction,
                rule_ids=tuple(sorted(set(old.rule_ids+edge.rule_ids))),
                source_backends=tuple(sorted(set(old.source_backends+edge.source_backends))),
                candidate_ids=tuple(sorted(set(old.candidate_ids+edge.candidate_ids))),
                provenance=old.provenance+edge.provenance,
            )
        else:
            self.edges[edge.edge_id]=edge
            self.by_parent[edge.parent_key].append(edge.edge_id)

    def backend_set(self)->tuple[str,...]:
        return tuple(sorted({b for e in self.edges.values() for b in e.source_backends}))

    def composite_edge_count(self)->int:
        return sum(1 for e in self.edges.values() if len(e.source_backends)>1)

    def find_routes(self, target_key:str, sink_keys:set[str], *, max_steps:int=8, max_routes:int=100)->list[list[str]]:
        routes=[]
        queue=deque([(frozenset([target_key]), tuple())])
        seen=set()
        while queue and len(routes)<max_routes:
            frontier, used=queue.popleft()
            if frontier.issubset(sink_keys):
                routes.append(list(used)); continue
            if len(used)>=max_steps:
                continue
            state=(frontier,used)
            if state in seen: continue
            seen.add(state)
            unresolved=sorted(frontier-sink_keys)[0]
            for eid in sorted(self.by_parent.get(unresolved,())):
                edge=self.edges[eid]
                new_frontier=set(frontier)
                new_frontier.remove(unresolved)
                new_frontier.update(edge.precursor_keys)
                queue.append((frozenset(new_frontier),used+(eid,)))
        return routes

def _split_reaction(step:ReactionStep)->tuple[list[str],list[str]]:
    if "=" not in step.reaction:
        raise ValueError(f"ReactionStep lacks '=' separator: {step.reaction!r}")
    left,right=step.reaction.split("=",1)
    return ([x.strip() for x in left.split("+") if x.strip()],
            [x.strip() for x in right.split("+") if x.strip()])

def _parent_side(step:ReactionStep)->str:
    explicit=step.metadata.get("retrosynthetic_parent_side") if step.metadata else None
    if explicit in {"left","right"}: return explicit
    if step.source_backend=="retrobiocat2": return "left"
    if step.source_backend=="doranet":
        return "left" if step.metadata.get("direction","retro")=="retro" else "right"
    if step.source_backend=="retropath2": return "right"
    return "left"

def build_reaction_graph(candidates:Iterable[PathwayCandidate])->EnsembleGraph:
    graph=EnsembleGraph()
    for cand in candidates:
        for step in cand.steps:
            left,right=_split_reaction(step)
            side=_parent_side(step)
            parent_tokens=left if side=="left" else right
            precursor_tokens=right if side=="left" else left
            for parent_token in parent_tokens:
                parent=resolve_compound(parent_token,source=step.source_backend)
                precursors=tuple(resolve_compound(x,source=step.source_backend) for x in precursor_tokens)
                payload="\n".join([parent.key,*sorted(p.key for p in precursors)])
                eid="rxn:"+hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
                graph.add_edge(
                    ReactionEdge(
                        edge_id=eid,
                        parent_key=parent.key,
                        precursor_keys=tuple(sorted(p.key for p in precursors)),
                        reaction=step.reaction,
                        rule_ids=tuple([step.rule_id] if step.rule_id else ()),
                        source_backends=tuple(sorted(set(cand.source_backends or ((step.source_backend or "unknown"),)))),
                        candidate_ids=(cand.candidate_id,),
                        provenance=(dict(step.metadata or {}),),
                    ),
                    (parent,*precursors),
                )
    for key in list(graph.by_parent):
        graph.by_parent[key]=sorted(set(graph.by_parent[key]))
    return graph
