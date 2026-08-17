"""Narrow completed-bar slow-momentum evidence for Phase-10 experiments."""

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import cast

from qap.market import AlignedInstrumentSeries, BarInterval, validate_bar_series
from qap.portfolio import AssetId


class MomentumEvidenceStatus(StrEnum):
    """Whether one declared slow-momentum lookback produced causal evidence."""

    VALID = "valid"
    INSUFFICIENT_HISTORY = "insufficient_history"


@dataclass(frozen=True, slots=True)
class SlowMomentumEvidence:
    """One causal log-price momentum observation for a declared lookback."""

    asset: AssetId
    interval: BarInterval
    lookback_bars: int
    as_of: datetime
    status: MomentumEvidenceStatus
    current_timestamp: datetime | None
    reference_timestamp: datetime | None
    score: float | None


def slow_log_momentum(
    series: AlignedInstrumentSeries,
    *,
    lookback_bars: int,
    as_of: datetime,
) -> SlowMomentumEvidence:
    """Compute log(P_t / P_t-L) from bars completed by ``as_of`` only."""

    raw_lookback = cast(object, lookback_bars)
    if isinstance(raw_lookback, bool) or not isinstance(raw_lookback, int):
        raise TypeError("lookback_bars must be an integer")
    if lookback_bars <= 0:
        raise ValueError("lookback_bars must be positive")

    history = validate_bar_series(series.bars).history_through(as_of)
    current_timestamp = history.bars[-1].candle_open_time if history.bars else None
    if len(history.bars) <= lookback_bars:
        return SlowMomentumEvidence(
            asset=series.instrument.base,
            interval=series.interval,
            lookback_bars=lookback_bars,
            as_of=history.as_of,
            status=MomentumEvidenceStatus.INSUFFICIENT_HISTORY,
            current_timestamp=current_timestamp,
            reference_timestamp=None,
            score=None,
        )

    current = history.bars[-1]
    reference = history.bars[-lookback_bars - 1]
    score = math.log(current.close) - math.log(reference.close)
    return SlowMomentumEvidence(
        asset=series.instrument.base,
        interval=series.interval,
        lookback_bars=lookback_bars,
        as_of=history.as_of,
        status=MomentumEvidenceStatus.VALID,
        current_timestamp=current.candle_open_time,
        reference_timestamp=reference.candle_open_time,
        score=score,
    )


__all__ = ["MomentumEvidenceStatus", "SlowMomentumEvidence", "slow_log_momentum"]
