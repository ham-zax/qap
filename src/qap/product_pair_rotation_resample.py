"""Incremental 15m -> 1h/4h/1d resampling helpers for PairRotationData."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from qap.market import BarInterval, MarketBar, ValidatedBarSeries, validate_bar_series
from qap.product_market_data_generation import resolve_immutable_generation
from qap.product_market_data_models import CurrentMarketDataGeneration
from qap.product_market_data_prepare import ProductMarketDataPreparationError

_BASE_INTERVAL = BarInterval("15m")
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def floor_to_interval(moment: datetime, interval: BarInterval) -> datetime:
    elapsed = moment - _EPOCH
    steps = elapsed // interval.duration
    return _EPOCH + steps * interval.duration


def ceil_to_interval(moment: datetime, interval: BarInterval) -> datetime:
    elapsed = moment - _EPOCH
    steps, remainder = divmod(elapsed, interval.duration)
    if remainder:
        steps += 1
    return _EPOCH + steps * interval.duration


def resample_15m(
    series: ValidatedBarSeries,
    target: BarInterval,
    *,
    start: datetime,
    cutoff: datetime,
) -> ValidatedBarSeries | None:
    if series.interval != _BASE_INTERVAL:
        raise ProductMarketDataPreparationError(
            "Pair rotation resampling requires a 15m source series."
        )
    if target.duration % _BASE_INTERVAL.duration != timedelta(0):
        raise ProductMarketDataPreparationError(
            f"Cannot derive {target.label} from 15m bars."
        )
    expected = target.duration // _BASE_INTERVAL.duration
    selected = tuple(
        bar
        for bar in series.bars
        if bar.candle_open_time >= start and bar.bar_end_exclusive <= cutoff
    )
    if not selected:
        return None
    grouped: dict[datetime, list[MarketBar]] = {}
    for bar in selected:
        bucket = floor_to_interval(bar.candle_open_time, target)
        grouped.setdefault(bucket, []).append(bar)
    derived: list[MarketBar] = []
    for bucket in sorted(grouped):
        group = grouped[bucket]
        if len(group) != expected:
            continue
        if group[0].candle_open_time != bucket:
            continue
        if group[-1].bar_end_exclusive != bucket + target.duration:
            continue
        present_volumes = [bar.volume for bar in group if bar.volume is not None]
        volume: float | None
        if len(present_volumes) != len(group):
            volume = None
        else:
            total_volume = 0.0
            for item in present_volumes:
                total_volume += item
            volume = total_volume
        derived.append(
            MarketBar(
                instrument=series.instrument,
                interval=target,
                candle_open_time=bucket,
                open=group[0].open,
                high=max(bar.high for bar in group),
                low=min(bar.low for bar in group),
                close=group[-1].close,
                volume=volume,
                source_close_time=None,
            )
        )
    if not derived:
        return None
    try:
        return validate_bar_series(derived)
    except (TypeError, ValueError) as exc:
        raise ProductMarketDataPreparationError(
            f"Derived {target.label} series is not contiguous."
        ) from exc


def derived_needs_update(
    existing: CurrentMarketDataGeneration | None,
    target: BarInterval,
    *,
    start: datetime,
    cutoff: datetime,
) -> bool:
    expected_start = ceil_to_interval(start, target)
    expected_end = floor_to_interval(cutoff, target)
    if expected_start >= expected_end:
        return False
    return not (
        existing is not None
        and existing.provenance_status == "complete"
        and existing.coverage_start is not None
        and existing.coverage_end_exclusive is not None
        and existing.coverage_start <= expected_start
        and existing.coverage_end_exclusive >= expected_end
    )


def extend_derived_15m(
    parent_series: ValidatedBarSeries,
    target: BarInterval,
    *,
    start: datetime,
    cutoff: datetime,
    existing: CurrentMarketDataGeneration | None,
    data_root: Path,
) -> ValidatedBarSeries | None:
    expected_start = ceil_to_interval(start, target)
    expected_end = floor_to_interval(cutoff, target)
    if expected_start >= expected_end:
        return None
    if (
        existing is not None
        and existing.provenance_status == "complete"
        and existing.coverage_start is not None
        and existing.coverage_end_exclusive is not None
    ):
        if (
            existing.coverage_start <= expected_start
            and existing.coverage_end_exclusive >= expected_end
        ):
            return None
        overlaps_or_touches = (
            expected_start <= existing.coverage_end_exclusive
            and expected_end >= existing.coverage_start
        )
        if overlaps_or_touches:
            _, existing_series = resolve_immutable_generation(
                data_root,
                dataset_id=existing.dataset_id,
                semantic_fingerprint=existing.semantic_fingerprint,
            )
            head = (
                resample_15m(
                    parent_series,
                    target,
                    start=expected_start,
                    cutoff=existing.coverage_start,
                )
                if expected_start < existing.coverage_start
                else None
            )
            tail = (
                resample_15m(
                    parent_series,
                    target,
                    start=existing.coverage_end_exclusive,
                    cutoff=expected_end,
                )
                if expected_end > existing.coverage_end_exclusive
                else None
            )
            if head is None and tail is None:
                return None
            bars: list[MarketBar] = []
            if head is not None:
                bars.extend(head.bars)
            bars.extend(existing_series.bars)
            if tail is not None:
                bars.extend(tail.bars)
            try:
                return validate_bar_series(bars)
            except (TypeError, ValueError) as exc:
                raise ProductMarketDataPreparationError(
                    f"Extended {target.label} series is not contiguous."
                ) from exc
    return resample_15m(parent_series, target, start=start, cutoff=cutoff)
