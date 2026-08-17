"""Immutable point-in-time instrument lifecycle evidence."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from typing import cast

from qap.portfolio import AssetId


class LifecycleEventType(StrEnum):
    """Venue lifecycle events admitted by the Scanner-V1 evidence contract."""

    LISTING_OR_TRADING_STARTED = "listing_or_trading_started"
    TRADING_SUSPENDED = "trading_suspended"
    TRADING_RESUMED = "trading_resumed"
    DELISTING_ANNOUNCED = "delisting_announced"
    DELISTED = "delisted"
    SYMBOL_RENAMED = "symbol_renamed"
    CONTRACT_OR_TOKEN_MIGRATED = "contract_or_token_migrated"


class LifecycleSourceType(StrEnum):
    """Evidence sources ordered separately by the frozen priority policy."""

    QAP_VENUE_SNAPSHOT = "qap_venue_snapshot"
    OFFICIAL_EXCHANGE_ANNOUNCEMENT = "official_exchange_announcement"
    OFFICIAL_EXCHANGE_METADATA = "official_exchange_metadata"
    OFFICIAL_EXCHANGE_HISTORY = "official_exchange_history"
    CURRENT_EXCHANGE_METADATA = "current_exchange_metadata"
    THIRD_PARTY_METADATA = "third_party_metadata"


class LifecycleConfidence(StrEnum):
    """Source-supplied confidence without replacing source-priority semantics."""

    CONFIRMED = "confirmed"
    REPORTED = "reported"
    CORROBORATING = "corroborating"


_SOURCE_PRIORITY = {
    LifecycleSourceType.QAP_VENUE_SNAPSHOT: 0,
    LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT: 1,
    LifecycleSourceType.OFFICIAL_EXCHANGE_METADATA: 2,
    LifecycleSourceType.OFFICIAL_EXCHANGE_HISTORY: 3,
    LifecycleSourceType.CURRENT_EXCHANGE_METADATA: 4,
    LifecycleSourceType.THIRD_PARTY_METADATA: 5,
}

_HISTORICAL_STATE_SOURCES = frozenset(
    {
        LifecycleSourceType.QAP_VENUE_SNAPSHOT,
        LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT,
        LifecycleSourceType.OFFICIAL_EXCHANGE_METADATA,
        LifecycleSourceType.OFFICIAL_EXCHANGE_HISTORY,
    }
)

_IDENTITY_CHANGE_EVENTS = frozenset(
    {
        LifecycleEventType.SYMBOL_RENAMED,
        LifecycleEventType.CONTRACT_OR_TOKEN_MIGRATED,
    }
)


def _text(value: object, *, field: str, lower: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized.lower() if lower else normalized


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def lifecycle_source_priority(source: LifecycleSourceType) -> int:
    """Return the frozen lower-is-stronger lifecycle evidence priority."""

    if not isinstance(cast(object, source), LifecycleSourceType):
        raise TypeError("source must be a LifecycleSourceType")
    return _SOURCE_PRIORITY[source]


def source_supports_historical_state(source: LifecycleSourceType) -> bool:
    """Whether this source type may establish historical lifecycle state."""

    if not isinstance(cast(object, source), LifecycleSourceType):
        raise TypeError("source must be a LifecycleSourceType")
    return source in _HISTORICAL_STATE_SOURCES


@dataclass(frozen=True, slots=True)
class AssetIdentityContinuity:
    """Explicit evidence that two asset-identity versions are continuous."""

    from_asset_identity_version: str
    to_asset_identity_version: str
    source_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "from_asset_identity_version",
            _text(
                self.from_asset_identity_version,
                field="from_asset_identity_version",
            ),
        )
        object.__setattr__(
            self,
            "to_asset_identity_version",
            _text(self.to_asset_identity_version, field="to_asset_identity_version"),
        )
        object.__setattr__(
            self,
            "source_id",
            _text(self.source_id, field="continuity source_id"),
        )


@dataclass(frozen=True, slots=True)
class InstrumentLifecycleEvent:
    """One immutable, source-attributed venue lifecycle fact."""

    canonical_asset_id: AssetId
    asset_identity_version: str
    venue: str
    venue_symbol: str
    quote_asset: AssetId
    event_type: LifecycleEventType
    effective_at: datetime
    observed_at: datetime
    source_type: LifecycleSourceType
    source_id: str
    confidence: LifecycleConfidence
    continuity: AssetIdentityContinuity | None = None

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.canonical_asset_id), AssetId):
            raise TypeError("canonical_asset_id must be an AssetId")
        if not isinstance(cast(object, self.quote_asset), AssetId):
            raise TypeError("quote_asset must be an AssetId")
        if not isinstance(cast(object, self.event_type), LifecycleEventType):
            raise TypeError("event_type must be a LifecycleEventType")
        if not isinstance(cast(object, self.source_type), LifecycleSourceType):
            raise TypeError("source_type must be a LifecycleSourceType")
        if not isinstance(cast(object, self.confidence), LifecycleConfidence):
            raise TypeError("confidence must be a LifecycleConfidence")
        if self.continuity is not None and not isinstance(
            cast(object, self.continuity), AssetIdentityContinuity
        ):
            raise TypeError("continuity must be an AssetIdentityContinuity or None")

        identity_version = _text(
            self.asset_identity_version,
            field="asset_identity_version",
        )
        continuity = self.continuity
        if (
            continuity is not None
            and continuity.to_asset_identity_version != identity_version
        ):
            raise ValueError(
                "continuity to_asset_identity_version must match the event identity"
            )

        object.__setattr__(self, "asset_identity_version", identity_version)
        object.__setattr__(self, "venue", _text(self.venue, field="venue", lower=True))
        object.__setattr__(
            self,
            "venue_symbol",
            _text(self.venue_symbol, field="venue_symbol"),
        )
        object.__setattr__(
            self,
            "effective_at",
            _utc(self.effective_at, field="effective_at"),
        )
        object.__setattr__(
            self,
            "observed_at",
            _utc(self.observed_at, field="observed_at"),
        )
        object.__setattr__(self, "source_id", _text(self.source_id, field="source_id"))

    @property
    def supports_history_continuity(self) -> bool:
        """Whether history may cross this event without assuming identity continuity."""

        return (
            self.event_type not in _IDENTITY_CHANGE_EVENTS
            or self.continuity is not None
        )

    @property
    def event_id(self) -> str:
        """Return a path-independent deterministic semantic event identifier."""

        digest = sha256()
        continuity = self.continuity
        values = (
            "qap.market.lifecycle-event.v1",
            self.canonical_asset_id.key,
            self.asset_identity_version,
            self.venue,
            self.venue_symbol,
            self.quote_asset.key,
            self.event_type.value,
            self.effective_at.isoformat(),
            self.observed_at.isoformat(),
            self.source_type.value,
            self.source_id,
            self.confidence.value,
            "" if continuity is None else continuity.from_asset_identity_version,
            "" if continuity is None else continuity.to_asset_identity_version,
            "" if continuity is None else continuity.source_id,
        )
        for value in values:
            digest.update(value.encode("utf-8"))
            digest.update(b"\0")
        return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class InstrumentLifecycleEvidence:
    """Lifecycle evidence scoped to one stable asset, venue, and quote coordinate."""

    canonical_asset_id: AssetId
    venue: str
    quote_asset: AssetId
    events: tuple[InstrumentLifecycleEvent, ...]

    @classmethod
    def empty(
        cls,
        *,
        canonical_asset_id: AssetId,
        venue: str,
        quote_asset: AssetId,
    ) -> "InstrumentLifecycleEvidence":
        return cls(
            canonical_asset_id=canonical_asset_id,
            venue=venue,
            quote_asset=quote_asset,
            events=(),
        )

    @classmethod
    def from_events(
        cls,
        events: Iterable[InstrumentLifecycleEvent],
    ) -> "InstrumentLifecycleEvidence":
        copied = tuple(events)
        if not copied:
            raise ValueError("use InstrumentLifecycleEvidence.empty for no evidence")
        first = copied[0]
        if any(
            event.canonical_asset_id != first.canonical_asset_id
            or event.venue != first.venue
            or event.quote_asset != first.quote_asset
            for event in copied
        ):
            raise ValueError(
                "lifecycle evidence must share the same asset, venue, and quote"
            )
        return cls(
            canonical_asset_id=first.canonical_asset_id,
            venue=first.venue,
            quote_asset=first.quote_asset,
            events=tuple(
                sorted(
                    copied,
                    key=lambda event: (
                        event.effective_at,
                        event.observed_at,
                        event.event_id,
                    ),
                )
            ),
        )

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.canonical_asset_id), AssetId):
            raise TypeError("canonical_asset_id must be an AssetId")
        if not isinstance(cast(object, self.quote_asset), AssetId):
            raise TypeError("quote_asset must be an AssetId")
        normalized_venue = _text(self.venue, field="venue", lower=True)
        copied = tuple(self.events)
        if any(
            not isinstance(cast(object, event), InstrumentLifecycleEvent)
            for event in copied
        ):
            raise TypeError("events must contain InstrumentLifecycleEvent values")
        if any(
            event.canonical_asset_id != self.canonical_asset_id
            or event.venue != normalized_venue
            or event.quote_asset != self.quote_asset
            for event in copied
        ):
            raise ValueError(
                "lifecycle evidence must share the same asset, venue, and quote"
            )
        object.__setattr__(self, "venue", normalized_venue)
        object.__setattr__(self, "events", copied)

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(event.event_id for event in self.events)

    @property
    def has_historical_state_evidence(self) -> bool:
        return any(
            source_supports_historical_state(event.source_type) for event in self.events
        )


__all__ = [
    "AssetIdentityContinuity",
    "InstrumentLifecycleEvent",
    "InstrumentLifecycleEvidence",
    "LifecycleConfidence",
    "LifecycleEventType",
    "LifecycleSourceType",
    "lifecycle_source_priority",
    "source_supports_historical_state",
]
