"""Fail-closed import contract for the frozen SynBioCrow 2.3 Galaxy holdout.

The 65-path Galaxy benchmark is historical-only in the 2.4 line.
This module validates frozen metadata/scored summaries when supplied, but it
never exposes a tuning API.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

FROZEN_DENOMINATOR = 65
FROZEN_RUNNABLE = 64
FROZEN_MAPPING_LIMITED_ID = "literature_10"

FROZEN_EXPECTED = {
    "ensemble_partial": 19,
    "retrobiocat2_partial": 13,
    "retropath_partial": 9,
    "doranet_partial": 0,
    "ensemble_exact_top50": 2,
    "retropath_exact_top50": 2,
    "ensemble_exact_top10": 0,
    "retropath_exact_top10": 0,
}

FROZEN_HASHES = {
    "sealed_predictions": "68fbf9440eecf3103ca70734bc7d71514978fbeab008ba0ab1734cab030f1200",
    "scored_benchmark": "4ccfb292295e9017098c061b36baacf1fcacf8ff95182a114b66ee4d7977d809",
    "error_analysis": "c7c960a866e3347e7355773648fc875243778a6e6f8ecbc8f2f7937ebefdd764",
}


@dataclass(frozen=True)
class HistoricalGalaxy23Summary:
    denominator: int
    runnable: int
    mapping_limited_id: str
    metrics: Dict[str, int]
    source_sha256: Optional[str] = None
    historical_only: bool = True
    tuning_permitted: bool = False

    def validate(self) -> None:
        if self.denominator != FROZEN_DENOMINATOR:
            raise ValueError("unexpected Galaxy 2.3 denominator")
        if self.runnable != FROZEN_RUNNABLE:
            raise ValueError("unexpected Galaxy 2.3 runnable count")
        if self.mapping_limited_id != FROZEN_MAPPING_LIMITED_ID:
            raise ValueError("unexpected Galaxy 2.3 mapping-limited target")
        for key, expected in FROZEN_EXPECTED.items():
            if key in self.metrics and int(self.metrics[key]) != expected:
                raise ValueError(
                    f"historical metric mismatch for {key}: "
                    f"{self.metrics[key]} != {expected}"
                )


def frozen_reference_summary() -> HistoricalGalaxy23Summary:
    out = HistoricalGalaxy23Summary(
        denominator=FROZEN_DENOMINATOR,
        runnable=FROZEN_RUNNABLE,
        mapping_limited_id=FROZEN_MAPPING_LIMITED_ID,
        metrics=dict(FROZEN_EXPECTED),
    )
    out.validate()
    return out


def load_summary_json(path: str) -> HistoricalGalaxy23Summary:
    """Load only an explicit aggregate historical summary.

    This function intentionally does not accept arbitrary per-target truth rows.
    """
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    required = ("denominator", "runnable", "mapping_limited_id", "metrics")
    missing = [k for k in required if k not in obj]
    if missing:
        raise ValueError(f"missing required historical-summary fields: {missing}")
    out = HistoricalGalaxy23Summary(
        denominator=int(obj["denominator"]),
        runnable=int(obj["runnable"]),
        mapping_limited_id=str(obj["mapping_limited_id"]),
        metrics={str(k): int(v) for k, v in dict(obj["metrics"]).items()},
        source_sha256=obj.get("source_sha256"),
    )
    out.validate()
    return out
