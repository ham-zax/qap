from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qap.experiment.paper_operation import run_paper_operation_to_artifact

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "tests/fixtures/paper/four_asset_forward_paper.json"


@pytest.fixture
def paper_operation_run_root(tmp_path: Path) -> tuple[Path, str]:
    run_root = tmp_path / "runs"
    artifact = run_paper_operation_to_artifact(
        SPEC,
        repository_root=ROOT,
        output_root=run_root / "paper-operations",
    )
    return run_root, artifact.operation_id


def test_paper_operation_list_surfaces_forward_paper_and_cost_context(
    paper_operation_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, operation_id = paper_operation_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=ROOT))
    )

    response = client.get("/api/paper-operations")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    summary = payload[0]
    assert summary["operation_id"] == operation_id
    assert summary["data_role"] == "forward_paper"
    assert summary["reconciliation_matches"] is True
    assert summary["fill_count"] == 3
    assert isinstance(summary["total_fee_quote"], str)
    assert isinstance(summary["total_slippage_quote"], str)
    assert isinstance(summary["bridge_residual"], str)
    assert len(summary["route_ids"]) == 3


def test_paper_operation_detail_preserves_routes_precision_and_research_boundary(
    paper_operation_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, operation_id = paper_operation_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=ROOT))
    )

    response = client.get(f"/api/paper-operations/{operation_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["operation_id"] == operation_id
    assert payload["data_role"] == "forward_paper"
    assert payload["bridge"] == "USDT"
    assert payload["reconciliation_matches"] is True
    assert [item["phase"] for item in payload["orders"]] == [
        "sell_to_bridge",
        "sell_to_bridge",
        "buy_from_bridge",
    ]
    assert all(item["route_id"].startswith("direct:") for item in payload["orders"])
    assert set(payload["market_metadata"]) == {"BTCUSDT", "ETHUSDT", "SOLUSDT"}
    assert all(
        isinstance(item["quantity_step"], str)
        for item in payload["market_metadata"].values()
    )
    assert payload["research_boundary"]["eligible_for_parameter_selection"] is False
    assert payload["research_boundary"]["eligible_for_deployment_evidence"] is False


def test_missing_paper_operation_has_stable_error_envelope(tmp_path: Path) -> None:
    from qap.api import ApiSettings, create_app

    client = TestClient(
        create_app(ApiSettings(run_root=tmp_path / "runs", market_data_root=ROOT))
    )

    response = client.get("/api/paper-operations/missing-operation")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "paper_operation_not_found",
            "message": "Paper operation was not found.",
            "context": {"operation_id": "missing-operation"},
        }
    }
