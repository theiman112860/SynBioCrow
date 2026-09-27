from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from synbiocrow.api import SynBioCrowRelease, ReleasePolicyError

@dataclass(frozen=True)
class FrozenPolicyReport:
    passed: bool
    checks: dict[str,bool]
    details: dict[str,Any]

EXPECTED = {
    "benchmark_v2_truth_accessed": False,
    "search_breadth_changed": False,
    "frozen_paper1_baseline_modified": False,
    "candidate_mature_certified_separation": "PRESERVED",
    "specialized_candidate_pathways": 6,
    "specialized_mature_pathways": 0,
    "specialized_certified_pathways": 0,
    "rc1_unique_candidate_constructs": 19,
}

def verify_frozen_2_1(repo_root: str|Path) -> FrozenPolicyReport:
    root=Path(repo_root)
    try:
        release=SynBioCrowRelease(root)
    except Exception as exc:
        return FrozenPolicyReport(
            False,
            {"release_contract_load":False},
            {"error":f"{type(exc).__name__}: {exc}"},
        )

    r=release.readiness
    a=release.abstention
    h=release.handoff
    checks={
        "release_contract_load":True,
        "benchmark_truth_isolated":r.get("benchmark_v2_truth_accessed") is False,
        "search_breadth_unchanged":r.get("search_breadth_changed") is False,
        "paper1_frozen":r.get("frozen_paper1_baseline_modified") is False,
        "lifecycle_separation":r.get("candidate_mature_certified_separation")=="PRESERVED",
        "specialized_counts":(
            r.get("specialized_candidate_pathways")==6
            and r.get("specialized_mature_pathways")==0
            and r.get("specialized_certified_pathways")==0
        ),
        "construct_count":r.get("rc1_unique_candidate_constructs")==19,
        "abstention_preserved":(
            a.get("state")=="CANDIDATE"
            and a.get("certification")=="NOT_CERTIFIED"
            and a.get("decision")=="FREEZE_AS_EXPLICIT_EVIDENCE_ABSTENTION"
            and a.get("search_expansion_authorized") is False
        ),
        "handoff_consistent":(
            h.get("candidate_pathways")==6
            and h.get("mature_pathways")==0
            and h.get("certified_pathways")==0
            and h.get("benchmark_v2_truth_accessed") is False
        ),
        "scientific_payload_not_rerun":(
            release.manifest.get("scientific_payload_changed") is False
            and release.manifest.get("scientific_search_rerun") is False
        ),
    }
    return FrozenPolicyReport(
        passed=all(checks.values()),
        checks=checks,
        details={
            "release":release.manifest.get("release"),
            "version":release.manifest.get("version"),
            "leading_candidate_id":a.get("leading_candidate_id"),
            "leading_rule":a.get("leading_rule"),
        },
    )
