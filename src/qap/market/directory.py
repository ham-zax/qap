"""Current public Spot directory observations before canonical asset resolution."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


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


def _fingerprint(value: object) -> str:
    normalized = _text(value, field="source_fingerprint", lower=True)
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError("source_fingerprint must be a SHA-256 hex string")
    return normalized


@dataclass(frozen=True, slots=True)
class CurrentSpotMarket:
    """One venue-local Spot market without assuming economic asset identity."""

    venue: str
    venue_symbol: str
    venue_base_asset: str
    venue_quote_asset: str
    status: str
    trading: bool

    def __post_init__(self) -> None:
        venue = _text(self.venue, field="venue", lower=True)
        venue_symbol = _text(self.venue_symbol, field="venue_symbol").upper()
        venue_base = _text(self.venue_base_asset, field="venue_base_asset").upper()
        venue_quote = _text(self.venue_quote_asset, field="venue_quote_asset").upper()
        if venue_base == venue_quote:
            raise ValueError("venue base and quote assets must be distinct")
        object.__setattr__(self, "venue", venue)
        object.__setattr__(self, "venue_symbol", venue_symbol)
        object.__setattr__(self, "venue_base_asset", venue_base)
        object.__setattr__(self, "venue_quote_asset", venue_quote)
        object.__setattr__(self, "status", _text(self.status, field="status"))


@dataclass(frozen=True, slots=True)
class CurrentSpotDirectoryObservation:
    """One exact current-directory observation from a supported public venue."""

    venue: str
    observed_at: datetime
    source_id: str
    source_fingerprint: str
    markets: tuple[CurrentSpotMarket, ...]

    def __post_init__(self) -> None:
        venue = _text(self.venue, field="venue", lower=True)
        markets = tuple(self.markets)
        if any(market.venue != venue for market in markets):
            raise ValueError("directory markets must match the observation venue")
        symbols = tuple(market.venue_symbol for market in markets)
        if len(symbols) != len(set(symbols)):
            raise ValueError("directory markets must have unique venue symbols")

        object.__setattr__(self, "venue", venue)
        object.__setattr__(
            self,
            "observed_at",
            _utc(self.observed_at, field="observed_at"),
        )
        object.__setattr__(self, "source_id", _text(self.source_id, field="source_id"))
        object.__setattr__(
            self, "source_fingerprint", _fingerprint(self.source_fingerprint)
        )
        object.__setattr__(self, "markets", markets)


__all__ = ["CurrentSpotDirectoryObservation", "CurrentSpotMarket"]
