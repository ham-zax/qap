"""Lab replay composition. Existing QAP fills and ledger own all inventory."""

from dataclasses import dataclass
from decimal import Decimal
from math import sqrt
from typing import Literal

import numpy as np

from qap.execution import (
    CostModel,
    Fill,
    execute_direct_rebalance_leg,
    execute_multi_asset_rebalance,
)
from qap.market import MarketBar, PriceSnapshot, ValidatedBarSeries
from qap.market.microstructure import PublicMarketMetadataSnapshot
from qap.policy import build_rebalance_plan
from qap.policy.lab_settings import LabSettings
from qap.policy.lab_signals import LabSignal
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    PortfolioLedger,
    PortfolioState,
    value_holdings_at_prices,
)
from qap.portfolio._decimal import divide
from qap.relationship.pair_measurements import Floats

USDT = AssetId("USDT")
ReplayKind = Literal["strategy", "daily", "weekly", "drift", "hodl", "hold_a", "hold_b"]


@dataclass(frozen=True, slots=True)
class LabInputs:
    first: ValidatedBarSeries
    second: ValidatedBarSeries
    direct: ValidatedBarSeries | None = None
    anchor: ValidatedBarSeries | None = None
    metadata: tuple[PublicMarketMetadataSnapshot, ...] = ()

    def __post_init__(self) -> None:
        times = tuple(bar.candle_open_time for bar in self.first.bars)
        for series in (self.second, self.direct, self.anchor):
            if (
                series is not None
                and tuple(bar.candle_open_time for bar in series.bars) != times
            ):
                raise ValueError(
                    "Every replay series must share the exact completed index."
                )
        if self.first.instrument.quote != USDT or self.second.instrument.quote != USDT:
            raise ValueError("Lab valuations require observed USDT markets.")
        if self.first.instrument.base == self.second.instrument.base:
            raise ValueError("Lab inputs must represent two distinct owned assets.")


@dataclass(frozen=True, slots=True)
class LabTrade:
    decision_index: int
    fill_index: int
    time: str
    direction: Literal["into_a", "into_b"]
    route: str
    fees_usdt: str
    slippage_usdt: str
    fills: tuple[Fill, ...]


@dataclass(frozen=True, slots=True)
class LabReplay:
    # Floating values are presentation/statistics projections, never inventory.
    values: Floats
    terminal_value: Decimal
    ending_state: PortfolioState
    trades: tuple[LabTrade, ...]
    costs_supported: bool
    last_rotation_index: int
    last_preference: float


def _prices(
    a: MarketBar, b: MarketBar, *, at_open: bool = False
) -> dict[AssetId, Decimal]:
    return {
        a.instrument.base: Decimal(str(a.open if at_open else a.close)),
        b.instrument.base: Decimal(str(b.open if at_open else b.close)),
        USDT: Decimal(1),
    }


def _costs(
    settings: LabSettings, inputs: LabInputs, index: int, notional: Decimal
) -> tuple[CostModel, bool]:
    bars = (
        (inputs.direct.bars[index],)
        if inputs.direct is not None
        else (inputs.first.bars[index], inputs.second.bars[index])
    )
    participation: list[float] = []
    supported = True
    for bar in bars:
        volume = bar.volume
        if volume is None or volume <= 0:
            supported = False
            continue
        quote_mark = 1.0
        if bar.instrument.quote != USDT:
            quote_mark = float(
                _prices(inputs.first.bars[index], inputs.second.bars[index])[
                    bar.instrument.quote
                ]
            )
        quote_volume = volume * bar.close * quote_mark
        participation.append(float(notional) / quote_volume)
    impact = float(settings.volume_impact_bps) * sqrt(max(participation, default=0.0))
    slippage = min(9999.0, float(settings.slippage_bps) + impact)
    return CostModel(settings.fee_bps, Decimal(str(slippage))), supported


def _execute(
    inputs: LabInputs,
    ledger: PortfolioLedger,
    settings: LabSettings,
    decision_index: int,
    fill_index: int,
    target_weight: Decimal,
) -> tuple[LabTrade | None, bool]:
    a, b = inputs.first.instrument.base, inputs.second.instrument.base
    current_prices = _prices(
        inputs.first.bars[decision_index], inputs.second.bars[decision_index]
    )
    snapshot = PriceSnapshot.from_prices(
        timestamp=inputs.first.bars[decision_index].bar_end_exclusive,
        numeraire=USDT,
        prices=current_prices,
    )
    target = AllocationTarget.for_basket(
        {a: target_weight, b: Decimal(1) - target_weight, USDT: Decimal(0)},
        basket=(a, b, USDT),
    )
    plan = build_rebalance_plan(
        current_state=ledger.current_state, target=target, prices=snapshot
    )
    notional = abs(plan.quantity_deltas.get(a, Decimal(0))) * current_prices[a]
    if notional < settings.minimum_notional:
        return None, True
    costs, supported = _costs(settings, inputs, decision_index, notional)
    next_a, next_b = inputs.first.bars[fill_index], inputs.second.bars[fill_index]
    identifier = f"lab-{decision_index}"
    execution_time = next_a.candle_open_time
    metadata = {
        snapshot.metadata.instrument: snapshot.metadata for snapshot in inputs.metadata
    }
    if inputs.direct is not None:
        direct = inputs.direct.bars[fill_index]
        execution = execute_direct_rebalance_leg(
            fill_id=f"{identifier}-direct",
            decision_id=identifier,
            execution_timestamp=execution_time,
            instrument=direct.instrument,
            quantity_deltas=plan.quantity_deltas,
            current_state=ledger.current_state,
            reference_price=Decimal(str(direct.open)),
            market_notional_reference_price=Decimal(str(direct.open)),
            cost_model=costs,
            market_metadata=metadata.get(direct.instrument),
        )
        fills = () if execution.fill is None else (execution.fill,)
    else:
        references = {
            next_a.instrument: Decimal(str(next_a.open)),
            next_b.instrument: Decimal(str(next_b.open)),
        }
        execution = execute_multi_asset_rebalance(
            decision_id=identifier,
            execution_timestamp=execution_time,
            plan=plan,
            bridge=USDT,
            instruments=(next_a.instrument, next_b.instrument),
            reference_prices=references,
            market_notional_reference_prices=references,
            market_metadata=metadata,
            cost_model=costs,
            require_market_metadata=bool(metadata),
        )
        fills = execution.fills
    if not fills:
        return None, supported
    before = ledger.current_state.quantity(a)
    marks = _prices(next_a, next_b, at_open=True)
    fees = slippage = Decimal(0)
    for fill in fills:
        ledger.apply_fill(fill)
        fees += fill.fee_amount * marks[fill.fee_asset]
        slippage += fill.slippage_value * marks[fill.instrument.quote]
    return LabTrade(
        decision_index,
        fill_index,
        execution_time.isoformat(),
        "into_a" if ledger.current_state.quantity(a) > before else "into_b",
        "direct" if inputs.direct is not None else "two legs via USDT",
        str(fees),
        str(slippage),
        fills,
    ), supported


def run_lab_replay(
    inputs: LabInputs,
    settings: LabSettings,
    signal: LabSignal,
    *,
    kind: ReplayKind = "strategy",
    start: int = 0,
    end: int | None = None,
    preferences: Floats | None = None,
) -> LabReplay:
    """Close decisions, next-open fills, no final-bar fill and no unowned sales."""
    end = len(inputs.first.bars) if end is None else end
    if not 0 <= start < end <= len(inputs.first.bars):
        raise ValueError("Replay bounds must contain a non-empty observed window.")
    a, b = inputs.first.instrument.base, inputs.second.instrument.base
    prices = _prices(inputs.first.bars[start], inputs.second.bars[start])
    weight = (
        Decimal(1)
        if kind == "hold_a"
        else Decimal(0)
        if kind == "hold_b"
        else settings.initial_weight
    )
    ledger = PortfolioLedger(
        PortfolioState.from_holdings(
            {
                a: divide(settings.starting_value * weight, prices[a]),
                b: divide(settings.starting_value * (1 - weight), prices[b]),
            }
        )
    )
    values = np.empty(end - start)
    trades: list[LabTrade] = []
    pending: tuple[int, Decimal, float] | None = None
    last_preference: float = 0.0
    last_rotation = start - max(settings.minimum_hold, settings.cooldown) - 1
    supported = True
    path = signal.preference if preferences is None else preferences
    interval_seconds = inputs.first.interval.duration.total_seconds()
    cadence = max(1, round(86400 / interval_seconds)) * (7 if kind == "weekly" else 1)
    for index in range(start, end):
        if pending is not None:
            previous, target, executed_preference = pending
            trade, cost_ok = _execute(inputs, ledger, settings, previous, index, target)
            supported = supported and cost_ok
            if trade is not None:
                trades.append(trade)
                last_rotation = index
                last_preference = float(executed_preference)
            pending = None
        # Read-only numeric copies accelerate curves/statistics without owning state.
        state = ledger.current_state
        current_a, current_b = inputs.first.bars[index], inputs.second.bars[index]
        value = (
            float(state.quantity(a)) * current_a.close
            + float(state.quantity(b)) * current_b.close
            + float(state.quantity(USDT))
        )
        values[index - start] = value
        if index == end - 1 or kind in ("hodl", "hold_a", "hold_b"):
            continue
        target_weight: Decimal | None = None
        next_preference: float = last_preference
        if kind in ("daily", "weekly") and (index - start + 1) % cadence == 0:
            target_weight = settings.initial_weight
        elif kind == "drift":
            actual = float(state.quantity(a)) * current_a.close / value
            if abs(actual - float(settings.initial_weight)) >= 0.05:
                target_weight = settings.initial_weight
        elif kind == "strategy" and np.isfinite(path[index]):
            next_preference = float(path[index])
            if next_preference != last_preference and index - last_rotation >= max(
                settings.minimum_hold, settings.cooldown
            ):
                target_weight = (
                    settings.initial_weight
                    + settings.rotation_size * Decimal(str(next_preference))
                )
        if target_weight is not None:
            pending = index, target_weight, next_preference
    final_prices = _prices(inputs.first.bars[end - 1], inputs.second.bars[end - 1])
    terminal = value_holdings_at_prices(ledger.current_state, final_prices)
    values[-1] = float(terminal)
    return LabReplay(
        values,
        terminal,
        ledger.current_state,
        tuple(trades),
        supported,
        last_rotation,
        last_preference,
    )
