import json
import zipfile

import pytest

pytestmark = pytest.mark.integration


def test_blocked_candidate_flow_produces_auditable_outputs(alpha90, tmp_path):
    candidate = tmp_path / "ordinary_source.zip"
    with zipfile.ZipFile(candidate, "w") as z:
        z.writestr("README.txt", "ordinary source tree without canonical benchmark provenance")

    work = tmp_path / "certification"
    summary, output_zip = alpha90.run(work, [candidate])

    assert summary["state"] == "BLOCKED_PENDING_CANONICAL_BENCHMARK_ARTIFACTS"
    assert summary["alpha90_2_allowed"] is False
    assert summary["run_synbiocrow"] is False
    assert summary["external_benchmark_tuning"] is False

    saved = json.loads((work / "alpha90_1_2_3_summary.json").read_text())
    assert saved["alpha90_2_allowed"] is False
    assert (work / "alpha90_1_2_3_candidate_audit.csv").exists()
    assert (work / "alpha90_1_2_3_semantic_audit.csv").exists()
    assert (work / "ALPHA90_1_2_3_CERTIFICATION_REPORT.md").exists()
    assert output_zip.exists()

    with zipfile.ZipFile(output_zip) as z:
        names = set(z.namelist())
    assert any(name.endswith("alpha90_1_2_3_summary.json") for name in names)
    assert any(name.endswith("ALPHA90_1_2_3_CERTIFICATION_REPORT.md") for name in names)
