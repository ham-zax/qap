"""Public unauthenticated Binance Spot WebSocket market-data stream client."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from qap.market.instruments import VenueInstrument
from qap.market.microstructure import (
    PublicBookSnapshot,
    public_book_snapshot_from_rows,
)

DEFAULT_BINANCE_WS_URL = "wss://data-stream.binance.vision"
_US_THRESHOLD = 100_000_000_000_000
_DEFAULT_CHANNELS = ("bookTicker", "depth20@100ms", "aggTrade")


class BinanceWsStreamError(RuntimeError):
    """Raised when public Binance WebSocket configuration or frames are invalid."""


@dataclass(frozen=True, slots=True)
class TimedL2Book:
    """One immutable L2 depth snapshot annotated with exchange and receive clocks."""

    instrument: VenueInstrument
    book: PublicBookSnapshot
    last_update_id: int
    exchange_time_us: int | None
    received_ns: int


@dataclass(frozen=True, slots=True)
class TimedBookTicker:
    """One top-of-book ticker update annotated with exchange and receive clocks."""

    venue_symbol: str
    update_id: int
    best_bid: float
    best_bid_qty: float
    best_ask: float
    best_ask_qty: float
    exchange_time_us: int | None
    received_ns: int


@dataclass(frozen=True, slots=True)
class TimedAggTrade:
    """One public aggregate trade event annotated with microsecond clocks."""

    venue_symbol: str
    agg_trade_id: int
    price: float
    quantity: float
    trade_time_us: int
    exchange_time_us: int | None
    is_buyer_maker: bool
    received_ns: int


def normalize_timestamp_us(value: object) -> int | None:
    """Normalize Binance millisecond or microsecond timestamps to microseconds."""

    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BinanceWsStreamError("stream timestamp must be a non-negative integer")
    return value * 1000 if value < _US_THRESHOLD else value


def build_stream_names(
    instruments: Sequence[VenueInstrument],
    *,
    channels: Sequence[str] = _DEFAULT_CHANNELS,
) -> tuple[str, ...]:
    """Build deterministic lowercase Binance combined stream names for spot symbols."""

    if not instruments:
        raise ValueError("at least one VenueInstrument is required")
    names: list[str] = []
    seen: set[str] = set()
    for instrument in instruments:
        if instrument.venue != "binance":
            raise ValueError("Binance WebSocket stream requires binance instruments")
        sym = instrument.venue_symbol.lower()
        for channel in channels:
            stream = f"{sym}@{channel}"
            if stream not in seen:
                seen.add(stream)
                names.append(stream)
    return tuple(names)


def build_binance_ws_url(
    instruments: Sequence[VenueInstrument],
    *,
    base_ws_url: str = DEFAULT_BINANCE_WS_URL,
    channels: Sequence[str] = _DEFAULT_CHANNELS,
) -> str:
    """Build the public market-data-only combined stream URL with microsecond units."""

    parsed = urlparse(base_ws_url)
    if parsed.scheme not in {"wss", "ws"} or not parsed.hostname:
        raise ValueError("base_ws_url must be a valid ws/wss URL")
    if parsed.username or parsed.password or "listenkey" in base_ws_url.lower():
        raise ValueError("private credentials or user streams are forbidden")
    host = parsed.hostname.lower()
    if host.endswith(("binance.com", "binance.us", "binance.vision")) and (
        host != "data-stream.binance.vision" or parsed.scheme != "wss"
    ):
        raise ValueError(
            "only Binance's public wss://data-stream.binance.vision endpoint is allowed"
        )
    streams = "/".join(build_stream_names(instruments, channels=channels))
    base = base_ws_url.rstrip("/")
    endpoint = base if base.endswith("/stream") else f"{base}/stream"
    return f"{endpoint}?streams={streams}&timeUnit=MICROSECOND"


def _int_field(mapping: Mapping[str, Any], key: str) -> int:
    val = mapping.get(key)
    if isinstance(val, bool) or not isinstance(val, int):
        raise BinanceWsStreamError(f"stream field {key!r} must be an integer")
    return val


def _float_field(mapping: Mapping[str, Any], key: str) -> float:
    val = mapping.get(key)
    if isinstance(val, bool) or not isinstance(val, (str, int, float)):
        raise BinanceWsStreamError(f"stream field {key!r} must be numeric")
    return float(val)


def _symbol_from(data: Mapping[str, Any], stream_name: str) -> str:
    raw = data.get("s")
    if isinstance(raw, str) and raw.strip():
        return raw.strip().upper()
    return stream_name.split("@", 1)[0].strip().upper() if "@" in stream_name else ""


def parse_binance_stream_message(
    raw_json: str,
    *,
    instruments_by_symbol: Mapping[str, VenueInstrument],
    received_ns: int,
    observed_at: datetime,
    last_update_ids: MutableMapping[str, int] | None = None,
) -> TimedL2Book | TimedBookTicker | TimedAggTrade | dict[str, Any] | None:
    """Parse one combined or control JSON frame from Binance Spot WebSocket."""

    try:
        parsed: object = json.loads(raw_json)
    except ValueError as exc:
        raise BinanceWsStreamError("stream frame is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise BinanceWsStreamError("stream frame must be a JSON object")
    envelope = cast(dict[str, Any], parsed)

    stream_name, data = "", envelope
    if "stream" in envelope and "data" in envelope:
        raw_stream, raw_data = envelope.get("stream"), envelope.get("data")
        if not isinstance(raw_stream, str) or not isinstance(raw_data, dict):
            raise BinanceWsStreamError("combined stream envelope is malformed")
        stream_name, data = raw_stream, cast(dict[str, Any], raw_data)

    if data.get("e") == "serverShutdown":
        out = dict(data)
        if "E" in data:
            out["exchange_time_us"] = normalize_timestamp_us(data.get("E"))
        return out

    symbol = _symbol_from(data, stream_name)
    exch_raw = data["E"] if "E" in data else data.get("T")
    if data.get("e") == "aggTrade" or stream_name.endswith("@aggTrade"):
        trade_time = normalize_timestamp_us(data.get("T"))
        if not symbol or trade_time is None:
            raise BinanceWsStreamError("aggTrade frame missing symbol or trade time")
        is_buyer_maker = data.get("m")
        if not isinstance(is_buyer_maker, bool):
            raise BinanceWsStreamError("aggTrade field 'm' must be boolean")
        return TimedAggTrade(
            symbol,
            _int_field(data, "a"),
            _float_field(data, "p"),
            _float_field(data, "q"),
            trade_time,
            normalize_timestamp_us(data.get("E")),
            is_buyer_maker,
            received_ns,
        )

    if ("lastUpdateId" in data and "bids" in data and "asks" in data) or (
        "@depth" in stream_name
    ):
        inst = {k.upper(): v for k, v in instruments_by_symbol.items()}.get(symbol)
        if inst is None:
            return None
        update_id = _int_field(data, "lastUpdateId")
        if last_update_ids is not None:
            latest = last_update_ids.get(symbol)
            if latest is not None and update_id < latest:
                return None
            last_update_ids[symbol] = update_id
        src = (
            f"binance-ws:{stream_name}"
            if stream_name
            else f"binance-ws:{symbol.lower()}@depth20@100ms"
        )
        book = public_book_snapshot_from_rows(
            instrument=inst,
            observed_at=observed_at,
            source_id=src,
            source_payload=data,
            bids=data.get("bids"),
            asks=data.get("asks"),
        )
        return TimedL2Book(
            inst, book, update_id, normalize_timestamp_us(exch_raw), received_ns
        )

    if ("u" in data and "b" in data and "a" in data) or stream_name.endswith(
        "@bookTicker"
    ):
        if not symbol:
            raise BinanceWsStreamError("bookTicker frame missing symbol")
        return TimedBookTicker(
            symbol,
            _int_field(data, "u"),
            _float_field(data, "b"),
            _float_field(data, "B"),
            _float_field(data, "a"),
            _float_field(data, "A"),
            normalize_timestamp_us(exch_raw),
            received_ns,
        )

    return None


def _append_segment(segment_path: Path, *, received_ns: int, raw_json: str) -> None:
    segment_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {"received_ns": received_ns, "raw": raw_json}, separators=(",", ":")
    )
    with segment_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


async def capture_binance_l2_window(
    instruments: Sequence[VenueInstrument],
    *,
    duration_seconds: float,
    segment_path: Path | None = None,
    base_ws_url: str = DEFAULT_BINANCE_WS_URL,
    stop_when_complete: bool = False,
    channels: Sequence[str] = _DEFAULT_CHANNELS,
) -> dict[str, TimedL2Book]:
    """Stream public Binance L2 books for a bounded window; return latest each."""

    if duration_seconds <= 0.0:
        raise ValueError("duration_seconds must be positive")
    instruments_by_symbol = {inst.venue_symbol.upper(): inst for inst in instruments}
    url = build_binance_ws_url(instruments, base_ws_url=base_ws_url, channels=channels)
    latest_books: dict[str, TimedL2Book] = {}
    latest_exch_us: dict[str, int] = {}
    last_update_ids: dict[str, int] = {}
    deadline = time.monotonic() + duration_seconds

    while time.monotonic() < deadline:
        try:
            async with connect(url, ping_interval=20, ping_timeout=20) as ws:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0.0:
                        return latest_books
                    try:
                        raw_msg = await asyncio.wait_for(ws.recv(), timeout=remaining)
                    except TimeoutError:
                        return latest_books
                    received_ns, observed_at = time.time_ns(), datetime.now(UTC)
                    raw_text = (
                        raw_msg
                        if isinstance(raw_msg, str)
                        else bytes(raw_msg).decode("utf-8")
                    )
                    if segment_path is not None:
                        _append_segment(
                            segment_path, received_ns=received_ns, raw_json=raw_text
                        )
                    parsed = parse_binance_stream_message(
                        raw_text,
                        instruments_by_symbol=instruments_by_symbol,
                        received_ns=received_ns,
                        observed_at=observed_at,
                        last_update_ids=last_update_ids,
                    )
                    if isinstance(parsed, dict) and parsed.get("e") == "serverShutdown":
                        break
                    if (
                        isinstance(parsed, TimedAggTrade)
                        and parsed.exchange_time_us is not None
                    ):
                        latest_exch_us[parsed.venue_symbol] = parsed.exchange_time_us
                    if isinstance(parsed, TimedL2Book):
                        sym = parsed.instrument.venue_symbol
                        if parsed.exchange_time_us is None and sym in latest_exch_us:
                            parsed = replace(
                                parsed, exchange_time_us=latest_exch_us[sym]
                            )
                        latest_books[sym] = parsed
                        if stop_when_complete and len(latest_books) == len(
                            instruments_by_symbol
                        ):
                            return latest_books
        except ConnectionClosed, OSError:
            if time.monotonic() >= deadline:
                break
            await asyncio.sleep(min(0.1, max(0.0, deadline - time.monotonic())))
    return latest_books


__all__ = [
    "BinanceWsStreamError",
    "DEFAULT_BINANCE_WS_URL",
    "TimedAggTrade",
    "TimedBookTicker",
    "TimedL2Book",
    "build_binance_ws_url",
    "build_stream_names",
    "capture_binance_l2_window",
    "normalize_timestamp_us",
    "parse_binance_stream_message",
]
