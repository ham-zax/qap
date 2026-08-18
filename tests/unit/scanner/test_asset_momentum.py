import inspect
import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import qap.scanner.asset_momentum as asset_momentum_module
import pytest
from qap.market import BarInterval, MarketBar, VenueInstrument, validate_bar_series
from qap.portfolio import AssetId
from qap.scanner.asset_momentum import (
    MomentumObservationStatus,
    build_asset_momentum_generation,
)
from qap.scanner.asset_momentum_artifacts import (
    AssetMomentumArtifactError,
    publish_asset_momentum_generation,
    read_asset_momentum_generation,
)
from qap.scanner.basket_protocol import SCANNER_V1_BASKET, basket_protocol_identity
from qap.scanner.protocol import ScannerHorizon
from qap.scanner.slices import EvaluatedSeries, evaluate_series
from qap.scanner.universe import (
    EligibleAssetRecord,
    HistoricalEligibilityState,
    UniverseSnapshot,
)

START = datetime(2026, 8, 1, tzinfo=UTC)
INTERVAL = BarInterval("1h")
CUTOFF = START + timedelta(days=2)
USDT = AssetId("USDT")


def _evaluated(
    asset: str,
    start_price: float,
    end_price: float,
    *,
    extra: int = 0,
) -> EvaluatedSeries:
    instrument = VenueInstrument(
        venue="binance",
        venue_symbol=f"{asset}USDT",
        base=AssetId(asset),
        quote=USDT,
    )
    count = 48 + extra
    bars: list[MarketBar] = []
    for index in range(count):
        fraction = min(index, 47) / 47
        price = start_price + (end_price - start_price) * fraction
        bars.append(
            MarketBar(
                instrument=instrument,
                interval=INTERVAL,
                candle_open_time=START + index * INTERVAL.duration,
                open=start_price if index == 0 else price,
                high=max(start_price, price, end_price) + 1,
                low=min(start_price, price, end_price) - 1,
                close=end_price if index == 47 else price,
                volume=10.0,
            )
        )
    return evaluate_series(
        validate_bar_series(tuple(bars)),
        dataset_id=f"binance-{asset.lower()}-1h",
        eligible_information_end=CUTOFF,
        lookback=timedelta(days=2),
    )


def _snapshot(values: dict[str, EvaluatedSeries]) -> UniverseSnapshot:
    records = tuple(
        EligibleAssetRecord(
            scan_id="a" * 64,
            venue="binance",
            horizon=ScannerHorizon.SHORT,
            asset_id=asset,
            venue_symbol=evaluated.instrument.venue_symbol,
            eligibility_state=HistoricalEligibilityState.KNOWN_ELIGIBLE,
            eligibility_reason="eligible_through_required_window",
            lifecycle_evidence_refs=(f"{asset}-listing",),
            source_artifact_fingerprint=evaluated.source_artifact_fingerprint,
            selection_slice_fingerprint=evaluated.selection_slice_fingerprint,
            bar_coverage=evaluated.bar_coverage,
            longest_missing_run=evaluated.longest_missing_run,
            automatic_eligible=True,
            forensic_research_allowed=False,
        )
        for asset, evaluated in sorted(values.items())
    )
    return UniverseSnapshot(
        scan_id="a" * 64,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        records=records,
        universe_snapshot_id="b" * 64,
    )


def test_basket_protocol_freezes_manual_single_scope_contract() -> None:
    protocol = SCANNER_V1_BASKET

    assert protocol.basket_construction_rule == "manual-only"
    assert protocol.one_venue_per_basket
    assert protocol.one_horizon_per_basket
    assert protocol.one_decision_resolution_per_basket
    assert protocol.maximum_selected_candidates_per_unordered_pair == 1
    assert protocol.pair_edge_weight_rule == "equal"
    assert not protocol.cross_horizon_combination_allowed
    assert not protocol.cross_venue_combination_allowed
    assert basket_protocol_identity(protocol) != basket_protocol_identity(
        replace(protocol, maximum_asset_tilt=protocol.maximum_asset_tilt / 2)
    )


def test_asset_momentum_scores_common_mode_and_deterministic_ties() -> None:
    series = {
        "AAA": _evaluated("AAA", 100.0, 200.0),
        "BBB": _evaluated("BBB", 100.0, 100.0),
        "CCC": _evaluated("CCC", 100.0, 50.0),
    }

    generation = build_asset_momentum_generation(
        _snapshot(series),
        series,
        as_of=CUTOFF,
    )
    rows = {item.asset_id: item for item in generation.observations}

    assert math.isclose(rows["AAA"].own_momentum or 0.0, math.log(2.0))
    assert rows["BBB"].own_momentum is not None
    assert math.isclose(rows["BBB"].own_momentum, 0.0)
    assert math.isclose(rows["CCC"].own_momentum or 0.0, math.log(0.5))
    assert rows["AAA"].common_mode is not None
    assert math.isclose(rows["AAA"].common_mode, 0.0, abs_tol=1e-15)
    assert rows["AAA"].rank == 1
    assert rows["BBB"].rank == 2
    assert rows["CCC"].rank == 3

    tied = {
        "AAA": _evaluated("AAA", 100.0, 100.0),
        "BBB": _evaluated("BBB", 100.0, 100.0),
    }
    tied_generation = build_asset_momentum_generation(
        _snapshot(tied), tied, as_of=CUTOFF
    )
    assert [(item.asset_id, item.rank) for item in tied_generation.observations] == [
        ("AAA", 1),
        ("BBB", 2),
    ]


def test_invalid_asset_stays_visible_and_scope_requires_two_valid_assets() -> None:
    series = {
        "AAA": _evaluated("AAA", 100.0, 110.0),
        "BBB": _evaluated("BBB", 100.0, 90.0),
    }
    snapshot = _snapshot(series)
    invalid = replace(
        snapshot.records[1],
        automatic_eligible=False,
        eligibility_reason="insufficient_bar_coverage",
    )
    snapshot = replace(snapshot, records=(snapshot.records[0], invalid))

    generation = build_asset_momentum_generation(snapshot, series, as_of=CUTOFF)
    rows = {item.asset_id: item for item in generation.observations}

    assert rows["BBB"].status is MomentumObservationStatus.INVALID
    assert rows["BBB"].reason == "insufficient_bar_coverage"
    assert rows["AAA"].status is MomentumObservationStatus.INVALID
    assert rows["AAA"].reason == "insufficient_valid_assets_for_common_mode"
    assert rows["AAA"].own_momentum is not None
    assert rows["AAA"].relative_momentum is None


def test_future_source_append_does_not_change_frozen_momentum_identity() -> None:
    original = {
        "AAA": _evaluated("AAA", 100.0, 110.0),
        "BBB": _evaluated("BBB", 100.0, 90.0),
    }
    snapshot = _snapshot(original)
    first = build_asset_momentum_generation(snapshot, original, as_of=CUTOFF)

    extended = {
        "AAA": _evaluated("AAA", 100.0, 110.0, extra=2),
        "BBB": _evaluated("BBB", 100.0, 90.0, extra=2),
    }
    second = build_asset_momentum_generation(snapshot, extended, as_of=CUTOFF)

    assert first.momentum_scan_id == second.momentum_scan_id
    assert (
        first.momentum_scan_id
        == replace(first, source_scan_id="c" * 64).momentum_scan_id
    )
    assert [item.selection_slice_fingerprint for item in first.observations] == [
        item.selection_slice_fingerprint for item in second.observations
    ]
    assert [item.source_artifact_fingerprint for item in first.observations] != [
        item.source_artifact_fingerprint for item in second.observations
    ]


def test_asset_momentum_owner_has_no_pair_graph_enumeration_path() -> None:
    source = inspect.getsource(asset_momentum_module)

    assert "qap.scanner.graph" not in source
    assert "build_ssd_graph" not in source
    assert "combinations(" not in source


def test_asset_momentum_artifact_round_trip_preserves_invalid_rows(
    tmp_path: Path,
) -> None:
    series = {
        "AAA": _evaluated("AAA", 100.0, 110.0),
        "BBB": _evaluated("BBB", 100.0, 90.0),
    }
    snapshot = _snapshot(series)
    snapshot = replace(
        snapshot,
        records=(
            snapshot.records[0],
            replace(
                snapshot.records[1],
                automatic_eligible=False,
                eligibility_reason="insufficient_bar_coverage",
            ),
        ),
    )
    generation = build_asset_momentum_generation(snapshot, series, as_of=CUTOFF)

    directory = publish_asset_momentum_generation(tmp_path, generation, snapshot)
    loaded, loaded_snapshot = read_asset_momentum_generation(directory)

    assert loaded == generation
    assert loaded_snapshot == snapshot
    assert loaded.observations[1].status is MomentumObservationStatus.INVALID


def test_asset_momentum_artifact_rejects_tamper_and_undeclared_file(
    tmp_path: Path,
) -> None:
    series = {
        "AAA": _evaluated("AAA", 100.0, 110.0),
        "BBB": _evaluated("BBB", 100.0, 90.0),
    }
    snapshot = _snapshot(series)
    generation = build_asset_momentum_generation(snapshot, series, as_of=CUTOFF)

    tampered = publish_asset_momentum_generation(tmp_path / "tamper", generation, snapshot)
    (tampered / "definition.json").write_text("{}", encoding="utf-8")
    with pytest.raises(AssetMomentumArtifactError, match="digest mismatch"):
        read_asset_momentum_generation(tampered)

    extra = publish_asset_momentum_generation(tmp_path / "extra", generation, snapshot)
    (extra / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(AssetMomentumArtifactError, match="file set mismatch"):
        read_asset_momentum_generation(extra)


def test_asset_momentum_artifact_reuses_frozen_semantic_generation_after_append(
    tmp_path: Path,
) -> None:
    original = {
        "AAA": _evaluated("AAA", 100.0, 110.0),
        "BBB": _evaluated("BBB", 100.0, 90.0),
    }
    snapshot = _snapshot(original)
    first = build_asset_momentum_generation(snapshot, original, as_of=CUTOFF)
    first_path = publish_asset_momentum_generation(tmp_path, first, snapshot)

    extended = {
        "AAA": _evaluated("AAA", 100.0, 110.0, extra=2),
        "BBB": _evaluated("BBB", 100.0, 90.0, extra=2),
    }
    second = build_asset_momentum_generation(snapshot, extended, as_of=CUTOFF)
    second_path = publish_asset_momentum_generation(tmp_path, second, snapshot)

    assert first.momentum_scan_id == second.momentum_scan_id
    assert second_path == first_path
    loaded, _ = read_asset_momentum_generation(first_path)
    assert loaded == first
