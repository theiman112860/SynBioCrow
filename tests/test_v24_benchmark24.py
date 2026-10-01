from synbiocrow.v24.benchmark24 import (
    Benchmark24Plan,
    Benchmark24Record,
    AssignedBenchmark24Record,
    build_plan,
    deterministic_family_split,
)
from synbiocrow.v24.manifests import BenchmarkSplit
from synbiocrow.v24.truthlock import TruthLock


def rec(i, family, historical=False):
    return Benchmark24Record(
        record_id=f"r{i}",
        target_id=f"t{i}",
        target_name=f"target-{i}",
        normalized_target=f"SMILES-{i}",
        family_id=family,
        source_ids=(f"source-{i}",),
        historical_23_member=historical,
    )


def test_family_assignment_is_deterministic():
    a = deterministic_family_split("family-A")
    b = deterministic_family_split("family-A")
    assert a == b


def test_same_family_cannot_cross_splits():
    p = Benchmark24Plan(
        benchmark_id="b", version="1", split_salt="s",
        assignments=[
            AssignedBenchmark24Record(rec(1, "fam"), BenchmarkSplit.DEVELOPMENT),
            AssignedBenchmark24Record(rec(2, "fam"), BenchmarkSplit.EVALUATION),
        ],
    )
    try:
        p.validate()
    except ValueError as exc:
        assert "family leakage" in str(exc)
    else:
        raise AssertionError("expected family leakage failure")


def test_historical_23_cannot_be_tunable():
    p = Benchmark24Plan(
        benchmark_id="b", version="1", split_salt="s",
        assignments=[
            AssignedBenchmark24Record(rec(1, "fam", True), BenchmarkSplit.DEVELOPMENT),
        ],
    )
    try:
        p.validate()
    except ValueError as exc:
        assert "frozen 2.3" in str(exc)
    else:
        raise AssertionError("expected historical leakage failure")


def test_build_plan_keeps_family_together():
    plan = build_plan([rec(1, "fam"), rec(2, "fam"), rec(3, "other")])
    fam_splits = {x.split for x in plan.assignments if x.record.family_id == "fam"}
    assert len(fam_splits) == 1


def test_truth_lock_requires_predate_seal():
    lock = TruthLock("b", 10, "a"*64, False)
    try:
        lock.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("expected truth-lock failure")
