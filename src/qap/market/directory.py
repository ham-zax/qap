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


def _boolean(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be a boolean")
    return value


@dataclass(frozen=True, slots=True)
class CurrencyChainEvidence:
    """Venue-reported chain and address, preserving case-sensitive addresses."""

    chain: str
    contract_address: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "chain", _text(self.chain, field="chain"))
        if self.contract_address is not None:
            object.__setattr__(
                self,
                "contract_address",
                _text(self.contract_address, field="contract_address"),
            )


@dataclass(frozen=True, slots=True)
class SpotCurrencyEvidence:
    """Descriptive evidence only; this does not establish economic identity."""

    venue_asset_code: str
    name: str | None = None
    chain: str | None = None
    chains: tuple[CurrencyChainEvidence, ...] = ()
    categories: tuple[str, ...] = ()
    delisted: bool | None = None
    trade_disabled: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "venue_asset_code",
            _text(self.venue_asset_code, field="venue_asset_code").upper(),
        )
        for field in ("name", "chain"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _text(value, field=field))
        for field in ("delisted", "trade_disabled"):
            value = getattr(self, field)
            if value is not None and not isinstance(value, bool):
                raise TypeError(f"{field} must be a boolean when present")
        object.__setattr__(self, "chains", tuple(self.chains))
        object.__setattr__(
            self,
            "categories",
            tuple(_text(v, field="category") for v in self.categories),
        )


@dataclass(frozen=True, slots=True)
class CurrentSpotMarket:
    """One venue-local Spot market without assuming economic asset identity."""

    venue: str
    venue_symbol: str
    venue_base_asset: str
    venue_quote_asset: str
    status: str
    trading: bool
    base_name: str | None = None
    quote_name: str | None = None
    buy_start: datetime | None = None
    pair_type: str | None = None
    spot_trading_allowed: bool | None = None
    permissions: tuple[str, ...] = ()
    permission_sets: tuple[tuple[str, ...], ...] = ()
    base_currency: SpotCurrencyEvidence | None = None
    quote_currency: SpotCurrencyEvidence | None = None

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
        for field in ("base_name", "quote_name", "pair_type"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _text(value, field=field))
        if self.buy_start is not None:
            object.__setattr__(
                self, "buy_start", _utc(self.buy_start, field="buy_start")
            )
        _boolean(self.trading, field="trading")
        if self.spot_trading_allowed is not None:
            _boolean(self.spot_trading_allowed, field="spot_trading_allowed")
        for code, currency in (
            (venue_base, self.base_currency),
            (venue_quote, self.quote_currency),
        ):
            if currency is not None and currency.venue_asset_code != code:
                raise ValueError("currency evidence must match the venue asset code")
        object.__setattr__(self, "permissions", tuple(self.permissions))
        object.__setattr__(
            self, "permission_sets", tuple(tuple(s) for s in self.permission_sets)
        )


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


__all__ = [
    "CurrencyChainEvidence",
    "CurrentSpotDirectoryObservation",
    "CurrentSpotMarket",
    "SpotCurrencyEvidence",
]
