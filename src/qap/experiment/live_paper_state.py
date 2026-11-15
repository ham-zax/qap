"""Pure state builders and projections for forward L2 paper sessions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from qap.experiment.live_paper_execution import USDT, instrument_to_dict
from qap.market import VenueInstrument
from qap.policy.lab_settings import LabSettings
from qap.portfolio import AssetId, PortfolioState, value_holdings_at_prices
from qap.portfolio._decimal import divide, exact_multiply
from qap.relationship.pair_measurements import Floats

SCHEMA_VERSION = "qap.lab.paper_session.v1"
MAX_CLOSE_HISTORY = 1999
DRIFT_TOLERANCE = 0.05
_ZERO = Decimal("0")
_HALF = 0.5
_NS_PER_MS = 1_000_000.0


def required_instruments(
    inst_a: VenueInstrument,
    inst_b: VenueInstrument,
    inst_anc: VenueInstrument | None,
) -> list[VenueInstrument]:
    """List each distinct venue market a session must watch, anchor last."""

    insts = [inst_a, inst_b]
    if inst_anc is not None and inst_anc.venue_symbol not in {
        inst_a.venue_symbol,
        inst_b.venue_symbol,
    }:
        insts.append(inst_anc)
    return insts


def new_session_state(
    *,
    session_id: str,
    actor_id: str,
    now_iso: str,
    coin_a: str,
    coin_b: str,
    anchor: str | None,
    bar: str,
    order_rtt_ms: float,
    max_staleness_ms: float,
    cfg: LabSettings,
    inst_a: VenueInstrument,
    inst_b: VenueInstrument,
    inst_anc: VenueInstrument | None,
    close_history: Mapping[str, Sequence[float]],
    init_holdings: Mapping[str, str],
) -> dict[str, Any]:
    """Build the initial persisted state with three identical starting ledgers."""

    entry = {
        "holdings": dict(init_holdings),
        "value_usdt": str(cfg.starting_value),
        "fees_usdt": "0",
        "slippage_usdt": "0",
        "rotations": 0,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "actor_id": actor_id,
        "status": "active",
        "created_at": now_iso,
        "updated_at": now_iso,
        "stopped_at": None,
        "coin_a": coin_a,
        "coin_b": coin_b,
        "anchor": anchor,
        "bar": bar,
        "order_rtt_ms": float(order_rtt_ms),
        "max_staleness_ms": float(max_staleness_ms),
        "starting_value": str(cfg.starting_value),
        "settings": cfg.model_dump(mode="json"),
        "instruments": {
            "a": instrument_to_dict(inst_a),
            "b": instrument_to_dict(inst_b),
            "anchor": None if inst_anc is None else instrument_to_dict(inst_anc),
        },
        "close_history": {sym: list(vals) for sym, vals in close_history.items()},
        "decisions_count": 0,
        "last_preference": 0.0,
        "last_rotation_step": None,
        "peak_value": float(cfg.starting_value),
        "parked": False,
        "portfolios": {
            "strategy": dict(entry),
            "hodl": dict(entry),
            "drift_control": dict(entry),
        },
        "trades": [],
        "latency_audit": [],
    }


def append_mid_closes(
    history: dict[str, list[float]],
    insts: Sequence[VenueInstrument],
    mids: Mapping[AssetId, Decimal],
    historical_closes: Mapping[str, Floats] | None,
) -> None:
    """Append the latest decision mid to each market's bounded close history."""

    for inst in insts:
        sym = inst.venue_symbol
        if historical_closes is not None and sym in historical_closes:
            values = [float(x) for x in historical_closes[sym][-MAX_CLOSE_HISTORY:]]
        else:
            values = list(history.get(sym, []))[-MAX_CLOSE_HISTORY:]
        values.append(float(mids[inst.base]))
        history[sym] = values


def strategy_trade_direction(
    state: PortfolioState,
    mids: Mapping[AssetId, Decimal],
    asset_a: AssetId,
    qty_a_before: Decimal,
) -> str:
    """Classify a completed strategy rebalance as into USDT, coin A, or coin B."""

    value = value_holdings_at_prices(state, mids)
    usdt_weight = float(divide(state.quantity(USDT), value)) if value > _ZERO else 0.0
    if usdt_weight > _HALF:
        return "into_usdt"
    return "into_a" if state.quantity(asset_a) > qty_a_before else "into_b"


def trade_record(
    *,
    step_index: int,
    decision_time: datetime,
    direction: str,
    fills: Sequence[Mapping[str, Any]],
    rejected: Sequence[str],
) -> dict[str, Any]:
    """Summarize one executed two-leg strategy rotation."""

    return {
        "step_index": step_index,
        "decision_time": decision_time.isoformat(),
        "direction": direction,
        "route": "two legs via USDT",
        "fees_usdt": str(sum((Decimal(f["fee"]) for f in fills), _ZERO)),
        "slippage_usdt": str(sum((Decimal(f["slippage_usdt"]) for f in fills), _ZERO)),
        "rejected_reasons": list(rejected),
        "fills": list(fills),
    }


def latency_record(
    *,
    step_index: int,
    t_exch_us: int | None,
    t_recv_ns: int,
    t_decide_ns: int,
    t_fill_leg1_ns: int,
    t_fill_leg2_ns: int,
    order_rtt_ms: float,
    age_leg1_ms: float | None,
    age_leg2_ms: float | None,
    preference: float | None,
    fills: Sequence[Mapping[str, Any]],
    rejected: Sequence[str],
) -> dict[str, Any]:
    """Record the four clocks and outcome of one decision step."""

    return {
        "step_index": step_index,
        "t_exch_us": t_exch_us,
        "t_recv_ns": t_recv_ns,
        "t_decide_ns": t_decide_ns,
        "t_fill_leg1_ns": t_fill_leg1_ns,
        "t_fill_leg2_ns": t_fill_leg2_ns,
        "order_rtt_ms": order_rtt_ms,
        "recv_to_decide_ms": (t_decide_ns - t_recv_ns) / _NS_PER_MS,
        "decide_to_fill_leg1_ms": (t_fill_leg1_ns - t_decide_ns) / _NS_PER_MS,
        "decide_to_fill_leg2_ms": (t_fill_leg2_ns - t_decide_ns) / _NS_PER_MS,
        "book_age_leg1_ms": age_leg1_ms,
        "book_age_leg2_ms": age_leg2_ms,
        "signal_preference": preference,
        "action": "swap" if fills else ("rejected" if rejected else "hold"),
        "rejected_reasons": list(rejected),
    }


def needs_drift_rebalance(
    state: PortfolioState,
    mids: Mapping[AssetId, Decimal],
    asset_a: AssetId,
    initial_weight: Decimal,
) -> bool:
    """Return whether the drift-control ledger left its initial weight band."""

    value = value_holdings_at_prices(state, mids)
    actual_a = (
        float(exact_multiply(state.quantity(asset_a), mids[asset_a])) / float(value)
        if value > _ZERO
        else float(initial_weight)
    )
    return abs(actual_a - float(initial_weight)) >= DRIFT_TOLERANCE


def session_list_row(view: Mapping[str, Any]) -> dict[str, Any]:
    """Project a public session view onto its compact list row."""

    keys = (
        "session_id",
        "actor_id",
        "status",
        "created_at",
        "updated_at",
        "coin_a",
        "coin_b",
        "anchor",
        "bar",
        "decisions_count",
        "vs_hodl_pct",
        "vs_control_pct",
        "simple_status",
    )
    row = {key: view[key] for key in keys}
    row["trades_count"] = len(view["trades"])
    return row
