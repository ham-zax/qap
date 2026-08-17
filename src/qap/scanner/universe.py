"""Point-in-time venue-local scanner universe admission."""

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from typing import cast

from qap.market import (
    InstrumentLifecycleEvidence,
    LifecycleEventType,
    LifecycleSourceType,
    lifecycle_source_priority,
)
from qap.scanner.catalog import ScannerSourceSpec
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, ScannerProtocol
from qap.scanner.slices import EvaluatedSeries


class HistoricalEligibilityState(StrEnum):
    KNOWN_ELIGIBLE = "known_eligible"
    KNOWN_INELIGIBLE = "known_ineligible"
    HISTORICAL_ELIGIBILITY_UNKNOWN = "historical_eligibility_unknown"


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    state: HistoricalEligibilityState
    reason: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UniverseAssetInput:
    source: ScannerSourceSpec
    evaluated: EvaluatedSeries
    lifecycle: InstrumentLifecycleEvidence


@dataclass(frozen=True, slots=True)
class EligibleAssetRecord:
    scan_id: str
    venue: str
    horizon: ScannerHorizon
    asset_id: str
    venue_symbol: str
    eligibility_state: HistoricalEligibilityState
    eligibility_reason: str
    lifecycle_evidence_refs: tuple[str, ...]
    source_artifact_fingerprint: str
    selection_slice_fingerprint: str
    bar_coverage: float
    longest_missing_run: int
    automatic_eligible: bool
    forensic_research_allowed: bool


@dataclass(frozen=True, slots=True)
class UniverseSnapshot:
    scan_id: str
    venue: str
    horizon: ScannerHorizon
    records: tuple[EligibleAssetRecord, ...]
    universe_snapshot_id: str

    @property
    def eligible_records(self) -> tuple[EligibleAssetRecord, ...]:
        return tuple(record for record in self.records if record.automatic_eligible)


_STATE_EVENT_TYPES = frozenset(
    {
        LifecycleEventType.LISTING_OR_TRADING_STARTED,
        LifecycleEventType.TRADING_SUSPENDED,
        LifecycleEventType.TRADING_RESUMED,
        LifecycleEventType.DELISTED,
    }
)

_HISTORICAL_STATE_SOURCES = frozenset(
    {
        LifecycleSourceType.QAP_VENUE_SNAPSHOT,
        LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT,
        LifecycleSourceType.OFFICIAL_EXCHANGE_METADATA,
    }
)

_ACTIVE_EVENTS = frozenset(
    {
        LifecycleEventType.LISTING_OR_TRADING_STARTED,
        LifecycleEventType.TRADING_RESUMED,
    }
)

_INACTIVE_EVENTS = frozenset(
    {
        LifecycleEventType.TRADING_SUSPENDED,
        LifecycleEventType.DELISTED,
    }
)


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _authoritative_state_events(
    evidence: InstrumentLifecycleEvidence,
    *,
    required_end: datetime,
) -> tuple[object, ...]:
    visible = tuple(
        event
        for event in evidence.events
        if event.observed_at <= required_end and event.effective_at <= required_end
    )
    groups: dict[datetime, list[object]] = defaultdict(list)
    for event in visible:
        if (
            event.source_type in _HISTORICAL_STATE_SOURCES
            and event.event_type in _STATE_EVENT_TYPES
        ):
            groups[event.effective_at].append(event)

    selected: list[object] = []
    for timestamp in sorted(groups):
        candidates = groups[timestamp]
        best_priority = min(
            lifecycle_source_priority(getattr(event, "source_type"))
            for event in candidates
        )
        strongest = tuple(
            event
            for event in candidates
            if lifecycle_source_priority(getattr(event, "source_type")) == best_priority
        )
        event_types = {getattr(event, "event_type") for event in strongest}
        if len(event_types) != 1:
            return ()
        selected.append(
            sorted(strongest, key=lambda event: getattr(event, "event_id"))[0]
        )
    return tuple(selected)


def classify_historical_eligibility(
    evidence: InstrumentLifecycleEvidence,
    *,
    required_start: datetime,
    required_end: datetime,
) -> EligibilityDecision:
    """Classify uninterrupted historical eligibility without current-state lookup."""

    if not isinstance(cast(object, evidence), InstrumentLifecycleEvidence):
        raise TypeError("evidence must be InstrumentLifecycleEvidence")
    start = _utc(required_start, field="required_start")
    end = _utc(required_end, field="required_end")
    if start >= end:
        raise ValueError("required_start must be before required_end")

    visible = tuple(
        event
        for event in evidence.events
        if event.observed_at <= end and event.effective_at <= end
    )
    evidence_ids = tuple(event.event_id for event in visible)
    identity_break = next(
        (
            event
            for event in visible
            if start < event.effective_at <= end
            and event.event_type
            in {
                LifecycleEventType.SYMBOL_RENAMED,
                LifecycleEventType.CONTRACT_OR_TOKEN_MIGRATED,
            }
            and not event.supports_history_continuity
        ),
        None,
    )
    if identity_break is not None:
        return EligibilityDecision(
            state=HistoricalEligibilityState.HISTORICAL_ELIGIBILITY_UNKNOWN,
            reason="identity_continuity_unknown",
            evidence_ids=evidence_ids,
        )

    state_events = _authoritative_state_events(evidence, required_end=end)
    if not state_events:
        return EligibilityDecision(
            state=HistoricalEligibilityState.HISTORICAL_ELIGIBILITY_UNKNOWN,
            reason="insufficient_historical_state_evidence",
            evidence_ids=evidence_ids,
        )

    active: bool | None = None
    for event in state_events:
        effective_at = getattr(event, "effective_at")
        event_type = getattr(event, "event_type")
        if effective_at > start:
            break
        if event_type in _ACTIVE_EVENTS:
            active = True
        elif event_type in _INACTIVE_EVENTS:
            active = False

    if active is False:
        return EligibilityDecision(
            state=HistoricalEligibilityState.KNOWN_INELIGIBLE,
            reason="inactive_at_required_start",
            evidence_ids=evidence_ids,
        )
    if active is None:
        first_state = next(
            (event for event in state_events if getattr(event, "effective_at") > start),
            None,
        )
        if first_state is not None:
            first_type = getattr(first_state, "event_type")
            if first_type is LifecycleEventType.LISTING_OR_TRADING_STARTED:
                return EligibilityDecision(
                    state=HistoricalEligibilityState.KNOWN_INELIGIBLE,
                    reason="trading_started_after_required_start",
                    evidence_ids=evidence_ids,
                )
            if first_type in _INACTIVE_EVENTS:
                return EligibilityDecision(
                    state=HistoricalEligibilityState.KNOWN_INELIGIBLE,
                    reason="lifecycle_interruption_in_required_window",
                    evidence_ids=evidence_ids,
                )
        return EligibilityDecision(
            state=HistoricalEligibilityState.HISTORICAL_ELIGIBILITY_UNKNOWN,
            reason="insufficient_historical_state_evidence",
            evidence_ids=evidence_ids,
        )

    for event in state_events:
        if not (start < getattr(event, "effective_at") <= end):
            continue
        if getattr(event, "event_type") in _INACTIVE_EVENTS:
            return EligibilityDecision(
                state=HistoricalEligibilityState.KNOWN_INELIGIBLE,
                reason="lifecycle_interruption_in_required_window",
                evidence_ids=evidence_ids,
            )

    return EligibilityDecision(
        state=HistoricalEligibilityState.KNOWN_ELIGIBLE,
        reason="eligible_through_required_window",
        evidence_ids=evidence_ids,
    )


def _snapshot_id(
    *,
    scan_id: str,
    venue: str,
    horizon: ScannerHorizon,
    records: tuple[EligibleAssetRecord, ...],
) -> str:
    payload = {
        "schema": "qap.scanner.universe-snapshot.v1",
        "scan_id": scan_id,
        "venue": venue,
        "horizon": horizon.value,
        "records": [
            {
                "asset_id": record.asset_id,
                "venue_symbol": record.venue_symbol,
                "eligibility_state": record.eligibility_state.value,
                "eligibility_reason": record.eligibility_reason,
                "lifecycle_evidence_refs": list(record.lifecycle_evidence_refs),
                "source_artifact_fingerprint": record.source_artifact_fingerprint,
                "selection_slice_fingerprint": record.selection_slice_fingerprint,
                "bar_coverage": record.bar_coverage.hex(),
                "longest_missing_run": record.longest_missing_run,
                "automatic_eligible": record.automatic_eligible,
                "forensic_research_allowed": record.forensic_research_allowed,
            }
            for record in records
        ],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_venue_horizon_universe(
    *,
    scan_id: str,
    venue: str,
    horizon: ScannerHorizon,
    inputs: tuple[UniverseAssetInput, ...],
    forensic: bool = False,
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> UniverseSnapshot:
    """Build one venue/horizon PIT universe while preserving every exclusion."""

    if not isinstance(cast(object, scan_id), str) or len(scan_id) != 64:
        raise ValueError("scan_id must be a 64-character semantic identifier")
    normalized_venue = venue.strip().lower()
    if normalized_venue not in protocol.venues:
        raise ValueError("venue is not admitted by the scanner protocol")
    horizon_protocol = protocol.horizon(horizon)

    records: list[EligibleAssetRecord] = []
    seen_assets: set[str] = set()
    for item in inputs:
        source = item.source
        evaluated = item.evaluated
        lifecycle = item.lifecycle
        if (
            source.venue != normalized_venue
            or evaluated.instrument.venue != normalized_venue
        ):
            raise ValueError("universe inputs must belong to the requested venue")
        if source.interval != horizon_protocol.graph_interval.label:
            raise ValueError(
                "universe input interval must match the horizon graph interval"
            )
        if evaluated.interval != horizon_protocol.graph_interval:
            raise ValueError("evaluated interval must match the horizon graph interval")
        if source.base_asset in seen_assets:
            raise ValueError(
                "one venue/horizon universe cannot contain duplicate assets"
            )
        seen_assets.add(source.base_asset)

        decision = classify_historical_eligibility(
            lifecycle,
            required_start=evaluated.window_start,
            required_end=evaluated.eligible_information_end,
        )
        automatic = decision.state is HistoricalEligibilityState.KNOWN_ELIGIBLE
        reason = decision.reason
        if source.quote_asset != protocol.quote_asset:
            automatic = False
            reason = "wrong_quote_asset"
        elif source.base_asset == protocol.quote_asset:
            automatic = False
            reason = "quote_asset_not_candidate"
        elif evaluated.bar_coverage < protocol.minimum_asset_coverage:
            automatic = False
            reason = "insufficient_bar_coverage"
        elif evaluated.longest_missing_run > protocol.maximum_missing_generator_bars:
            automatic = False
            reason = "missing_run_too_long"

        records.append(
            EligibleAssetRecord(
                scan_id=scan_id,
                venue=normalized_venue,
                horizon=horizon,
                asset_id=source.base_asset,
                venue_symbol=source.venue_symbol,
                eligibility_state=decision.state,
                eligibility_reason=reason,
                lifecycle_evidence_refs=decision.evidence_ids,
                source_artifact_fingerprint=evaluated.source_artifact_fingerprint,
                selection_slice_fingerprint=evaluated.selection_slice_fingerprint,
                bar_coverage=evaluated.bar_coverage,
                longest_missing_run=evaluated.longest_missing_run,
                automatic_eligible=automatic,
                forensic_research_allowed=(
                    forensic
                    and decision.state
                    is HistoricalEligibilityState.HISTORICAL_ELIGIBILITY_UNKNOWN
                ),
            )
        )

    ordered = tuple(
        sorted(records, key=lambda record: (record.asset_id, record.venue_symbol))
    )
    return UniverseSnapshot(
        scan_id=scan_id,
        venue=normalized_venue,
        horizon=horizon,
        records=ordered,
        universe_snapshot_id=_snapshot_id(
            scan_id=scan_id,
            venue=normalized_venue,
            horizon=horizon,
            records=ordered,
        ),
    )


__all__ = [
    "EligibilityDecision",
    "EligibleAssetRecord",
    "HistoricalEligibilityState",
    "UniverseAssetInput",
    "UniverseSnapshot",
    "build_venue_horizon_universe",
    "classify_historical_eligibility",
]
