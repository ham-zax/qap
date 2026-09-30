"""Pure parsing of venue-local directory evidence, separate from acquisition."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import cast

from qap.market.directory import (
    CurrencyChainEvidence,
    CurrentSpotDirectoryObservation,
    CurrentSpotMarket,
    SpotCurrencyEvidence,
)
from qap.market.microstructure import public_payload_fingerprint


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("directory item must be a JSON object")
    return cast(Mapping[str, object], value)


def _list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("directory rows must be a JSON array")
    return cast(list[object], value)


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("directory text must be a non-empty string")
    return value.strip()


def _optional_text(value: object) -> str | None:
    if value is None or value == "":
        return None
    return _text(value)


def _optional_bool(value: object) -> bool | None:
    if value is not None and not isinstance(value, bool):
        raise ValueError("directory flag must be a boolean")
    return value


def _texts(value: object) -> tuple[str, ...]:
    return tuple(_text(v) for v in _list(value))


def _buy_start(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("buy_start must be a non-negative Unix timestamp in seconds")
    return (
        None
        if value == 0
        else datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=value)
    )


def gate_currencies_from_payload(payload: object) -> tuple[SpotCurrencyEvidence, ...]:
    currencies: list[SpotCurrencyEvidence] = []
    for raw in _list(payload):
        item = _mapping(raw)
        chains: list[CurrencyChainEvidence] = []
        for raw_chain in _list(item.get("chains", [])):
            chain = _mapping(raw_chain)
            chains.append(
                CurrencyChainEvidence(
                    chain=_text(chain.get("name")),
                    contract_address=_optional_text(chain.get("addr")),
                )
            )
        currencies.append(
            SpotCurrencyEvidence(
                venue_asset_code=_text(item.get("currency")),
                name=_optional_text(item.get("name")),
                chain=_optional_text(item.get("chain")),
                chains=tuple(chains),
                categories=_texts(item.get("category", [])),
                delisted=_optional_bool(item.get("delisted")),
                trade_disabled=_optional_bool(item.get("trade_disabled")),
            )
        )
    codes = tuple(c.venue_asset_code for c in currencies)
    if len(set(codes)) != len(codes):
        raise ValueError("currency evidence must have unique venue asset codes")
    return tuple(currencies)


def gate_directory_from_payload(
    payload: object,
    *,
    currencies_payload: object | None = None,
    observed_at: datetime | None = None,
) -> CurrentSpotDirectoryObservation:
    currencies = {
        c.venue_asset_code: c
        for c in (
            ()
            if currencies_payload is None
            else gate_currencies_from_payload(currencies_payload)
        )
    }
    markets: list[CurrentSpotMarket] = []
    for raw_pair in _list(payload):
        item = _mapping(raw_pair)
        pair_type = _optional_text(item.get("type"))
        if pair_type is not None and pair_type != "normal":
            continue
        status = _text(item.get("trade_status"))
        symbol = _text(item.get("id")).upper()
        if "_" not in symbol:
            raise ValueError("Gate currency pair must contain '_' orientation")
        base = _text(item.get("base")).upper()
        quote = _text(item.get("quote")).upper()
        base_currency = currencies.get(base)
        quote_currency = currencies.get(quote)
        markets.append(
            CurrentSpotMarket(
                venue="gate",
                venue_symbol=symbol,
                venue_base_asset=base,
                venue_quote_asset=quote,
                status=status,
                trading=status.lower() == "tradable",
                base_name=_optional_text(item.get("base_name"))
                or (None if base_currency is None else base_currency.name),
                quote_name=_optional_text(item.get("quote_name"))
                or (None if quote_currency is None else quote_currency.name),
                buy_start=_buy_start(item.get("buy_start")),
                pair_type=pair_type,
                base_currency=base_currency,
                quote_currency=quote_currency,
            )
        )
    source_id = "gate:/api/v4/spot/currency_pairs"
    source_payload = payload
    if currencies_payload is not None:
        source_id += "+/api/v4/spot/currencies"
        source_payload = {"currency_pairs": payload, "currencies": currencies_payload}
    return CurrentSpotDirectoryObservation(
        venue="gate",
        observed_at=datetime.now(UTC) if observed_at is None else observed_at,
        source_id=source_id,
        source_fingerprint=public_payload_fingerprint(source_payload),
        markets=tuple(markets),
    )


def binance_directory_from_payload(
    payload: object,
    *,
    observed_at: datetime | None = None,
) -> CurrentSpotDirectoryObservation:
    markets: list[CurrentSpotMarket] = []
    for raw_symbol in _list(_mapping(payload).get("symbols")):
        item = _mapping(raw_symbol)
        status = _text(item.get("status"))
        spot_allowed = _optional_bool(item.get("isSpotTradingAllowed"))
        if spot_allowed is None:
            raise ValueError("isSpotTradingAllowed must be a boolean")
        markets.append(
            CurrentSpotMarket(
                venue="binance",
                venue_symbol=_text(item.get("symbol")),
                venue_base_asset=_text(item.get("baseAsset")),
                venue_quote_asset=_text(item.get("quoteAsset")),
                status=status,
                trading=status == "TRADING" and spot_allowed,
                spot_trading_allowed=spot_allowed,
                permissions=_texts(item.get("permissions", [])),
                permission_sets=tuple(
                    _texts(group) for group in _list(item.get("permissionSets", []))
                ),
            )
        )
    return CurrentSpotDirectoryObservation(
        venue="binance",
        observed_at=datetime.now(UTC) if observed_at is None else observed_at,
        source_id="binance:/api/v3/exchangeInfo",
        source_fingerprint=public_payload_fingerprint(payload),
        markets=tuple(markets),
    )
