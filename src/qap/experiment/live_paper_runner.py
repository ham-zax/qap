"""Actor-scoped forward Binance WebSocket L2 paper trading session manager."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import Any, cast

import numpy as np

from qap.artifact_integrity import build_integrity_record, read_and_validate_integrity
from qap.experiment.live_paper_execution import (
    USDT,
    BookProvider,
    canonical_json,
    capture_live_books,
    decide_strategy_target,
    default_instrument,
    holdings_dict,
    instrument_from_dict,
    ledger_from_holdings,
    mid_decimal,
    public_session_view,
    record_portfolio_fills,
    sweep_rebalance,
)
from qap.experiment.live_paper_state import (
    append_mid_closes,
    latency_record,
    needs_drift_rebalance,
    new_session_state,
    required_instruments,
    session_list_row,
    strategy_trade_direction,
    trade_record,
)
from qap.file_lock import FileLock
from qap.market import MarketMetadata, VenueInstrument
from qap.market.binance_ws_stream import TimedL2Book
from qap.policy.lab_settings import LabSettings
from qap.policy.lab_signals import signal_path
from qap.portfolio import AssetId, value_holdings_at_prices
from qap.portfolio._decimal import divide, exact_multiply
from qap.relationship.pair_measurements import Floats

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_ZERO = Decimal("0")
_ONE = Decimal("1")


class LivePaperError(RuntimeError):
    """Raised when live paper session state or inputs are invalid."""


class LivePaperSessionNotFoundError(LivePaperError):
    """Raised when a requested paper session does not exist."""


class LivePaperSessionManager:
    """Manage actor-scoped forward L2 paper sessions with integrity guarantees."""

    def __init__(
        self,
        run_root: Path,
        *,
        actor_id: str = "local",
        book_provider: BookProvider | None = None,
    ) -> None:
        if not _ID_RE.match(actor_id):
            raise LivePaperError(
                "Actor ID must be 1-64 alphanumeric, underscore, or hyphen characters."
            )
        self.actor_id = actor_id
        base = run_root / "product" / "pair-rotation-lab"
        self.root = base if actor_id == "local" else base / "actors" / actor_id
        self.sessions_root = self.root / "paper-sessions"
        self._book_provider = book_provider or capture_live_books

    @staticmethod
    def _validate_session_id(session_id: str) -> None:
        if not _ID_RE.match(session_id):
            raise LivePaperError("Paper session identifier is invalid.")

    def _session_dir(self, session_id: str) -> Path:
        self._validate_session_id(session_id)
        return self.sessions_root / session_id

    def _lock(self, session_id: str) -> FileLock:
        self._validate_session_id(session_id)
        return FileLock(self.sessions_root / f".{session_id}.lock")

    def _save_state(self, session_id: str, state: dict[str, Any]) -> None:
        directory = self._session_dir(session_id)
        directory.mkdir(parents=True, exist_ok=True)
        tmp_session = directory / ".session.json.tmp"
        tmp_session.write_bytes(canonical_json(state))
        os.replace(tmp_session, directory / "session.json")
        integrity = build_integrity_record(
            directory, artifact_id=session_id, file_names=("session.json",)
        )
        tmp_integrity = directory / ".integrity.json.tmp"
        tmp_integrity.write_text(integrity.model_dump_json(), encoding="utf-8")
        os.replace(tmp_integrity, directory / "integrity.json")

    def _load_state(self, session_id: str) -> dict[str, Any]:
        directory = self._session_dir(session_id)
        if not directory.is_dir():
            raise LivePaperSessionNotFoundError(
                f"Paper session {session_id!r} not found."
            )
        try:
            read_and_validate_integrity(
                directory,
                artifact_id=session_id,
                required_files=frozenset({"session.json"}),
                allowed_files=frozenset({"session.json"}),
            )
            raw: object = json.loads(
                (directory / "session.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            raise LivePaperError(
                "Paper session integrity check failed. Files were preserved."
            ) from exc
        if not isinstance(raw, dict):
            raise LivePaperError("Paper session state is malformed.")
        state = cast(dict[str, Any], raw)
        if state.get("session_id") != session_id:
            raise LivePaperError("Paper session state is malformed.")
        return state

    def create_session(
        self,
        coin_a: str,
        coin_b: str,
        *,
        anchor: str | None = None,
        bar: str = "1h",
        settings: LabSettings | None = None,
        order_rtt_ms: float = 75.0,
        max_staleness_ms: float = 500.0,
        initial_books: Mapping[str, TimedL2Book] | None = None,
        instruments: Mapping[str, VenueInstrument] | None = None,
        historical_closes: Mapping[str, Floats] | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        if coin_a == coin_b:
            raise LivePaperError("coin_a and coin_b must be distinct.")
        if order_rtt_ms <= 0.0 or max_staleness_ms <= 0.0:
            raise LivePaperError("order_rtt_ms and max_staleness_ms must be positive.")
        cfg = settings or LabSettings()
        inst_map: Mapping[str, VenueInstrument] = instruments or {}
        inst_a = inst_map.get("a") or default_instrument(coin_a)
        inst_b = inst_map.get("b") or default_instrument(coin_b)
        inst_anc = (
            None
            if anchor is None
            else (inst_map.get("anchor") or default_instrument(anchor))
        )
        req_insts = required_instruments(inst_a, inst_b, inst_anc)
        books = initial_books or self._book_provider(req_insts)
        for inst in req_insts:
            if inst.venue_symbol not in books:
                raise LivePaperError(
                    f"Missing initial L2 book for {inst.venue_symbol}."
                )
        mid_a = mid_decimal(books[inst_a.venue_symbol])
        mid_b = mid_decimal(books[inst_b.venue_symbol])
        qty_a = divide(exact_multiply(cfg.starting_value, cfg.initial_weight), mid_a)
        qty_b = divide(
            exact_multiply(cfg.starting_value, _ONE - cfg.initial_weight), mid_b
        )
        close_history = {
            inst.venue_symbol: (
                [float(x) for x in historical_closes[inst.venue_symbol][-1999:]]
                if historical_closes is not None
                and inst.venue_symbol in historical_closes
                else [books[inst.venue_symbol].book.mid_price]
            )
            for inst in req_insts
        }
        sid = session_id or uuid.uuid4().hex[:16]
        self._validate_session_id(sid)
        state = new_session_state(
            session_id=sid,
            actor_id=self.actor_id,
            now_iso=datetime.now(UTC).isoformat(),
            coin_a=coin_a,
            coin_b=coin_b,
            anchor=anchor,
            bar=bar,
            order_rtt_ms=order_rtt_ms,
            max_staleness_ms=max_staleness_ms,
            cfg=cfg,
            inst_a=inst_a,
            inst_b=inst_b,
            inst_anc=inst_anc,
            close_history=close_history,
            init_holdings={inst_a.base.key: str(qty_a), inst_b.base.key: str(qty_b)},
        )
        with self._lock(sid):
            if self._session_dir(sid).exists():
                raise LivePaperError(f"Paper session {sid!r} already exists.")
            self._save_state(sid, state)
        return public_session_view(state)

    def step_session(
        self,
        session_id: str,
        *,
        books: Mapping[str, TimedL2Book] | None = None,
        historical_closes: Mapping[str, Floats] | None = None,
        decide_ns: int | None = None,
        fill_books_leg1: Mapping[str, TimedL2Book] | None = None,
        fill_books_leg2: Mapping[str, TimedL2Book] | None = None,
        market_metadata: Mapping[str, MarketMetadata] | None = None,
    ) -> dict[str, Any]:
        with self._lock(session_id):
            state = self._load_state(session_id)
            if state["status"] != "active":
                raise LivePaperError("Paper session is already stopped.")
            cfg = LabSettings.model_validate(state["settings"])
            inst_a = instrument_from_dict(state["instruments"]["a"])
            inst_b = instrument_from_dict(state["instruments"]["b"])
            raw_anc = state["instruments"].get("anchor")
            inst_anc = None if raw_anc is None else instrument_from_dict(raw_anc)
            req_insts = required_instruments(inst_a, inst_b, inst_anc)
            inst_by_asset = {inst.base: inst for inst in req_insts}
            has_third = inst_anc is not None and inst_anc.base not in (
                inst_a.base,
                inst_b.base,
                USDT,
            )
            basket: tuple[AssetId, ...] = (
                (inst_a.base, inst_b.base, inst_anc.base, USDT)
                if has_third and inst_anc is not None
                else (inst_a.base, inst_b.base, USDT)
            )
            decision_books = books or self._book_provider(req_insts)
            for inst in req_insts:
                if inst.venue_symbol not in decision_books:
                    raise LivePaperError(
                        f"Missing L2 book snapshot for {inst.venue_symbol}."
                    )
            mid_prices: dict[AssetId, Decimal] = {USDT: _ONE}
            for inst in req_insts:
                mid_prices[inst.base] = mid_decimal(decision_books[inst.venue_symbol])

            close_hist = cast(dict[str, list[float]], state["close_history"])
            append_mid_closes(close_hist, req_insts, mid_prices, historical_closes)
            sig = signal_path(
                np.asarray(close_hist[inst_a.venue_symbol], dtype=np.float64),
                np.asarray(close_hist[inst_b.venue_symbol], dtype=np.float64),
                cfg,
                None
                if inst_anc is None
                else np.asarray(close_hist[inst_anc.venue_symbol], dtype=np.float64),
            )
            t_recv_ns = max(
                decision_books[i.venue_symbol].received_ns for i in req_insts
            )
            t_decide_ns = (
                decide_ns if decide_ns is not None else max(time.time_ns(), t_recv_ns)
            )
            if t_decide_ns < t_recv_ns:
                raise LivePaperError("decide_ns cannot precede book receipt timestamp.")
            exch = [decision_books[i.venue_symbol].exchange_time_us for i in req_insts]
            known_exch = [t for t in exch if t is not None]
            rtt_ms = float(state["order_rtt_ms"])
            max_stale = float(state["max_staleness_ms"])
            rtt_ns = int(rtt_ms * 1_000_000)
            t_fill_leg1_ns = t_decide_ns + rtt_ns
            t_fill_leg2_ns = t_decide_ns + 2 * rtt_ns
            decision_time = decision_books[inst_a.venue_symbol].book.observed_at
            step_idx = int(state["decisions_count"]) + 1

            strat_ledger = ledger_from_holdings(
                state["portfolios"]["strategy"]["holdings"]
            )
            hodl_ledger = ledger_from_holdings(state["portfolios"]["hodl"]["holdings"])
            drift_ledger = ledger_from_holdings(
                state["portfolios"]["drift_control"]["holdings"]
            )
            strat_val = value_holdings_at_prices(strat_ledger.current_state, mid_prices)
            peak_val = max(float(state["peak_value"]), float(strat_val))
            pref_val = (
                float(sig.preference[-1])
                if sig.available and np.isfinite(sig.preference[-1])
                else None
            )
            target_weights, next_pref, parked, peak_val = decide_strategy_target(
                cfg=cfg,
                inst_a=inst_a,
                inst_b=inst_b,
                inst_anc=inst_anc,
                has_third_anc=has_third,
                strat_val=float(strat_val),
                peak_value=peak_val,
                parked=bool(state["parked"]),
                last_pref=float(state["last_preference"]),
                last_rot=state.get("last_rotation_step"),
                step_index=step_idx,
                pref_val=pref_val,
            )

            leg_cache: dict[str, Mapping[str, TimedL2Book]] = {}
            sweep = partial(
                sweep_rebalance,
                session_id=session_id,
                step_index=step_idx,
                mid_prices=mid_prices,
                inst_by_asset=inst_by_asset,
                basket=basket,
                settings=cfg,
                order_rtt_ms=rtt_ms,
                max_staleness_ms=max_stale,
                t_fill_leg1_ns=t_fill_leg1_ns,
                t_fill_leg2_ns=t_fill_leg2_ns,
                req_insts=req_insts,
                book_provider=self._book_provider,
                leg_cache=leg_cache,
                fill_books_leg1=fill_books_leg1,
                fill_books_leg2=fill_books_leg2,
                meta_map=dict(market_metadata or {}),
                decision_time=decision_time,
            )
            strat_fills: list[dict[str, Any]] = []
            strat_rejected: list[str] = []
            age1 = age2 = None
            qty_a_before = strat_ledger.current_state.quantity(inst_a.base)
            next_parked = bool(state["parked"])
            next_peak_val = max(float(state["peak_value"]), float(strat_val))
            if target_weights is not None:
                strat_fills, strat_rejected, age1, age2 = sweep(
                    ledger=strat_ledger,
                    portfolio_key="strategy",
                    target_weights=target_weights,
                )
                if strat_fills:
                    state["last_preference"], state["last_rotation_step"] = (
                        next_pref,
                        step_idx,
                    )
                    next_parked = parked
                    next_peak_val = peak_val
                    record_portfolio_fills(state["portfolios"]["strategy"], strat_fills)
                    state["trades"].append(
                        trade_record(
                            step_index=step_idx,
                            decision_time=decision_time,
                            direction=strategy_trade_direction(
                                strat_ledger.current_state,
                                mid_prices,
                                inst_a.base,
                                qty_a_before,
                            ),
                            fills=strat_fills,
                            rejected=strat_rejected,
                        )
                    )

            if needs_drift_rebalance(
                drift_ledger.current_state, mid_prices, inst_a.base, cfg.initial_weight
            ):
                drift_fills, _, _, _ = sweep(
                    ledger=drift_ledger,
                    portfolio_key="drift",
                    target_weights={
                        inst_a.base: cfg.initial_weight,
                        inst_b.base: _ONE - cfg.initial_weight,
                        USDT: _ZERO,
                    },
                )
                if drift_fills:
                    record_portfolio_fills(
                        state["portfolios"]["drift_control"], drift_fills
                    )

            mark_prices = dict(mid_prices)
            latest_fill_books = (
                leg_cache.get("leg2")
                or fill_books_leg2
                or leg_cache.get("leg1")
                or fill_books_leg1
            )
            if latest_fill_books:
                for inst in req_insts:
                    if inst.venue_symbol in latest_fill_books:
                        mark_prices[inst.base] = mid_decimal(
                            latest_fill_books[inst.venue_symbol]
                        )
            for key, ledger in (
                ("strategy", strat_ledger),
                ("hodl", hodl_ledger),
                ("drift_control", drift_ledger),
            ):
                portfolio = state["portfolios"][key]
                portfolio["holdings"] = holdings_dict(ledger.current_state)
                portfolio["value_usdt"] = str(
                    value_holdings_at_prices(ledger.current_state, mark_prices)
                )

            state["decisions_count"] = step_idx
            state["peak_value"], state["parked"] = next_peak_val, next_parked
            state["updated_at"] = datetime.now(UTC).isoformat()
            state["latency_audit"].append(
                latency_record(
                    step_index=step_idx,
                    t_exch_us=max(known_exch) if known_exch else None,
                    t_recv_ns=t_recv_ns,
                    t_decide_ns=t_decide_ns,
                    t_fill_leg1_ns=t_fill_leg1_ns,
                    t_fill_leg2_ns=t_fill_leg2_ns,
                    order_rtt_ms=rtt_ms,
                    age_leg1_ms=age1,
                    age_leg2_ms=age2,
                    preference=pref_val,
                    fills=strat_fills,
                    rejected=strat_rejected,
                )
            )
            self._save_state(session_id, state)
            return public_session_view(state)

    def read_session(self, session_id: str) -> dict[str, Any]:
        with self._lock(session_id):
            return public_session_view(self._load_state(session_id))

    def stop_session(self, session_id: str) -> dict[str, Any]:
        with self._lock(session_id):
            state = self._load_state(session_id)
            if state["status"] != "stopped":
                now = datetime.now(UTC).isoformat()
                state["status"], state["stopped_at"], state["updated_at"] = (
                    "stopped",
                    now,
                    now,
                )
                self._save_state(session_id, state)
            return public_session_view(state)

    def list_sessions(
        self, *, limit: int = 25, offset: int = 0
    ) -> list[dict[str, Any]]:
        if not self.sessions_root.is_dir():
            return []
        dirs = sorted(
            (
                p
                for p in self.sessions_root.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            ),
            key=lambda p: p.stat().st_mtime_ns,
            reverse=True,
        )
        return [
            session_list_row(public_session_view(self._load_state(path.name)))
            for path in dirs[offset : offset + limit]
        ]


__all__ = [
    "LivePaperError",
    "LivePaperSessionManager",
    "LivePaperSessionNotFoundError",
]
