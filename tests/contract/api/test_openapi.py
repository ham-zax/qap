# pyright: reportUnknownVariableType=false

import json
import subprocess
import sys
from pathlib import Path

from qap.api import ApiSettings, create_app

REPOSITORY_ROOT = Path(__file__).parents[3]


def test_openapi_exposes_stable_operation_ids_and_public_dtos(tmp_path: Path) -> None:
    app = create_app(ApiSettings(run_root=tmp_path / "runs"))
    schema = app.openapi()

    operation_ids = {
        operation["operationId"]
        for methods in schema["paths"].values()
        for operation in methods.values()
        if isinstance(operation, dict) and "operationId" in operation
    }
    assert operation_ids == {
        "getHealth",
        "listExperiments",
        "getExperiment",
        "getPortfolio",
        "getPortfolioPerformance",
        "getPairSeries",
        "getPairEvidence",
        "getAnchorLens",
        "listPaperOperations",
        "getPaperOperation",
    }

    schemas = set(schema["components"]["schemas"])
    assert {
        "RunSummaryDto",
        "ExperimentDetailDto",
        "PortfolioSnapshotDto",
        "PortfolioPerformanceDto",
        "PairEvidenceDto",
        "PairSeriesDto",
        "AnchorLensDto",
        "RebalanceDecisionAuditDto",
        "PaperOperationSummaryDto",
        "PaperOperationDetailDto",
    } <= schemas


def test_openapi_export_script_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    command = [
        sys.executable,
        str(REPOSITORY_ROOT / "scripts" / "export_openapi.py"),
    ]

    subprocess.run([*command, str(first)], cwd=REPOSITORY_ROOT, check=True)
    subprocess.run([*command, str(second)], cwd=REPOSITORY_ROOT, check=True)

    assert first.read_bytes() == second.read_bytes()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["info"]["title"] == "QAP Research Evidence API"
    assert payload["paths"]["/api/experiments"]["get"]["operationId"] == (
        "listExperiments"
    )
