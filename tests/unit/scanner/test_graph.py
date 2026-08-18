from dataclasses import replace
from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from qap.market import BarInterval, MarketBar, VenueInstrument, validate_bar_series
from qap.portfolio import AssetId
from qap.scanner.graph import ManualPairPin, build_ssd_graph, normalized_log_ssd
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon
from qap.scanner.slices import EvaluatedSeries, evaluate_series
from qap.scanner.universe import (
    EligibleAssetRecord,
    HistoricalEligibilityState,
    UniverseSnapshot,
)

USDT = AssetId("USDT")
START = datetime(2026, 1, 1, tzinfo=UTC)
INTERVAL = BarInterval("1h")


def _evaluated(
    asset: str, values: tuple[float, ...], *, venue: str = "binance"
) -> EvaluatedSeries:
    asset_id = AssetId(asset)
    instrument = VenueInstrument(
        venue=venue,
        venue_symbol=f"{asset_id.key}USDT",
        base=asset_id,
        quote=USDT,
    )
    bars = tuple(
        MarketBar(
            instrument=instrument,
            interval=INTERVAL,
            candle_open_time=START + index * INTERVAL.duration,
            open=value,
            high=value + 0.1,
            low=value - 0.1,
            close=value,
            volume=10.0,
        )
        for index, value in enumerate(values)
    )
    series = validate_bar_series(bars)
    return evaluate_series(
        series,
        dataset_id=f"{venue}-{asset.lower()}-1h",
        eligible_information_end=START + len(values) * INTERVAL.duration,
        lookback=len(values) * INTERVAL.duration,
    )


def _snapshot(series_by_asset: dict[str, EvaluatedSeries]) -> UniverseSnapshot:
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
        for asset, evaluated in sorted(series_by_asset.items())
    )
    return UniverseSnapshot(
        scan_id="a" * 64,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        records=records,
        universe_snapshot_id="b" * 64,
    )


@given(
    left=st.lists(
        st.floats(
            min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False
        ),
        min_size=2,
        max_size=30,
    ),
    scale_left=st.floats(
        min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False
    ),
    scale_right=st.floats(
        min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False
    ),
)
def test_normalized_log_ssd_is_symmetric_and_initial_price_scale_invariant(
    left: list[float],
    scale_left: float,
    scale_right: float,
) -> None:
    right = [value * 1.01 + 0.5 for value in left]

    baseline = normalized_log_ssd(tuple(left), tuple(right))
    reciprocal_order = normalized_log_ssd(tuple(right), tuple(left))
    scaled = normalized_log_ssd(
        tuple(value * scale_left for value in left),
        tuple(value * scale_right for value in right),
    )

    assert reciprocal_order == pytest.approx(baseline, rel=1e-12, abs=1e-15)
    assert scaled == pytest.approx(baseline, rel=1e-10, abs=1e-12)


def test_neighbor_ties_are_deterministic_and_union_directed_selection() -> None:
    series = {
        "A": _evaluated("A", (10.0, 11.0, 12.0, 13.0)),
        "B": _evaluated("B", (20.0, 22.0, 24.0, 26.0)),
        "C": _evaluated("C", (30.0, 33.0, 36.0, 39.0)),
        "D": _evaluated("D", (10.0, 10.2, 10.4, 10.6)),
    }
    protocol = replace(SCANNER_V1_SLICE1, neighbors_per_asset=1)

    graph = build_ssd_graph(
        _snapshot(series),
        series_by_asset=series,
        protocol=protocol,
    )

    assert graph.eligible_asset_count == 4
    assert graph.universe_snapshot_id == "b" * 64
    assert graph.total_valid_pair_comparisons == 6
    assert len(graph.distance_digest) == 64
    assert tuple(record.pair_id for record in graph.records) == tuple(
        sorted(record.pair_id for record in graph.records)
    )
    assert any(record.selected_by_a != record.selected_by_b for record in graph.records)


def test_manual_pin_overlap_keeps_one_pair_with_both_lineage_flags() -> None:
    series = {
        "A": _evaluated("A", (10.0, 11.0, 12.0, 13.0)),
        "B": _evaluated("B", (20.0, 22.0, 24.0, 26.0)),
        "C": _evaluated("C", (10.0, 10.1, 10.2, 10.3)),
    }

    graph = build_ssd_graph(
        _snapshot(series),
        series_by_asset=series,
        manual_pins=(ManualPairPin(AssetId("A"), AssetId("B")),),
    )
    pair = next(record for record in graph.records if record.pair_id == "A/B")

    assert pair.automatic_neighbor_selected
    assert pair.manual_pinned
    assert sum(record.pair_id == "A/B" for record in graph.records) == 1


def test_manual_pin_can_add_valid_pair_outside_k_cutoff() -> None:
    series = {
        "A": _evaluated("A", (10.0, 11.0, 12.0, 13.0)),
        "B": _evaluated("B", (20.0, 22.0, 24.0, 26.0)),
        "C": _evaluated("C", (10.0, 10.1, 10.2, 10.3)),
        "D": _evaluated("D", (100.0, 90.0, 80.0, 70.0)),
    }
    protocol = replace(SCANNER_V1_SLICE1, neighbors_per_asset=1)

    graph = build_ssd_graph(
        _snapshot(series),
        series_by_asset=series,
        manual_pins=(ManualPairPin(AssetId("A"), AssetId("D")),),
        protocol=protocol,
    )
    pinned = next(record for record in graph.records if record.pair_id == "A/D")

    assert pinned.manual_pinned
    assert not pinned.automatic_neighbor_selected


def test_graph_rejects_cross_venue_series_and_invalid_pin_assets() -> None:
    series = {
        "A": _evaluated("A", (10.0, 11.0, 12.0, 13.0)),
        "B": _evaluated("B", (20.0, 22.0, 24.0, 26.0)),
    }
    wrong_venue = dict(series)
    wrong_venue["B"] = _evaluated(
        "B",
        (20.0, 22.0, 24.0, 26.0),
        venue="gate",
    )

    with pytest.raises(ValueError, match="requested venue"):
        build_ssd_graph(_snapshot(series), series_by_asset=wrong_venue)

    with pytest.raises(ValueError, match="manual pin assets must be eligible"):
        build_ssd_graph(
            _snapshot(series),
            series_by_asset=series,
            manual_pins=(ManualPairPin(AssetId("A"), AssetId("Z")),),
        )
