from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qap.api.errors import ApiBoundaryError
from qap.api.paper_operation_views import PaperOperationReader
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
    assert summary["artifact_status"] == "valid"
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
    assert payload["evidence_class"] == "operational_dry_run"
    assert payload["prospective_candidate_evidence"] is False
    assert payload["bridge"] == "USDT"
    assert payload["fee_bps"] == "10"
    assert payload["slippage_bps"] == "10"
    assert len(payload["code_fingerprint"]) == 64
    assert payload["market_notional_reference_prices"] == {
        "BTCUSDT": "63643.03000000",
        "ETHUSDT": "1906.42000000",
        "SOLUSDT": "75.80000000",
    }
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
    assert payload["market_metadata"]["ETHUSDT"]["market_maximum_quantity"] == (
        "2870.37341004"
    )
    assert {item["asset"] for item in payload["tracking_errors"]} == {
        "BTC",
        "ETH",
        "SOL",
        "USDT",
    }
    assert payload["reconciliation"]["economic_differences"] == []
    assert (
        payload["reconciliation"]["recomputed_fee_total"] == payload["total_fee_quote"]
    )
    assert (
        payload["reconciliation"]["expected_terminal_value"]
        == payload["reconciliation"]["recomputed_terminal_value"]
    )
    assert payload["research_boundary"]["eligible_for_parameter_selection"] is False
    assert payload["research_boundary"]["eligible_for_deployment_evidence"] is False


def test_paper_operation_reader_rejects_parent_path_escape(tmp_path: Path) -> None:
    root = tmp_path / "paper-operations"
    generated = run_paper_operation_to_artifact(
        SPEC,
        repository_root=ROOT,
        output_root=root,
    )
    (tmp_path / "paper_operation.json").write_bytes(
        generated.operation_file.read_bytes()
    )

    reader = PaperOperationReader(root)
    with pytest.raises(ApiBoundaryError) as error:
        reader.detail("..")

    assert error.value.status_code == 404
    assert error.value.code == "paper_operation_not_found"


def test_paper_operation_list_surfaces_corrupt_entry_without_hiding_valid(
    paper_operation_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, operation_id = paper_operation_run_root
    corrupt = run_root / "paper-operations" / "broken-operation"
    corrupt.mkdir()
    (corrupt / "paper_operation.json").write_text("{broken", encoding="utf-8")
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=ROOT))
    )

    response = client.get("/api/paper-operations")

    assert response.status_code == 200
    items = {item["operation_id"]: item for item in response.json()}
    assert items[operation_id]["artifact_status"] == "valid"
    assert items["broken-operation"]["artifact_status"] == "invalid"
    assert items["broken-operation"]["error"]["code"] == "corrupt_paper_operation"


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
