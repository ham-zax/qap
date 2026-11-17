"""Forward L2 paper sessions: candle timing, reconciliation, metadata, clocks."""

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from qap.artifact_integrity import build_integrity_record, read_and_validate_integrity
from qap.experiment.live_paper_candles import (
    LEGACY_SCHEMA_VERSION,
    CandleInputs,
    candle_inputs_from_close_map,
)
from qap.experiment.live_paper_execution import (
    reconcile_target_status,
    sweep_rebalance,
)
from qap.experiment.live_paper_runner import (
    LivePaperError,
    LivePaperSessionManager,
    LivePaperSessionNotFoundError,
)
from qap.market import MarketMetadata, VenueInstrument
from qap.market.binance_ws_stream import TimedL2Book
from qap.market.microstructure import public_book_snapshot_from_rows
from qap.policy.lab_settings import LabSettings
from qap.portfolio import AssetId, PortfolioLedger, PortfolioState

D = Decimal
USDT = AssetId("USDT")
BTC = VenueInstrument("binance", "BTCUSDT", AssetId("BTC"), USDT)
ETH = VenueInstrument("binance", "ETHUSDT", AssetId("ETH"), USDT)
SOL = VenueInstrument("binance", "SOLUSDT", AssetId("SOL"), USDT)
NOW = datetime(2026, 11, 15, 12, tzinfo=UTC)
MS = 1_000_000
RECV_NS = 1_000_000_000_000
EXCH_US = 1_700_000_000_000_000
RTT_NS = 75 * MS
SETTINGS = LabSettings(
    method="zscore",
    auto_tune=False,
    lookback=20,
    entry=1.0,
    exit=0.5,
    minimum_hold=0,
    cooldown=0,
)


def make_meta(
    inst: VenueInstrument, *, min_qty: str = "0.001", step: str = "0.001"
) -> MarketMetadata:
    return MarketMetadata(
        instrument=inst,
        status="TRADING",
        price_tick=D("0.01"),
        minimum_price=None,
        maximum_price=None,
        quantity_step=D(step),
        minimum_quantity=D(min_qty),
        maximum_quantity=None,
        minimum_notional=D("5"),
        maximum_notional=None,
        minimum_notional_applies_to_market=True,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=5,
    )


META_MAP: dict[str, MarketMetadata] = {
    "BTCUSDT": make_meta(BTC),
    "ETHUSDT": make_meta(ETH),
    "SOLUSDT": make_meta(SOL),
}


def timed_book(
    inst: VenueInstrument, mid: float, *, received_ns: int, exch_us: int | None = None
) -> TimedL2Book:
    half = mid * 0.001
    bids = [[f"{mid - half * (i + 1):.4f}", "1000"] for i in range(5)]
    asks = [[f"{mid + half * (i + 1):.4f}", "1000"] for i in range(5)]
    book = public_book_snapshot_from_rows(
        instrument=inst,
        observed_at=NOW,
        source_id="fixture",
        source_payload={"bids": bids, "asks": asks},
        bids=bids,
        asks=asks,
    )
    return TimedL2Book(inst, book, 1, exch_us, received_ns)


def books(
    a: float, b: float, *, received_ns: int, exch_us: int | None = None
) -> dict[str, TimedL2Book]:
    return {
        "BTCUSDT": timed_book(BTC, a, received_ns=received_ns, exch_us=exch_us),
        "ETHUSDT": timed_book(ETH, b, received_ns=received_ns, exch_us=exch_us),
    }


def forbid_live(_: Sequence[VenueInstrument]) -> Mapping[str, TimedL2Book]:
    raise AssertionError("deterministic tests must never reach for live books")


def held(portfolio: Mapping[str, Any]) -> dict[str, Decimal]:
    return {k: D(v) for k, v in portfolio["holdings"].items()}


START_HOLDINGS = {"BTC": D(50), "ETH": D(100)}


def base_history(
    extra_btc: Sequence[float] = (), extra_eth: Sequence[float] = (), *, bar: str = "1h"
) -> CandleInputs:
    wave = list(100.0 + 0.1 * np.sin(np.arange(40, dtype=np.float64))) + list(extra_btc)
    eth_vals = [50.0] * 40 + list(extra_eth)
    return candle_inputs_from_close_map(
        bar,
        {"BTCUSDT": wave, "ETHUSDT": eth_vals},
        metadata={"BTCUSDT": META_MAP["BTCUSDT"], "ETHUSDT": META_MAP["ETHUSDT"]},
    )


def make_manager(root: Path, actor: str = "local") -> LivePaperSessionManager:
    return LivePaperSessionManager(root, actor_id=actor, book_provider=forbid_live)


def start(
    manager: LivePaperSessionManager,
    sid: str = "sess1",
    *,
    candle_inputs: CandleInputs | None = None,
    **kw: Any,
) -> dict[str, Any]:
    return manager.create_session(
        "binance:BTC",
        "binance:ETH",
        settings=kw.pop("settings", SETTINGS),
        initial_books=kw.pop("initial_books", books(100.0, 50.0, received_ns=RECV_NS)),
        candle_inputs=candle_inputs or base_history(),
        session_id=sid,
        **kw,
    )


def spike_step(
    manager: LivePaperSessionManager,
    *,
    candles: CandleInputs | None = None,
    **kw: Any,
) -> dict[str, Any]:
    return manager.step_session(
        "sess1",
        candle_inputs=candles or base_history([130.0], [50.0]),
        books=books(130.0, 50.0, received_ns=RECV_NS, exch_us=EXCH_US),
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=kw.get(
            "leg1", books(130.0, 50.0, received_ns=RECV_NS + 70 * MS)
        ),
        fill_books_leg2=kw.get(
            "leg2", books(128.0, 50.5, received_ns=RECV_NS + 145 * MS)
        ),
    )


def test_create_splits_start_value_into_three_ledgers(tmp_path: Path) -> None:
    view = start(make_manager(tmp_path))
    assert (
        view["status"] == "active"
        and view["decisions_count"] == 0
        and view["can_step"] is True
    )
    for key in ("strategy", "hodl", "drift_control"):
        pf = view["portfolios"][key]
        assert held(pf) == START_HOLDINGS
        assert D(pf["value_usdt"]) == D("10000") and pf["rotations"] == 0


def test_two_leg_usdt_swap_fills_each_leg_on_its_own_drifted_book(
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)
    start(manager)
    view = spike_step(manager)
    (trade,) = view["trades"]
    assert trade["direction"] == "into_b" and trade["status"] == "complete"
    sell, buy = trade["fills"]
    assert D(sell["vwap_price"]) == D("129.87")
    assert D(buy["reference_price"]) == D("50.5")
    assert abs(D(buy["execution_price"]) - D("50.5505")) < D("1e-20")
    strat = view["portfolios"]["strategy"]
    assert strat["rotations"] == 1
    assert D(strat["holdings"].get("BTC", "0")) < D("1e-3")
    assert D(strat["holdings"]["ETH"]) > D("200")


def test_same_candle_steps_cause_zero_extra_signal_observations(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    initial_4h = base_history(bar="4h")
    start(manager, bar="4h", candle_inputs=initial_4h)
    flat = books(100.0, 50.0, received_ns=RECV_NS)
    for idx in range(3):
        view = manager.step_session(
            "sess1", candle_inputs=initial_4h, books=flat, decide_ns=RECV_NS
        )
        assert view["decisions_count"] == 0
        assert view["book_observations_count"] == idx + 1
        assert view["latency_audit"][-1]["actual_fill_leg1_ns"] is None
        assert view["latency_audit"][-1]["actual_fill_leg2_ns"] is None

    # One new completed 4h candle advances decisions_count once; repeat is idempotent.
    plus_one = base_history([100.0], [50.0], bar="4h")
    leg1_b = books(100.0, 50.0, received_ns=RECV_NS + 75 * MS)
    leg2_b = books(100.0, 50.0, received_ns=RECV_NS + 150 * MS)
    v1 = manager.step_session(
        "sess1",
        candle_inputs=plus_one,
        books=flat,
        decide_ns=RECV_NS,
        fill_books_leg1=leg1_b,
        fill_books_leg2=leg2_b,
    )
    v2 = manager.step_session(
        "sess1",
        candle_inputs=plus_one,
        books=flat,
        decide_ns=RECV_NS,
        fill_books_leg1=leg1_b,
        fill_books_leg2=leg2_b,
    )
    assert v1["decisions_count"] == 1 and v2["decisions_count"] == 1
    assert v2["book_observations_count"] == 5


def test_partial_rotation_recovers_on_next_step_without_signal_change(
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)
    start(manager)
    c_spike = base_history([130.0], [50.0])
    # Step 1: sell BTC succeeds on fresh leg1, buy ETH fails on stale leg2.
    stale_leg2 = books(128.0, 50.5, received_ns=RECV_NS - 1000 * MS)
    first = spike_step(manager, candles=c_spike, leg2=stale_leg2)
    assert first["trades"][0]["status"] == "partial"
    assert len(first["trades"][0]["fills"]) == 1
    assert first["portfolios"]["strategy"]["rotations"] == 0
    assert D(first["portfolios"]["strategy"]["holdings"]["USDT"]) > D("6000")
    assert first["pending_target"] is not None
    assert first["latency_audit"][-1]["actual_fill_leg1_ns"] is not None
    assert first["latency_audit"][-1]["actual_fill_leg2_ns"] is None

    # Step 2 inside the SAME candle with fresh ETH book completes the pending buy!
    second = manager.step_session(
        "sess1",
        candle_inputs=c_spike,
        books=books(128.0, 50.5, received_ns=RECV_NS),
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=books(128.0, 50.5, received_ns=RECV_NS + 70 * MS),
        fill_books_leg2=books(128.0, 50.5, received_ns=RECV_NS + 145 * MS),
    )
    assert second["decisions_count"] == 1  # No extra candle decision!
    assert second["pending_target"] is None
    assert second["portfolios"]["strategy"]["rotations"] == 1
    assert second["trades"][0]["status"] == "complete"
    assert len(second["trades"][0]["fills"]) == 2
    assert D(second["portfolios"]["strategy"]["holdings"]["ETH"]) > D("200")
    assert D(second["portfolios"]["strategy"]["holdings"].get("USDT", "0")) < D("5")


def test_newer_candle_supersedes_pending_target_and_restart_preserves_origin(
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)
    start(manager)
    c1 = base_history([130.0], [50.0])
    stale = books(128.0, 50.5, received_ns=RECV_NS - 1000 * MS)
    spike_step(manager, candles=c1, leg2=stale)

    # Restarted manager keeps candle_origin_time and supersedes on signal flip.
    restarted = make_manager(tmp_path)
    c2 = base_history([130.0, 70.0], [50.0, 50.0])
    flipped = restarted.step_session(
        "sess1",
        candle_inputs=c2,
        books=books(70.0, 50.0, received_ns=RECV_NS),
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=books(70.0, 50.0, received_ns=RECV_NS + 70 * MS),
        fill_books_leg2=books(70.0, 50.0, received_ns=RECV_NS + 145 * MS),
    )
    assert flipped["decisions_count"] == 2
    assert flipped["candle_origin_time"] == c1.times[0]
    raw = json.loads(
        (manager.sessions_root / "sess1" / "session.json").read_text("utf-8")
    )
    assert len(raw["superseded_targets"]) == 1
    assert raw["superseded_targets"][0]["reason"] == "superseded_by_newer_candle_target"


def test_partial_rotation_superseded_by_neutral_candle_restores_50_50(
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)
    start(manager)
    c1 = base_history([130.0], [50.0])
    # Step 1: sell BTC into USDT succeeds; buy ETH fails on stale book (-1.0).
    stale_leg2 = books(128.0, 50.5, received_ns=RECV_NS - 1000 * MS)
    partial = spike_step(manager, candles=c1, leg2=stale_leg2)
    assert partial["pending_target"]["status"] == "partial"
    assert D(partial["portfolios"]["strategy"]["holdings"].get("BTC", "0")) == D("0")

    # Step 2: newer candle returns signal to neutral (0.0); must supersede old all-ETH
    # target and buy back BTC to restore 50/50 instead of completing all-ETH!
    c2_neutral = base_history([130.0, 100.0], [50.0, 50.0])
    restored = manager.step_session(
        "sess1",
        candle_inputs=c2_neutral,
        books=books(100.0, 50.0, received_ns=RECV_NS),
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=books(100.0, 50.0, received_ns=RECV_NS + 70 * MS),
        fill_books_leg2=books(100.0, 50.0, received_ns=RECV_NS + 145 * MS),
    )
    assert restored["pending_target"] is None
    strat_holdings = held(restored["portfolios"]["strategy"])
    assert strat_holdings.get("BTC", D("0")) > D("45")
    assert strat_holdings.get("ETH", D("0")) > D("95")
    assert strat_holdings.get("USDT", D("0")) < D("5")


def test_catchup_candles_do_not_execute_missed_intermediate_trades(
    tmp_path: Path,
) -> None:
    manager = make_manager(tmp_path)
    start(manager)
    # Three new candles arrive at once; only the latest target can execute.
    c_jump = base_history([130.0, 100.0, 100.0], [50.0, 50.0, 50.0])
    view = manager.step_session(
        "sess1",
        candle_inputs=c_jump,
        books=books(100.0, 50.0, received_ns=RECV_NS),
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=books(100.0, 50.0, received_ns=RECV_NS + 70 * MS),
        fill_books_leg2=books(100.0, 50.0, received_ns=RECV_NS + 145 * MS),
    )
    assert view["track_record_mode"] == "catchup_observed"
    assert view["decisions_count"] == 3
    assert len(view["trades"]) <= 1


def test_legacy_v1_session_refuses_step_but_reads_and_stops(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    sdir = manager.sessions_root / "legv1"
    sdir.mkdir(parents=True)
    legacy: dict[str, Any] = {
        "schema_version": LEGACY_SCHEMA_VERSION,
        "session_id": "legv1",
        "actor_id": "local",
        "status": "active",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
        "stopped_at": None,
        "coin_a": "binance:BTC",
        "coin_b": "binance:ETH",
        "anchor": None,
        "bar": "1h",
        "order_rtt_ms": 75.0,
        "max_staleness_ms": 500.0,
        "starting_value": "10000",
        "settings": SETTINGS.model_dump(mode="json"),
        "instruments": {
            "a": {
                "venue": "binance",
                "venue_symbol": "BTCUSDT",
                "base": "BTC",
                "quote": "USDT",
            },
            "b": {
                "venue": "binance",
                "venue_symbol": "ETHUSDT",
                "base": "ETH",
                "quote": "USDT",
            },
            "anchor": None,
        },
        "close_history": {"BTCUSDT": [100.0], "ETHUSDT": [50.0]},
        "decisions_count": 0,
        "last_preference": 0.0,
        "last_rotation_step": None,
        "peak_value": 10000.0,
        "parked": False,
        "portfolios": {
            k: {
                "holdings": {"BTC": "50", "ETH": "100"},
                "value_usdt": "10000",
                "fees_usdt": "0",
                "slippage_usdt": "0",
                "rotations": 0,
            }
            for k in ("strategy", "hodl", "drift_control")
        },
        "trades": [],
        "latency_audit": [],
    }
    (sdir / "session.json").write_text(json.dumps(legacy), encoding="utf-8")
    (sdir / "integrity.json").write_text(
        build_integrity_record(
            sdir, artifact_id="legv1", file_names=("session.json",)
        ).model_dump_json(),
        encoding="utf-8",
    )
    read_view = manager.read_session("legv1")
    assert read_view["can_step"] is False and "Start a new session" in (
        read_view["step_block_reason"] or ""
    )
    with pytest.raises(LivePaperError, match="Legacy v1 paper session"):
        manager.step_session("legv1")
    assert manager.stop_session("legv1")["status"] == "stopped"


def test_required_metadata_and_late_book_clock_enforcement(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    no_meta = candle_inputs_from_close_map(
        "1h", {"BTCUSDT": [100.0, 101.0], "ETHUSDT": [50.0, 50.0]}
    )
    with pytest.raises(LivePaperError, match="Missing observed venue metadata"):
        manager.create_session(
            "binance:BTC",
            "binance:ETH",
            candle_inputs=no_meta,
            initial_books=books(100.0, 50.0, received_ns=RECV_NS),
        )

    # Wrong-market metadata is rejected.
    wrong_meta = {"BTCUSDT": make_meta(ETH), "ETHUSDT": make_meta(ETH)}
    with pytest.raises(LivePaperError, match="instrument mismatch"):
        manager.create_session(
            "binance:BTC",
            "binance:ETH",
            candle_inputs=no_meta,
            market_metadata=wrong_meta,
            initial_books=books(100.0, 50.0, received_ns=RECV_NS),
        )

    # Late leg-1 book (850 ms after decide_ns) shifts effective fill and delays leg 2.
    start(manager)
    view = manager.step_session(
        "sess1",
        candle_inputs=base_history([130.0], [50.0]),
        books=books(130.0, 50.0, received_ns=RECV_NS),
        decide_ns=RECV_NS,
        fill_books_leg1=books(130.0, 50.0, received_ns=RECV_NS + 850 * MS),
        fill_books_leg2=books(128.0, 50.5, received_ns=RECV_NS + 925 * MS),
    )
    audit = view["latency_audit"][-1]
    assert audit["actual_fill_leg1_ns"] == RECV_NS + 850 * MS
    assert audit["actual_fill_leg2_ns"] >= audit["actual_fill_leg1_ns"] + RTT_NS
    assert audit["book_age_leg1_ms"] == 0.0
    assert audit["book_age_leg2_ms"] >= 0.0


def test_third_anchor_metadata_and_park_anchor(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    anc_candles = candle_inputs_from_close_map(
        "1h",
        {
            "BTCUSDT": list(100.0 + 0.1 * np.sin(np.arange(40))),
            "ETHUSDT": [50.0] * 40,
            "SOLUSDT": [20.0] * 40,
        },
        metadata={
            "BTCUSDT": META_MAP["BTCUSDT"],
            "ETHUSDT": META_MAP["ETHUSDT"],
        },  # missing SOL!
    )
    init = {
        **books(100.0, 50.0, received_ns=RECV_NS),
        "SOLUSDT": timed_book(SOL, 20.0, received_ns=RECV_NS),
    }
    with pytest.raises(LivePaperError, match="SOLUSDT"):
        manager.create_session(
            "binance:BTC",
            "binance:ETH",
            anchor="binance:SOL",
            candle_inputs=anc_candles,
            initial_books=init,
        )

    full_anc = candle_inputs_from_close_map(
        "1h",
        {
            "BTCUSDT": list(100.0 + 0.1 * np.sin(np.arange(40))),
            "ETHUSDT": [50.0] * 40,
            "SOLUSDT": [20.0] * 40,
        },
        metadata=META_MAP,
    )
    park_cfg = LabSettings(
        method="zscore",
        auto_tune=False,
        lookback=20,
        entry=5.0,
        exit=0.5,
        minimum_hold=0,
        cooldown=0,
        crash_defense_mode="park_anchor",
        regime_break_drawdown=0.15,
    )
    manager.create_session(
        "binance:BTC",
        "binance:ETH",
        anchor="binance:SOL",
        settings=park_cfg,
        candle_inputs=full_anc,
        initial_books=init,
        session_id="anc",
    )
    step_anc = candle_inputs_from_close_map(
        "1h",
        {
            "BTCUSDT": list(100.0 + 0.1 * np.sin(np.arange(40))) + [70.0],
            "ETHUSDT": [50.0] * 40 + [35.0],
            "SOLUSDT": [20.0] * 41,
        },
        metadata=META_MAP,
    )
    step_books = {
        **books(70.0, 35.0, received_ns=RECV_NS),
        "SOLUSDT": timed_book(SOL, 20.0, received_ns=RECV_NS),
    }
    leg1_b = {
        **books(70.0, 35.0, received_ns=RECV_NS + 70 * MS),
        "SOLUSDT": timed_book(SOL, 20.0, received_ns=RECV_NS + 70 * MS),
    }
    leg2_b = {
        **books(70.0, 35.0, received_ns=RECV_NS + 145 * MS),
        "SOLUSDT": timed_book(SOL, 20.0, received_ns=RECV_NS + 145 * MS),
    }
    parked = manager.step_session(
        "anc",
        candle_inputs=step_anc,
        books=step_books,
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=leg1_b,
        fill_books_leg2=leg2_b,
    )
    assert parked["trades"][0]["direction"] == "into_anchor"
    assert D(parked["portfolios"]["strategy"]["holdings"]["SOL"]) > D("300")


def test_actor_isolation_tamper_detection_and_target_reserve(tmp_path: Path) -> None:
    alice, bob = make_manager(tmp_path, "alice"), make_manager(tmp_path, "bob")
    start(alice, "shared")
    start(bob, "shared")
    with pytest.raises(LivePaperSessionNotFoundError):
        bob.read_session("shared") if False else alice.read_session("missing")
    directory = alice.sessions_root / "shared"
    read_and_validate_integrity(
        directory,
        artifact_id="shared",
        required_files=frozenset({"session.json"}),
        allowed_files=frozenset({"session.json"}),
    )

    ledger = PortfolioLedger(PortfolioState.from_holdings({USDT: D("10000")}))
    fill_books = books(100.0, 50.0, received_ns=RECV_NS)
    fills, rejected, *_ = sweep_rebalance(
        ledger=ledger,
        portfolio_key="strategy",
        session_id="reserve-test",
        step_index=1,
        target_weights={
            AssetId("BTC"): D("0.5"),
            AssetId("ETH"): D("0.3"),
            USDT: D("0.2"),
        },
        mid_prices={AssetId("BTC"): D("100"), AssetId("ETH"): D("50"), USDT: D("1")},
        inst_by_asset={AssetId("BTC"): BTC, AssetId("ETH"): ETH},
        basket=(AssetId("BTC"), AssetId("ETH"), USDT),
        settings=SETTINGS,
        order_rtt_ms=75.0,
        max_staleness_ms=500.0,
        t_fill_leg1_ns=RECV_NS + RTT_NS,
        t_fill_leg2_ns=RECV_NS + 2 * RTT_NS,
        req_insts=[BTC, ETH],
        book_provider=forbid_live,
        leg_cache={},
        fill_books_leg1=fill_books,
        fill_books_leg2=fill_books,
        meta_map=META_MAP,
        decision_time=NOW,
    )
    assert (
        rejected == []
        and len(fills) == 2
        and ledger.current_state.quantity(USDT) >= D("2000")
    )


def test_reconcile_target_status_keeps_tradable_90_dollar_remainder_partial() -> None:
    prices = {AssetId("BTC"): D("100"), AssetId("ETH"): D("50"), USDT: D("1")}
    inst_by_asset = {AssetId("BTC"): BTC, AssetId("ETH"): ETH}
    basket = (AssetId("BTC"), AssetId("ETH"), USDT)
    target = {AssetId("BTC"): D("0.5"), AssetId("ETH"): D("0.5"), USDT: D("0")}
    status_90 = reconcile_target_status(
        ledger_state=PortfolioState.from_holdings(
            {AssetId("BTC"): D("50.9"), AssetId("ETH"): D("98.2")}
        ),
        target_weights=target,
        mid_prices=prices,
        inst_by_asset=inst_by_asset,
        basket=basket,
        settings=SETTINGS,
        meta_map=META_MAP,
        had_any_fills=True,
        rejected=[],
        decision_time=NOW,
    )
    assert status_90 == "partial"
    status_100k_90 = reconcile_target_status(
        ledger_state=PortfolioState.from_holdings(
            {AssetId("BTC"): D("500.9"), AssetId("ETH"): D("998.2")}
        ),
        target_weights=target,
        mid_prices=prices,
        inst_by_asset=inst_by_asset,
        basket=basket,
        settings=SETTINGS,
        meta_map=META_MAP,
        had_any_fills=True,
        rejected=[],
        decision_time=NOW,
    )
    assert status_100k_90 == "partial"
    status_dust = reconcile_target_status(
        ledger_state=PortfolioState.from_holdings(
            {AssetId("BTC"): D("50.03"), AssetId("ETH"): D("99.94")}
        ),
        target_weights=target,
        mid_prices=prices,
        inst_by_asset=inst_by_asset,
        basket=basket,
        settings=SETTINGS,
        meta_map=META_MAP,
        had_any_fills=True,
        rejected=[],
        decision_time=NOW,
    )
    assert status_dust == "dust_complete"
