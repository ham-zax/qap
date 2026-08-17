# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPOSITORY_ROOT = Path(__file__).parents[3]


def test_pair_series_preserves_canonical_identity_and_explicit_orientation(
    pair_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = pair_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    forward = client.get(
        f"/api/pairs/ETH/BTC/series?run_id={run_id}&orientation=ETH/BTC"
    )
    reverse = client.get(
        f"/api/pairs/ETH/BTC/series?run_id={run_id}&orientation=BTC/ETH"
    )

    assert forward.status_code == 200
    assert reverse.status_code == 200
    forward_payload = forward.json()
    reverse_payload = reverse.json()
    assert forward_payload["schema_version"] == "qap.api.pair_series.v1"
    assert forward_payload["canonical_pair"] == ["BTC", "ETH"]
    assert reverse_payload["canonical_pair"] == ["BTC", "ETH"]
    assert forward_payload["requested_orientation"] == "ETH/BTC"
    assert reverse_payload["requested_orientation"] == "BTC/ETH"
    assert forward_payload["fit_reciprocity"] == "exact_transform"
    assert forward_payload["evidence_reciprocity"] == "exact_transform"
    assert forward_payload["base_source_fingerprint"] == (
        "6b8937160dfe5d523e06937cb2c175934487b59fd77605b439e8bad7b1a79426"
    )
    assert forward_payload["quote_source_fingerprint"] == (
        "1443f2d96c061b5d143242d84821de94f67d05e9eaca64c7eb1f89c12b655cff"
    )
    assert forward_payload["ratio"][0]["value"] == pytest.approx(2205.0 / 42050.0)
    assert reverse_payload["ratio"][0]["value"] == pytest.approx(42050.0 / 2205.0)
    assert (
        forward_payload["ratio"][0]["value"] * reverse_payload["ratio"][0]["value"]
    ) == pytest.approx(1.0)
    assert (
        forward_payload["log_ratio"][0]["value"]
        + reverse_payload["log_ratio"][0]["value"]
    ) == pytest.approx(0.0, abs=1e-12)
    assert forward_payload["normalized_base"][0]["value"] == 1.0
    assert forward_payload["normalized_quote"][0]["value"] == 1.0


def test_pair_series_includes_persisted_strategy_rebalance_markers(
    pair_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = pair_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    response = client.get(
        f"/api/pairs/ETH/BTC/series?run_id={run_id}&orientation=ETH/BTC"
    )

    assert response.status_code == 200
    markers = response.json()["rebalance_markers"]
    assert markers == []


def test_pair_series_rejects_orientation_not_matching_path_assets(
    pair_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = pair_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    response = client.get(
        f"/api/pairs/ETH/BTC/series?run_id={run_id}&orientation=ETH/USDT"
    )

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "invalid_pair_orientation",
        "message": "Pair orientation does not match the requested assets.",
        "context": {"asset_x": "ETH", "asset_y": "BTC", "orientation": "ETH/USDT"},
    }


def test_anchor_lens_uses_committed_common_reference_and_rejects_unknown_anchor(
    pair_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = pair_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    response = client.get(f"/api/pairs/ETH/BTC/anchor?run_id={run_id}&anchor=USDT")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "qap.api.anchor_lens.v1"
    assert payload["canonical_pair"] == ["BTC", "ETH"]
    assert payload["requested_orientation"] == "ETH/BTC"
    assert payload["anchor"] == "USDT"
    assert payload["reduction"] == "none"
    assert payload["anchor_source_fingerprint"] is None
    assert payload["pair_ratio"][0]["value"] == pytest.approx(2205.0 / 42050.0)
    assert payload["base_to_anchor"][0]["value"] == 2205.0
    assert payload["quote_to_anchor"][0]["value"] == 42050.0
    assert math.isfinite(payload["max_ratio_decomposition_error"])
    assert payload["max_ratio_decomposition_error"] <= 1e-12

    unavailable = client.get(f"/api/pairs/ETH/BTC/anchor?run_id={run_id}&anchor=SOL")
    assert unavailable.status_code == 404
    assert unavailable.json()["error"] == {
        "code": "anchor_unavailable",
        "message": "Anchor series is unavailable for this run.",
        "context": {"run_id": run_id, "anchor": "SOL"},
    }
