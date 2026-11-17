"""Pure L2 rebalance execution and reconciliation helpers for live paper sessions."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from qap.execution.fills import Fill, FillSide
from qap.execution.l2_book_fill import sweep_l2_taker_order
from qap.execution.precision import MarketPrecision, MarketPrecisionError
from qap.market import MarketMetadata, PriceSnapshot, VenueInstrument
from qap.market.binance_ws_stream import TimedL2Book, capture_binance_l2_window
from qap.policy import build_rebalance_plan
from qap.policy.lab_settings import LabSettings
from qap.portfolio import AllocationTarget, AssetId, PortfolioLedger, PortfolioState
from qap.portfolio._decimal import divide, exact_add, exact_multiply, exact_subtract

_ZERO = Decimal("0")
_ONE = Decimal("1")
_TWO = Decimal("2")
USDT = AssetId("USDT")
BookProvider = Callable[[Sequence[VenueInstrument]], Mapping[str, TimedL2Book]]


def canonical_json(value: Any) -> bytes:
    def encode(item: object) -> str:
        if isinstance(item, datetime):
            return item.isoformat()
        if isinstance(item, Decimal):
            return str(item)
        raise TypeError(f"Unsupported paper session value: {type(item).__name__}")

    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=encode
    ).encode("utf-8")


def default_instrument(coin: str) -> VenueInstrument:
    code = coin.split(":", 1)[-1].strip().upper()
    if not code:
        raise ValueError("Coin listing cannot be empty.")
    return VenueInstrument("binance", f"{code}USDT", AssetId(code), USDT)


def mid_decimal(book: TimedL2Book) -> Decimal:
    bid = Decimal(str(book.book.best_bid))
    ask = Decimal(str(book.book.best_ask))
    return divide(exact_add(bid, ask), _TWO)


def capture_live_books(
    instruments: Sequence[VenueInstrument], duration_seconds: float = 5.0
) -> dict[str, TimedL2Book]:
    async def _run() -> dict[str, TimedL2Book]:
        return await capture_binance_l2_window(
            instruments, duration_seconds=duration_seconds, stop_when_complete=True
        )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_run())
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, _run()).result()


def window_book_provider(duration_seconds: float) -> BookProvider:
    def provider(instruments: Sequence[VenueInstrument]) -> Mapping[str, TimedL2Book]:
        return capture_live_books(instruments, duration_seconds)

    return provider


def instrument_from_dict(raw: Mapping[str, Any]) -> VenueInstrument:
    return VenueInstrument(
        venue=str(raw["venue"]),
        venue_symbol=str(raw["venue_symbol"]),
        base=AssetId(str(raw["base"])),
        quote=AssetId(str(raw["quote"])),
    )


def ledger_from_holdings(raw: Mapping[str, str]) -> PortfolioLedger:
    return PortfolioLedger(
        PortfolioState.from_holdings({AssetId(k): Decimal(v) for k, v in raw.items()})
    )


def holdings_dict(state: PortfolioState) -> dict[str, str]:
    return {asset.key: str(qty) for asset, qty in state.holdings.items()}


def fill_record(
    fill: Fill, *, levels_consumed: int, vwap_price: Decimal
) -> dict[str, Any]:
    return {
        "fill_id": fill.fill_id,
        "market": fill.venue_symbol,
        "side": fill.side.value,
        "base_asset": fill.base.key,
        "quote_asset": fill.quote.key,
        "base_quantity": str(fill.base_quantity),
        "execution_price": str(fill.execution_price),
        "reference_price": str(fill.reference_price),
        "vwap_price": str(vwap_price),
        "gross_quote_notional": str(fill.gross_quote_notional),
        "fee": str(fill.fee_amount),
        "fee_asset": fill.fee_asset.key,
        "slippage_usdt": str(fill.slippage_value),
        "levels_consumed": levels_consumed,
    }


def decide_strategy_target(
    *,
    cfg: LabSettings,
    inst_a: VenueInstrument,
    inst_b: VenueInstrument,
    inst_anc: VenueInstrument | None,
    has_third_anc: bool,
    strat_val: float,
    peak_value: float,
    parked: bool,
    last_pref: float,
    last_rot: int | None,
    step_index: int,
    pref_val: float | None,
) -> tuple[dict[AssetId, Decimal] | None, float, bool, float, str | None]:
    drawdown = 0.0 if peak_value <= 0 else (1.0 - strat_val / peak_value)
    min_gap = max(cfg.minimum_hold, cfg.cooldown)
    cooldown_ok = last_rot is None or (step_index - last_rot) >= min_gap
    target_weights: dict[AssetId, Decimal] | None = None
    next_pref = last_pref
    reason: str | None = None

    if (
        cfg.crash_defense_mode in ("park_usdt", "park_anchor")
        and not parked
        and drawdown >= cfg.regime_break_drawdown
        and cooldown_ok
    ):
        parked = True
        reason = "crash_defense"
        if cfg.crash_defense_mode == "park_usdt":
            target_weights = {inst_a.base: _ZERO, inst_b.base: _ZERO, USDT: _ONE}
        elif inst_anc is not None and inst_anc.base == inst_a.base:
            target_weights = {inst_a.base: _ONE, inst_b.base: _ZERO, USDT: _ZERO}
        elif inst_anc is not None and inst_anc.base == inst_b.base:
            target_weights = {inst_a.base: _ZERO, inst_b.base: _ONE, USDT: _ZERO}
        elif has_third_anc and inst_anc is not None:
            target_weights = {
                inst_a.base: _ZERO,
                inst_b.base: _ZERO,
                inst_anc.base: _ONE,
                USDT: _ZERO,
            }
    elif parked:
        reenter_ok = last_rot is None or (step_index - last_rot) >= min_gap * 2
        if (
            (strat_val >= peak_value or reenter_ok)
            and pref_val is not None
            and pref_val != 0.0
        ):
            peak_value = strat_val
            parked = False
            next_pref = pref_val
            reason = "reenter"
            w_a = cfg.initial_weight + cfg.rotation_size * Decimal(str(next_pref))
            target_weights = {inst_a.base: w_a, inst_b.base: _ONE - w_a, USDT: _ZERO}
    elif pref_val is not None and pref_val != last_pref and cooldown_ok:
        next_pref = pref_val
        reason = "signal_change"
        w_a = cfg.initial_weight + cfg.rotation_size * Decimal(str(next_pref))
        target_weights = {inst_a.base: w_a, inst_b.base: _ONE - w_a, USDT: _ZERO}

    return target_weights, next_pref, parked, peak_value, reason


def _is_tradable_leg(
    asset: AssetId,
    qty_delta: Decimal,
    mid_price: Decimal,
    inst_by_asset: Mapping[AssetId, VenueInstrument],
    meta_map: Mapping[str, MarketMetadata],
    minimum_notional: Decimal,
) -> bool:
    notional = exact_multiply(qty_delta.copy_abs(), mid_price)
    if notional < minimum_notional:
        return False
    inst = inst_by_asset.get(asset)
    if inst is None:
        return False
    meta = meta_map.get(inst.venue_symbol)
    if meta is None:
        return True
    precision = MarketPrecision(meta)
    rounded = precision.quantity_down(qty_delta.copy_abs())
    if rounded <= _ZERO:
        return False
    try:
        precision.validate_fill(
            base_quantity=rounded,
            execution_price=mid_price,
            market_notional_reference_price=mid_price,
        )
    except MarketPrecisionError:
        return False
    return True


def reconcile_target_status(
    *,
    ledger_state: PortfolioState,
    target_weights: Mapping[AssetId, Decimal],
    mid_prices: Mapping[AssetId, Decimal],
    inst_by_asset: Mapping[AssetId, VenueInstrument],
    basket: tuple[AssetId, ...],
    settings: LabSettings,
    meta_map: Mapping[str, MarketMetadata],
    had_any_fills: bool,
    rejected: Sequence[str],
    decision_time: datetime,
) -> str:
    snapshot = PriceSnapshot.from_prices(
        timestamp=decision_time, numeraire=USDT, prices=mid_prices
    )
    target = AllocationTarget.for_basket(
        {asset: target_weights.get(asset, _ZERO) for asset in basket},
        basket=basket,
    )
    remaining = build_rebalance_plan(
        current_state=ledger_state, target=target, prices=snapshot
    )
    tradable_sells = [
        (asset, delta)
        for asset, delta in remaining.quantity_deltas.items()
        if asset != USDT
        and delta < _ZERO
        and _is_tradable_leg(
            asset,
            delta,
            mid_prices[asset],
            inst_by_asset,
            meta_map,
            settings.minimum_notional,
        )
    ]
    available_usdt = ledger_state.quantity(USDT) + sum(
        (
            exact_multiply(delta.copy_abs(), mid_prices[asset])
            for asset, delta in tradable_sells
        ),
        _ZERO,
    )
    tradable_buys = any(
        _is_tradable_leg(
            asset,
            min(delta, available_usdt / mid_prices[asset]),
            mid_prices[asset],
            inst_by_asset,
            meta_map,
            settings.minimum_notional,
        )
        for asset, delta in remaining.quantity_deltas.items()
        if asset != USDT and delta > _ZERO and available_usdt > _ZERO
    )
    tradable_left = bool(tradable_sells) or tradable_buys
    if not tradable_left and not rejected:
        return (
            "dust_complete"
            if remaining.one_way_rebalance_notional > _ZERO
            else "complete"
        )
    if not tradable_left and had_any_fills:
        return "dust_complete"
    if had_any_fills:
        return "partial"
    return "rejected"


def _effective_exec_time(tbook: TimedL2Book, effective_fill_ns: int) -> datetime:
    extra_us = max(0, (effective_fill_ns - tbook.received_ns) // 1000)
    return tbook.book.observed_at + timedelta(microseconds=extra_us)


def _sleep_until_epoch_ns(target_ns: int) -> None:
    remaining_s = (target_ns - time.time_ns()) / 1_000_000_000.0
    if remaining_s > 0.0:
        deadline = time.monotonic() + remaining_s
        while (left := deadline - time.monotonic()) > 0.0:
            time.sleep(left)


def sweep_rebalance(
    *,
    ledger: PortfolioLedger,
    portfolio_key: str,
    session_id: str,
    step_index: int,
    attempt_index: int | None = None,
    target_weights: Mapping[AssetId, Decimal],
    mid_prices: Mapping[AssetId, Decimal],
    inst_by_asset: Mapping[AssetId, VenueInstrument],
    basket: tuple[AssetId, ...],
    settings: LabSettings,
    order_rtt_ms: float,
    max_staleness_ms: float,
    t_decide_ns: int | None = None,
    t_fill_leg1_ns: int,
    t_fill_leg2_ns: int,
    req_insts: Sequence[VenueInstrument],
    book_provider: BookProvider,
    leg_cache: dict[str, Mapping[str, TimedL2Book]],
    fill_books_leg1: Mapping[str, TimedL2Book] | None,
    fill_books_leg2: Mapping[str, TimedL2Book] | None,
    meta_map: Mapping[str, MarketMetadata],
    decision_time: datetime,
    applied_fill_ids: set[str] | None = None,
) -> tuple[
    list[dict[str, Any]],
    list[str],
    float | None,
    float | None,
    int | None,
    int | None,
    int,
    int,
]:
    snapshot = PriceSnapshot.from_prices(
        timestamp=decision_time, numeraire=USDT, prices=mid_prices
    )
    target = AllocationTarget.for_basket(
        {asset: target_weights.get(asset, _ZERO) for asset in basket},
        basket=basket,
    )
    plan = build_rebalance_plan(
        current_state=ledger.current_state, target=target, prices=snapshot
    )
    rtt_ns = int(order_rtt_ms * 1_000_000)
    req_leg1_ns = t_fill_leg1_ns
    req_leg2_ns = t_fill_leg2_ns
    if plan.one_way_rebalance_notional < settings.minimum_notional:
        return [], [], None, None, None, None, req_leg1_ns, req_leg2_ns

    sells = [
        (asset, delta.copy_abs())
        for asset, delta in plan.quantity_deltas.items()
        if asset != USDT and delta < _ZERO
    ]
    buys = [
        (asset, delta)
        for asset, delta in plan.quantity_deltas.items()
        if asset != USDT and delta > _ZERO
    ]
    fills_out: list[dict[str, Any]] = []
    rejected: list[str] = []
    age1: float | None = None
    age2: float | None = None
    actual_leg1_ns: int | None = None
    actual_leg2_ns: int | None = None
    seen_fills: set[str] = applied_fill_ids if applied_fill_ids is not None else set()
    tag = f"a{attempt_index}" if attempt_index is not None else f"s{step_index}"

    if sells:
        if "leg1" not in leg_cache:
            if fill_books_leg1 is not None:
                leg_cache["leg1"] = fill_books_leg1
            else:
                _sleep_until_epoch_ns(req_leg1_ns)
                leg_cache["leg1"] = book_provider(req_insts)
        books1 = leg_cache["leg1"]
        for idx, (asset, qty) in enumerate(sells):
            inst = inst_by_asset[asset]
            if inst.venue_symbol not in books1:
                rejected.append(f"missing_book:{inst.venue_symbol}")
                continue
            fid = f"{session_id}-{tag}-{portfolio_key}-sell{idx}"
            if fid in seen_fills:
                continue
            tbook = books1[inst.venue_symbol]
            eff_ns = max(req_leg1_ns, tbook.received_ns)
            res = sweep_l2_taker_order(
                fill_id=fid,
                decision_id=f"{session_id}-{tag}-{portfolio_key}",
                execution_timestamp=_effective_exec_time(tbook, eff_ns),
                side=FillSide.SELL,
                book=tbook.book,
                book_received_ns=tbook.received_ns,
                target_fill_ns=req_leg1_ns,
                fee_bps=settings.fee_bps,
                base_quantity=min(qty, ledger.current_state.quantity(asset)),
                max_staleness_ms=max_staleness_ms,
                market_metadata=meta_map.get(inst.venue_symbol),
            )
            age1 = res.book_age_ms if age1 is None else max(age1, res.book_age_ms)
            if res.fill is not None and res.vwap_price is not None:
                ledger.apply_fill(res.fill)
                seen_fills.add(fid)
                fills_out.append(
                    fill_record(
                        res.fill,
                        levels_consumed=res.levels_consumed,
                        vwap_price=res.vwap_price,
                    )
                )
                actual_leg1_ns = (
                    res.effective_fill_ns
                    if actual_leg1_ns is None
                    else max(actual_leg1_ns, res.effective_fill_ns)
                )
            elif res.rejected_reason is not None:
                rejected.append(res.rejected_reason)

    if actual_leg1_ns is not None:
        base_decide = t_decide_ns if t_decide_ns is not None else (req_leg1_ns - rtt_ns)
        req_leg2_ns = max(base_decide + 2 * rtt_ns, actual_leg1_ns + rtt_ns)

    target_usdt_reserve = plan.target_values.get(USDT, _ZERO)
    avail_usdt = max(
        _ZERO,
        exact_subtract(ledger.current_state.quantity(USDT), target_usdt_reserve),
    )
    if buys and avail_usdt > _ZERO:
        if "leg2" not in leg_cache:
            if fill_books_leg2 is not None:
                leg_cache["leg2"] = fill_books_leg2
            else:
                _sleep_until_epoch_ns(req_leg2_ns)
                leg_cache["leg2"] = book_provider(req_insts)
        books2 = leg_cache["leg2"]
        total_req = sum(
            (exact_multiply(delta, mid_prices[asset]) for asset, delta in buys),
            _ZERO,
        )
        for idx, (asset, delta) in enumerate(buys):
            inst = inst_by_asset[asset]
            if inst.venue_symbol not in books2:
                rejected.append(f"missing_book:{inst.venue_symbol}")
                continue
            fid = f"{session_id}-{tag}-{portfolio_key}-buy{idx}"
            if fid in seen_fills:
                continue
            spendable_now = max(
                _ZERO,
                exact_subtract(
                    ledger.current_state.quantity(USDT), target_usdt_reserve
                ),
            )
            if target_weights.get(USDT, _ZERO) == _ZERO and len(buys) == 1:
                budget = spendable_now
            elif total_req > _ZERO:
                share = divide(exact_multiply(delta, mid_prices[asset]), total_req)
                budget = min(spendable_now, exact_multiply(avail_usdt, share))
            else:
                budget = _ZERO
            if budget <= _ZERO:
                continue
            tbook = books2[inst.venue_symbol]
            eff_ns = max(req_leg2_ns, tbook.received_ns)
            res = sweep_l2_taker_order(
                fill_id=fid,
                decision_id=f"{session_id}-{tag}-{portfolio_key}",
                execution_timestamp=_effective_exec_time(tbook, eff_ns),
                side=FillSide.BUY,
                book=tbook.book,
                book_received_ns=tbook.received_ns,
                target_fill_ns=req_leg2_ns,
                fee_bps=settings.fee_bps,
                quote_budget=budget,
                max_staleness_ms=max_staleness_ms,
                market_metadata=meta_map.get(inst.venue_symbol),
            )
            age2 = res.book_age_ms if age2 is None else max(age2, res.book_age_ms)
            if res.fill is not None and res.vwap_price is not None:
                ledger.apply_fill(res.fill)
                seen_fills.add(fid)
                fills_out.append(
                    fill_record(
                        res.fill,
                        levels_consumed=res.levels_consumed,
                        vwap_price=res.vwap_price,
                    )
                )
                actual_leg2_ns = (
                    res.effective_fill_ns
                    if actual_leg2_ns is None
                    else max(actual_leg2_ns, res.effective_fill_ns)
                )
            elif res.rejected_reason is not None:
                rejected.append(res.rejected_reason)

    return (
        fills_out,
        rejected,
        age1,
        age2,
        actual_leg1_ns,
        actual_leg2_ns,
        req_leg1_ns,
        req_leg2_ns,
    )


def record_portfolio_fills(
    entry: dict[str, Any], fills: Sequence[Mapping[str, Any]], *, completed: bool = True
) -> None:
    fee_sum = sum((Decimal(str(f["fee"])) for f in fills), _ZERO)
    slip_sum = sum((Decimal(str(f["slippage_usdt"])) for f in fills), _ZERO)
    entry["fees_usdt"] = str(exact_add(Decimal(str(entry["fees_usdt"])), fee_sum))
    entry["slippage_usdt"] = str(
        exact_add(Decimal(str(entry["slippage_usdt"])), slip_sum)
    )
    if completed:
        entry["rotations"] = int(entry["rotations"]) + 1
