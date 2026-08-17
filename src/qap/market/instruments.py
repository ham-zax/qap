"""Explicit mappings between stable QAP assets and venue instruments."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from qap.portfolio import AssetId, PairId, PairOrientation


def _normalized_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _validated_assets(base: object, quote: object) -> tuple[AssetId, AssetId]:
    if not isinstance(base, AssetId) or not isinstance(quote, AssetId):
        raise TypeError("instrument base and quote must be AssetId values")
    if base == quote:
        raise ValueError("instrument base and quote must be distinct")
    return base, quote


def _validated_optional_utc(timestamp: object, *, field: str) -> datetime | None:
    if timestamp is None:
        return None
    if not isinstance(timestamp, datetime):
        raise TypeError(f"{field} validity timestamp must be a datetime")
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError(f"{field} validity timestamp must be timezone-aware UTC")
    return timestamp.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class VenueInstrument:
    """One observed venue symbol with explicit stable base/quote identity."""

    venue: str
    venue_symbol: str
    base: AssetId
    quote: AssetId
    valid_from: datetime | None = None
    valid_to: datetime | None = None

    def __post_init__(self) -> None:
        venue = _normalized_text(self.venue, field="venue").lower()
        venue_symbol = _normalized_text(self.venue_symbol, field="venue symbol")
        base, quote = _validated_assets(self.base, self.quote)
        valid_from = _validated_optional_utc(self.valid_from, field="valid_from")
        valid_to = _validated_optional_utc(self.valid_to, field="valid_to")
        if valid_from is not None and valid_to is not None and valid_from >= valid_to:
            raise ValueError("instrument validity requires valid_from before valid_to")

        object.__setattr__(self, "venue", venue)
        object.__setattr__(self, "venue_symbol", venue_symbol)
        object.__setattr__(self, "base", base)
        object.__setattr__(self, "quote", quote)
        object.__setattr__(self, "valid_from", valid_from)
        object.__setattr__(self, "valid_to", valid_to)

    @property
    def orientation(self) -> PairOrientation:
        """Return the venue's explicit BASE/QUOTE orientation."""

        return PairOrientation(base=self.base, quote=self.quote)

    @property
    def pair_id(self) -> PairId:
        """Return the orientation-independent relationship identity."""

        return self.orientation.pair_id
