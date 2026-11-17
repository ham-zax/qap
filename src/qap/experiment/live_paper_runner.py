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
from pathlib import Path
from typing import Any, cast

from qap.artifact_integrity import build_integrity_record, read_and_validate_integrity
from qap.experiment.live_paper_candles import (
    CandleInputs,
    LivePaperCandleError,
    candle_inputs_from_close_map,
    plan_candle_ingestion,
)
from qap.experiment.live_paper_execution import (
    USDT,
    BookProvider,
    canonical_json,
    capture_live_books,
    default_instrument,
    holdings_dict,
    instrument_from_dict,
    ledger_from_holdings,
    mid_decimal,
)
from qap.experiment.live_paper_reconcile import (
    advance_candle_signals,
    reconcile_portfolio_step,
    weights_to_str,
)
from qap.experiment.live_paper_state import (
    is_legacy_v1,
    latency_record,
    metadata_from_record,
    metadata_to_record,
    needs_drift_rebalance,
    new_session_state,
    public_session_view,
    required_instruments,
    session_list_row,
)
from qap.file_lock import FileLock
from qap.market import MarketMetadata, VenueInstrument
from qap.market.binance_ws_stream import TimedL2Book
from qap.policy.lab_settings import LabSettings
from qap.portfolio import AssetId, value_holdings_at_prices
from qap.portfolio._decimal import divide, exact_multiply

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
        anchor_mode: str = "pinned",
        bar: str = "1h",
        settings: LabSettings | None = None,
        order_rtt_ms: float = 75.0,
        max_staleness_ms: float = 500.0,
        initial_books: Mapping[str, TimedL2Book] | None = None,
        instruments: Mapping[str, VenueInstrument] | None = None,
        candle_inputs: CandleInputs | None = None,
        market_metadata: Mapping[str, MarketMetadata] | None = None,
        require_metadata: bool = True,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        if coin_a == coin_b:
            raise LivePaperError("coin_a and coin_b must be distinct.")
        if order_rtt_ms <= 0.0 or max_staleness_ms <= 0.0:
            raise LivePaperError("order_rtt_ms and max_staleness_ms must be positive.")
        if candle_inputs is None:
            raise LivePaperError(
                "Timestamped completed candle inputs are required to start "
                "a paper session."
            )
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
        try:
            plan = plan_candle_ingestion([], {}, candle_inputs, req_insts)
        except LivePaperCandleError as exc:
            raise LivePaperError(str(exc)) from exc

        combined_meta: dict[str, MarketMetadata] = dict(candle_inputs.metadata)
        if market_metadata:
            combined_meta.update(market_metadata)
        if require_metadata:
            missing_meta = [
                inst.venue_symbol
                for inst in req_insts
                if inst.venue_symbol not in combined_meta
            ]
            if missing_meta:
                raise LivePaperError(
                    f"Missing observed venue metadata for {', '.join(missing_meta)}."
                )
        for inst in req_insts:
            meta = combined_meta.get(inst.venue_symbol)
            if meta is not None and meta.instrument != inst:
                raise LivePaperError(
                    f"Market metadata instrument mismatch for {inst.venue_symbol}."
                )

        meta_records = {
            sym: metadata_to_record(
                meta,
                source_id=candle_inputs.metadata_provenance.get(sym, {}).get(
                    "source_id", "observed"
                ),
                observed_at=candle_inputs.metadata_provenance.get(sym, {}).get(
                    "observed_at", ""
                ),
                sha256=candle_inputs.metadata_provenance.get(sym, {}).get(
                    "payload_sha256", ""
                ),
            )
            for sym, meta in combined_meta.items()
        }

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
        sid = session_id or uuid.uuid4().hex[:16]
        self._validate_session_id(sid)
        state = new_session_state(
            session_id=sid,
            actor_id=self.actor_id,
            now_iso=datetime.now(UTC).isoformat(),
            coin_a=coin_a,
            coin_b=coin_b,
            anchor=anchor,
            anchor_mode=anchor_mode,
            bar=bar,
            order_rtt_ms=order_rtt_ms,
            max_staleness_ms=max_staleness_ms,
            cfg=cfg,
            inst_a=inst_a,
            inst_b=inst_b,
            inst_anc=inst_anc,
            candle_times=plan.new_times,
            candle_closes=plan.new_closes,
            market_metadata=meta_records,
            init_holdings={inst_a.base.key: str(qty_a), inst_b.base.key: str(qty_b)},
        )
        with self._lock(sid):
            if self._session_dir(sid).exists():
                raise LivePaperError(f"Paper session {sid!r} already exists.")
            self._save_state(sid, state)
        return public_session_view(state)

    @staticmethod
    def _resolve_step_meta(
        state: Mapping[str, Any],
        req_insts: list[VenueInstrument],
        candle_inputs: CandleInputs,
        override_meta: Mapping[str, MarketMetadata] | None,
        require_metadata: bool,
    ) -> dict[str, MarketMetadata]:
        meta_map: dict[str, MarketMetadata] = {
            sym: metadata_from_record(rec)
            for sym, rec in state.get("market_metadata", {}).items()
        }
        meta_map.update(candle_inputs.metadata)
        if override_meta:
            meta_map.update(override_meta)
        for inst in req_insts:
            meta = meta_map.get(inst.venue_symbol)
            if meta is None and require_metadata:
                raise LivePaperError(
                    f"Missing observed venue metadata for {inst.venue_symbol}."
                )
            if meta is not None and meta.instrument != inst:
                raise LivePaperError(
                    f"Market metadata instrument mismatch for {inst.venue_symbol}."
                )
        return meta_map

    def step_session(
        self,
        session_id: str,
        *,
        candle_inputs: CandleInputs | None = None,
        books: Mapping[str, TimedL2Book] | None = None,
        decide_ns: int | None = None,
        fill_books_leg1: Mapping[str, TimedL2Book] | None = None,
        fill_books_leg2: Mapping[str, TimedL2Book] | None = None,
        market_metadata: Mapping[str, MarketMetadata] | None = None,
        require_metadata: bool = True,
    ) -> dict[str, Any]:
        with self._lock(session_id):
            state = self._load_state(session_id)
            if is_legacy_v1(state):
                raise LivePaperError(
                    "Legacy v1 paper session uses untimed closes and cannot step. "
                    "Start a new session."
                )
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
            candle_times = cast(list[int], state["candle_times"])
            candle_closes = cast(dict[str, list[float]], state["candle_closes"])
            step_candles = candle_inputs or candle_inputs_from_close_map(
                str(state["bar"]), candle_closes, times=candle_times
            )
            try:
                ingest = plan_candle_ingestion(
                    candle_times, candle_closes, step_candles, req_insts
                )
            except LivePaperCandleError as exc:
                raise LivePaperError(str(exc)) from exc
            meta_map = self._resolve_step_meta(
                state, req_insts, step_candles, market_metadata, require_metadata
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
            req_leg1_ns = t_decide_ns + rtt_ns
            req_leg2_ns = t_decide_ns + 2 * rtt_ns
            decision_time = decision_books[inst_a.venue_symbol].book.observed_at
            attempt_idx = int(state.get("step_attempts_count", 0)) + 1

            strat_ledger = ledger_from_holdings(
                state["portfolios"]["strategy"]["holdings"]
            )
            hodl_ledger = ledger_from_holdings(state["portfolios"]["hodl"]["holdings"])
            drift_ledger = ledger_from_holdings(
                state["portfolios"]["drift_control"]["holdings"]
            )
            strat_val = value_holdings_at_prices(strat_ledger.current_state, mid_prices)

            pref_val, obs_type = advance_candle_signals(
                state=state,
                ingest=ingest,
                req_insts=req_insts,
                inst_a=inst_a,
                inst_b=inst_b,
                inst_anc=inst_anc,
                has_third=has_third,
                cfg=cfg,
                strat_val=strat_val,
                attempt_idx=attempt_idx,
            )

            applied_fill_ids = set(cast(list[str], state.get("applied_fill_ids", [])))
            leg_cache: dict[str, Mapping[str, TimedL2Book]] = {}
            step_idx = int(state["decisions_count"])
            (
                strat_fills,
                strat_rejected,
                exec_status,
                age1,
                age2,
                act1,
                act2,
                eff_req1,
                eff_req2,
            ) = reconcile_portfolio_step(
                state=state,
                pending_key="pending_target",
                portfolio_key="strategy",
                ledger=strat_ledger,
                inst_a=inst_a,
                inst_b=inst_b,
                inst_anc=inst_anc,
                inst_by_asset=inst_by_asset,
                basket=basket,
                cfg=cfg,
                mid_prices=mid_prices,
                meta_map=meta_map,
                decision_time=decision_time,
                attempt_idx=attempt_idx,
                step_idx=step_idx,
                t_decide_ns=t_decide_ns,
                req_leg1_ns=req_leg1_ns,
                req_leg2_ns=req_leg2_ns,
                rtt_ms=rtt_ms,
                max_stale=max_stale,
                req_insts=req_insts,
                book_provider=self._book_provider,
                leg_cache=leg_cache,
                fill_books_leg1=fill_books_leg1,
                fill_books_leg2=fill_books_leg2,
                applied_fill_ids=applied_fill_ids,
            )

            if state.get("pending_drift_target") is None and needs_drift_rebalance(
                drift_ledger.current_state, mid_prices, inst_a.base, cfg.initial_weight
            ):
                state["pending_drift_target"] = {
                    "target_id": f"{session_id}-drift-{attempt_idx}",
                    "target_weights": weights_to_str(
                        {
                            inst_a.base: cfg.initial_weight,
                            inst_b.base: _ONE - cfg.initial_weight,
                            USDT: _ZERO,
                        }
                    ),
                    "reason": "drift_rebalance",
                    "status": "pending",
                    "fills": [],
                    "attempts": 0,
                }
            if state.get("pending_drift_target") is not None:
                reconcile_portfolio_step(
                    state=state,
                    pending_key="pending_drift_target",
                    portfolio_key="drift_control",
                    ledger=drift_ledger,
                    inst_a=inst_a,
                    inst_b=inst_b,
                    inst_anc=inst_anc,
                    inst_by_asset=inst_by_asset,
                    basket=basket,
                    cfg=cfg,
                    mid_prices=mid_prices,
                    meta_map=meta_map,
                    decision_time=decision_time,
                    attempt_idx=attempt_idx,
                    step_idx=step_idx,
                    t_decide_ns=t_decide_ns,
                    req_leg1_ns=req_leg1_ns,
                    req_leg2_ns=req_leg2_ns,
                    rtt_ms=rtt_ms,
                    max_stale=max_stale,
                    req_insts=req_insts,
                    book_provider=self._book_provider,
                    leg_cache=leg_cache,
                    fill_books_leg1=fill_books_leg1,
                    fill_books_leg2=fill_books_leg2,
                    applied_fill_ids=applied_fill_ids,
                )

            state["applied_fill_ids"] = sorted(applied_fill_ids)
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

            state["step_attempts_count"] = attempt_idx
            state["book_observations_count"] = attempt_idx
            state["updated_at"] = datetime.now(UTC).isoformat()
            state["latency_audit"].append(
                latency_record(
                    step_index=step_idx,
                    attempt_index=attempt_idx,
                    candle_time=candle_times[-1],
                    observation_type=obs_type,
                    execution_status=exec_status,
                    t_exch_us=max(known_exch) if known_exch else None,
                    t_recv_ns=t_recv_ns,
                    t_decide_ns=t_decide_ns,
                    requested_fill_leg1_ns=eff_req1,
                    requested_fill_leg2_ns=eff_req2,
                    actual_fill_leg1_ns=act1,
                    actual_fill_leg2_ns=act2,
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

    def read_session_raw_anchor(
        self, session_id: str
    ) -> tuple[str, str, str | None, str, str]:
        with self._lock(session_id):
            state = self._load_state(session_id)
            if is_legacy_v1(state):
                raise LivePaperError(
                    "Legacy v1 paper session uses untimed closes and cannot step. "
                    "Start a new session."
                )
            default_mode = "none" if state.get("anchor") is None else "pinned"
            return (
                str(state["coin_a"]),
                str(state["coin_b"]),
                None if state.get("anchor") is None else str(state["anchor"]),
                str(state.get("anchor_mode", default_mode)),
                str(state["bar"]),
            )

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
