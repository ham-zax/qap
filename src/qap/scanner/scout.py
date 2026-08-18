"""Non-authoritative two-asset ranking scout for Scanner-V1 Slice 1."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import cast

from qap.portfolio import AssetId
from qap.scanner.protocol import HistoricalCostPolicy
from qap.scanner.trials import ScannerTrial, preference_score


class ScoutTrialStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ScoutTrialRecord:
    candidate_id: str
    scan_id: str
    venue: str
    horizon: str
    pair_id: str
    orientation: str
    resolution: str
    model_family: str
    template_id: str
    trial_status: ScoutTrialStatus
    failure_reason: str | None
    scout_relative_wealth_proxy: float | None
    scout_turnover_proxy: float
    signal_count: int
    automatic_neighbor_selected: bool
    manual_pinned: bool


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def scout_target_weights(z_score: float) -> tuple[float, float] | None:
    """Map oriented z-score to (numerator, denominator) target weights or NO_ACTION."""

    if isinstance(cast(object, z_score), bool) or not isinstance(
        cast(object, z_score), (int, float)
    ):
        raise TypeError("z_score must be numeric")
    score = float(z_score)
    if not math.isfinite(score):
        raise ValueError("z_score must be finite")
    magnitude = abs(score)
    if magnitude <= 0.5:
        return (0.5, 0.5)
    if magnitude < 1.5:
        return None
    preference = preference_score(score)
    return (0.6, 0.4) if preference > 0.0 else (0.4, 0.6)


def _record(
    trial: ScannerTrial,
    *,
    status: ScoutTrialStatus,
    failure_reason: str | None,
    relative_wealth: float | None,
    turnover: float,
    signal_count: int,
) -> ScoutTrialRecord:
    orientation = f"{trial.orientation.base.key}/{trial.orientation.quote.key}"
    return ScoutTrialRecord(
        candidate_id=trial.candidate_id,
        scan_id=trial.scan_id,
        venue=trial.venue,
        horizon=trial.horizon.value,
        pair_id=trial.pair_id,
        orientation=orientation,
        resolution=trial.resolution.label,
        model_family=trial.model_family.value,
        template_id=trial.template_id.value,
        trial_status=status,
        failure_reason=failure_reason,
        scout_relative_wealth_proxy=relative_wealth,
        scout_turnover_proxy=turnover,
        signal_count=signal_count,
        automatic_neighbor_selected=trial.automatic_neighbor_selected,
        manual_pinned=trial.manual_pinned,
    )


def _prices(
    prices_by_asset: Mapping[AssetId, Sequence[float]],
    *,
    asset: AssetId,
    expected_count: int,
) -> tuple[float, ...]:
    try:
        raw_values = prices_by_asset[asset]
    except KeyError as exc:
        raise ValueError(f"missing scout prices for {asset.key}") from exc
    values = tuple(float(value) for value in raw_values)
    if len(values) != expected_count:
        raise ValueError("scout price paths must match the timestamp count")
    if any(not math.isfinite(value) or value <= 0.0 for value in values):
        raise ValueError("scout prices must be positive finite values")
    return values


def _validated_timestamps(
    timestamps: Sequence[datetime],
    *,
    evaluation_start: datetime,
    evaluation_end: datetime,
) -> tuple[datetime, ...]:
    start = _utc(evaluation_start, field="evaluation_start")
    end = _utc(evaluation_end, field="evaluation_end")
    if end <= start:
        raise ValueError("evaluation_end must be after evaluation_start")
    copied = tuple(_utc(value, field="timestamp") for value in timestamps)
    if len(copied) < 2:
        raise ValueError("scout requires at least two evaluation observations")
    if copied[0] != start or copied[-1] != end:
        raise ValueError("scout timestamps must span the exact evaluation window")
    if any(current <= previous for previous, current in zip(copied, copied[1:])):
        raise ValueError("scout timestamps must be strictly increasing")
    return copied


def _friction_rate(cost_policy: HistoricalCostPolicy) -> float:
    if not isinstance(cast(object, cost_policy), HistoricalCostPolicy):
        raise TypeError("cost_policy must be a HistoricalCostPolicy")
    rate = float(cost_policy.fee_bps + cost_policy.slippage_bps) / 10_000.0
    if not math.isfinite(rate) or rate < 0.0:
        raise ValueError("scout friction rate must be finite and non-negative")
    return rate


def run_scout_trial(
    trial: ScannerTrial,
    *,
    timestamps: Sequence[datetime],
    z_scores: Sequence[float | None],
    prices_by_asset: Mapping[AssetId, Sequence[float]],
    evaluation_start: datetime,
    evaluation_end: datetime,
    cost_policy: HistoricalCostPolicy,
) -> ScoutTrialRecord:
    """Run one causal float-quantity ranking proxy without fills or venue precision."""

    if not isinstance(cast(object, trial), ScannerTrial):
        raise TypeError("trial must be a ScannerTrial")
    times = _validated_timestamps(
        timestamps,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
    )
    scores = tuple(z_scores)
    if len(scores) != len(times):
        raise ValueError("z_scores must match the timestamp count")
    if any(score is None for score in scores):
        return _record(
            trial,
            status=ScoutTrialStatus.INVALID,
            failure_reason="insufficient_evidence",
            relative_wealth=None,
            turnover=0.0,
            signal_count=0,
        )
    numeric_scores = tuple(float(cast(float, score)) for score in scores)
    if any(not math.isfinite(score) for score in numeric_scores):
        return _record(
            trial,
            status=ScoutTrialStatus.INVALID,
            failure_reason="non_finite_evidence",
            relative_wealth=None,
            turnover=0.0,
            signal_count=0,
        )

    numerator_asset = trial.orientation.base
    denominator_asset = trial.orientation.quote
    numerator_prices = _prices(
        prices_by_asset,
        asset=numerator_asset,
        expected_count=len(times),
    )
    denominator_prices = _prices(
        prices_by_asset,
        asset=denominator_asset,
        expected_count=len(times),
    )
    friction_rate = _friction_rate(cost_policy)

    numerator_quantity = 0.5 / numerator_prices[0]
    denominator_quantity = 0.5 / denominator_prices[0]
    passive_numerator_quantity = numerator_quantity
    passive_denominator_quantity = denominator_quantity
    turnover_total = 0.0
    active_signal_count = 0

    for position in range(1, len(times)):
        signal = numeric_scores[position - 1]
        if abs(signal) >= 1.5:
            active_signal_count += 1
        target = scout_target_weights(signal)
        if target is None:
            continue

        numerator_price = numerator_prices[position]
        denominator_price = denominator_prices[position]
        numerator_value = numerator_quantity * numerator_price
        denominator_value = denominator_quantity * denominator_price
        pretrade_wealth = numerator_value + denominator_value
        if not math.isfinite(pretrade_wealth) or pretrade_wealth <= 0.0:
            return _record(
                trial,
                status=ScoutTrialStatus.INVALID,
                failure_reason="invalid_proxy_wealth",
                relative_wealth=None,
                turnover=turnover_total,
                signal_count=active_signal_count,
            )

        pretrade_numerator_weight = numerator_value / pretrade_wealth
        pretrade_denominator_weight = denominator_value / pretrade_wealth
        turnover = 0.5 * (
            abs(target[0] - pretrade_numerator_weight)
            + abs(target[1] - pretrade_denominator_weight)
        )
        friction = pretrade_wealth * turnover * friction_rate
        post_cost_wealth = pretrade_wealth - friction
        if not math.isfinite(post_cost_wealth) or post_cost_wealth <= 0.0:
            return _record(
                trial,
                status=ScoutTrialStatus.INVALID,
                failure_reason="invalid_proxy_wealth",
                relative_wealth=None,
                turnover=turnover_total + turnover,
                signal_count=active_signal_count,
            )
        turnover_total += turnover
        numerator_quantity = target[0] * post_cost_wealth / numerator_price
        denominator_quantity = target[1] * post_cost_wealth / denominator_price

    terminal_strategy = (
        numerator_quantity * numerator_prices[-1]
        + denominator_quantity * denominator_prices[-1]
    )
    terminal_passive = (
        passive_numerator_quantity * numerator_prices[-1]
        + passive_denominator_quantity * denominator_prices[-1]
    )
    if (
        not math.isfinite(terminal_strategy)
        or not math.isfinite(terminal_passive)
        or terminal_passive <= 0.0
    ):
        return _record(
            trial,
            status=ScoutTrialStatus.INVALID,
            failure_reason="invalid_proxy_wealth",
            relative_wealth=None,
            turnover=turnover_total,
            signal_count=active_signal_count,
        )
    if active_signal_count == 0:
        return _record(
            trial,
            status=ScoutTrialStatus.INVALID,
            failure_reason="no_active_signal",
            relative_wealth=None,
            turnover=turnover_total,
            signal_count=0,
        )

    relative_wealth = terminal_strategy / terminal_passive - 1.0
    if not math.isfinite(relative_wealth):
        return _record(
            trial,
            status=ScoutTrialStatus.INVALID,
            failure_reason="invalid_proxy_wealth",
            relative_wealth=None,
            turnover=turnover_total,
            signal_count=active_signal_count,
        )
    return _record(
        trial,
        status=ScoutTrialStatus.VALID,
        failure_reason=None,
        relative_wealth=relative_wealth,
        turnover=turnover_total,
        signal_count=active_signal_count,
    )


__all__ = [
    "ScoutTrialRecord",
    "ScoutTrialStatus",
    "run_scout_trial",
    "scout_target_weights",
]
