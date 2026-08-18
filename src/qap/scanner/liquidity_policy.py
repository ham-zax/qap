"""Capacity, coverage, and qualification policy for Scanner-V1 Slice 2."""

import math
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import cast

from qap.market import MarketMetadata, PublicBookSnapshot
from qap.portfolio._decimal import (
    divide,
    exact_add,
    exact_multiply,
    exact_subtract,
    exact_sum,
)
from qap.scanner.liquidity import (
    BookSide,
    FrictionEvidence,
    book_mid_price,
    friction_evidence,
    walk_quote_notional,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1
from qap.scanner.slice2_contract import (
    C95_QUANTILE,
    DAILY_COVERAGE_MINIMUM,
    DEPTH_CADENCE,
    L1_CADENCE,
    LIQUIDITY_POLICY_VERSION,
    MINIMUM_QUALIFICATION_WINDOW,
    OVERALL_COVERAGE_MINIMUM,
    SAFE_CAPACITY_HAIRCUT,
    STRUCTURAL_REBALANCE_FRACTION,
    TARGET_BASE_WEIGHTS,
)

_ZERO = Decimal("0")
_ONE = Decimal("1")
_TWO = Decimal("2")


class QualificationState(StrEnum):
    RESEARCH_ONLY = "research_only"
    SMALL_CAPACITY = "small_capacity"
    TRADABLE_NOW = "tradable_now"


class QualificationReason(StrEnum):
    ALL_CURRENT_EVIDENCE_SATISFIED = "all_current_evidence_satisfied"
    ELIGIBILITY_UNRESOLVED = "eligibility_unresolved"
    MICROSTRUCTURE_COVERAGE_INSUFFICIENT = "microstructure_coverage_insufficient"
    INSTRUMENT_NOT_TWO_WAY_TRADABLE = "instrument_not_two_way_tradable"
    CAPACITY_UNKNOWN = "capacity_unknown"
    ORDER_CONSTRAINTS_UNSATISFIED = "order_constraints_unsatisfied"
    ECONOMIC_GATES_FAILED = "economic_gates_failed"
    REQUESTED_CAPITAL_ABOVE_CEILING = "requested_capital_above_ceiling"
    NO_SUPPORTED_LOWER_CAPITAL = "no_supported_lower_capital"


@dataclass(frozen=True, slots=True)
class DirectionalC95Result:
    side: BookSide
    quote_notional: Decimal
    required_observations: int
    fillable_observations: int
    infeasible_observations: int
    c95_friction_bps: Decimal | None
    adverse_friction_budget_bps: Decimal

    @property
    def feasible(self) -> bool:
        return (
            self.required_observations > 0
            and self.infeasible_observations == 0
            and self.fillable_observations == self.required_observations
            and self.c95_friction_bps is not None
        )

    @property
    def within_adverse_budget(self) -> bool | None:
        if not self.feasible or self.c95_friction_bps is None:
            return None
        return self.c95_friction_bps <= self.adverse_friction_budget_bps


@dataclass(frozen=True, slots=True)
class TwoSidedC95Result:
    quote_notional: Decimal
    required_snapshots: int
    infeasible_snapshots: int
    buy_c95_friction_bps: Decimal | None
    sell_c95_friction_bps: Decimal | None
    c95_friction_bps: Decimal | None
    adverse_friction_budget_bps: Decimal

    @property
    def feasible(self) -> bool:
        return (
            self.required_snapshots > 0
            and self.infeasible_snapshots == 0
            and self.c95_friction_bps is not None
        )


@dataclass(frozen=True, slots=True)
class DirectionalSafeSizeResult:
    side: BookSide
    q_star: Decimal | None
    q_safe: Decimal | None
    quote_notional_tolerance: Decimal
    adverse_fee_bps: Decimal
    adverse_slippage_budget_bps: Decimal
    evaluations: tuple[DirectionalC95Result, ...]


@dataclass(frozen=True, slots=True)
class CaptureCoverageResult:
    window_start: datetime
    window_end: datetime
    l1_expected_slots: int
    l1_captured_slots: int
    depth_expected_slots: int
    depth_captured_slots: int
    l1_overall_coverage: Decimal
    depth_overall_coverage: Decimal
    minimum_l1_daily_coverage: Decimal
    minimum_depth_daily_coverage: Decimal
    satisfied: bool


@dataclass(frozen=True, slots=True)
class RequiredTradeFractions:
    current_base_weight: Decimal
    required_buy: Decimal
    required_sell: Decimal


@dataclass(frozen=True, slots=True)
class CandidateCapacity:
    current_base_weight: Decimal
    q_safe_buy: Decimal
    q_safe_sell: Decimal
    required_buy_fraction: Decimal
    required_sell_fraction: Decimal
    buy_capital_ceiling: Decimal
    sell_capital_ceiling: Decimal
    candidate_capital_ceiling: Decimal


@dataclass(frozen=True, slots=True)
class QualificationDecision:
    state: QualificationState
    reason: QualificationReason
    as_of: datetime
    requested_capital: Decimal
    estimated_capital_ceiling: Decimal | None
    liquidity_policy_version: str = LIQUIDITY_POLICY_VERSION


def _positive_decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be a Decimal")
    if not value.is_finite() or value <= _ZERO:
        raise ValueError(f"{field} must be positive finite")
    return value


def _weight(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be a Decimal")
    if not value.is_finite() or not _ZERO <= value <= _ONE:
        raise ValueError(f"{field} must be finite within [0, 1]")
    return value


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _adverse_budget_bps() -> Decimal:
    policy = SCANNER_V1_SLICE1.cost_policy
    return exact_add(policy.adverse_fee_bps, policy.adverse_slippage_bps)


def _nearest_rank_95(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("C95 requires at least one finite observation")
    ordered = tuple(sorted(values))
    index = max(0, math.ceil(C95_QUANTILE * Decimal(len(ordered))) - 1)
    return ordered[index]


def evaluate_directional_c95(
    evidence: tuple[FrictionEvidence, ...],
    *,
    side: BookSide,
    quote_notional: Decimal,
) -> DirectionalC95Result:
    requested = _positive_decimal(quote_notional, field="quote_notional")
    if not isinstance(cast(object, side), BookSide):
        raise TypeError("side must be a BookSide")
    rows = tuple(evidence)
    if not rows:
        raise ValueError("C95 requires at least one required observation")
    ids = tuple(row.snapshot_id for row in rows)
    if len(set(ids)) != len(ids):
        raise ValueError("directional C95 snapshot IDs must be unique")
    if any(row.side is not side for row in rows):
        raise ValueError("directional C95 evidence must use one side")
    if any(row.quote_notional_requested != requested for row in rows):
        raise ValueError("C95 evidence must share the tested quote notional")
    fillable = tuple(row for row in rows if row.fillable)
    infeasible = len(rows) - len(fillable)
    c95: Decimal | None = None
    if infeasible == 0:
        totals = tuple(row.total_friction_bps for row in fillable)
        if any(value is None for value in totals):
            raise ValueError("fillable friction evidence must carry total friction")
        c95 = _nearest_rank_95(cast(tuple[Decimal, ...], totals))
    return DirectionalC95Result(
        side=side,
        quote_notional=requested,
        required_observations=len(rows),
        fillable_observations=len(fillable),
        infeasible_observations=infeasible,
        c95_friction_bps=c95,
        adverse_friction_budget_bps=_adverse_budget_bps(),
    )


def evaluate_two_sided_c95(
    evidence: tuple[FrictionEvidence, ...],
    *,
    quote_notional: Decimal,
) -> TwoSidedC95Result:
    requested = _positive_decimal(quote_notional, field="quote_notional")
    rows = tuple(evidence)
    buy = tuple(row for row in rows if row.side is BookSide.BUY_BASE)
    sell = tuple(row for row in rows if row.side is BookSide.SELL_BASE)
    buy_ids = {row.snapshot_id for row in buy}
    sell_ids = {row.snapshot_id for row in sell}
    if not buy_ids or buy_ids != sell_ids:
        raise ValueError(
            "two-sided C95 requires the same buy/sell snapshot denominator"
        )
    buy_result = evaluate_directional_c95(
        buy, side=BookSide.BUY_BASE, quote_notional=requested
    )
    sell_result = evaluate_directional_c95(
        sell, side=BookSide.SELL_BASE, quote_notional=requested
    )
    infeasible_ids = {row.snapshot_id for row in rows if not row.fillable}
    combined: Decimal | None = None
    if not infeasible_ids:
        assert buy_result.c95_friction_bps is not None
        assert sell_result.c95_friction_bps is not None
        combined = max(
            buy_result.c95_friction_bps,
            sell_result.c95_friction_bps,
        )
    return TwoSidedC95Result(
        quote_notional=requested,
        required_snapshots=len(buy_ids),
        infeasible_snapshots=len(infeasible_ids),
        buy_c95_friction_bps=buy_result.c95_friction_bps,
        sell_c95_friction_bps=sell_result.c95_friction_bps,
        c95_friction_bps=combined,
        adverse_friction_budget_bps=_adverse_budget_bps(),
    )


def _validate_snapshot_set(
    snapshots: tuple[PublicBookSnapshot, ...],
) -> tuple[PublicBookSnapshot, ...]:
    if not snapshots:
        raise ValueError("liquidity capacity requires at least one book snapshot")
    first = snapshots[0].instrument
    if any(item.instrument != first for item in snapshots):
        raise ValueError("liquidity capacity snapshots must use one instrument")
    ids = tuple(item.snapshot_id for item in snapshots)
    if len(set(ids)) != len(ids):
        raise ValueError("liquidity capacity snapshot IDs must be unique")
    return snapshots


def _visible_quote_depth(snapshot: PublicBookSnapshot, side: BookSide) -> Decimal:
    levels = snapshot.asks if side is BookSide.BUY_BASE else snapshot.bids
    return exact_sum(
        tuple(
            exact_multiply(Decimal(str(level.price)), Decimal(str(level.quantity)))
            for level in levels
        )
    )


def _evaluate_snapshot_set(
    snapshots: tuple[PublicBookSnapshot, ...],
    *,
    side: BookSide,
    quote_notional: Decimal,
) -> DirectionalC95Result:
    fee_bps = SCANNER_V1_SLICE1.cost_policy.adverse_fee_bps
    evidence = tuple(
        friction_evidence(
            walk_quote_notional(snapshot, side=side, quote_notional=quote_notional),
            fee_bps=fee_bps,
        )
        for snapshot in snapshots
    )
    return evaluate_directional_c95(evidence, side=side, quote_notional=quote_notional)


def find_directional_safe_size(
    snapshots: tuple[PublicBookSnapshot, ...],
    *,
    side: BookSide,
    market_metadata: MarketMetadata,
) -> DirectionalSafeSizeResult:
    books = _validate_snapshot_set(tuple(snapshots))
    if not isinstance(cast(object, market_metadata), MarketMetadata):
        raise TypeError("market_metadata must be MarketMetadata")
    if market_metadata.instrument != books[0].instrument:
        raise ValueError("market metadata must match liquidity snapshot instrument")
    quantity_step = (
        market_metadata.market_quantity_step or market_metadata.quantity_step
    )
    tolerance = max(
        exact_multiply(book_mid_price(item), quantity_step) for item in books
    )
    upper = min(_visible_quote_depth(item, side) for item in books)
    quantity_limits = tuple(
        value
        for value in (
            market_metadata.maximum_quantity,
            market_metadata.market_maximum_quantity,
        )
        if value is not None
    )
    if quantity_limits:
        maximum_quantity = min(quantity_limits)
        upper = min(
            upper,
            *(exact_multiply(book_mid_price(item), maximum_quantity) for item in books),
        )
    if (
        market_metadata.maximum_notional_applies_to_market
        and market_metadata.maximum_notional is not None
    ):
        upper = min(upper, market_metadata.maximum_notional)
    if upper <= _ZERO:
        raise ValueError("captured book cannot establish an executable upper bound")

    evaluations: list[DirectionalC95Result] = []

    def evaluate(size: Decimal) -> DirectionalC95Result:
        result = _evaluate_snapshot_set(books, side=side, quote_notional=size)
        evaluations.append(result)
        return result

    upper_result = evaluate(upper)
    if upper_result.within_adverse_budget is True:
        q_star: Decimal | None = upper
    else:
        low = _ZERO
        high = upper
        while exact_subtract(high, low) > tolerance:
            midpoint = divide(exact_add(low, high), _TWO)
            if midpoint <= _ZERO or midpoint == low or midpoint == high:
                break
            result = evaluate(midpoint)
            if result.within_adverse_budget is True:
                low = midpoint
            else:
                high = midpoint
        q_star = low if low > _ZERO else None
    q_safe = None if q_star is None else exact_multiply(q_star, SAFE_CAPACITY_HAIRCUT)
    policy = SCANNER_V1_SLICE1.cost_policy
    return DirectionalSafeSizeResult(
        side=side,
        q_star=q_star,
        q_safe=q_safe,
        quote_notional_tolerance=tolerance,
        adverse_fee_bps=policy.adverse_fee_bps,
        adverse_slippage_budget_bps=policy.adverse_slippage_bps,
        evaluations=tuple(evaluations),
    )


def _scheduled_coverage(
    observations: tuple[datetime, ...],
    *,
    cadence: timedelta,
    window_start: datetime,
    window_end: datetime,
) -> tuple[int, int, Decimal, Decimal]:
    span = window_end - window_start
    if span <= timedelta(0) or span % cadence != timedelta(0):
        raise ValueError(
            "coverage window must divide exactly into the scheduled cadence"
        )
    expected = span // cadence
    if expected <= 0:
        raise ValueError("coverage window must contain scheduled observations")
    slots: set[int] = set()
    for raw in observations:
        timestamp = _utc(raw, field="observation timestamp")
        if window_start <= timestamp < window_end:
            slots.add(int((timestamp - window_start) // cadence))
    expected_by_day: Counter[date] = Counter()
    captured_by_day: Counter[date] = Counter()
    for slot in range(expected):
        expected_by_day[(window_start + slot * cadence).date()] += 1
    for slot in slots:
        captured_by_day[(window_start + slot * cadence).date()] += 1
    overall = divide(Decimal(len(slots)), Decimal(expected))
    daily = tuple(
        divide(Decimal(captured_by_day[day]), Decimal(count))
        for day, count in sorted(expected_by_day.items())
    )
    return expected, len(slots), overall, min(daily)


def evaluate_capture_contract(
    l1_observations: tuple[datetime, ...],
    depth_observations: tuple[datetime, ...],
    *,
    window_end: datetime,
) -> CaptureCoverageResult:
    end = _utc(window_end, field="window_end")
    start = end - MINIMUM_QUALIFICATION_WINDOW
    l1_expected, l1_captured, l1_overall, l1_daily = _scheduled_coverage(
        tuple(l1_observations), cadence=L1_CADENCE, window_start=start, window_end=end
    )
    depth_expected, depth_captured, depth_overall, depth_daily = _scheduled_coverage(
        tuple(depth_observations),
        cadence=DEPTH_CADENCE,
        window_start=start,
        window_end=end,
    )
    satisfied = (
        l1_overall >= OVERALL_COVERAGE_MINIMUM
        and depth_overall >= OVERALL_COVERAGE_MINIMUM
        and l1_daily >= DAILY_COVERAGE_MINIMUM
        and depth_daily >= DAILY_COVERAGE_MINIMUM
    )
    return CaptureCoverageResult(
        window_start=start,
        window_end=end,
        l1_expected_slots=l1_expected,
        l1_captured_slots=l1_captured,
        depth_expected_slots=depth_expected,
        depth_captured_slots=depth_captured,
        l1_overall_coverage=l1_overall,
        depth_overall_coverage=depth_overall,
        minimum_l1_daily_coverage=l1_daily,
        minimum_depth_daily_coverage=depth_daily,
        satisfied=satisfied,
    )


def required_trade_fractions(current_base_weight: Decimal) -> RequiredTradeFractions:
    weight = _weight(current_base_weight, field="current_base_weight")
    current_buy = max(
        (max(exact_subtract(target, weight), _ZERO) for target in TARGET_BASE_WEIGHTS),
        default=_ZERO,
    )
    current_sell = max(
        (max(exact_subtract(weight, target), _ZERO) for target in TARGET_BASE_WEIGHTS),
        default=_ZERO,
    )
    return RequiredTradeFractions(
        current_base_weight=weight,
        required_buy=max(STRUCTURAL_REBALANCE_FRACTION, current_buy),
        required_sell=max(STRUCTURAL_REBALANCE_FRACTION, current_sell),
    )


def candidate_capital_ceiling(
    *,
    q_safe_buy: Decimal | None,
    q_safe_sell: Decimal | None,
    current_base_weight: Decimal | None,
) -> CandidateCapacity | None:
    if q_safe_buy is None or q_safe_sell is None or current_base_weight is None:
        return None
    buy = _positive_decimal(q_safe_buy, field="q_safe_buy")
    sell = _positive_decimal(q_safe_sell, field="q_safe_sell")
    required = required_trade_fractions(current_base_weight)
    buy_ceiling = divide(buy, required.required_buy)
    sell_ceiling = divide(sell, required.required_sell)
    return CandidateCapacity(
        current_base_weight=required.current_base_weight,
        q_safe_buy=buy,
        q_safe_sell=sell,
        required_buy_fraction=required.required_buy,
        required_sell_fraction=required.required_sell,
        buy_capital_ceiling=buy_ceiling,
        sell_capital_ceiling=sell_ceiling,
        candidate_capital_ceiling=min(buy_ceiling, sell_ceiling),
    )


def _decision(
    state: QualificationState,
    reason: QualificationReason,
    *,
    as_of: datetime,
    requested_capital: Decimal,
    ceiling: Decimal | None,
) -> QualificationDecision:
    return QualificationDecision(
        state=state,
        reason=reason,
        as_of=as_of,
        requested_capital=requested_capital,
        estimated_capital_ceiling=ceiling,
    )


def qualify_candidate(
    *,
    as_of: datetime,
    requested_capital: Decimal,
    candidate_capital_ceiling: Decimal | None,
    eligibility_resolved: bool,
    capture_contract_satisfied: bool,
    current_two_way_trading: bool,
    order_constraints_satisfied: bool,
    economic_gates_at_requested_capital: bool,
    lower_tested_capital: Decimal | None,
    economic_gates_at_lower_capital: bool,
) -> QualificationDecision:
    timestamp = _utc(as_of, field="as_of")
    requested = _positive_decimal(requested_capital, field="requested_capital")
    ceiling = (
        None
        if candidate_capital_ceiling is None
        else _positive_decimal(
            candidate_capital_ceiling, field="candidate_capital_ceiling"
        )
    )
    lower = (
        None
        if lower_tested_capital is None
        else _positive_decimal(lower_tested_capital, field="lower_tested_capital")
    )
    if not eligibility_resolved:
        return _decision(
            QualificationState.RESEARCH_ONLY,
            QualificationReason.ELIGIBILITY_UNRESOLVED,
            as_of=timestamp,
            requested_capital=requested,
            ceiling=ceiling,
        )
    if not capture_contract_satisfied:
        return _decision(
            QualificationState.RESEARCH_ONLY,
            QualificationReason.MICROSTRUCTURE_COVERAGE_INSUFFICIENT,
            as_of=timestamp,
            requested_capital=requested,
            ceiling=ceiling,
        )
    if not current_two_way_trading:
        return _decision(
            QualificationState.RESEARCH_ONLY,
            QualificationReason.INSTRUMENT_NOT_TWO_WAY_TRADABLE,
            as_of=timestamp,
            requested_capital=requested,
            ceiling=ceiling,
        )
    if ceiling is None:
        return _decision(
            QualificationState.RESEARCH_ONLY,
            QualificationReason.CAPACITY_UNKNOWN,
            as_of=timestamp,
            requested_capital=requested,
            ceiling=None,
        )
    if not order_constraints_satisfied:
        return _decision(
            QualificationState.RESEARCH_ONLY,
            QualificationReason.ORDER_CONSTRAINTS_UNSATISFIED,
            as_of=timestamp,
            requested_capital=requested,
            ceiling=ceiling,
        )
    if requested <= ceiling:
        if economic_gates_at_requested_capital:
            return _decision(
                QualificationState.TRADABLE_NOW,
                QualificationReason.ALL_CURRENT_EVIDENCE_SATISFIED,
                as_of=timestamp,
                requested_capital=requested,
                ceiling=ceiling,
            )
        return _decision(
            QualificationState.RESEARCH_ONLY,
            QualificationReason.ECONOMIC_GATES_FAILED,
            as_of=timestamp,
            requested_capital=requested,
            ceiling=ceiling,
        )
    if lower is not None and lower <= ceiling and economic_gates_at_lower_capital:
        return _decision(
            QualificationState.SMALL_CAPACITY,
            QualificationReason.REQUESTED_CAPITAL_ABOVE_CEILING,
            as_of=timestamp,
            requested_capital=requested,
            ceiling=ceiling,
        )
    return _decision(
        QualificationState.RESEARCH_ONLY,
        QualificationReason.NO_SUPPORTED_LOWER_CAPITAL,
        as_of=timestamp,
        requested_capital=requested,
        ceiling=ceiling,
    )


__all__ = [
    "CandidateCapacity",
    "CaptureCoverageResult",
    "DirectionalC95Result",
    "DirectionalSafeSizeResult",
    "QualificationDecision",
    "QualificationReason",
    "QualificationState",
    "RequiredTradeFractions",
    "TwoSidedC95Result",
    "candidate_capital_ceiling",
    "evaluate_capture_contract",
    "evaluate_directional_c95",
    "evaluate_two_sided_c95",
    "find_directional_safe_size",
    "qualify_candidate",
    "required_trade_fractions",
]
