"""Studies compute from sealed data and reopen without consulting current data."""

from datetime import timedelta
from decimal import Decimal
from math import exp, sin
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qap.api.app import create_app
from qap.api.settings import ApiSettings
from qap.market import BarInterval, MarketBar, validate_bar_series
from qap.market.metadata import MarketMetadata
from qap.market.microstructure import public_market_metadata_snapshot_from_metadata
from qap.market.microstructure_storage import append_public_market_metadata_snapshot
from qap.product_lab_metadata import (
    _path as lab_metadata_path,  # pyright: ignore[reportPrivateUsage]
)
from qap.product_market_data import ProductMarketData
from qap.product_market_data_models import (
    MarketDataGenerationInput,
    MarketDataUpstreamSource,
)
from qap.product_market_data_prepare import product_dataset_id
from qap.product_universe import ProductUniverse, ResolvedProductInstrument

from .pair_rotation_support import NOW, publish_directory
from .test_pair_rotation_analysis import prepared as prepared

COMMAND = {
    "coin_a": "binance:W",
    "coin_b": "binance:BTC",
    "bar": "1h",
    "days": 30,
    "band_lookback": 20,
    "settings": {"lookback": 40, "auto_tune": False},
}

# Settings whose sealed varying bars produce real validation rotations.
TRADING_SETTINGS = {"lookback": 40, "auto_tune": False, "entry": 1.0}


def publish_lab_metadata(
    data_root: Path, instruments: tuple[ResolvedProductInstrument, ...]
) -> None:
    """Write canonical immutable venue constraints for the supplied instruments."""
    for instrument in instruments:
        append_public_market_metadata_snapshot(
            lab_metadata_path(data_root, instrument.instrument),
            public_market_metadata_snapshot_from_metadata(
                metadata=MarketMetadata(
                    instrument=instrument.instrument,
                    status="TRADING",
                    price_tick=Decimal("0.000001"),
                    minimum_price=None,
                    maximum_price=None,
                    quantity_step=Decimal("0.000001"),
                    minimum_quantity=None,
                    maximum_quantity=None,
                    minimum_notional=None,
                    maximum_notional=None,
                    minimum_notional_applies_to_market=False,
                    maximum_notional_applies_to_market=False,
                    notional_average_price_minutes=5,
                ),
                observed_at=NOW,
                source_id=f"binance-exchangeInfo:{instrument.instrument.venue_symbol}",
            ),
        )


def varying_study_client(
    root: Path, *, metadata_legs: int = 2, cutoff_shift_hours: int = 0
) -> TestClient:
    """Publish 720 varying sealed bars and up to two venue metadata observations."""
    settings = ApiSettings(run_root=root / "runs", market_data_root=root)
    owner = ProductUniverse(settings.run_root)
    publish_directory(owner)
    scope = owner.research_scope(("binance:W", "binance:BTC"))
    data = ProductMarketData(settings.run_root, root)
    interval = BarInterval("1h")
    observed_at = NOW + timedelta(hours=cutoff_shift_hours)
    end = observed_at.replace(minute=0, second=0, microsecond=0)
    for leg, instrument in enumerate(scope.instruments):
        bars: list[MarketBar] = []
        for index in range(720):
            movement = (
                0.04 * sin(index * 0.3) if leg == 0 else 0.003 * sin(index * 0.17)
            )
            price = exp(index * 0.0001 + movement)
            bars.append(
                MarketBar(
                    instrument=instrument.instrument,
                    interval=interval,
                    candle_open_time=end - timedelta(hours=720 - index),
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1_000_000.0,
                )
            )
        data.publish_generation(
            scope,
            MarketDataGenerationInput(
                dataset_id=product_dataset_id(instrument, interval),
                resolved_instrument=instrument,
                series=validate_bar_series(tuple(bars)),
                acquisition_implementation="offline-lab-contract",
                upstream_sources=(
                    MarketDataUpstreamSource(
                        provider="binance",
                        source_family="offline-contract",
                        source_id=instrument.instrument.venue_symbol,
                        retrieved_at=observed_at,
                        source_fingerprint="1" * 64,
                    ),
                ),
            ),
        )
    publish_lab_metadata(root, scope.instruments[:metadata_legs])
    return TestClient(create_app(settings))


def test_study_returns_walk_forward_proof_and_counts_changed_settings(
    tmp_path: Path,
) -> None:
    client = varying_study_client(tmp_path)
    first = client.post(
        "/api/pair-rotation/studies",
        json=COMMAND | {"settings": {"lookback": 40, "auto_tune": False, "entry": 1.0}},
    )
    assert first.status_code == 200, first.text
    result = first.json()["result"]
    assert result["call"]["status"] == "identity_unresolved"
    assert len(result["folds"]) == 8
    assert result["wealth"]["window_kind"] == "validation"
    assert result["proof"]["settings_tried"] == 1
    assert result["proof"]["control"] in ("daily", "weekly", "drift")
    assert result["proof"]["corrected_p_value"] is not None
    assert "cost_paid_pct" in result["proof"]
    assert "gross_vs_hodl_pct" in result["proof"]
    assert "cost_gate_passed" in result["proof"]
    assert "tuning_cost_pct" in result["proof"]
    assert "tuning_gross_vs_hodl_pct" in result["proof"]
    assert result["trades"]
    assert all(
        trade["fill_index"] == trade["decision_index"] + 1 for trade in result["trades"]
    )
    changed = client.post(
        "/api/pair-rotation/studies",
        json=COMMAND | {"settings": {"lookback": 40, "auto_tune": False, "entry": 1.5}},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["study_id"] != first.json()["study_id"]
    assert changed.json()["result"]["proof"]["settings_tried"] == 2
    assert changed.json()["result"]["proof"]["validation_reused"] is True
    reopened = client.get(f"/api/pair-rotation/studies/{first.json()['study_id']}")
    assert reopened.json() == first.json()


def test_new_cutoff_labels_reuse_without_counting_the_same_settings_again(
    tmp_path: Path,
) -> None:
    client = varying_study_client(tmp_path)
    command = COMMAND | {"settings": TRADING_SETTINGS}
    first = client.post("/api/pair-rotation/studies", json=command)
    assert first.status_code == 200, first.text
    original = first.json()
    assert original["result"]["proof"]["settings_tried"] == 1
    assert original["result"]["proof"]["validation_reused"] is False
    assert client.post("/api/pair-rotation/studies", json=command).json() == original

    varying_study_client(tmp_path, cutoff_shift_hours=1)
    second = client.post("/api/pair-rotation/studies", json=command)
    assert second.status_code == 200, second.text
    updated = second.json()
    assert updated["result"]["proof"]["settings_tried"] == 1
    assert updated["result"]["proof"]["validation_reused"] is True
    assert updated["study_id"] != original["study_id"]
    assert (
        updated["result"]["analysis"]["data_through"]
        != original["result"]["analysis"]["data_through"]
    )
    assert client.post("/api/pair-rotation/studies", json=command).json() == updated
    reopened = client.get(f"/api/pair-rotation/studies/{original['study_id']}")
    assert reopened.status_code == 200, reopened.text
    assert reopened.json() == original


@pytest.mark.parametrize("metadata_legs", [0, 1])
def test_partial_execution_metadata_blocks_the_study(
    tmp_path: Path, metadata_legs: int
) -> None:
    client = varying_study_client(tmp_path, metadata_legs=metadata_legs)
    response = client.post(
        "/api/pair-rotation/studies",
        json=COMMAND | {"settings": TRADING_SETTINGS},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    result = body["result"]
    assert result["call"]["status"] == "execution_data_missing"
    assert result["call"]["target_weight_a"] is None
    assert result["proof"]["passes"] is False
    assert result["proof"]["control"] is None
    assert result["proof"]["raw_p_value"] is None
    assert result["proof"]["corrected_p_value"] is None
    assert result["proof"]["validation_trades"] == 0
    assert result["wealth"]["window_kind"] == "context_only"
    assert set(result["wealth"]["value"]) == {"hodl", "hold_a", "hold_b"}
    assert result["trades"] == []
    assert result["folds"] == []
    assert set(result["statistics"]) == {"hodl", "hold_a", "hold_b"}
    assert len(result["execution_metadata"]) == metadata_legs
    reopened = client.get(f"/api/pair-rotation/studies/{body['study_id']}")
    assert reopened.status_code == 200, reopened.text
    assert reopened.json() == body


def test_create_reopen_pin_and_list_preserve_the_original_result(
    prepared: tuple[TestClient, Path],
) -> None:
    client, root = prepared
    universe = ProductUniverse(root / "runs")
    scope = universe.research_scope(
        ("binance:W", "binance:BTC"), refresh_bindings=False
    )
    publish_lab_metadata(root / "data", scope.instruments)
    response = client.post("/api/pair-rotation/studies", json=COMMAND)
    assert response.status_code == 200, response.text
    body = response.json()
    identifier = body["study_id"]
    assert len(identifier) == 64
    assert body["pinned"] is False
    result = body["result"]
    assert result["analysis"]["bars_used"] == 720
    assert result["call"]["status"] == "insufficient_history"
    assert result["proof"]["passes"] is False
    assert result["proof"]["final_oos_used"] is False
    assert result["proof"]["settings_tried"] == 1
    assert result["wealth"]["window_kind"] == "context_only"
    assert Decimal(result["wealth"]["terminal_values"]["hodl"]) == Decimal("10000")
    assert result["trades"] == []
    assert result["signal"]["values"] == [None] * 720

    snapshot = (
        root / "runs/product/pair-rotation-lab/studies" / identifier / "result.json"
    )
    original = snapshot.read_bytes()
    for pinned in (True, False):
        response = client.post(
            f"/api/pair-rotation/studies/{identifier}/pin", json={"pinned": pinned}
        )
        assert response.status_code == 200, response.text
        assert response.json()["pinned"] is pinned
        assert response.json()["result"] == result
        assert snapshot.read_bytes() == original

    # A saved study reads its own evidence, even after current data becomes invalid.
    for path in (root / "data").rglob("*.parquet"):
        path.write_bytes(b"invalid current generation")
    response = client.get(f"/api/pair-rotation/studies/{identifier}")
    assert response.status_code == 200, response.text
    assert response.json() == body
    response = client.get("/api/pair-rotation/studies")
    assert response.status_code == 200, response.text
    assert response.json()["studies"][0]["study_id"] == identifier
    assert (
        response.json()["studies"][0]["data_through"]
        == result["analysis"]["data_through"]
    )
    assert client.post("/api/pair-rotation/studies", json=COMMAND).status_code == 409

    snapshot.write_bytes(b"tampered snapshot")
    response = client.get(f"/api/pair-rotation/studies/{identifier}")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "lab_saved_result_unavailable"


def test_study_requests_reject_bad_settings_and_missing_data(tmp_path: Path) -> None:
    client = TestClient(
        create_app(ApiSettings(run_root=tmp_path / "runs", market_data_root=tmp_path))
    )
    for change in (
        {"coin_b": "binance:W"},
        {"bar": "2h"},
        {"settings": {"method": "lead_lag"}},
        {"settings": {"entry": 0.1, "exit": 0.5}},
        {"settings": {"fee_bps": 0}},
        {"settings": {"rotation_size": "0.6"}},
        {"settings": {"copula_probability": 0.36, "copula_exit_band": 0.15}},
    ):
        assert (
            client.post("/api/pair-rotation/studies", json=COMMAND | change).status_code
            == 422
        )
    response = client.post("/api/pair-rotation/studies", json=COMMAND)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "lab_study_unavailable"
    response = client.get("/api/pair-rotation/studies/invalid-id")
    assert response.status_code == 409
    assert client.get("/api/pair-rotation/studies").json()["studies"] == []


def test_sample_workspace_refuses_study_and_pin_writes(tmp_path: Path) -> None:
    client = TestClient(
        create_app(ApiSettings(run_root=tmp_path, workspace_mode="sample"))
    )
    for path, body in (
        ("/api/pair-rotation/studies", COMMAND),
        (f"/api/pair-rotation/studies/{'a' * 64}/pin", {"pinned": True}),
    ):
        response = client.post(path, json=body)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "pair_rotation_read_only"
    assert not (tmp_path / "product/pair-rotation-lab").exists()


def test_study_defaults_rotation_size_and_persists_s1_bands(tmp_path: Path) -> None:
    client = varying_study_client(tmp_path)
    response = client.post(
        "/api/pair-rotation/studies",
        json=COMMAND
        | {
            "settings": {
                "lookback": 80,
                "auto_tune": False,
                "method": "trend",
                "trend_deadband": 0.003,
                "copula_exit_band": 0.12,
            }
        },
    )
    assert response.status_code == 200, response.text
    requested = response.json()["result"]["requested_settings"]
    assert Decimal(requested["rotation_size"]) == Decimal("0.5")
    assert requested["trend_deadband"] == pytest.approx(0.003)
    assert requested["copula_exit_band"] == pytest.approx(0.12)
