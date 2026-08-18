"""Immutable public microstructure evidence with exact provenance."""

import json
import math
import string
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import cast

from qap.market.instruments import VenueInstrument
from qap.market.metadata import MarketMetadata


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


def public_payload_fingerprint(payload: object) -> str:
    """Return the canonical fingerprint for one public JSON payload."""

    try:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("public payload must be canonical JSON data") from exc
    return sha256(encoded).hexdigest()


def _decimal_text(value: object) -> str | None:
    return None if value is None else str(value)


def _metadata_payload(metadata: MarketMetadata) -> dict[str, object]:
    return {
        "venue": metadata.instrument.venue,
        "venue_symbol": metadata.instrument.venue_symbol,
        "base_asset": metadata.instrument.base.key,
        "quote_asset": metadata.instrument.quote.key,
        "status": metadata.status,
        "price_tick": str(metadata.price_tick),
        "minimum_price": _decimal_text(metadata.minimum_price),
        "maximum_price": _decimal_text(metadata.maximum_price),
        "quantity_step": str(metadata.quantity_step),
        "minimum_quantity": _decimal_text(metadata.minimum_quantity),
        "maximum_quantity": _decimal_text(metadata.maximum_quantity),
        "minimum_notional": _decimal_text(metadata.minimum_notional),
        "maximum_notional": _decimal_text(metadata.maximum_notional),
        "minimum_notional_applies_to_market": (
            metadata.minimum_notional_applies_to_market
        ),
        "maximum_notional_applies_to_market": (
            metadata.maximum_notional_applies_to_market
        ),
        "notional_average_price_minutes": metadata.notional_average_price_minutes,
        "market_quantity_step": _decimal_text(metadata.market_quantity_step),
        "market_minimum_quantity": _decimal_text(metadata.market_minimum_quantity),
        "market_maximum_quantity": _decimal_text(metadata.market_maximum_quantity),
    }


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


@dataclass(frozen=True, slots=True)
class PublicMarketMetadataSnapshot:
    """One observed public instrument-state/constraint record."""

    metadata: MarketMetadata
    observed_at: datetime
    source_id: str
    source_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.metadata), MarketMetadata):
            raise TypeError("metadata must be MarketMetadata")
        object.__setattr__(
            self,
            "observed_at",
            _validated_utc(self.observed_at, field="observed_at"),
        )
        object.__setattr__(self, "source_id", _text(self.source_id, field="source_id"))
        object.__setattr__(
            self,
            "source_fingerprint",
            _fingerprint(self.source_fingerprint, field="source_fingerprint"),
        )

    @property
    def snapshot_id(self) -> str:
        payload = {
            "identity_version": "qap.market.public-metadata-snapshot.v1",
            "observed_at": self.observed_at.isoformat(),
            "source_id": self.source_id,
            "source_fingerprint": self.source_fingerprint,
            **_metadata_payload(self.metadata),
        }
        return public_payload_fingerprint(payload)


def public_market_metadata_snapshot(
    *,
    metadata: MarketMetadata,
    observed_at: datetime,
    source_id: str,
    source_payload: object,
) -> PublicMarketMetadataSnapshot:
    """Bind normalized public constraints to exact observation provenance."""

    return PublicMarketMetadataSnapshot(
        metadata=metadata,
        observed_at=observed_at,
        source_id=source_id,
        source_fingerprint=public_payload_fingerprint(source_payload),
    )


def public_market_metadata_snapshot_from_metadata(
    *,
    metadata: MarketMetadata,
    observed_at: datetime,
    source_id: str,
) -> PublicMarketMetadataSnapshot:
    """Bind normalized public constraints to an immutable observation."""

    return PublicMarketMetadataSnapshot(
        metadata=metadata,
        observed_at=observed_at,
        source_id=source_id,
        source_fingerprint=public_payload_fingerprint(_metadata_payload(metadata)),
    )


def _book_number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise TypeError(f"{field} must be a JSON number or decimal string")
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be numeric") from exc


def _book_levels(value: object, *, side: str) -> tuple[BookLevel, ...]:
    if not isinstance(value, list):
        raise TypeError(f"{side} must be a JSON list")
    rows = cast(list[object], value)
    levels: list[BookLevel] = []
    for position, raw_level in enumerate(rows):
        if not isinstance(raw_level, list):
            raise ValueError(f"{side} level {position} must contain price and quantity")
        items = cast(list[object], raw_level)
        if len(items) != 2:
            raise ValueError(f"{side} level {position} must contain price and quantity")
        levels.append(
            BookLevel(
                price=_book_number(items[0], field=f"{side}[{position}].price"),
                quantity=_book_number(items[1], field=f"{side}[{position}].quantity"),
            )
        )
    return tuple(levels)


def public_book_snapshot_from_rows(
    *,
    instrument: VenueInstrument,
    observed_at: datetime,
    source_id: str,
    source_payload: object,
    bids: object,
    asks: object,
) -> PublicBookSnapshot:
    """Normalize exact public bid/ask rows into immutable QAP evidence."""

    return PublicBookSnapshot(
        instrument=instrument,
        observed_at=observed_at,
        source_id=source_id,
        source_fingerprint=public_payload_fingerprint(source_payload),
        bids=_book_levels(bids, side="bids"),
        asks=_book_levels(asks, side="asks"),
    )


__all__ = [
    "BookLevel",
    "PublicBookSnapshot",
    "PublicMarketMetadataSnapshot",
    "public_book_snapshot_from_rows",
    "public_market_metadata_snapshot",
    "public_market_metadata_snapshot_from_metadata",
    "public_payload_fingerprint",
]
