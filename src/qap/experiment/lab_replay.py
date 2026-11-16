"""Lab replay composition. Existing QAP fills and ledger own all inventory."""

from collections.abc import Mapping
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
    direction: Literal["into_a", "into_b", "into_usdt", "into_anchor"]
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
    a: MarketBar,
    b: MarketBar,
    anchor: MarketBar | None = None,
    *,
    at_open: bool = False,
) -> dict[AssetId, Decimal]:
    prices = {
        a.instrument.base: Decimal(str(a.open if at_open else a.close)),
        b.instrument.base: Decimal(str(b.open if at_open else b.close)),
        USDT: Decimal(1),
    }
    if anchor is not None and anchor.instrument.base not in prices:
        prices[anchor.instrument.base] = Decimal(
            str(anchor.open if at_open else anchor.close)
        )
    return prices


def _quote_mark(inputs: LabInputs, index: int, quote: AssetId) -> float:
    if quote == USDT:
        return 1.0
    anchor_bar = None if inputs.anchor is None else inputs.anchor.bars[index]
    return float(
        _prices(inputs.first.bars[index], inputs.second.bars[index], anchor_bar)[quote]
    )


def _costs(
    settings: LabSettings,
    inputs: LabInputs,
    index: int,
    notional: Decimal,
    *,
    use_direct: bool | None = None,
    use_third_anchor: bool = False,
) -> tuple[CostModel, bool]:
    direct_route = (inputs.direct is not None) if use_direct is None else use_direct
    if direct_route and inputs.direct is not None:
        legs: tuple[ValidatedBarSeries, ...] = (inputs.direct,)
    elif use_third_anchor and inputs.anchor is not None:
        legs = (inputs.first, inputs.second, inputs.anchor)
    else:
        legs = (inputs.first, inputs.second)
    participation_terms: list[float] = []
    supported = True
    for series in legs:
        bar = series.bars[index]
        volume = bar.volume
        if volume is not None and volume > 0:
            quote_volume = (
                float(volume)
                * float(bar.close)
                * _quote_mark(inputs, index, bar.instrument.quote)
            )
            penalty = 1.0
        else:
            prior_volumes: list[float] = []
            for i in range(max(0, index - 20), index):
                prior_bar = series.bars[i]
                prior_vol = prior_bar.volume
                if prior_vol is not None and prior_vol > 0:
                    prior_volumes.append(
                        float(prior_vol)
                        * float(prior_bar.close)
                        * _quote_mark(inputs, i, bar.instrument.quote)
                    )
            if len(prior_volumes) < 5:
                supported = False
                continue
            quote_volume = float(np.median(prior_volumes))
            penalty = 2.0
        participation_terms.append(penalty * sqrt(float(notional) / quote_volume))
    impact = float(settings.volume_impact_bps) * max(participation_terms, default=0.0)
    slippage = min(9999.0, float(settings.slippage_bps) + impact)
    return CostModel(settings.fee_bps, Decimal(str(slippage))), supported


def _execute(
    inputs: LabInputs,
    ledger: PortfolioLedger,
    settings: LabSettings,
    decision_index: int,
    fill_index: int,
    target_weights: Mapping[AssetId, Decimal],
) -> tuple[LabTrade | None, bool]:
    a, b = inputs.first.instrument.base, inputs.second.instrument.base
    anchor_asset = None if inputs.anchor is None else inputs.anchor.instrument.base
    has_third_anchor = anchor_asset is not None and anchor_asset not in (a, b, USDT)
    basket: tuple[AssetId, ...] = (
        (a, b, anchor_asset, USDT)
        if has_third_anchor and anchor_asset is not None
        else (a, b, USDT)
    )
    anchor_bar = None if inputs.anchor is None else inputs.anchor.bars[decision_index]
    current_prices = _prices(
        inputs.first.bars[decision_index],
        inputs.second.bars[decision_index],
        anchor_bar,
    )
    snapshot = PriceSnapshot.from_prices(
        timestamp=inputs.first.bars[decision_index].bar_end_exclusive,
        numeraire=USDT,
        prices=current_prices,
    )
    target = AllocationTarget.for_basket(
        {asset: target_weights.get(asset, Decimal(0)) for asset in basket},
        basket=basket,
    )
    plan = build_rebalance_plan(
        current_state=ledger.current_state, target=target, prices=snapshot
    )
    notional = plan.one_way_rebalance_notional
    if notional < settings.minimum_notional:
        return None, True
    uses_only_ab = target_weights.get(USDT, Decimal(0)) == 0 and (
        not has_third_anchor
        or anchor_asset is None
        or (
            target_weights.get(anchor_asset, Decimal(0)) == 0
            and ledger.current_state.quantity(anchor_asset) == 0
        )
    )
    used_direct = uses_only_ab and inputs.direct is not None
    use_third_anchor = (
        not used_direct
        and has_third_anchor
        and anchor_asset is not None
        and inputs.anchor is not None
        and (
            target_weights.get(anchor_asset, Decimal(0)) > 0
            or ledger.current_state.quantity(anchor_asset) > 0
        )
    )
    costs, supported = _costs(
        settings,
        inputs,
        decision_index,
        notional,
        use_direct=used_direct,
        use_third_anchor=use_third_anchor,
    )
    next_a, next_b = inputs.first.bars[fill_index], inputs.second.bars[fill_index]
    next_anchor = None if inputs.anchor is None else inputs.anchor.bars[fill_index]
    identifier = f"lab-{decision_index}"
    execution_time = next_a.candle_open_time
    metadata = {
        snapshot.metadata.instrument: snapshot.metadata for snapshot in inputs.metadata
    }
    if used_direct and inputs.direct is not None:
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
        instruments_list = [next_a.instrument, next_b.instrument]
        references = {
            next_a.instrument: Decimal(str(next_a.open)),
            next_b.instrument: Decimal(str(next_b.open)),
        }
        if (
            has_third_anchor
            and anchor_asset is not None
            and next_anchor is not None
            and (
                target_weights.get(anchor_asset, Decimal(0)) > 0
                or ledger.current_state.quantity(anchor_asset) > 0
            )
        ):
            instruments_list.append(next_anchor.instrument)
            references[next_anchor.instrument] = Decimal(str(next_anchor.open))
        execution = execute_multi_asset_rebalance(
            decision_id=identifier,
            execution_timestamp=execution_time,
            plan=plan,
            bridge=USDT,
            instruments=tuple(instruments_list),
            reference_prices=references,
            market_notional_reference_prices=references,
            market_metadata=metadata,
            cost_model=costs,
            require_market_metadata=bool(metadata),
        )
        fills = execution.fills
    if not fills:
        return None, supported
    before_a = ledger.current_state.quantity(a)
    marks = _prices(next_a, next_b, next_anchor, at_open=True)
    fees = slippage = Decimal(0)
    for fill in fills:
        ledger.apply_fill(fill)
        fees += fill.fee_amount * marks[fill.fee_asset]
        slippage += fill.slippage_value * marks[fill.instrument.quote]
    total_val = value_holdings_at_prices(ledger.current_state, marks)
    usdt_weight = (
        float(ledger.current_state.quantity(USDT)) / float(total_val)
        if total_val > 0
        else 0.0
    )
    anchor_weight = (
        float(ledger.current_state.quantity(anchor_asset) * marks[anchor_asset])
        / float(total_val)
        if (has_third_anchor and anchor_asset is not None and total_val > 0)
        else 0.0
    )
    direction: Literal["into_a", "into_b", "into_usdt", "into_anchor"]
    if usdt_weight > 0.5:
        direction = "into_usdt"
    elif anchor_weight > 0.5:
        direction = "into_anchor"
    elif ledger.current_state.quantity(a) > before_a:
        direction = "into_a"
    else:
        direction = "into_b"
    return LabTrade(
        decision_index,
        fill_index,
        execution_time.isoformat(),
        direction,
        "direct" if used_direct else "two legs via USDT",
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
    anchor_asset = None if inputs.anchor is None else inputs.anchor.instrument.base
    has_third_anchor = anchor_asset is not None and anchor_asset not in (a, b, USDT)
    values = np.empty(end - start)
    trades: list[LabTrade] = []
    pending: tuple[int, dict[AssetId, Decimal], float] | None = None
    last_preference: float = 0.0
    last_rotation = start - max(settings.minimum_hold, settings.cooldown) - 1
    peak_value = float(settings.starting_value)
    parked = False
    supported = True
    path = signal.preference if preferences is None else preferences
    interval_seconds = inputs.first.interval.duration.total_seconds()
    cadence = max(1, round(86400 / interval_seconds)) * (7 if kind == "weekly" else 1)
    min_gap = max(settings.minimum_hold, settings.cooldown)
    for index in range(start, end):
        if pending is not None:
            previous, target_map, executed_preference = pending
            trade, cost_ok = _execute(
                inputs, ledger, settings, previous, index, target_map
            )
            supported = supported and cost_ok
            if trade is not None:
                trades.append(trade)
                last_rotation = index
                last_preference = float(executed_preference)
            pending = None
        # Read-only numeric copies accelerate curves/statistics without owning state.
        state = ledger.current_state
        current_a, current_b = inputs.first.bars[index], inputs.second.bars[index]
        anchor_val = (
            float(state.quantity(anchor_asset)) * inputs.anchor.bars[index].close
            if (
                has_third_anchor
                and anchor_asset is not None
                and inputs.anchor is not None
            )
            else 0.0
        )
        value = (
            float(state.quantity(a)) * current_a.close
            + float(state.quantity(b)) * current_b.close
            + float(state.quantity(USDT))
            + anchor_val
        )
        values[index - start] = value
        if index == end - 1 or kind in ("hodl", "hold_a", "hold_b"):
            continue
        target_map_next: dict[AssetId, Decimal] | None = None
        next_preference: float = last_preference
        if kind in ("daily", "weekly") and (index - start + 1) % cadence == 0:
            target_map_next = {
                a: settings.initial_weight,
                b: Decimal(1) - settings.initial_weight,
                USDT: Decimal(0),
            }
        elif kind == "drift":
            actual = float(state.quantity(a)) * current_a.close / value
            if abs(actual - float(settings.initial_weight)) >= 0.05:
                target_map_next = {
                    a: settings.initial_weight,
                    b: Decimal(1) - settings.initial_weight,
                    USDT: Decimal(0),
                }
        elif kind == "strategy":
            peak_value = max(peak_value, value)
            drawdown = 0.0 if peak_value <= 0 else (1.0 - value / peak_value)
            cooldown_ok = index - last_rotation >= min_gap
            if (
                settings.crash_defense_mode in ("park_usdt", "park_anchor")
                and not parked
                and drawdown >= settings.regime_break_drawdown
                and cooldown_ok
            ):
                parked = True
                if settings.crash_defense_mode == "park_usdt":
                    target_map_next = {a: Decimal(0), b: Decimal(0), USDT: Decimal(1)}
                elif anchor_asset == a:
                    target_map_next = {a: Decimal(1), b: Decimal(0), USDT: Decimal(0)}
                elif anchor_asset == b:
                    target_map_next = {a: Decimal(0), b: Decimal(1), USDT: Decimal(0)}
                elif has_third_anchor and anchor_asset is not None:
                    target_map_next = {
                        a: Decimal(0),
                        b: Decimal(0),
                        anchor_asset: Decimal(1),
                        USDT: Decimal(0),
                    }
            elif parked:
                reenter_ok = index - last_rotation >= min_gap * 2
                if (
                    (value >= peak_value or reenter_ok)
                    and np.isfinite(path[index])
                    and float(path[index]) != 0.0
                ):
                    peak_value = value
                    parked = False
                    next_preference = float(path[index])
                    w_a = settings.initial_weight + settings.rotation_size * Decimal(
                        str(next_preference)
                    )
                    target_map_next = {a: w_a, b: Decimal(1) - w_a, USDT: Decimal(0)}
            elif np.isfinite(path[index]):
                next_preference = float(path[index])
                if next_preference != last_preference and cooldown_ok:
                    w_a = settings.initial_weight + settings.rotation_size * Decimal(
                        str(next_preference)
                    )
                    target_map_next = {a: w_a, b: Decimal(1) - w_a, USDT: Decimal(0)}
        if target_map_next is not None:
            pending = index, target_map_next, next_preference
    final_anchor = None if inputs.anchor is None else inputs.anchor.bars[end - 1]
    final_prices = _prices(
        inputs.first.bars[end - 1], inputs.second.bars[end - 1], final_anchor
    )
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
