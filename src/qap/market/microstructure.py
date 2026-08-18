"""Immutable public microstructure evidence with exact provenance."""

import json
import math
import string
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import cast

from qap.market.instruments import VenueInstrument


def _validated_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _fingerprint(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 64 or any(
        character not in string.hexdigits.lower() for character in normalized
    ):
        raise ValueError(f"{field} must be a SHA-256 hex fingerprint")
    return normalized


def _positive_finite(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{field} must be positive finite")
    return numeric


@dataclass(frozen=True, slots=True)
class BookLevel:
    """One immutable public-book price level."""

    price: float
    quantity: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "price", _positive_finite(self.price, field="price"))
        object.__setattr__(
            self,
            "quantity",
            _positive_finite(self.quantity, field="quantity"),
        )


@dataclass(frozen=True, slots=True)
class PublicBookSnapshot:
    """One bounded public order-book observation; evidence only, never authority."""

    instrument: VenueInstrument
    observed_at: datetime
    source_id: str
    source_fingerprint: str
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.instrument), VenueInstrument):
            raise TypeError("instrument must be a VenueInstrument")
        observed_at = _validated_utc(self.observed_at, field="observed_at")
        source_id = _text(self.source_id, field="source_id")
        source_fingerprint = _fingerprint(
            self.source_fingerprint,
            field="source_fingerprint",
        )
        bids = tuple(self.bids)
        asks = tuple(self.asks)
        if not bids or not asks:
            raise ValueError("public book snapshot requires non-empty bids and asks")
        if any(
            not isinstance(cast(object, level), BookLevel) for level in (*bids, *asks)
        ):
            raise TypeError("book levels must be BookLevel values")
        if any(left.price <= right.price for left, right in zip(bids, bids[1:])):
            raise ValueError("bids must be strictly descending")
        if any(left.price >= right.price for left, right in zip(asks, asks[1:])):
            raise ValueError("asks must be strictly ascending")
        if bids[0].price >= asks[0].price:
            raise ValueError("best bid must be below best ask")
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "source_fingerprint", source_fingerprint)
        object.__setattr__(self, "bids", bids)
        object.__setattr__(self, "asks", asks)

    @property
    def best_bid(self) -> float:
        return self.bids[0].price

    @property
    def best_ask(self) -> float:
        return self.asks[0].price

    @property
    def mid_price(self) -> float:
        return (self.best_bid + self.best_ask) / 2.0

    @property
    def snapshot_id(self) -> str:
        payload = {
            "identity_version": "qap.market.public-book-snapshot.v1",
            "venue": self.instrument.venue,
            "venue_symbol": self.instrument.venue_symbol,
            "base_asset": self.instrument.base.key,
            "quote_asset": self.instrument.quote.key,
            "observed_at": self.observed_at.isoformat(),
            "source_id": self.source_id,
            "source_fingerprint": self.source_fingerprint,
            "bids": [[level.price.hex(), level.quantity.hex()] for level in self.bids],
            "asks": [[level.price.hex(), level.quantity.hex()] for level in self.asks],
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return sha256(encoded).hexdigest()


__all__ = ["BookLevel", "PublicBookSnapshot"]
