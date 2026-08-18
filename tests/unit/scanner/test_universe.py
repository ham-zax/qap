from dataclasses import replace
from datetime import UTC, datetime, timedelta

from qap.market import (
    BarInterval,
    InstrumentLifecycleEvent,
    InstrumentLifecycleEvidence,
    LifecycleConfidence,
    LifecycleEventType,
    LifecycleSourceType,
    MarketBar,
    VenueInstrument,
    validate_bar_series,
)
from qap.portfolio import AssetId
from qap.scanner.catalog import ScannerSourceSpec
from qap.scanner.protocol import ScannerHorizon
from qap.scanner.slices import evaluate_series
from qap.scanner.universe import (
    HistoricalEligibilityState,
    UniverseAssetInput,
    build_venue_horizon_universe,
    classify_historical_eligibility,
)

BTC = AssetId("BTC")
USDT = AssetId("USDT")
START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(days=30)


def _event(
    event_type: LifecycleEventType,
    *,
    effective_at: datetime,
    source_type: LifecycleSourceType = (
        LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT
    ),
) -> InstrumentLifecycleEvent:
    return InstrumentLifecycleEvent(
        canonical_asset_id=BTC,
        asset_identity_version="btc-v1",
        venue="binance",
        venue_symbol="BTCUSDT",
        quote_asset=USDT,
        event_type=event_type,
        effective_at=effective_at,
        observed_at=min(effective_at, END),
        source_type=source_type,
        source_id=f"{source_type.value}:{event_type.value}:{effective_at.isoformat()}",
        confidence=LifecycleConfidence.CONFIRMED,
    )


def test_listing_before_window_without_interruption_is_known_eligible() -> None:
    evidence = InstrumentLifecycleEvidence.from_events(
        (
            _event(
                LifecycleEventType.LISTING_OR_TRADING_STARTED,
                effective_at=START - timedelta(days=10),
            ),
        )
    )

    decision = classify_historical_eligibility(
        evidence,
        required_start=START,
        required_end=END,
    )

    assert decision.state is HistoricalEligibilityState.KNOWN_ELIGIBLE
    assert decision.reason == "eligible_through_required_window"


def test_current_exchange_status_cannot_backfill_historical_eligibility() -> None:
    evidence = InstrumentLifecycleEvidence.from_events(
        (
            _event(
                LifecycleEventType.LISTING_OR_TRADING_STARTED,
                effective_at=START - timedelta(days=10),
                source_type=LifecycleSourceType.CURRENT_EXCHANGE_METADATA,
            ),
        )
    )

    decision = classify_historical_eligibility(
        evidence,
        required_start=START,
        required_end=END,
    )

    assert decision.state is HistoricalEligibilityState.HISTORICAL_ELIGIBILITY_UNKNOWN
    assert decision.reason == "insufficient_historical_state_evidence"


def test_suspension_inside_required_window_is_known_ineligible_even_if_resumed() -> (
    None
):
    evidence = InstrumentLifecycleEvidence.from_events(
        (
            _event(
                LifecycleEventType.LISTING_OR_TRADING_STARTED,
                effective_at=START - timedelta(days=10),
            ),
            _event(
                LifecycleEventType.TRADING_SUSPENDED,
                effective_at=START + timedelta(days=5),
            ),
            _event(
                LifecycleEventType.TRADING_RESUMED,
                effective_at=START + timedelta(days=6),
            ),
        )
    )

    decision = classify_historical_eligibility(
        evidence,
        required_start=START,
        required_end=END,
    )

    assert decision.state is HistoricalEligibilityState.KNOWN_INELIGIBLE
    assert decision.reason == "lifecycle_interruption_in_required_window"


def test_listing_started_inside_required_window_is_known_ineligible() -> None:
    evidence = InstrumentLifecycleEvidence.from_events(
        (
            _event(
                LifecycleEventType.LISTING_OR_TRADING_STARTED,
                effective_at=START + timedelta(days=2),
            ),
        )
    )

    decision = classify_historical_eligibility(
        evidence,
        required_start=START,
        required_end=END,
    )

    assert decision.state is HistoricalEligibilityState.KNOWN_INELIGIBLE
    assert decision.reason == "trading_started_after_required_start"


def test_unmapped_identity_change_fails_closed_to_unknown() -> None:
    evidence = InstrumentLifecycleEvidence.from_events(
        (
            _event(
                LifecycleEventType.LISTING_OR_TRADING_STARTED,
                effective_at=START - timedelta(days=10),
            ),
            _event(
                LifecycleEventType.SYMBOL_RENAMED,
                effective_at=START + timedelta(days=2),
            ),
        )
    )

    decision = classify_historical_eligibility(
        evidence,
        required_start=START,
        required_end=END,
    )

    assert decision.state is HistoricalEligibilityState.HISTORICAL_ELIGIBILITY_UNKNOWN
    assert decision.reason == "identity_continuity_unknown"


def _asset_input(*, venue: str, bars: int = 30 * 24) -> UniverseAssetInput:
    instrument = VenueInstrument(
        venue=venue,
        venue_symbol="BTCUSDT" if venue == "binance" else "BTC_USDT",
        base=BTC,
        quote=USDT,
    )
    interval = BarInterval("1h")
    market_bars = tuple(
        MarketBar(
            instrument=instrument,
            interval=interval,
            candle_open_time=START + index * interval.duration,
            open=100.0 + index,
            high=101.0 + index,
            low=99.0 + index,
            close=100.5 + index,
            volume=10.0,
        )
        for index in range(bars)
    )
    series = validate_bar_series(market_bars)
    evaluated = evaluate_series(
        series,
        dataset_id=f"{venue}-btcusdt-1h",
        eligible_information_end=END,
        lookback=timedelta(days=30),
    )
    source = ScannerSourceSpec(
        dataset_id=evaluated.dataset_id,
        relative_path=f"market/{venue}-btcusdt.parquet",
        venue=venue,
        venue_symbol=instrument.venue_symbol,
        base_asset="BTC",
        quote_asset="USDT",
        interval="1h",
        expected_semantic_fingerprint=evaluated.source_artifact_fingerprint,
        lifecycle_evidence_ids=(f"{venue}-listing",),
    )
    lifecycle = InstrumentLifecycleEvidence.from_events(
        (
            InstrumentLifecycleEvent(
                canonical_asset_id=BTC,
                asset_identity_version="btc-v1",
                venue=venue,
                venue_symbol=instrument.venue_symbol,
                quote_asset=USDT,
                event_type=LifecycleEventType.LISTING_OR_TRADING_STARTED,
                effective_at=START - timedelta(days=100),
                observed_at=START - timedelta(days=100),
                source_type=LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT,
                source_id=f"{venue}-listing",
                confidence=LifecycleConfidence.CONFIRMED,
            ),
        )
    )
    return UniverseAssetInput(source=source, evaluated=evaluated, lifecycle=lifecycle)


def test_venue_horizon_universe_preserves_venue_identity_and_snapshot_id() -> None:
    binance = build_venue_horizon_universe(
        scan_id="a" * 64,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        inputs=(_asset_input(venue="binance"),),
    )
    gate = build_venue_horizon_universe(
        scan_id="a" * 64,
        venue="gate",
        horizon=ScannerHorizon.SHORT,
        inputs=(_asset_input(venue="gate"),),
    )

    assert binance.records[0].automatic_eligible
    assert gate.records[0].automatic_eligible
    assert binance.records[0].venue == "binance"
    assert gate.records[0].venue == "gate"
    assert binance.universe_snapshot_id != gate.universe_snapshot_id


def test_future_source_extent_does_not_change_causal_universe_identity() -> None:
    baseline_input = _asset_input(venue="binance")
    changed_fingerprint = "f" * 64
    changed_input = UniverseAssetInput(
        source=baseline_input.source.model_copy(
            update={"expected_semantic_fingerprint": changed_fingerprint}
        ),
        evaluated=replace(
            baseline_input.evaluated,
            source_artifact_fingerprint=changed_fingerprint,
        ),
        lifecycle=baseline_input.lifecycle,
    )

    baseline = build_venue_horizon_universe(
        scan_id="a" * 64,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        inputs=(baseline_input,),
    )
    changed = build_venue_horizon_universe(
        scan_id="b" * 64,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        inputs=(changed_input,),
    )

    assert baseline.records[0].source_artifact_fingerprint != (
        changed.records[0].source_artifact_fingerprint
    )
    assert baseline.records[0].selection_slice_fingerprint == (
        changed.records[0].selection_slice_fingerprint
    )
    assert baseline.universe_snapshot_id == changed.universe_snapshot_id


def test_insufficient_bar_coverage_excludes_without_rewriting_lifecycle_state() -> None:
    short = _asset_input(venue="binance", bars=(30 * 24) - 40)

    snapshot = build_venue_horizon_universe(
        scan_id="b" * 64,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        inputs=(short,),
    )
    record = snapshot.records[0]

    assert record.eligibility_state is HistoricalEligibilityState.KNOWN_ELIGIBLE
    assert record.eligibility_reason == "insufficient_bar_coverage"
    assert not record.automatic_eligible
