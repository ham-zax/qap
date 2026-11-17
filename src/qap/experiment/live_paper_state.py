"""Pure state builders and projections for forward L2 paper sessions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from qap.experiment.live_paper_candles import LEGACY_SCHEMA_VERSION, SCHEMA_VERSION
from qap.market import MarketMetadata, VenueInstrument
from qap.policy.lab_settings import LabSettings
from qap.portfolio import AssetId, PortfolioState, value_holdings_at_prices
from qap.portfolio._decimal import divide, exact_multiply

USDT = AssetId("USDT")
DRIFT_TOLERANCE = 0.05
_ZERO = Decimal("0")
_ONE = Decimal("1")
_HALF = 0.5
_NS_PER_MS = 1_000_000.0


def instrument_to_dict(inst: VenueInstrument) -> dict[str, str]:
    return {
        "venue": inst.venue,
        "venue_symbol": inst.venue_symbol,
        "base": inst.base.key,
        "quote": inst.quote.key,
    }


def metadata_to_record(
    meta: MarketMetadata,
    *,
    source_id: str = "observed",
    observed_at: str = "",
    sha256: str = "",
) -> dict[str, Any]:
    def _opt_str(val: Decimal | None) -> str | None:
        return None if val is None else str(val)

    return {
        "instrument": instrument_to_dict(meta.instrument),
        "status": meta.status,
        "price_tick": str(meta.price_tick),
        "minimum_price": _opt_str(meta.minimum_price),
        "maximum_price": _opt_str(meta.maximum_price),
        "quantity_step": str(meta.quantity_step),
        "minimum_quantity": _opt_str(meta.minimum_quantity),
        "maximum_quantity": _opt_str(meta.maximum_quantity),
        "minimum_notional": _opt_str(meta.minimum_notional),
        "maximum_notional": _opt_str(meta.maximum_notional),
        "minimum_notional_applies_to_market": bool(
            meta.minimum_notional_applies_to_market
        ),
        "maximum_notional_applies_to_market": bool(
            meta.maximum_notional_applies_to_market
        ),
        "notional_average_price_minutes": int(meta.notional_average_price_minutes),
        "market_quantity_step": _opt_str(meta.market_quantity_step),
        "market_minimum_quantity": _opt_str(meta.market_minimum_quantity),
        "market_maximum_quantity": _opt_str(meta.market_maximum_quantity),
        "source_id": source_id,
        "observed_at": observed_at,
        "payload_sha256": sha256,
    }


def metadata_from_record(raw: Mapping[str, Any]) -> MarketMetadata:
    inst_raw = raw["instrument"]
    inst = VenueInstrument(
        venue=str(inst_raw["venue"]),
        venue_symbol=str(inst_raw["venue_symbol"]),
        base=AssetId(str(inst_raw["base"])),
        quote=AssetId(str(inst_raw["quote"])),
    )

    def _opt_dec(key: str) -> Decimal | None:
        val = raw.get(key)
        return None if val is None else Decimal(str(val))

    return MarketMetadata(
        instrument=inst,
        status=str(raw["status"]),
        price_tick=Decimal(str(raw["price_tick"])),
        minimum_price=_opt_dec("minimum_price"),
        maximum_price=_opt_dec("maximum_price"),
        quantity_step=Decimal(str(raw["quantity_step"])),
        minimum_quantity=_opt_dec("minimum_quantity"),
        maximum_quantity=_opt_dec("maximum_quantity"),
        minimum_notional=_opt_dec("minimum_notional"),
        maximum_notional=_opt_dec("maximum_notional"),
        minimum_notional_applies_to_market=bool(
            raw["minimum_notional_applies_to_market"]
        ),
        maximum_notional_applies_to_market=bool(
            raw["maximum_notional_applies_to_market"]
        ),
        notional_average_price_minutes=int(raw["notional_average_price_minutes"]),
        market_quantity_step=_opt_dec("market_quantity_step"),
        market_minimum_quantity=_opt_dec("market_minimum_quantity"),
        market_maximum_quantity=_opt_dec("market_maximum_quantity"),
    )


def required_instruments(
    inst_a: VenueInstrument,
    inst_b: VenueInstrument,
    inst_anc: VenueInstrument | None,
) -> list[VenueInstrument]:
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
    anchor_mode: str,
    bar: str,
    order_rtt_ms: float,
    max_staleness_ms: float,
    cfg: LabSettings,
    inst_a: VenueInstrument,
    inst_b: VenueInstrument,
    inst_anc: VenueInstrument | None,
    candle_times: Sequence[int],
    candle_closes: Mapping[str, Sequence[float]],
    market_metadata: Mapping[str, Mapping[str, Any]],
    init_holdings: Mapping[str, str],
) -> dict[str, Any]:
    entry = {
        "holdings": dict(init_holdings),
        "value_usdt": str(cfg.starting_value),
        "fees_usdt": "0",
        "slippage_usdt": "0",
        "rotations": 0,
    }
    times_list = [int(t) for t in candle_times]
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
        "anchor_mode": anchor_mode,
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
        "market_metadata": {sym: dict(val) for sym, val in market_metadata.items()},
        "candle_origin_time": times_list[0],
        "last_candle_time": times_list[-1],
        "candle_times": times_list,
        "candle_closes": {
            sym: [float(v) for v in vals] for sym, vals in candle_closes.items()
        },
        "decisions_count": 0,
        "book_observations_count": 0,
        "step_attempts_count": 0,
        "track_record_mode": "continuous_forward",
        "catchup_count": 0,
        "last_preference": 0.0,
        "last_rotation_step": None,
        "peak_value": float(cfg.starting_value),
        "parked": False,
        "pending_target": None,
        "pending_drift_target": None,
        "superseded_targets": [],
        "applied_fill_ids": [],
        "portfolios": {
            "strategy": dict(entry),
            "hodl": dict(entry),
            "drift_control": dict(entry),
        },
        "trades": [],
        "latency_audit": [],
    }


def strategy_trade_direction(
    state: PortfolioState,
    mids: Mapping[AssetId, Decimal],
    asset_a: AssetId,
    asset_b: AssetId,
    asset_anc: AssetId | None,
    target_weights: Mapping[AssetId, Decimal],
    qty_a_before: Decimal,
) -> str:
    if target_weights.get(USDT, _ZERO) > Decimal("0.5"):
        return "into_usdt"
    if (
        asset_anc is not None
        and asset_anc not in (asset_a, asset_b, USDT)
        and target_weights.get(asset_anc, _ZERO) > Decimal("0.5")
    ):
        return "into_anchor"
    value = value_holdings_at_prices(state, mids)
    usdt_weight = float(divide(state.quantity(USDT), value)) if value > _ZERO else 0.0
    if usdt_weight > _HALF and target_weights.get(USDT, _ZERO) > _ZERO:
        return "into_usdt"
    if target_weights.get(asset_a, _ZERO) > target_weights.get(asset_b, _ZERO):
        return "into_a"
    if target_weights.get(asset_b, _ZERO) > target_weights.get(asset_a, _ZERO):
        return "into_b"
    return "into_a" if state.quantity(asset_a) >= qty_a_before else "into_b"


def trade_record(
    *,
    step_index: int,
    decision_time: datetime,
    direction: str,
    status: str,
    fills: Sequence[Mapping[str, Any]],
    rejected: Sequence[str],
    target_id: str | None = None,
) -> dict[str, Any]:
    return {
        "target_id": target_id,
        "step_index": step_index,
        "decision_time": decision_time.isoformat(),
        "direction": direction,
        "status": status,
        "route": "two legs via USDT",
        "fees_usdt": str(sum((Decimal(f["fee"]) for f in fills), _ZERO)),
        "slippage_usdt": str(sum((Decimal(f["slippage_usdt"]) for f in fills), _ZERO)),
        "rejected_reasons": list(rejected),
        "fills": list(fills),
    }


def latency_record(
    *,
    step_index: int,
    attempt_index: int,
    candle_time: int | None,
    observation_type: str,
    execution_status: str,
    t_exch_us: int | None,
    t_recv_ns: int,
    t_decide_ns: int,
    requested_fill_leg1_ns: int,
    requested_fill_leg2_ns: int,
    actual_fill_leg1_ns: int | None,
    actual_fill_leg2_ns: int | None,
    order_rtt_ms: float,
    age_leg1_ms: float | None,
    age_leg2_ms: float | None,
    preference: float | None,
    fills: Sequence[Mapping[str, Any]],
    rejected: Sequence[str],
) -> dict[str, Any]:
    eff1 = (
        actual_fill_leg1_ns
        if actual_fill_leg1_ns is not None
        else requested_fill_leg1_ns
    )
    eff2 = (
        actual_fill_leg2_ns
        if actual_fill_leg2_ns is not None
        else requested_fill_leg2_ns
    )
    return {
        "step_index": step_index,
        "attempt_index": attempt_index,
        "candle_time": candle_time,
        "observation_type": observation_type,
        "execution_status": execution_status,
        "legacy_clock": False,
        "t_exch_us": t_exch_us,
        "t_recv_ns": t_recv_ns,
        "t_decide_ns": t_decide_ns,
        "t_fill_leg1_ns": eff1,
        "t_fill_leg2_ns": eff2,
        "requested_fill_leg1_ns": requested_fill_leg1_ns,
        "requested_fill_leg2_ns": requested_fill_leg2_ns,
        "actual_fill_leg1_ns": actual_fill_leg1_ns,
        "actual_fill_leg2_ns": actual_fill_leg2_ns,
        "order_rtt_ms": order_rtt_ms,
        "recv_to_decide_ms": (t_decide_ns - t_recv_ns) / _NS_PER_MS,
        "decide_to_fill_leg1_ms": (eff1 - t_decide_ns) / _NS_PER_MS,
        "decide_to_fill_leg2_ms": (eff2 - t_decide_ns) / _NS_PER_MS,
        "actual_decide_to_fill_leg1_ms": (
            None
            if actual_fill_leg1_ns is None
            else (actual_fill_leg1_ns - t_decide_ns) / _NS_PER_MS
        ),
        "actual_decide_to_fill_leg2_ms": (
            None
            if actual_fill_leg2_ns is None
            else (actual_fill_leg2_ns - t_decide_ns) / _NS_PER_MS
        ),
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
    value = value_holdings_at_prices(state, mids)
    actual_a = (
        float(exact_multiply(state.quantity(asset_a), mids[asset_a])) / float(value)
        if value > _ZERO
        else float(initial_weight)
    )
    return abs(actual_a - float(initial_weight)) >= DRIFT_TOLERANCE


def is_legacy_v1(state: Mapping[str, Any]) -> bool:
    return state.get("schema_version", LEGACY_SCHEMA_VERSION) == LEGACY_SCHEMA_VERSION


def simple_status_text(
    *,
    status: str,
    can_step: bool,
    decisions_count: int,
    trades_count: int,
    has_pending: bool,
    vs_hodl_pct: float,
    vs_control_pct: float,
) -> str:
    if not can_step and status == "active":
        return (
            "Legacy v1 session cannot step. Start a new session for "
            "timestamped candles."
        )
    if status == "stopped":
        return (
            f"Stopped after {decisions_count} candle decision(s) and "
            f"{trades_count} swap(s): "
            f"{vs_hodl_pct:+.2f}% vs HODL, {vs_control_pct:+.2f}% vs drift control."
        )
    if has_pending:
        return (
            f"Active ({decisions_count} candle(s)): partial target pending retry; "
            f"{vs_hodl_pct:+.2f}% vs HODL, {vs_control_pct:+.2f}% vs drift control."
        )
    if trades_count == 0:
        return (
            f"Active ({decisions_count} candle(s)); "
            "tracking 50/50 HODL with no swaps yet."
        )
    hodl_rel = "ahead of" if vs_hodl_pct >= 0 else "behind"
    ctrl_rel = "ahead of" if vs_control_pct >= 0 else "behind"
    return (
        f"Active ({trades_count} swap(s)): {hodl_rel} HODL ({vs_hodl_pct:+.2f}%), "
        f"{ctrl_rel} drift control ({vs_control_pct:+.2f}%)."
    )


def public_session_view(state: dict[str, Any]) -> dict[str, Any]:
    schema_version = str(state.get("schema_version") or LEGACY_SCHEMA_VERSION)
    is_legacy = schema_version == LEGACY_SCHEMA_VERSION
    status = str(state["status"])
    can_step = status == "active" and not is_legacy
    step_block_reason = (
        "Legacy v1 session uses untimed closes. Start a new session."
        if is_legacy
        else ("Paper session is already stopped." if status != "active" else None)
    )
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
    pending = state.get("pending_target")
    audit_out = [
        {
            **row,
            "attempt_index": row.get("attempt_index", row["step_index"]),
            "candle_time": row.get("candle_time"),
            "observation_type": row.get("observation_type", "legacy_step"),
            "execution_status": row.get("execution_status", row.get("action", "hold")),
            "legacy_clock": row.get("legacy_clock", is_legacy),
            "requested_fill_leg1_ns": row.get(
                "requested_fill_leg1_ns", row["t_fill_leg1_ns"]
            ),
            "requested_fill_leg2_ns": row.get(
                "requested_fill_leg2_ns", row["t_fill_leg2_ns"]
            ),
            "actual_fill_leg1_ns": row.get("actual_fill_leg1_ns"),
            "actual_fill_leg2_ns": row.get("actual_fill_leg2_ns"),
            "actual_decide_to_fill_leg1_ms": row.get("actual_decide_to_fill_leg1_ms"),
            "actual_decide_to_fill_leg2_ms": row.get("actual_decide_to_fill_leg2_ms"),
        }
        for row in state["latency_audit"]
    ]
    return {
        "schema_version": schema_version,
        "session_id": state["session_id"],
        "actor_id": state["actor_id"],
        "status": status,
        "can_step": can_step,
        "step_block_reason": step_block_reason,
        "created_at": state["created_at"],
        "updated_at": state["updated_at"],
        "stopped_at": state.get("stopped_at"),
        "coin_a": state["coin_a"],
        "coin_b": state["coin_b"],
        "anchor": state.get("anchor"),
        "anchor_mode": state.get("anchor_mode", "auto"),
        "bar": state["bar"],
        "order_rtt_ms": float(state["order_rtt_ms"]),
        "max_staleness_ms": float(state["max_staleness_ms"]),
        "settings": dict(state["settings"]),
        "simple_status": simple_status_text(
            status=status,
            can_step=can_step,
            decisions_count=decisions,
            trades_count=len(trades),
            has_pending=pending is not None,
            vs_hodl_pct=vs_hodl,
            vs_control_pct=vs_ctrl,
        ),
        "vs_hodl_pct": vs_hodl,
        "vs_control_pct": vs_ctrl,
        "decisions_count": decisions,
        "book_observations_count": int(state.get("book_observations_count", decisions)),
        "track_record_mode": str(
            state.get(
                "track_record_mode",
                "legacy" if is_legacy else "continuous_forward",
            )
        ),
        "candle_origin_time": state.get("candle_origin_time"),
        "last_candle_time": state.get("last_candle_time"),
        "pending_target": (
            None
            if pending is None
            else {
                "target_id": pending["target_id"],
                "status": pending["status"],
                "reason": pending["reason"],
                "target_weights": dict(pending["target_weights"]),
                "attempts": int(pending["attempts"]),
                "fills_count": len(pending.get("fills", [])),
            }
        ),
        "market_metadata_provenance": {
            sym: {
                "observed_at": meta.get("observed_at", ""),
                "source_id": meta.get("source_id", ""),
                "payload_sha256": meta.get("payload_sha256", ""),
            }
            for sym, meta in state.get("market_metadata", {}).items()
        },
        "portfolios": portfolios_out,
        "trades": [
            {
                **t,
                "status": t.get("status", "complete"),
                "target_id": t.get("target_id"),
            }
            for t in trades
        ],
        "latency_audit": audit_out,
    }


def session_list_row(view: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "session_id",
        "schema_version",
        "actor_id",
        "status",
        "can_step",
        "step_block_reason",
        "created_at",
        "updated_at",
        "coin_a",
        "coin_b",
        "anchor",
        "bar",
        "decisions_count",
        "book_observations_count",
        "track_record_mode",
        "vs_hodl_pct",
        "vs_control_pct",
        "simple_status",
    )
    row = {key: view[key] for key in keys}
    row["trades_count"] = len(view["trades"])
    return row
