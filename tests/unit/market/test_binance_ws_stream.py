"""Deterministic Binance WebSocket frame parsing and bounded capture (no network)."""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any

import pytest

from qap.market import VenueInstrument
from qap.market import binance_ws_stream as stream_module
from qap.market.binance_ws_stream import (
    BinanceWsStreamError,
    TimedAggTrade,
    TimedBookTicker,
    TimedL2Book,
    build_binance_ws_url,
    build_stream_names,
    capture_binance_l2_window,
    normalize_timestamp_us,
    parse_binance_stream_message,
)
from qap.portfolio import AssetId

BTC = VenueInstrument("binance", "BTCUSDT", AssetId("BTC"), AssetId("USDT"))
ETH = VenueInstrument("binance", "ETHUSDT", AssetId("ETH"), AssetId("USDT"))
BY_SYMBOL = {"BTCUSDT": BTC, "ETHUSDT": ETH}
NOW = datetime(2026, 11, 15, 12, tzinfo=UTC)
RECV_NS = 1_700_000_000_000_000_000


def depth_frame(symbol: str = "btcusdt", update_id: int = 100, **extra: Any) -> str:
    return json.dumps(
        {
            "stream": f"{symbol}@depth20@100ms",
            "data": {
                "lastUpdateId": update_id,
                "bids": [["100.0", "1.0"], ["99.0", "2.0"]],
                "asks": [["101.0", "1.0"], ["102.0", "2.0"]],
                **extra,
            },
        }
    )


def parse(raw: str, ids: dict[str, int] | None = None) -> object:
    return parse_binance_stream_message(
        raw,
        instruments_by_symbol=BY_SYMBOL,
        received_ns=RECV_NS,
        observed_at=NOW,
        last_update_ids=ids,
    )


def test_timestamps_normalize_milliseconds_and_microseconds_to_microseconds() -> None:
    assert normalize_timestamp_us(1_700_000_000_123) == 1_700_000_000_123_000
    assert normalize_timestamp_us(1_700_000_000_123_456) == 1_700_000_000_123_456
    assert normalize_timestamp_us(None) is None
    for bad in (-1, True, "1700000000000", 1.5):
        with pytest.raises(BinanceWsStreamError):
            normalize_timestamp_us(bad)


def test_stream_names_are_lowercase_deterministic_and_deduplicated() -> None:
    names = build_stream_names(
        [BTC, ETH, BTC], channels=("bookTicker", "depth20@100ms")
    )
    assert names == (
        "btcusdt@bookTicker",
        "btcusdt@depth20@100ms",
        "ethusdt@bookTicker",
        "ethusdt@depth20@100ms",
    )
    with pytest.raises(ValueError, match="at least one"):
        build_stream_names([])
    other = VenueInstrument("kraken", "BTCUSDT", AssetId("BTC"), AssetId("USDT"))
    with pytest.raises(ValueError, match="binance instruments"):
        build_stream_names([other])


def test_url_is_public_market_data_only_with_microsecond_time_unit() -> None:
    url = build_binance_ws_url([BTC], channels=("depth20@100ms",))
    assert url == (
        "wss://data-stream.binance.vision/stream"
        "?streams=btcusdt@depth20@100ms&timeUnit=MICROSECOND"
    )
    assert build_binance_ws_url([BTC], base_ws_url="ws://127.0.0.1:9/").startswith(
        "ws://127.0.0.1:9/stream?streams=btcusdt@bookTicker/"
    )
    for forbidden in (
        "wss://stream.binance.com:9443",
        "ws://data-stream.binance.vision",
        "wss://user:pw@127.0.0.1",
        "wss://127.0.0.1/ws/listenKey123",
        "https://example.com",
    ):
        with pytest.raises(ValueError):
            build_binance_ws_url([BTC], base_ws_url=forbidden)


def test_depth20_frame_parses_to_timed_l2_book_with_both_clocks() -> None:
    parsed = parse(depth_frame(E=1_700_000_000_123_456))
    assert isinstance(parsed, TimedL2Book)
    assert parsed.instrument == BTC
    assert parsed.last_update_id == 100
    assert parsed.exchange_time_us == 1_700_000_000_123_456
    assert parsed.received_ns == RECV_NS
    assert parsed.book.observed_at == NOW
    assert (parsed.book.best_bid, parsed.book.best_ask) == (100.0, 101.0)
    assert parsed.book.source_id == "binance-ws:btcusdt@depth20@100ms"


def test_stale_last_update_id_is_rejected_but_equal_id_is_kept() -> None:
    ids: dict[str, int] = {}
    assert isinstance(parse(depth_frame(update_id=100), ids), TimedL2Book)
    assert ids == {"BTCUSDT": 100}
    assert parse(depth_frame(update_id=99), ids) is None
    assert ids == {"BTCUSDT": 100}
    assert isinstance(parse(depth_frame(update_id=100), ids), TimedL2Book)
    assert isinstance(parse(depth_frame(update_id=101), ids), TimedL2Book)
    assert ids["BTCUSDT"] == 101
    # Sequences are tracked per symbol.
    assert isinstance(parse(depth_frame("ethusdt", update_id=5), ids), TimedL2Book)


def test_depth_for_an_unsubscribed_symbol_is_ignored() -> None:
    assert parse(depth_frame("solusdt")) is None


def test_book_ticker_frame_parses_top_of_book() -> None:
    raw = json.dumps(
        {
            "stream": "btcusdt@bookTicker",
            "data": {
                "u": 400900217,
                "s": "BTCUSDT",
                "b": "100.0",
                "B": "1.5",
                "a": "101.0",
                "A": "2.5",
            },
        }
    )
    parsed = parse(raw)
    assert parsed == TimedBookTicker(
        "BTCUSDT", 400900217, 100.0, 1.5, 101.0, 2.5, None, RECV_NS
    )


@pytest.mark.parametrize(
    ("event_ms_or_us", "trade_ms_or_us", "event_us", "trade_us"),
    [
        (
            1_700_000_000_000,
            1_700_000_000_001,
            1_700_000_000_000_000,
            1_700_000_000_001_000,
        ),
        (
            1_700_000_000_000_123,
            1_700_000_000_000_456,
            1_700_000_000_000_123,
            1_700_000_000_000_456,
        ),
    ],
)
def test_agg_trade_accepts_millisecond_and_microsecond_units(
    event_ms_or_us: int, trade_ms_or_us: int, event_us: int, trade_us: int
) -> None:
    raw = json.dumps(
        {
            "e": "aggTrade",
            "E": event_ms_or_us,
            "s": "BTCUSDT",
            "a": 12345,
            "p": "100.5",
            "q": "0.25",
            "T": trade_ms_or_us,
            "m": True,
        }
    )
    parsed = parse(raw)
    assert parsed == TimedAggTrade(
        "BTCUSDT", 12345, 100.5, 0.25, trade_us, event_us, True, RECV_NS
    )


def test_server_shutdown_control_frame_is_surfaced_with_normalized_clock() -> None:
    parsed = parse(json.dumps({"e": "serverShutdown", "E": 1_700_000_000_000}))
    assert isinstance(parsed, dict)
    assert parsed["e"] == "serverShutdown"
    assert parsed["exchange_time_us"] == 1_700_000_000_000_000


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "[1, 2]",
        json.dumps({"stream": 5, "data": {}}),
        json.dumps(
            {
                "e": "aggTrade",
                "s": "BTCUSDT",
                "a": 1,
                "p": "1",
                "q": "1",
                "T": 1_700_000_000_000,
                "m": "yes",
            }
        ),
        json.dumps(
            {"stream": "btcusdt@depth20@100ms", "data": {"bids": [], "asks": []}}
        ),
    ],
)
def test_malformed_frames_fail_closed(raw: str) -> None:
    with pytest.raises(BinanceWsStreamError):
        parse(raw)


class FakeSocket:
    """Async context manager that replays frames, then blocks like an idle socket."""

    def __init__(self, frames: list[str]) -> None:
        self.frames = list(frames)

    async def __aenter__(self) -> "FakeSocket":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def recv(self) -> str:
        if self.frames:
            return self.frames.pop(0)
        await asyncio.sleep(3600)
        raise AssertionError("unreachable")


def test_capture_returns_latest_book_per_symbol_and_records_raw_segment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    frames = [
        depth_frame("btcusdt", 1),
        depth_frame("btcusdt", 0),  # stale: dropped
        depth_frame("btcusdt", 2),
        depth_frame("ethusdt", 7),
    ]
    urls: list[str] = []

    def fake_connect(url: str, **_: object) -> FakeSocket:
        urls.append(url)
        return FakeSocket(frames)

    monkeypatch.setattr(stream_module, "connect", fake_connect)
    segment = tmp_path / "segments" / "raw.jsonl"
    books = asyncio.run(
        capture_binance_l2_window(
            [BTC, ETH],
            duration_seconds=5.0,
            segment_path=segment,
            stop_when_complete=True,
            channels=("depth20@100ms",),
        )
    )
    assert sorted(books) == ["BTCUSDT", "ETHUSDT"]
    assert books["BTCUSDT"].last_update_id == 2
    assert books["ETHUSDT"].last_update_id == 7
    assert urls == [
        "wss://data-stream.binance.vision/stream"
        "?streams=btcusdt@depth20@100ms/ethusdt@depth20@100ms&timeUnit=MICROSECOND"
    ]
    rows = [json.loads(line) for line in segment.read_text("utf-8").splitlines()]
    assert [json.loads(r["raw"])["data"]["lastUpdateId"] for r in rows] == [1, 0, 2, 7]
    assert all(isinstance(r["received_ns"], int) for r in rows)


def test_capture_window_expires_with_partial_books(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_connect(url: str, **_: object) -> FakeSocket:
        del url
        return FakeSocket([depth_frame()])

    monkeypatch.setattr(stream_module, "connect", fake_connect)
    books = asyncio.run(capture_binance_l2_window([BTC, ETH], duration_seconds=0.2))
    assert list(books) == ["BTCUSDT"]


def test_capture_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError, match="positive"):
        asyncio.run(capture_binance_l2_window([BTC], duration_seconds=0.0))
