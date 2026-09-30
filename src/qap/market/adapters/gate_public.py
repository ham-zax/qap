"""Bounded unauthenticated Gate Spot public microstructure acquisition."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Self, cast

import httpx

from qap.market.adapters.spot_directory import (
    gate_currencies_from_payload,
    gate_directory_from_payload,
)
from qap.market.directory import CurrentSpotDirectoryObservation, SpotCurrencyEvidence
from qap.market.instruments import VenueInstrument
from qap.market.metadata import MarketMetadata
from qap.market.microstructure import (
    PublicBookSnapshot,
    public_book_snapshot_from_rows,
)
from qap.portfolio import AssetId

_PUBLIC_BASE_URL = "https://api.gateio.ws/api/v4"


class GatePublicDataError(RuntimeError):
    """Raised for explicit Gate public-source or response failures."""


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise GatePublicDataError(f"{field} must be a JSON object")
    return cast(Mapping[str, object], value)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GatePublicDataError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_decimal(value: object, *, field: str) -> Decimal | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise GatePublicDataError(f"{field} must be an exact decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise GatePublicDataError(f"{field} must be an exact decimal string") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise GatePublicDataError(f"{field} must be positive finite when present")
    return parsed


def _precision_step(value: object, *, field: str) -> Decimal:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise GatePublicDataError(f"{field} must be a non-negative integer")
    return Decimal(1).scaleb(-value)


def _validated_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _normalized_pair(value: object) -> str:
    pair = _text(value, field="currency pair").upper()
    if "_" not in pair:
        raise GatePublicDataError("Gate currency pair must contain '_' orientation")
    return pair


def _minimum(*values: Decimal | None) -> Decimal | None:
    present = tuple(value for value in values if value is not None)
    return min(present) if present else None


class GatePublicAdapter:
    """Synchronous Gate Spot public metadata/depth client with no auth capability."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        if client is not None and transport is not None:
            raise ValueError("provide either client or transport, not both")
        if client is None:
            self._client = httpx.Client(
                timeout=timeout_seconds,
                headers={"Accept": "application/json"},
                transport=transport,
            )
            self._owns_client = True
        else:
            self._client = client
            self._owns_client = False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _get_json(
        self,
        path: str,
        *,
        params: Mapping[str, str | int],
    ) -> object:
        try:
            response = self._client.get(f"{_PUBLIC_BASE_URL}{path}", params=params)
        except httpx.HTTPError as exc:
            raise GatePublicDataError(f"Gate public request failed: {exc}") from exc
        if response.status_code == 429:
            raise GatePublicDataError("Gate public request returned HTTP 429")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GatePublicDataError(
                f"Gate public request returned HTTP {response.status_code}"
            ) from exc
        try:
            payload: object = response.json()
        except ValueError as exc:
            raise GatePublicDataError(
                "Gate public response was not valid JSON"
            ) from exc
        return payload

    def fetch_market_metadata(
        self,
        *,
        venue_symbol: str,
        base: AssetId,
        quote: AssetId,
        venue_base_asset: str,
        venue_quote_asset: str,
    ) -> MarketMetadata:
        pair = _normalized_pair(venue_symbol)
        payload = self._get_json(f"/spot/currency_pairs/{pair}", params={})
        return self.market_metadata_from_payload(
            payload,
            venue_symbol=pair,
            base=base,
            quote=quote,
            venue_base_asset=venue_base_asset,
            venue_quote_asset=venue_quote_asset,
        )

    def fetch_spot_directory(
        self,
        *,
        observed_at: datetime | None = None,
    ) -> CurrentSpotDirectoryObservation:
        """Fetch current normal Gate Spot markets without guessing identity."""

        payload = self._get_json("/spot/currency_pairs", params={})
        currencies_payload = self._get_json("/spot/currencies", params={})
        return self.spot_directory_from_payload(
            payload, currencies_payload=currencies_payload, observed_at=observed_at
        )

    @staticmethod
    def spot_directory_from_payload(
        payload: object,
        *,
        observed_at: datetime | None = None,
        currencies_payload: object | None = None,
    ) -> CurrentSpotDirectoryObservation:
        """Normalize raw Gate pairs while preserving venue-local asset codes."""

        try:
            return gate_directory_from_payload(
                payload, currencies_payload=currencies_payload, observed_at=observed_at
            )
        except (TypeError, ValueError, OverflowError) as exc:
            raise GatePublicDataError(f"Gate directory is invalid: {exc}") from exc

    def fetch_spot_currencies(self) -> tuple[SpotCurrencyEvidence, ...]:
        payload = self._get_json("/spot/currencies", params={})
        return self.spot_currencies_from_payload(payload)

    @staticmethod
    def spot_currencies_from_payload(
        payload: object,
    ) -> tuple[SpotCurrencyEvidence, ...]:
        try:
            return gate_currencies_from_payload(payload)
        except (TypeError, ValueError) as exc:
            raise GatePublicDataError(f"Gate currencies are invalid: {exc}") from exc

    @staticmethod
    def market_metadata_from_payload(
        payload: object,
        *,
        venue_symbol: str,
        base: AssetId,
        quote: AssetId,
        venue_base_asset: str,
        venue_quote_asset: str,
    ) -> MarketMetadata:
        item = _mapping(payload, field="currency pair response")
        pair = _normalized_pair(venue_symbol)
        if _normalized_pair(item.get("id")) != pair:
            raise GatePublicDataError("currency pair id does not match request")
        venue_base = _text(item.get("base"), field="base").upper()
        venue_quote = _text(item.get("quote"), field="quote").upper()
        if (
            venue_base != _text(venue_base_asset, field="venue base").upper()
            or venue_quote != _text(venue_quote_asset, field="venue quote").upper()
        ):
            raise GatePublicDataError(
                "currency pair orientation does not match mapping"
            )
        pair_type = item.get("type")
        if pair_type is not None and _text(pair_type, field="type") != "normal":
            raise GatePublicDataError("only normal Gate Spot pairs are supported")

        quantity_step = _precision_step(
            item.get("amount_precision"), field="amount_precision"
        )
        price_tick = _precision_step(item.get("precision"), field="precision")
        minimum_quantity = _optional_decimal(
            item.get("min_base_amount"), field="min_base_amount"
        )
        maximum_quantity = _optional_decimal(
            item.get("max_base_amount"), field="max_base_amount"
        )
        minimum_notional = _optional_decimal(
            item.get("min_quote_amount"), field="min_quote_amount"
        )
        maximum_notional = _optional_decimal(
            item.get("max_quote_amount"), field="max_quote_amount"
        )
        market_maximum_quantity = _optional_decimal(
            item.get("market_order_max_stock", item.get("max_market_order_stock")),
            field="market_order_max_stock",
        )
        market_maximum_notional = _optional_decimal(
            item.get("market_order_max_money", item.get("max_market_order_money")),
            field="market_order_max_money",
        )
        return MarketMetadata(
            instrument=VenueInstrument(
                venue="gate",
                venue_symbol=pair,
                base=base,
                quote=quote,
            ),
            status=_text(item.get("trade_status"), field="trade_status"),
            price_tick=price_tick,
            minimum_price=None,
            maximum_price=None,
            quantity_step=quantity_step,
            minimum_quantity=minimum_quantity,
            maximum_quantity=_minimum(maximum_quantity, market_maximum_quantity),
            minimum_notional=minimum_notional,
            maximum_notional=_minimum(maximum_notional, market_maximum_notional),
            minimum_notional_applies_to_market=minimum_notional is not None,
            maximum_notional_applies_to_market=(
                maximum_notional is not None or market_maximum_notional is not None
            ),
            notional_average_price_minutes=0,
            market_quantity_step=quantity_step,
            market_minimum_quantity=minimum_quantity,
            market_maximum_quantity=market_maximum_quantity,
        )

    def fetch_l1_book(
        self,
        *,
        instrument: VenueInstrument,
        observed_at: datetime | None = None,
    ) -> PublicBookSnapshot:
        return self.fetch_shallow_depth(
            instrument=instrument,
            limit=1,
            observed_at=observed_at,
        )

    def fetch_shallow_depth(
        self,
        *,
        instrument: VenueInstrument,
        limit: int,
        observed_at: datetime | None = None,
    ) -> PublicBookSnapshot:
        if instrument.venue != "gate":
            raise ValueError("Gate adapter requires a gate VenueInstrument")
        if isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("depth limit must be an integer between 1 and 100")
        payload = self._get_json(
            "/spot/order_book",
            params={
                "currency_pair": instrument.venue_symbol,
                "interval": "0",
                "limit": limit,
            },
        )
        item = _mapping(payload, field="order book response")
        observed = (
            datetime.now(UTC)
            if observed_at is None
            else _validated_utc(observed_at, field="observed_at")
        )
        return public_book_snapshot_from_rows(
            instrument=instrument,
            observed_at=observed,
            source_id=f"gate:/api/v4/spot/order_book?limit={limit}",
            source_payload=payload,
            bids=item.get("bids"),
            asks=item.get("asks"),
        )


__all__ = ["GatePublicAdapter", "GatePublicDataError"]
