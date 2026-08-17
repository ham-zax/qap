# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPOSITORY_ROOT = Path(__file__).parents[3]


def test_pair_evidence_reads_persisted_model_observations_without_recomputation(
    model_evidence_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = model_evidence_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    response = client.get(
        f"/api/pairs/BTC/USDT/evidence?run_id={run_id}&orientation=BTC/USDT"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "qap.api.pair_evidence.v1"
    assert payload["canonical_pair"] == ["BTC", "USDT"]
    assert payload["requested_orientation"] == "BTC/USDT"
    assert len(payload["series"]) == 1
    evidence = payload["series"][0]
    assert evidence["persisted_orientation"] == "BTC/USDT"
    assert evidence["model_id"] == "rolling_log_ratio_zscore"
    assert evidence["model_version"] == "1"
    assert evidence["evidence_field"] == "score"
    assert evidence["fit_reciprocity"] == "exact_transform"
    assert evidence["evidence_reciprocity"] == "exact_transform"
    assert len(evidence["points"]) == 12
    assert evidence["points"][0]["status"] == "insufficient_history"
    assert evidence["points"][0]["value"] is None
    assert evidence["points"][2]["status"] == "valid"
    assert isinstance(evidence["points"][2]["value"], float)
    assert len(evidence["points"][2]["input_fingerprint"]) == 64


def test_pair_evidence_reorients_exact_reciprocal_model_scores(
    model_evidence_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = model_evidence_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    forward = client.get(
        f"/api/pairs/BTC/USDT/evidence?run_id={run_id}&orientation=BTC/USDT"
    )
    reverse = client.get(
        f"/api/pairs/BTC/USDT/evidence?run_id={run_id}&orientation=USDT/BTC"
    )

    assert forward.status_code == 200
    assert reverse.status_code == 200
    forward_points = forward.json()["series"][0]["points"]
    reverse_points = reverse.json()["series"][0]["points"]
    for direct, reciprocal in zip(forward_points, reverse_points, strict=True):
        assert reciprocal["status"] == direct["status"]
        if direct["value"] is None:
            assert reciprocal["value"] is None
        else:
            assert reciprocal["value"] == pytest.approx(-direct["value"], abs=1e-12)


def test_pair_evidence_is_empty_for_model_free_run(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = populated_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    response = client.get(
        f"/api/pairs/BTC/USDT/evidence?run_id={run_id}&orientation=BTC/USDT"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["canonical_pair"] == ["BTC", "USDT"]
    assert payload["requested_orientation"] == "BTC/USDT"
    assert payload["series"] == []


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
    assert forward_payload["available_anchors"] == ["BTC", "ETH", "USDT"]
    assert forward_payload["identity_coordinate_assets"] == ["USDT"]
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


def test_pair_series_chart_points_use_observation_availability_time(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = populated_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    response = client.get(
        f"/api/pairs/BTC/USDT/series?run_id={run_id}&orientation=BTC/USDT"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ratio"][0]["timestamp"] == "2024-01-01T01:00:00Z"
    selected = next(
        marker for marker in payload["rebalance_markers"] if marker["selected"]
    )
    assert selected["timestamp"] == payload["ratio"][1]["timestamp"]


def test_pair_series_supports_the_run_common_quote_as_an_identity_leg(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app
    from qap.portfolio import AssetId
    from qap.relationship import identity_source_fingerprint

    run_root, run_id = populated_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    direct = client.get(
        f"/api/pairs/BTC/USDT/series?run_id={run_id}&orientation=BTC/USDT"
    )
    reverse = client.get(
        f"/api/pairs/BTC/USDT/series?run_id={run_id}&orientation=USDT/BTC"
    )

    assert direct.status_code == 200
    assert reverse.status_code == 200
    direct_payload = direct.json()
    reverse_payload = reverse.json()
    identity_fingerprint = identity_source_fingerprint(AssetId("USDT"))
    assert direct_payload["canonical_pair"] == ["BTC", "USDT"]
    assert direct_payload["available_anchors"] == ["BTC", "USDT"]
    assert direct_payload["identity_coordinate_assets"] == ["USDT"]
    assert direct_payload["quote_source_fingerprint"] == identity_fingerprint
    assert reverse_payload["base_source_fingerprint"] == identity_fingerprint
    assert all(point["value"] == 1.0 for point in direct_payload["normalized_quote"])
    assert (
        direct_payload["ratio"][0]["value"] * reverse_payload["ratio"][0]["value"]
    ) == pytest.approx(1.0)

    anchor = client.get(
        f"/api/pairs/BTC/USDT/anchor?run_id={run_id}&anchor=USDT&orientation=BTC/USDT"
    )
    assert anchor.status_code == 200
    anchor_payload = anchor.json()
    assert anchor_payload["reduction"] == "anchor_is_quote"
    assert anchor_payload["quote_source_fingerprint"] == identity_fingerprint
    assert anchor_payload["anchor_source_fingerprint"] == identity_fingerprint
    assert all(point["value"] == 1.0 for point in anchor_payload["quote_to_anchor"])


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
    from qap.portfolio import AssetId
    from qap.relationship import identity_source_fingerprint

    run_root, run_id = pair_run_root
    client = TestClient(
        create_app(ApiSettings(run_root=run_root, market_data_root=REPOSITORY_ROOT))
    )

    response = client.get(
        f"/api/pairs/ETH/BTC/anchor?run_id={run_id}&anchor=USDT&orientation=BTC/ETH"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "qap.api.anchor_lens.v1"
    assert payload["canonical_pair"] == ["BTC", "ETH"]
    assert payload["requested_orientation"] == "BTC/ETH"
    assert payload["identity_coordinate_assets"] == ["USDT"]
    assert payload["anchor"] == "USDT"
    assert payload["reduction"] == "none"
    assert payload["anchor_source_fingerprint"] == identity_source_fingerprint(
        AssetId("USDT")
    )
    assert payload["pair_ratio"][0]["value"] == pytest.approx(42050.0 / 2205.0)
    assert payload["base_to_anchor"][0]["value"] == 42050.0
    assert payload["quote_to_anchor"][0]["value"] == 2205.0
    assert math.isfinite(payload["max_ratio_decomposition_error"])
    assert payload["max_ratio_decomposition_error"] <= 1e-12

    unavailable = client.get(f"/api/pairs/ETH/BTC/anchor?run_id={run_id}&anchor=SOL")
    assert unavailable.status_code == 404
    assert unavailable.json()["error"] == {
        "code": "anchor_unavailable",
        "message": "Anchor series is unavailable for this run.",
        "context": {"run_id": run_id, "anchor": "SOL"},
    }
