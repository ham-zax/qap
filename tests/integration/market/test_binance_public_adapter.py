import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from qap.market import BarInterval
from qap.market.adapters.binance_public import (
    BinancePublicAdapter,
    BinancePublicDataError,
)
from qap.portfolio import AssetId


def _exchange_info(
    *,
    base: str = "BTC",
    quote: str = "USDT",
    spot_allowed: bool = True,
) -> dict[str, object]:
    return {
        "timezone": "UTC",
        "serverTime": 1_704_067_200_000,
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "baseAsset": base,
                "quoteAsset": quote,
                "isSpotTradingAllowed": spot_allowed,
                "permissionSets": [["SPOT"]],
            }
        ],
    }


def _klines() -> list[list[object]]:
    return [
        [
            1_704_067_200_000,
            "42000.0",
            "42100.0",
            "41900.0",
            "42050.0",
            "100.0",
            1_704_070_799_999,
            "4205000.0",
            1000,
            "50.0",
            "2102500.0",
            "0",
        ],
        [
            1_704_070_800_000,
            "42050.0",
            "42200.0",
            "42000.0",
            "42150.0",
            "101.0",
            1_704_074_399_999,
            "4257150.0",
            1001,
            "50.5",
            "2128575.0",
            "0",
        ],
        [
            1_704_074_400_000,
            "42150.0",
            "42300.0",
            "42100.0",
            "42250.0",
            "102.0",
            1_704_077_999_999,
            "4309500.0",
            1002,
            "51.0",
            "2154750.0",
            "0",
        ],
    ]


def _transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def test_exchange_info_maps_only_the_explicit_public_spot_orientation() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_exchange_info())

    with BinancePublicAdapter(transport=_transport(handler)) as adapter:
        instrument = adapter.fetch_instrument(
            venue_symbol="BTCUSDT",
            base=AssetId("BTC"),
            quote=AssetId("USDT"),
        )

    assert instrument.venue == "binance"
    assert instrument.venue_symbol == "BTCUSDT"
    assert instrument.base == AssetId("BTC")
    assert instrument.quote == AssetId("USDT")
    assert instrument.valid_from is None
    assert instrument.valid_to is None
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "GET"
    assert request.url.host == "data-api.binance.vision"
    assert request.url.path == "/api/v3/exchangeInfo"
    assert request.url.params["symbol"] == "BTCUSDT"
    assert "X-MBX-APIKEY" not in request.headers
    assert "signature" not in request.url.params


def test_exchange_info_rejects_orientation_mismatch_and_non_spot_symbol() -> None:
    def inverted(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_exchange_info(base="USDT", quote="BTC"))

    with BinancePublicAdapter(transport=_transport(inverted)) as adapter:
        with pytest.raises(BinancePublicDataError, match="orientation"):
            adapter.fetch_instrument(
                venue_symbol="BTCUSDT",
                base=AssetId("BTC"),
                quote=AssetId("USDT"),
            )

    def not_spot(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_exchange_info(spot_allowed=False))

    with BinancePublicAdapter(transport=_transport(not_spot)) as adapter:
        with pytest.raises(BinancePublicDataError, match="Spot trading"):
            adapter.fetch_instrument(
                venue_symbol="BTCUSDT",
                base=AssetId("BTC"),
                quote=AssetId("USDT"),
            )


def test_kline_response_preserves_source_timestamps_and_validates_series() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v3/exchangeInfo":
            return httpx.Response(200, json=_exchange_info())
        return httpx.Response(200, json=_klines())

    with BinancePublicAdapter(transport=_transport(handler)) as adapter:
        instrument = adapter.fetch_instrument(
            venue_symbol="BTCUSDT",
            base=AssetId("BTC"),
            quote=AssetId("USDT"),
        )
        series = adapter.fetch_klines(
            instrument=instrument,
            interval=BarInterval("1h"),
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end_exclusive=datetime(2024, 1, 1, 3, tzinfo=UTC),
        )

    assert len(series) == 3
    assert series.bars[0].candle_open_time == datetime(2024, 1, 1, tzinfo=UTC)
    assert series.bars[0].source_close_time == datetime(
        2024,
        1,
        1,
        0,
        59,
        59,
        999000,
        tzinfo=UTC,
    )
    assert series.bars[0].bar_end_exclusive == datetime(2024, 1, 1, 1, tzinfo=UTC)
    request = requests[-1]
    assert request.url.path == "/api/v3/klines"
    assert request.url.params["symbol"] == "BTCUSDT"
    assert request.url.params["interval"] == "1h"
    assert request.url.params["startTime"] == "1704067200000"
    assert request.url.params["endTime"] == "1704077999999"
    assert request.url.params["limit"] == "1000"
    assert "X-MBX-APIKEY" not in request.headers


def test_kline_gap_and_public_http_failures_are_explicit() -> None:
    gapped = _klines()
    del gapped[1]

    def gap_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=gapped)

    instrument = BinancePublicAdapter.instrument_from_payload(
        _exchange_info(),
        venue_symbol="BTCUSDT",
        base=AssetId("BTC"),
        quote=AssetId("USDT"),
    )
    with BinancePublicAdapter(transport=_transport(gap_handler)) as adapter:
        with pytest.raises(BinancePublicDataError, match="validation"):
            adapter.fetch_klines(
                instrument=instrument,
                interval=BarInterval("1h"),
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end_exclusive=datetime(2024, 1, 1, 3, tzinfo=UTC),
            )

    def rate_limited(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"code": -1003, "msg": "Too many requests"})

    with BinancePublicAdapter(transport=_transport(rate_limited)) as adapter:
        with pytest.raises(BinancePublicDataError, match="429"):
            adapter.fetch_instrument(
                venue_symbol="BTCUSDT",
                base=AssetId("BTC"),
                quote=AssetId("USDT"),
            )


def test_fetch_klines_rejects_future_end_before_any_network_call() -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json=[])

    instrument = BinancePublicAdapter.instrument_from_payload(
        _exchange_info(),
        venue_symbol="BTCUSDT",
        base=AssetId("BTC"),
        quote=AssetId("USDT"),
    )
    with BinancePublicAdapter(transport=_transport(handler)) as adapter:
        with pytest.raises(ValueError, match="completed historical bars"):
            adapter.fetch_klines(
                instrument=instrument,
                interval=BarInterval("1h"),
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end_exclusive=datetime(2999, 1, 1, tzinfo=UTC),
            )

    assert called is False


@pytest.mark.parametrize(
    "row",
    [_klines()[0][:-1], [*_klines()[0], "unexpected"]],
)
def test_kline_parser_requires_the_documented_twelve_field_shape(
    row: list[object],
) -> None:
    instrument = BinancePublicAdapter.instrument_from_payload(
        _exchange_info(),
        venue_symbol="BTCUSDT",
        base=AssetId("BTC"),
        quote=AssetId("USDT"),
    )

    with pytest.raises(BinancePublicDataError, match="exactly twelve"):
        BinancePublicAdapter.klines_from_payload(
            [row],
            instrument=instrument,
            interval=BarInterval("1h"),
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end_exclusive=datetime(2024, 1, 1, 1, tzinfo=UTC),
        )


@pytest.mark.parametrize("payload", [_klines()[1:], _klines()[:-1]])
def test_fetch_klines_rejects_partial_requested_window_coverage(
    payload: list[list[object]],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    instrument = BinancePublicAdapter.instrument_from_payload(
        _exchange_info(),
        venue_symbol="BTCUSDT",
        base=AssetId("BTC"),
        quote=AssetId("USDT"),
    )
    with BinancePublicAdapter(transport=_transport(handler)) as adapter:
        with pytest.raises(BinancePublicDataError, match="exact requested window"):
            adapter.fetch_klines(
                instrument=instrument,
                interval=BarInterval("1h"),
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end_exclusive=datetime(2024, 1, 1, 3, tzinfo=UTC),
            )


def test_kline_parser_rejects_a_bar_not_completed_by_the_requested_end() -> None:
    instrument = BinancePublicAdapter.instrument_from_payload(
        _exchange_info(),
        venue_symbol="BTCUSDT",
        base=AssetId("BTC"),
        quote=AssetId("USDT"),
    )

    with pytest.raises(BinancePublicDataError, match="completed"):
        BinancePublicAdapter.klines_from_payload(
            [_klines()[0]],
            instrument=instrument,
            interval=BarInterval("1h"),
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end_exclusive=datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=30),
        )


@pytest.mark.live_network
@pytest.mark.skipif(
    os.environ.get("QAP_LIVE_NETWORK") != "1",
    reason="set QAP_LIVE_NETWORK=1 to run the public unauthenticated smoke",
)
def test_live_public_exchange_info_smoke() -> None:
    with BinancePublicAdapter() as adapter:
        instrument = adapter.fetch_instrument(
            venue_symbol="BTCUSDT",
            base=AssetId("BTC"),
            quote=AssetId("USDT"),
        )

    assert instrument.venue_symbol == "BTCUSDT"
