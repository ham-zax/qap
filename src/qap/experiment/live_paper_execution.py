"""Pure L2 rebalance execution and Simple+Pro view helpers for live paper sessions."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from typing import Any

from qap.execution.fills import Fill, FillSide
from qap.execution.l2_book_fill import sweep_l2_taker_order
from qap.market import MarketMetadata, PriceSnapshot, VenueInstrument
from qap.market.binance_ws_stream import TimedL2Book, capture_binance_l2_window
from qap.policy import build_rebalance_plan
from qap.policy.lab_settings import LabSettings
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    PortfolioLedger,
    PortfolioState,
)
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
    """Build a live book provider that streams for at most `duration_seconds`."""

    def provider(instruments: Sequence[VenueInstrument]) -> Mapping[str, TimedL2Book]:
        return capture_live_books(instruments, duration_seconds)

    return provider


def instrument_to_dict(inst: VenueInstrument) -> dict[str, str]:
    return {
        "venue": inst.venue,
        "venue_symbol": inst.venue_symbol,
        "base": inst.base.key,
        "quote": inst.quote.key,
    }


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
) -> tuple[dict[AssetId, Decimal] | None, float, bool, float]:
    drawdown = 0.0 if peak_value <= 0 else (1.0 - strat_val / peak_value)
    min_gap = max(cfg.minimum_hold, cfg.cooldown)
    cooldown_ok = last_rot is None or (step_index - last_rot) >= min_gap
    target_weights: dict[AssetId, Decimal] | None = None
    next_pref = last_pref

    if (
        cfg.crash_defense_mode in ("park_usdt", "park_anchor")
        and not parked
        and drawdown >= cfg.regime_break_drawdown
        and cooldown_ok
    ):
        parked = True
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
            w_a = cfg.initial_weight + cfg.rotation_size * Decimal(str(next_pref))
            target_weights = {inst_a.base: w_a, inst_b.base: _ONE - w_a, USDT: _ZERO}
    elif pref_val is not None and pref_val != last_pref and cooldown_ok:
        next_pref = pref_val
        w_a = cfg.initial_weight + cfg.rotation_size * Decimal(str(next_pref))
        target_weights = {inst_a.base: w_a, inst_b.base: _ONE - w_a, USDT: _ZERO}

    return target_weights, next_pref, parked, peak_value


def sweep_rebalance(
    *,
    ledger: PortfolioLedger,
    portfolio_key: str,
    session_id: str,
    step_index: int,
    target_weights: Mapping[AssetId, Decimal],
    mid_prices: Mapping[AssetId, Decimal],
    inst_by_asset: Mapping[AssetId, VenueInstrument],
    basket: tuple[AssetId, ...],
    settings: LabSettings,
    order_rtt_ms: float,
    max_staleness_ms: float,
    t_fill_leg1_ns: int,
    t_fill_leg2_ns: int,
    req_insts: Sequence[VenueInstrument],
    book_provider: BookProvider,
    leg_cache: dict[str, Mapping[str, TimedL2Book]],
    fill_books_leg1: Mapping[str, TimedL2Book] | None,
    fill_books_leg2: Mapping[str, TimedL2Book] | None,
    meta_map: Mapping[str, MarketMetadata],
    decision_time: datetime,
) -> tuple[list[dict[str, Any]], list[str], float | None, float | None]:
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
    if plan.one_way_rebalance_notional < settings.minimum_notional:
        return [], [], None, None

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

    if sells:
        if "leg1" not in leg_cache:
            if fill_books_leg1 is not None:
                leg_cache["leg1"] = fill_books_leg1
            else:
                time.sleep(order_rtt_ms / 1000.0)
                leg_cache["leg1"] = book_provider(req_insts)
        books1 = leg_cache["leg1"]
        for idx, (asset, qty) in enumerate(sells):
            inst = inst_by_asset[asset]
            if inst.venue_symbol not in books1:
                rejected.append(f"missing_book:{inst.venue_symbol}")
                continue
            tbook = books1[inst.venue_symbol]
            res = sweep_l2_taker_order(
                fill_id=f"{session_id}-s{step_index}-{portfolio_key}-sell{idx}",
                decision_id=f"{session_id}-s{step_index}-{portfolio_key}",
                execution_timestamp=tbook.book.observed_at,
                side=FillSide.SELL,
                book=tbook.book,
                book_received_ns=tbook.received_ns,
                target_fill_ns=t_fill_leg1_ns,
                fee_bps=settings.fee_bps,
                base_quantity=min(qty, ledger.current_state.quantity(asset)),
                max_staleness_ms=max_staleness_ms,
                market_metadata=meta_map.get(inst.venue_symbol),
            )
            age1 = res.book_age_ms
            if res.fill is not None and res.vwap_price is not None:
                ledger.apply_fill(res.fill)
                fills_out.append(
                    fill_record(
                        res.fill,
                        levels_consumed=res.levels_consumed,
                        vwap_price=res.vwap_price,
                    )
                )
            elif res.rejected_reason is not None:
                rejected.append(res.rejected_reason)

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
                time.sleep(order_rtt_ms / 1000.0)
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
                budget = min(
                    spendable_now,
                    exact_multiply(avail_usdt, share),
                )
            else:
                budget = _ZERO
            if budget <= _ZERO:
                continue
            tbook = books2[inst.venue_symbol]
            res = sweep_l2_taker_order(
                fill_id=f"{session_id}-s{step_index}-{portfolio_key}-buy{idx}",
                decision_id=f"{session_id}-s{step_index}-{portfolio_key}",
                execution_timestamp=tbook.book.observed_at,
                side=FillSide.BUY,
                book=tbook.book,
                book_received_ns=tbook.received_ns,
                target_fill_ns=t_fill_leg2_ns,
                fee_bps=settings.fee_bps,
                quote_budget=budget,
                max_staleness_ms=max_staleness_ms,
                market_metadata=meta_map.get(inst.venue_symbol),
            )
            age2 = res.book_age_ms
            if res.fill is not None and res.vwap_price is not None:
                ledger.apply_fill(res.fill)
                fills_out.append(
                    fill_record(
                        res.fill,
                        levels_consumed=res.levels_consumed,
                        vwap_price=res.vwap_price,
                    )
                )
            elif res.rejected_reason is not None:
                rejected.append(res.rejected_reason)

    return fills_out, rejected, age1, age2


def record_portfolio_fills(
    entry: dict[str, Any], fills: Sequence[Mapping[str, Any]]
) -> None:
    fee_sum = sum((Decimal(str(f["fee"])) for f in fills), _ZERO)
    slip_sum = sum((Decimal(str(f["slippage_usdt"])) for f in fills), _ZERO)
    entry["fees_usdt"] = str(exact_add(Decimal(str(entry["fees_usdt"])), fee_sum))
    entry["slippage_usdt"] = str(
        exact_add(Decimal(str(entry["slippage_usdt"])), slip_sum)
    )
    entry["rotations"] = int(entry["rotations"]) + 1


def simple_status_text(
    *,
    status: str,
    decisions_count: int,
    trades_count: int,
    vs_hodl_pct: float,
    vs_control_pct: float,
) -> str:
    if status == "stopped":
        return (
            f"Stopped after {decisions_count} check(s) and {trades_count} swap(s): "
            f"{vs_hodl_pct:+.2f}% vs HODL, {vs_control_pct:+.2f}% vs drift control."
        )
    if trades_count == 0:
        return (
            f"Active ({decisions_count} check(s)); "
            "tracking 50/50 HODL with no swaps yet."
        )
    hodl_rel = "ahead of" if vs_hodl_pct >= 0 else "behind"
    ctrl_rel = "ahead of" if vs_control_pct >= 0 else "behind"
    return (
        f"Active ({trades_count} swap(s)): {hodl_rel} HODL ({vs_hodl_pct:+.2f}%), "
        f"{ctrl_rel} drift control ({vs_control_pct:+.2f}%)."
    )


def public_session_view(state: dict[str, Any]) -> dict[str, Any]:
    starting = Decimal(str(state["starting_value"]))
    portfolios_out: dict[str, Any] = {}
    for key in ("strategy", "hodl", "drift_control"):
        p = state["portfolios"][key]
        val = Decimal(str(p["value_usdt"]))
        ret_pct = (
            float(divide(val, starting) - _ONE) * 100.0 if starting > _ZERO else 0.0
        )
        portfolios_out[key] = {
            "value_usdt": str(val),
            "return_pct": ret_pct,
            "holdings": dict(p["holdings"]),
            "fees_usdt": str(p["fees_usdt"]),
            "slippage_usdt": str(p["slippage_usdt"]),
            "rotations": int(p["rotations"]),
        }
    strat_val = Decimal(str(portfolios_out["strategy"]["value_usdt"]))
    hodl_val = Decimal(str(portfolios_out["hodl"]["value_usdt"]))
    ctrl_val = Decimal(str(portfolios_out["drift_control"]["value_usdt"]))
    vs_hodl = (
        float(divide(strat_val, hodl_val) - _ONE) * 100.0 if hodl_val > _ZERO else 0.0
    )
    vs_ctrl = (
        float(divide(strat_val, ctrl_val) - _ONE) * 100.0 if ctrl_val > _ZERO else 0.0
    )
    trades = list(state["trades"])
    decisions = int(state["decisions_count"])
    status = str(state["status"])
    return {
        "session_id": state["session_id"],
        "actor_id": state["actor_id"],
        "status": status,
        "created_at": state["created_at"],
        "updated_at": state["updated_at"],
        "stopped_at": state.get("stopped_at"),
        "coin_a": state["coin_a"],
        "coin_b": state["coin_b"],
        "anchor": state.get("anchor"),
        "bar": state["bar"],
        "order_rtt_ms": float(state["order_rtt_ms"]),
        "max_staleness_ms": float(state["max_staleness_ms"]),
        "settings": dict(state["settings"]),
        "simple_status": simple_status_text(
            status=status,
            decisions_count=decisions,
            trades_count=len(trades),
            vs_hodl_pct=vs_hodl,
            vs_control_pct=vs_ctrl,
        ),
        "vs_hodl_pct": vs_hodl,
        "vs_control_pct": vs_ctrl,
        "decisions_count": decisions,
        "portfolios": portfolios_out,
        "trades": trades,
        "latency_audit": list(state["latency_audit"]),
    }
