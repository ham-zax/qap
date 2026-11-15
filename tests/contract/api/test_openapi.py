# pyright: reportUnknownVariableType=false

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

from qap.api import ApiSettings, create_app

REPOSITORY_ROOT = Path(__file__).parents[3]

RETIRED_PATH_PREFIXES = (
    "/api/basket-runs",
    "/api/baskets",
    "/api/captures",
    "/api/forward",
    "/api/history",
    "/api/product-pair-study",
    "/api/product-research",
    "/api/qualifications",
    "/api/research-recipes",
    "/api/scanner",
    "/api/scans",
)


def test_openapi_exposes_stable_operation_ids_and_public_dtos(tmp_path: Path) -> None:
    app = create_app(ApiSettings(run_root=tmp_path / "runs"))
    schema = app.openapi()

    declared_operation_ids = [
        cast(str, operation["operationId"])
        for methods in schema["paths"].values()
        for operation in methods.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(declared_operation_ids) == len(set(declared_operation_ids))
    operation_ids = set(declared_operation_ids)
    assert {
        "getAnchorLens",
        "getExperiment",
        "getHealth",
        "getOperation",
        "getPairEvidence",
        "getPairSeries",
        "getPaperOperation",
        "getPortfolio",
        "getPortfolioPerformance",
        "getResearchUniverse",
        "listExperiments",
        "listOperations",
        "listPaperOperations",
        "refreshResearchUniverseDirectory",
    } <= operation_ids

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
        "OperationDto",
        "WorkspaceStatusDto",
        "ResearchUniverseDto",
        "ProductMarketDataDto",
        "LabStudyDto",
        "LabStudyRequestDto",
        "LabStudyResultDto",
        "LabAnalysisDto",
        "LabSettings-Input",
        "LabSettings-Output",
    } <= schemas


def test_openapi_retires_legacy_workbench_surfaces(tmp_path: Path) -> None:
    app = create_app(ApiSettings(run_root=tmp_path / "runs"))
    schema = app.openapi()

    retired = sorted(
        path
        for path in schema["paths"]
        if any(
            path == prefix or path.startswith(f"{prefix}/")
            for prefix in RETIRED_PATH_PREFIXES
        )
    )
    assert retired == []


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
    assert payload["info"]["title"] == "QAP Research Application API"
    assert payload["paths"]["/api/experiments"]["get"]["operationId"] == (
        "listExperiments"
    )
