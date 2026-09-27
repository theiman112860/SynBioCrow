from __future__ import annotations
import json, hashlib
from pathlib import Path
from typing import Any, Dict

class ReleasePolicyError(RuntimeError):
    pass

def _load(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

class SynBioCrowRelease:
    """Read-only stable API over the sealed SynBioCrow 2.1 scientific release."""

    def __init__(self, release_dir: str | Path):
        root = Path(release_dir)
        nested = root / "release" / "2.1.0"
        self.release_dir = nested if (nested / "release_manifest.json").exists() else root
        self.manifest = _load(self.release_dir / "release_manifest.json")
        self.readiness = _load(self.release_dir / "release_readiness_manifest.json")
        self.abstention = _load(self.release_dir / "specialized_generator_abstention_ledger.json")
        self.handoff = _load(self.release_dir / "ensemble_release_handoff.json")
        self._validate_frozen_contract()

    def _validate_frozen_contract(self) -> None:
        r, a, h = self.readiness, self.abstention, self.handoff
        checks = {
            "benchmark_v2_truth_accessed": r.get("benchmark_v2_truth_accessed") is False,
            "search_breadth_changed": r.get("search_breadth_changed") is False,
            "frozen_paper1_baseline_modified": r.get("frozen_paper1_baseline_modified") is False,
            "candidate_separation": r.get("candidate_mature_certified_separation") == "PRESERVED",
            "specialized_candidates": r.get("specialized_candidate_pathways") == 6,
            "specialized_mature": r.get("specialized_mature_pathways") == 0,
            "specialized_certified": r.get("specialized_certified_pathways") == 0,
            "rc1_constructs": r.get("rc1_unique_candidate_constructs") == 19,
            "abstention_state": a.get("state") == "CANDIDATE" and a.get("certification") == "NOT_CERTIFIED",
            "handoff_state": h.get("candidate_pathways") == 6 and h.get("mature_pathways") == 0 and h.get("certified_pathways") == 0,
        }
        failed = [k for k, v in checks.items() if not v]
        if failed:
            raise ReleasePolicyError("Frozen release contract violated: " + ", ".join(failed))

    def status(self) -> Dict[str, Any]:
        return {
            "version": self.manifest["version"],
            "release": self.manifest["release"],
            "release_status": self.manifest.get("release_status", "FINAL"),
            "integrated_regression": self.manifest["integrated_regression"],
            "api_package": self.manifest["api_package"],
            "documentation": self.manifest["documentation"],
            "github_release_assembly": self.manifest["github_release_assembly"],
            "unique_candidate_constructs": self.readiness["rc1_unique_candidate_constructs"],
            "specialized_candidate_pathways": self.readiness["specialized_candidate_pathways"],
        }

    def policies(self) -> Dict[str, Any]:
        return dict(self.manifest["frozen_policies"])

    def specialized_summary(self) -> Dict[str, Any]:
        return {
            "candidate": self.readiness["specialized_candidate_pathways"],
            "mature": self.readiness["specialized_mature_pathways"],
            "certified": self.readiness["specialized_certified_pathways"],
            "leading_candidate_id": self.abstention["leading_candidate_id"],
            "leading_rule": self.abstention["leading_rule"],
            "decision": self.abstention["decision"],
            "reason_codes": list(self.abstention["reason_codes"]),
        }

    def abstention_ledger(self) -> Dict[str, Any]:
        return dict(self.abstention)

    def provenance(self) -> Dict[str, Any]:
        return dict(self.manifest["provenance"])

    def verify_files(self) -> Dict[str, bool]:
        results = {}
        for rel, expected in self.manifest.get("file_sha256", {}).items():
            p = self.release_dir / rel
            results[rel] = p.exists() and _sha256_file(p) == expected
        return results
