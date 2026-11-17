"""Pure completed-candle validation and causal ingestion for live paper sessions."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from qap.experiment.lab_replay import LabInputs
from qap.market import MarketBar, MarketMetadata, VenueInstrument

LEGACY_SCHEMA_VERSION = "qap.lab.paper_session.v1"
SCHEMA_VERSION = "qap.lab.paper_session.v2"
BAR_SECONDS: Mapping[str, int] = {
    "1m": 60,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


class LivePaperCandleError(ValueError):
    """Raised when paper session candle inputs are unordered, altered, or invalid."""


@dataclass(frozen=True, slots=True)
class CandleInputs:
    """Authoritative timestamped completed candles and observed venue metadata."""

    bar: str
    times: tuple[int, ...]
    closes: Mapping[str, tuple[float, ...]]
    datasets: tuple[dict[str, Any], ...] = ()
    metadata: Mapping[str, MarketMetadata] = field(
        default_factory=lambda: dict[str, MarketMetadata]()
    )
    metadata_provenance: Mapping[str, dict[str, Any]] = field(
        default_factory=lambda: dict[str, dict[str, Any]]()
    )
    resolved_anchor: str | None = None


@dataclass(frozen=True, slots=True)
class CandleIngestPlan:
    """Validated non-overlapping tail of newly completed candles."""

    new_times: tuple[int, ...]
    new_closes: Mapping[str, tuple[float, ...]]
    overlap_count: int
    new_count: int


def _validate_series_bars(bars: tuple[MarketBar, ...], step_seconds: int) -> None:
    if not bars:
        raise LivePaperCandleError("Completed candle history cannot be empty.")
    prev_time: int | None = None
    for bar in bars:
        t_sec = int(bar.candle_open_time.timestamp())
        close = float(bar.close)
        if not math.isfinite(close) or close <= 0.0:
            sym = bar.instrument.venue_symbol
            raise LivePaperCandleError(
                f"Non-positive or non-finite candle close for {sym}."
            )
        if prev_time is not None:
            if t_sec <= prev_time:
                raise LivePaperCandleError(
                    "Candle timestamps must be strictly ascending."
                )
            if t_sec - prev_time != step_seconds:
                raise LivePaperCandleError(
                    f"Non-contiguous candle gap at {bar.candle_open_time.isoformat()}."
                )
        prev_time = t_sec


def candle_inputs_from_lab_inputs(
    inputs: LabInputs,
    bar: str,
    *,
    datasets: Sequence[Mapping[str, Any]] = (),
    resolved_anchor: str | None = None,
) -> CandleInputs:
    """Convert validated LabInputs into aligned timestamped CandleInputs."""

    if bar not in BAR_SECONDS:
        raise LivePaperCandleError(f"Unsupported bar interval {bar!r}.")
    step_seconds = BAR_SECONDS[bar]
    series_list = [inputs.first, inputs.second]
    if inputs.anchor is not None and inputs.anchor.instrument.venue_symbol not in {
        inputs.first.instrument.venue_symbol,
        inputs.second.instrument.venue_symbol,
    }:
        series_list.append(inputs.anchor)
    base_times = tuple(int(b.candle_open_time.timestamp()) for b in inputs.first.bars)
    closes: dict[str, tuple[float, ...]] = {}
    for series in series_list:
        _validate_series_bars(series.bars, step_seconds)
        t_seq = tuple(int(b.candle_open_time.timestamp()) for b in series.bars)
        if t_seq != base_times:
            raise LivePaperCandleError(
                f"Misaligned candle timestamps for {series.instrument.venue_symbol}."
            )
        closes[series.instrument.venue_symbol] = tuple(
            float(b.close) for b in series.bars
        )
    meta_map: dict[str, MarketMetadata] = {}
    meta_prov: dict[str, dict[str, Any]] = {}
    for snap in inputs.metadata:
        sym = snap.metadata.instrument.venue_symbol
        meta_map[sym] = snap.metadata
        meta_prov[sym] = {
            "instrument": {
                "venue": snap.metadata.instrument.venue,
                "venue_symbol": sym,
                "base": snap.metadata.instrument.base.key,
                "quote": snap.metadata.instrument.quote.key,
            },
            "source_id": snap.source_id,
            "observed_at": snap.observed_at.isoformat(),
            "payload_sha256": snap.source_fingerprint,
        }
    return CandleInputs(
        bar=bar,
        times=base_times,
        closes=closes,
        datasets=tuple(dict(item) for item in datasets),
        metadata=meta_map,
        metadata_provenance=meta_prov,
        resolved_anchor=resolved_anchor,
    )


def candle_inputs_from_close_map(
    bar: str,
    closes_by_symbol: Mapping[str, Sequence[float]],
    *,
    times: Sequence[int] | None = None,
    start_epoch_s: int = 1_700_000_000,
    metadata: Mapping[str, MarketMetadata] | None = None,
    resolved_anchor: str | None = None,
) -> CandleInputs:
    """Build deterministic timestamped CandleInputs for unit tests."""

    if bar not in BAR_SECONDS:
        raise LivePaperCandleError(f"Unsupported bar interval {bar!r}.")
    if not closes_by_symbol:
        raise LivePaperCandleError("closes_by_symbol cannot be empty.")
    step_seconds = BAR_SECONDS[bar]
    lengths = {len(vals) for vals in closes_by_symbol.values()}
    if len(lengths) != 1 or 0 in lengths:
        raise LivePaperCandleError("All symbols must share a non-empty equal length.")
    count = next(iter(lengths))
    t_tuple = (
        tuple(int(t) for t in times)
        if times is not None
        else tuple(start_epoch_s + idx * step_seconds for idx in range(count))
    )
    if len(t_tuple) != count:
        raise LivePaperCandleError("times length must match close series length.")
    for prev, curr in zip(t_tuple, t_tuple[1:]):
        if curr <= prev or curr - prev != step_seconds:
            raise LivePaperCandleError("Candle times must be strictly contiguous.")
    norm_closes: dict[str, tuple[float, ...]] = {}
    for sym, vals in closes_by_symbol.items():
        floats = tuple(float(x) for x in vals)
        if any(not math.isfinite(x) or x <= 0.0 for x in floats):
            raise LivePaperCandleError(f"Invalid candle close for {sym}.")
        norm_closes[sym] = floats
    return CandleInputs(
        bar=bar,
        times=t_tuple,
        closes=norm_closes,
        metadata=dict(metadata or {}),
        resolved_anchor=resolved_anchor,
    )


def validate_required_candle_symbols(
    inputs: CandleInputs, req_insts: Sequence[VenueInstrument]
) -> None:
    for inst in req_insts:
        if inst.venue_symbol not in inputs.closes:
            raise LivePaperCandleError(
                f"Missing completed candle history for {inst.venue_symbol}."
            )
        if len(inputs.closes[inst.venue_symbol]) != len(inputs.times):
            raise LivePaperCandleError(
                f"Misaligned candle count for {inst.venue_symbol}."
            )


def plan_candle_ingestion(
    existing_times: Sequence[int],
    existing_closes: Mapping[str, Sequence[float]],
    incoming: CandleInputs,
    req_insts: Sequence[VenueInstrument],
) -> CandleIngestPlan:
    """Validate overlap idempotency/equality and extract contiguous new tail candles."""

    if incoming.bar not in BAR_SECONDS:
        raise LivePaperCandleError(f"Unsupported bar interval {incoming.bar!r}.")
    step_seconds = BAR_SECONDS[incoming.bar]
    validate_required_candle_symbols(incoming, req_insts)
    if not incoming.times:
        raise LivePaperCandleError("Incoming candle history cannot be empty.")
    for prev, curr in zip(incoming.times, incoming.times[1:]):
        if curr <= prev or curr - prev != step_seconds:
            raise LivePaperCandleError("Incoming candle timestamps are non-contiguous.")

    if not existing_times:
        return CandleIngestPlan(
            new_times=incoming.times,
            new_closes={
                inst.venue_symbol: incoming.closes[inst.venue_symbol]
                for inst in req_insts
            },
            overlap_count=0,
            new_count=len(incoming.times),
        )

    existing_index = {t: idx for idx, t in enumerate(existing_times)}
    last_existing = existing_times[-1]
    if incoming.times[-1] < last_existing:
        raise LivePaperCandleError(
            "Incoming candles end earlier than the session's last consumed candle."
        )

    overlap_indices: list[int] = []
    tail_indices: list[int] = []
    for idx, t_sec in enumerate(incoming.times):
        if t_sec <= last_existing:
            if t_sec not in existing_index:
                raise LivePaperCandleError(
                    f"Unordered or missing historical candle at timestamp {t_sec}."
                )
            existing_pos = existing_index[t_sec]
            for inst in req_insts:
                sym = inst.venue_symbol
                old_val = float(existing_closes[sym][existing_pos])
                new_val = float(incoming.closes[sym][idx])
                if not math.isclose(old_val, new_val, rel_tol=1e-12, abs_tol=1e-12):
                    raise LivePaperCandleError(
                        f"Historical candle content mismatch for {sym} at {t_sec}."
                    )
            overlap_indices.append(idx)
        else:
            tail_indices.append(idx)

    if tail_indices:
        first_new_t = incoming.times[tail_indices[0]]
        if first_new_t - last_existing != step_seconds:
            raise LivePaperCandleError(
                f"Gap between last consumed candle {last_existing} and {first_new_t}."
            )
    elif not overlap_indices:
        raise LivePaperCandleError("No matching candles found in incoming window.")

    new_times = tuple(incoming.times[i] for i in tail_indices)
    new_closes = {
        inst.venue_symbol: tuple(
            incoming.closes[inst.venue_symbol][i] for i in tail_indices
        )
        for inst in req_insts
    }
    return CandleIngestPlan(
        new_times=new_times,
        new_closes=new_closes,
        overlap_count=len(overlap_indices),
        new_count=len(new_times),
    )
