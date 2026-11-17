"""Causal candle signal progression and pending-target reconciliation helpers."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import numpy as np

from qap.experiment.live_paper_candles import CandleIngestPlan
from qap.experiment.live_paper_execution import (
    BookProvider,
    decide_strategy_target,
    reconcile_target_status,
    record_portfolio_fills,
    sweep_rebalance,
)
from qap.experiment.live_paper_state import strategy_trade_direction, trade_record
from qap.market import MarketMetadata, VenueInstrument
from qap.market.binance_ws_stream import TimedL2Book
from qap.policy.lab_settings import LabSettings
from qap.policy.lab_signals import signal_path
from qap.portfolio import AssetId, PortfolioLedger

_ZERO = Decimal("0")


def weights_to_str(weights: Mapping[AssetId, Decimal]) -> dict[str, str]:
    return {asset.key: str(val) for asset, val in weights.items()}


def weights_from_str(raw: Mapping[str, str]) -> dict[AssetId, Decimal]:
    return {AssetId(key): Decimal(val) for key, val in raw.items()}


def update_trade_entry(
    state: dict[str, Any],
    *,
    target_id: str,
    step_index: int,
    decision_time: datetime,
    direction: str,
    status: str,
    new_fills: list[dict[str, Any]],
    rejected: list[str],
) -> None:
    trades = cast(list[dict[str, Any]], state["trades"])
    for item in reversed(trades):
        if item.get("target_id") == target_id:
            combined = list(item["fills"]) + new_fills
            item["fills"] = combined
            item["status"] = status
            item["direction"] = direction
            item["decision_time"] = decision_time.isoformat()
            item["rejected_reasons"] = list(rejected)
            item["fees_usdt"] = str(sum((Decimal(f["fee"]) for f in combined), _ZERO))
            item["slippage_usdt"] = str(
                sum((Decimal(f["slippage_usdt"]) for f in combined), _ZERO)
            )
            return
    if new_fills:
        trades.append(
            trade_record(
                step_index=step_index,
                decision_time=decision_time,
                direction=direction,
                status=status,
                fills=new_fills,
                rejected=rejected,
                target_id=target_id,
            )
        )


def advance_candle_signals(
    *,
    state: dict[str, Any],
    ingest: CandleIngestPlan,
    req_insts: list[VenueInstrument],
    inst_a: VenueInstrument,
    inst_b: VenueInstrument,
    inst_anc: VenueInstrument | None,
    has_third: bool,
    cfg: LabSettings,
    strat_val: Decimal,
    attempt_idx: int,
) -> tuple[float | None, str]:
    """Advance causal strategy signals across newly completed candles."""

    candle_times = cast(list[int], state["candle_times"])
    candle_closes = cast(dict[str, list[float]], state["candle_closes"])
    if ingest.new_count == 0:
        state["peak_value"] = max(float(state["peak_value"]), float(strat_val))
        pending = state.get("pending_target")
        pref = None if pending is None else float(pending["target_preference"])
        return pref, "book_retry"

    old_len = len(candle_times)
    candle_times.extend(ingest.new_times)
    for inst in req_insts:
        candle_closes[inst.venue_symbol].extend(ingest.new_closes[inst.venue_symbol])
    state["last_candle_time"] = candle_times[-1]
    if ingest.new_count > 1:
        obs_type = "catchup_candle"
        state["track_record_mode"] = "catchup_observed"
        state["catchup_count"] = int(state.get("catchup_count", 0)) + 1
    else:
        obs_type = "new_candle"

    sig = signal_path(
        np.asarray(candle_closes[inst_a.venue_symbol], dtype=np.float64),
        np.asarray(candle_closes[inst_b.venue_symbol], dtype=np.float64),
        cfg,
        None
        if inst_anc is None
        else np.asarray(candle_closes[inst_anc.venue_symbol], dtype=np.float64),
    )
    prev_pending = cast(dict[str, Any] | None, state.get("pending_target"))
    sim_pref = (
        float(prev_pending["target_preference"])
        if prev_pending is not None
        else float(state["last_preference"])
    )
    sim_rot = state.get("last_rotation_step")
    sim_parked = (
        bool(prev_pending["target_parked"])
        if prev_pending is not None
        else bool(state["parked"])
    )
    sim_peak = max(float(state["peak_value"]), float(strat_val))
    latest_target: tuple[dict[AssetId, Decimal], float, bool, float, str] | None = None
    decisions_count = int(state["decisions_count"])
    pref_val: float | None = None

    for offset in range(ingest.new_count):
        idx = old_len + offset
        decisions_count += 1
        cur_pref = (
            float(sig.preference[idx])
            if sig.available and np.isfinite(sig.preference[idx])
            else None
        )
        pref_val = cur_pref
        tw, npref, npark, npeak, reason = decide_strategy_target(
            cfg=cfg,
            inst_a=inst_a,
            inst_b=inst_b,
            inst_anc=inst_anc,
            has_third_anc=has_third,
            strat_val=float(strat_val),
            peak_value=sim_peak,
            parked=sim_parked,
            last_pref=sim_pref,
            last_rot=sim_rot,
            step_index=decisions_count,
            pref_val=cur_pref,
        )
        if tw is not None and reason is not None:
            latest_target = (tw, npref, npark, npeak, reason)
            sim_pref = npref
            sim_parked = npark
        sim_peak = npeak

    state["decisions_count"] = decisions_count
    state["peak_value"] = sim_peak
    if latest_target is not None:
        tw, npref, npark, npeak, reason = latest_target
        if prev_pending is not None:
            cast(list[dict[str, Any]], state["superseded_targets"]).append(
                {
                    "target_id": prev_pending["target_id"],
                    "reason": "superseded_by_newer_candle_target",
                    "superseded_at_step": decisions_count,
                    "previous_status": prev_pending["status"],
                }
            )
        had_partial_fills = bool(prev_pending and prev_pending.get("fills"))
        if (
            not had_partial_fills
            and npref == float(state["last_preference"])
            and npark == bool(state["parked"])
        ):
            state["pending_target"] = None
        else:
            sid = str(state["session_id"])
            state["pending_target"] = {
                "target_id": f"{sid}-t{decisions_count}-{attempt_idx}",
                "target_weights": weights_to_str(tw),
                "target_preference": npref,
                "target_parked": npark,
                "target_peak_value": npeak,
                "reason": reason,
                "created_step": decisions_count,
                "created_candle_time": candle_times[-1],
                "status": "pending",
                "fills": [],
                "attempts": 0,
            }
    return pref_val, obs_type


def reconcile_portfolio_step(
    *,
    state: dict[str, Any],
    pending_key: str,
    portfolio_key: str,
    ledger: PortfolioLedger,
    inst_a: VenueInstrument,
    inst_b: VenueInstrument,
    inst_anc: VenueInstrument | None,
    inst_by_asset: Mapping[AssetId, VenueInstrument],
    basket: tuple[AssetId, ...],
    cfg: LabSettings,
    mid_prices: Mapping[AssetId, Decimal],
    meta_map: Mapping[str, MarketMetadata],
    decision_time: datetime,
    attempt_idx: int,
    step_idx: int,
    t_decide_ns: int,
    req_leg1_ns: int,
    req_leg2_ns: int,
    rtt_ms: float,
    max_stale: float,
    req_insts: list[VenueInstrument],
    book_provider: BookProvider,
    leg_cache: dict[str, Mapping[str, TimedL2Book]],
    fill_books_leg1: Mapping[str, TimedL2Book] | None,
    fill_books_leg2: Mapping[str, TimedL2Book] | None,
    applied_fill_ids: set[str],
) -> tuple[
    list[dict[str, Any]],
    list[str],
    str,
    float | None,
    float | None,
    int | None,
    int | None,
    int,
    int,
]:
    pending = cast(dict[str, Any] | None, state.get(pending_key))
    if pending is None:
        return [], [], "hold", None, None, None, None, req_leg1_ns, req_leg2_ns

    target_weights = weights_from_str(pending["target_weights"])
    qty_a_before = ledger.current_state.quantity(inst_a.base)
    fills, rejected, age1, age2, act1, act2, eff_req1, eff_req2 = sweep_rebalance(
        ledger=ledger,
        portfolio_key=portfolio_key,
        session_id=str(state["session_id"]),
        step_index=step_idx,
        attempt_index=attempt_idx,
        target_weights=target_weights,
        mid_prices=mid_prices,
        inst_by_asset=inst_by_asset,
        basket=basket,
        settings=cfg,
        order_rtt_ms=rtt_ms,
        max_staleness_ms=max_stale,
        t_decide_ns=t_decide_ns,
        t_fill_leg1_ns=req_leg1_ns,
        t_fill_leg2_ns=req_leg2_ns,
        req_insts=req_insts,
        book_provider=book_provider,
        leg_cache=leg_cache,
        fill_books_leg1=fill_books_leg1,
        fill_books_leg2=fill_books_leg2,
        meta_map=meta_map,
        decision_time=decision_time,
        applied_fill_ids=applied_fill_ids,
    )
    pending["attempts"] = int(pending.get("attempts", 0)) + 1
    pending["fills"] = list(pending.get("fills", [])) + fills
    had_any_fills = len(pending["fills"]) > 0
    recon_status = reconcile_target_status(
        ledger_state=ledger.current_state,
        target_weights=target_weights,
        mid_prices=mid_prices,
        inst_by_asset=inst_by_asset,
        basket=basket,
        settings=cfg,
        meta_map=meta_map,
        had_any_fills=had_any_fills,
        rejected=rejected,
        decision_time=decision_time,
    )
    completed = recon_status in ("complete", "dust_complete")
    if fills:
        record_portfolio_fills(
            state["portfolios"][portfolio_key], fills, completed=completed
        )
        if portfolio_key == "strategy":
            direction = strategy_trade_direction(
                ledger.current_state,
                mid_prices,
                inst_a.base,
                inst_b.base,
                None if inst_anc is None else inst_anc.base,
                target_weights,
                qty_a_before,
            )
            update_trade_entry(
                state,
                target_id=str(pending["target_id"]),
                step_index=step_idx,
                decision_time=decision_time,
                direction=direction,
                status="complete" if completed else "partial",
                new_fills=fills,
                rejected=rejected,
            )
    elif completed and had_any_fills:
        state["portfolios"][portfolio_key]["rotations"] = (
            int(state["portfolios"][portfolio_key]["rotations"]) + 1
        )
        if portfolio_key == "strategy":
            for item in reversed(cast(list[dict[str, Any]], state["trades"])):
                if item.get("target_id") == pending["target_id"]:
                    item["status"] = "complete"
                    break

    if completed:
        if portfolio_key == "strategy":
            state["last_preference"] = float(pending["target_preference"])
            state["last_rotation_step"] = step_idx
            state["parked"] = bool(pending["target_parked"])
            state["peak_value"] = float(pending["target_peak_value"])
        state[pending_key] = None
    else:
        pending["status"] = recon_status
        state[pending_key] = pending
    return fills, rejected, recon_status, age1, age2, act1, act2, eff_req1, eff_req2
