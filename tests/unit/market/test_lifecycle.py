from datetime import UTC, datetime, timedelta, timezone

import pytest

from qap.market.lifecycle import (
    AssetIdentityContinuity,
    InstrumentLifecycleEvent,
    InstrumentLifecycleEvidence,
    LifecycleConfidence,
    LifecycleEventType,
    LifecycleSourceType,
    lifecycle_source_priority,
    source_supports_historical_state,
)
from qap.portfolio import AssetId

AS_OF = datetime(2026, 1, 1, tzinfo=UTC)
BTC = AssetId("BTC")
USDT = AssetId("USDT")


def _event(
    event_type: LifecycleEventType = LifecycleEventType.LISTING_OR_TRADING_STARTED,
    *,
    effective_at: datetime = AS_OF,
    observed_at: datetime = AS_OF,
    source_type: LifecycleSourceType = (
        LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT
    ),
    continuity: AssetIdentityContinuity | None = None,
) -> InstrumentLifecycleEvent:
    return InstrumentLifecycleEvent(
        canonical_asset_id=BTC,
        asset_identity_version="btc-v1",
        venue=" BINANCE ",
        venue_symbol=" BTCUSDT ",
        quote_asset=USDT,
        event_type=event_type,
        effective_at=effective_at,
        observed_at=observed_at,
        source_type=source_type,
        source_id=" announcement-123 ",
        confidence=LifecycleConfidence.CONFIRMED,
        continuity=continuity,
    )


def test_required_lifecycle_event_types_are_explicit() -> None:
    assert {event.value for event in LifecycleEventType} == {
        "listing_or_trading_started",
        "trading_suspended",
        "trading_resumed",
        "delisting_announced",
        "delisted",
        "symbol_renamed",
        "contract_or_token_migrated",
    }


def test_event_normalizes_identity_and_has_stable_semantic_id() -> None:
    first = _event()
    second = _event()

    assert first.venue == "binance"
    assert first.venue_symbol == "BTCUSDT"
    assert first.source_id == "announcement-123"
    assert first.event_id == second.event_id
    assert len(first.event_id) == 64


def test_event_rejects_non_utc_timestamps() -> None:
    with pytest.raises(ValueError, match="effective_at must be timezone-aware UTC"):
        _event(effective_at=datetime(2026, 1, 1))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware UTC"):
        _event(observed_at=datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1))))


def test_source_priority_matches_frozen_evidence_order() -> None:
    ordered = (
        LifecycleSourceType.QAP_VENUE_SNAPSHOT,
        LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT,
        LifecycleSourceType.OFFICIAL_EXCHANGE_METADATA,
        LifecycleSourceType.OFFICIAL_EXCHANGE_HISTORY,
        LifecycleSourceType.CURRENT_EXCHANGE_METADATA,
        LifecycleSourceType.THIRD_PARTY_METADATA,
    )

    assert [lifecycle_source_priority(source) for source in ordered] == list(range(6))
    assert source_supports_historical_state(LifecycleSourceType.QAP_VENUE_SNAPSHOT)
    assert source_supports_historical_state(
        LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT
    )
    assert not source_supports_historical_state(
        LifecycleSourceType.CURRENT_EXCHANGE_METADATA
    )
    assert not source_supports_historical_state(
        LifecycleSourceType.THIRD_PARTY_METADATA
    )


def test_rename_or_migration_needs_explicit_continuity_to_join_history() -> None:
    unmapped = _event(LifecycleEventType.SYMBOL_RENAMED)
    mapped = _event(
        LifecycleEventType.CONTRACT_OR_TOKEN_MIGRATED,
        continuity=AssetIdentityContinuity(
            from_asset_identity_version="btc-v0",
            to_asset_identity_version="btc-v1",
            source_id="migration-map-1",
        ),
    )

    assert not unmapped.supports_history_continuity
    assert mapped.supports_history_continuity


def test_evidence_bundle_is_one_asset_venue_quote_and_orders_events_causally() -> None:
    resumed = _event(
        LifecycleEventType.TRADING_RESUMED,
        effective_at=AS_OF + timedelta(days=2),
        observed_at=AS_OF + timedelta(days=2),
    )
    suspended = _event(
        LifecycleEventType.TRADING_SUSPENDED,
        effective_at=AS_OF + timedelta(days=1),
        observed_at=AS_OF + timedelta(days=1),
    )
    evidence = InstrumentLifecycleEvidence.from_events((resumed, suspended))

    assert evidence.canonical_asset_id == BTC
    assert evidence.venue == "binance"
    assert evidence.quote_asset == USDT
    assert tuple(event.event_type for event in evidence.events) == (
        LifecycleEventType.TRADING_SUSPENDED,
        LifecycleEventType.TRADING_RESUMED,
    )
    assert evidence.evidence_ids == tuple(event.event_id for event in evidence.events)


def test_empty_evidence_is_unknown_not_negative_lifecycle_evidence() -> None:
    evidence = InstrumentLifecycleEvidence.empty(
        canonical_asset_id=BTC,
        venue="binance",
        quote_asset=USDT,
    )

    assert evidence.events == ()
    assert evidence.evidence_ids == ()
    assert not evidence.has_historical_state_evidence


def test_bundle_rejects_mixed_venue_evidence() -> None:
    other_venue = InstrumentLifecycleEvent(
        canonical_asset_id=BTC,
        asset_identity_version="btc-v1",
        venue="gate",
        venue_symbol="BTC_USDT",
        quote_asset=USDT,
        event_type=LifecycleEventType.LISTING_OR_TRADING_STARTED,
        effective_at=AS_OF,
        observed_at=AS_OF,
        source_type=LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT,
        source_id="gate-listing",
        confidence=LifecycleConfidence.CONFIRMED,
    )

    with pytest.raises(ValueError, match="same asset, venue, and quote"):
        InstrumentLifecycleEvidence.from_events((_event(), other_venue))
