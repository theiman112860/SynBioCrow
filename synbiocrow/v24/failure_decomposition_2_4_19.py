"""SynBioCrow 2.4.19 development-only failure-mode decomposition.

Consumes the corrected 2.4.18.1 audit and frozen 2.4.16 ranking.  It does not
alter ranking or generation.  It quantifies whether each development target is
primarily limited by candidate-space coverage, ranking placement, or both.
"""
from __future__ import annotations
from typing import Any,Mapping
import math

def percentile(rank:int|None,n:int)->float|None:
    if rank is None or n<=0:return None
    return (rank-1)/max(1,n-1)

def classify(best_similarity:float|None,best_rank:int|None,n:int,
             near_threshold:float=.45,good_rank:int=50)->str:
    if best_similarity is None:return "NO_MEASURABLE_INTERNAL_ANCHOR"
    near=best_similarity>=near_threshold
    ranked=best_rank is not None and best_rank<=good_rank
    if near and ranked:return "CANDIDATE_PRESENT_AND_RANKED"
    if near and not ranked:return "RANKING_LIMITED"
    if (not near) and ranked:return "GENERATION_COVERAGE_LIMITED"
    return "GENERATION_AND_RANKING_LIMITED"

def decompose(record:Mapping[str,Any],candidate_count:int)->dict:
    s=record.get("best_internal_anchor_similarity_mean")
    r=record.get("best_candidate_rank_2_4_16")
    return {
      "record_id":record["record_id"],"target_name":record.get("target_name"),
      "candidate_count":candidate_count,"best_internal_anchor_similarity_mean":s,
      "best_candidate_rank_2_4_16":r,"best_candidate_rank_percentile":percentile(r,candidate_count),
      "failure_mode":classify(s,r,candidate_count),
      "near_miss_threshold":0.45,"good_rank_threshold":50,
    }
