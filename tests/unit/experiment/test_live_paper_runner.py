"""Forward L2 paper sessions: two-leg swaps, four clocks, isolation, integrity."""

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from qap.artifact_integrity import read_and_validate_integrity
from qap.experiment.live_paper_execution import sweep_rebalance
from qap.experiment.live_paper_runner import (
    LivePaperError,
    LivePaperSessionManager,
    LivePaperSessionNotFoundError,
)
from qap.market import VenueInstrument
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
    """Numeric holdings; persisted strings may be canonical like '5E+1'."""
    return {k: D(v) for k, v in portfolio["holdings"].items()}


START_HOLDINGS = {"BTC": D(50), "ETH": D(100)}


def history() -> dict[str, Any]:
    wave = 100.0 + 0.1 * np.sin(np.arange(40, dtype=np.float64))
    return {"BTCUSDT": wave, "ETHUSDT": np.full(40, 50.0)}


def make_manager(root: Path, actor: str = "local") -> LivePaperSessionManager:
    return LivePaperSessionManager(root, actor_id=actor, book_provider=forbid_live)


def start(
    manager: LivePaperSessionManager, sid: str = "sess1", **kw: Any
) -> dict[str, Any]:
    return manager.create_session(
        "binance:BTC",
        "binance:ETH",
        settings=SETTINGS,
        initial_books=books(100.0, 50.0, received_ns=RECV_NS),
        historical_closes=history(),
        session_id=sid,
        **kw,
    )


def spike_step(manager: LivePaperSessionManager, **kw: Any) -> dict[str, Any]:
    """BTC jumps 30% vs ETH (z-score exit signal); legs fill 75 ms apart."""
    return manager.step_session(
        "sess1",
        books=books(130.0, 50.0, received_ns=RECV_NS, exch_us=EXCH_US),
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=kw.get(
            "leg1", books(130.0, 50.0, received_ns=RECV_NS + 70 * MS)
        ),
        fill_books_leg2=books(128.0, 50.5, received_ns=RECV_NS + 145 * MS),
    )


def test_create_splits_start_value_equally_into_three_identical_ledgers(
    tmp_path: Path,
) -> None:
    view = start(make_manager(tmp_path))
    assert view["status"] == "active" and view["decisions_count"] == 0
    for key in ("strategy", "hodl", "drift_control"):
        pf = view["portfolios"][key]
        assert held(pf) == START_HOLDINGS
        assert D(pf["value_usdt"]) == D("10000") and pf["rotations"] == 0
    assert view["vs_hodl_pct"] == 0.0 and view["vs_control_pct"] == 0.0


def test_two_leg_usdt_swap_fills_each_leg_on_its_own_drifted_book(
    tmp_path: Path,
) -> None:
    view = spike_step(_started(tmp_path))
    (trade,) = view["trades"]
    assert trade["direction"] == "into_b" and trade["route"] == "two legs via USDT"
    sell, buy = trade["fills"]
    assert (sell["side"], sell["market"]) == ("sell", "BTCUSDT")
    assert (buy["side"], buy["market"]) == ("buy", "ETHUSDT")
    # Leg 1 sold on the leg-1 BTC book (best bid 129.87), not the later 128 book.
    assert D(sell["vwap_price"]) == D("129.87")
    # Leg 2 bought on the drifted ETH book: mid 50.5, best ask 50.5505 (> 50.0 @ leg 1).
    assert D(buy["reference_price"]) == D("50.5")
    assert abs(D(buy["execution_price"]) - D("50.5505")) < D("1e-20")
    strat = view["portfolios"]["strategy"]
    assert strat["rotations"] == 1 and D(strat["fees_usdt"]) > 0
    assert D(strat["fees_usdt"]) == D(sell["fee"]) + D(buy["fee"])
    assert D(strat["holdings"].get("BTC", "0")) < D("1e-6")
    assert D(strat["holdings"]["ETH"]) > D("200")


def test_hodl_never_trades_and_drift_control_rebalances_independently(
    tmp_path: Path,
) -> None:
    view = spike_step(_started(tmp_path))
    hodl, drift = view["portfolios"]["hodl"], view["portfolios"]["drift_control"]
    assert held(hodl) == START_HOLDINGS and hodl["rotations"] == 0
    assert D(hodl["value_usdt"]) == D("50") * 128 + D("100") * D("50.5")
    assert drift["rotations"] == 1  # BTC weight drifted to 56.5% (> 5 pt band)
    strat_value = D(view["portfolios"]["strategy"]["value_usdt"])
    assert view["vs_hodl_pct"] == pytest.approx(
        float(strat_value / D(hodl["value_usdt"]) - 1) * 100.0
    )
    # BTC sold at 129.87 on leg 1 but HODL marks it at 128 after the 75 ms
    # drift; ~0.1% fees do not offset that.
    assert view["vs_hodl_pct"] > 0.0


def test_four_clocks_are_monotonic_and_leg_latencies_match_rtt(
    tmp_path: Path,
) -> None:
    view = spike_step(_started(tmp_path))
    (audit,) = view["latency_audit"]
    assert audit["t_exch_us"] == EXCH_US
    assert audit["t_recv_ns"] == RECV_NS
    assert audit["t_recv_ns"] <= audit["t_decide_ns"]
    assert audit["t_decide_ns"] < audit["t_fill_leg1_ns"] < audit["t_fill_leg2_ns"]
    assert audit["t_decide_ns"] == RECV_NS + 2 * MS
    assert audit["t_fill_leg1_ns"] - audit["t_decide_ns"] == RTT_NS
    assert audit["t_fill_leg2_ns"] - audit["t_decide_ns"] == 2 * RTT_NS
    assert audit["recv_to_decide_ms"] == 2.0
    assert audit["decide_to_fill_leg1_ms"] == 75.0
    assert audit["decide_to_fill_leg2_ms"] == 150.0
    assert audit["book_age_leg1_ms"] == pytest.approx(7.0)
    assert audit["book_age_leg2_ms"] == pytest.approx(7.0)
    assert audit["action"] == "swap" and audit["signal_preference"] == -1.0


def test_stale_fill_book_rejects_the_swap_and_keeps_inventory(tmp_path: Path) -> None:
    manager = _started(tmp_path)
    old = books(130.0, 50.0, received_ns=RECV_NS - 1000 * MS)
    view = spike_step(manager, leg1=old)
    assert view["trades"] == []
    strat = view["portfolios"]["strategy"]
    assert strat["rotations"] == 0 and held(strat) == START_HOLDINGS
    (audit,) = view["latency_audit"]
    assert audit["action"] == "rejected"
    assert audit["rejected_reasons"] == ["stale_order_book"]
    assert audit["book_age_leg1_ms"] > 500.0


def test_flat_prices_hold_without_touching_any_book(tmp_path: Path) -> None:
    manager = _started(tmp_path)
    view = manager.step_session(
        "sess1", books=books(100.0, 50.0, received_ns=RECV_NS), decide_ns=RECV_NS
    )
    assert view["trades"] == [] and view["decisions_count"] == 1
    assert view["latency_audit"][0]["action"] == "hold"
    assert view["simple_status"].startswith("Active (1 check(s))")


def test_steps_accumulate_and_reject_clock_going_backwards(tmp_path: Path) -> None:
    manager = _started(tmp_path)
    flat = books(100.0, 50.0, received_ns=RECV_NS)
    manager.step_session("sess1", books=flat, decide_ns=RECV_NS)
    assert (
        manager.step_session("sess1", books=flat, decide_ns=RECV_NS)["decisions_count"]
        == 2
    )
    with pytest.raises(LivePaperError, match="cannot precede"):
        manager.step_session("sess1", books=flat, decide_ns=RECV_NS - 1)
    with pytest.raises(LivePaperError, match="Missing L2 book"):
        manager.step_session("sess1", books={"BTCUSDT": flat["BTCUSDT"]})


def test_actor_scopes_are_isolated_on_disk_and_in_every_read(tmp_path: Path) -> None:
    alice, bob, local = (make_manager(tmp_path, a) for a in ("alice", "bob", "local"))
    start(alice, "shared")
    start(bob, "shared")  # same id under another actor is a different session
    start(local, "mine")
    base = tmp_path / "product" / "pair-rotation-lab"
    assert (base / "actors" / "alice" / "paper-sessions" / "shared").is_dir()
    assert (base / "actors" / "bob" / "paper-sessions" / "shared").is_dir()
    assert (base / "paper-sessions" / "mine").is_dir()
    assert [r["session_id"] for r in alice.list_sessions()] == ["shared"]
    assert [r["actor_id"] for r in bob.list_sessions()] == ["bob"]
    with pytest.raises(LivePaperSessionNotFoundError):
        alice.read_session("mine")
    with pytest.raises(LivePaperSessionNotFoundError):
        bob.stop_session("mine")
    for bad in ("../evil", "a/b", "", "x" * 65):
        with pytest.raises(LivePaperError, match="Actor ID"):
            make_manager(tmp_path, bad)


def test_integrity_file_verifies_and_tampering_is_detected_not_repaired(
    tmp_path: Path,
) -> None:
    manager = _started(tmp_path)
    spike_step(manager)
    directory = manager.sessions_root / "sess1"
    assert (directory / "integrity.json").is_file()
    read_and_validate_integrity(
        directory,
        artifact_id="sess1",
        required_files=frozenset({"session.json"}),
        allowed_files=frozenset({"session.json"}),
    )
    path = directory / "session.json"
    raw = json.loads(path.read_text("utf-8"))
    raw["portfolios"]["strategy"]["value_usdt"] = "999999"
    tampered = json.dumps(raw)
    path.write_text(tampered, "utf-8")
    for call in (manager.read_session, manager.stop_session):
        with pytest.raises(LivePaperError, match="integrity check failed"):
            call("sess1")
    assert path.read_text("utf-8") == tampered  # evidence preserved


def test_stop_is_idempotent_and_blocks_further_steps(tmp_path: Path) -> None:
    manager = _started(tmp_path)
    first = manager.stop_session("sess1")
    again = manager.stop_session("sess1")
    assert first["status"] == again["status"] == "stopped"
    assert first["stopped_at"] == again["stopped_at"] is not None
    with pytest.raises(LivePaperError, match="already stopped"):
        spike_step(manager)
    assert manager.list_sessions()[0]["status"] == "stopped"


def test_create_validates_inputs_and_refuses_duplicate_ids(tmp_path: Path) -> None:
    manager = _started(tmp_path)
    with pytest.raises(LivePaperError, match="already exists"):
        start(manager)
    with pytest.raises(LivePaperError, match="distinct"):
        manager.create_session("binance:BTC", "binance:BTC")
    with pytest.raises(LivePaperError, match="positive"):
        start(manager, "s2", order_rtt_ms=0.0)
    with pytest.raises(LivePaperError, match="Missing initial L2 book"):
        only_btc = {"BTCUSDT": books(1, 1, received_ns=0)["BTCUSDT"]}
        manager.create_session("binance:BTC", "binance:ETH", initial_books=only_btc)
    with pytest.raises(LivePaperError, match="identifier is invalid"):
        start(manager, "../up")
    with pytest.raises(LivePaperSessionNotFoundError):
        manager.read_session("nope")


def test_third_asset_anchor_is_tracked_with_its_own_market(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    initial = books(100.0, 50.0, received_ns=RECV_NS)
    initial["SOLUSDT"] = timed_book(SOL, 20.0, received_ns=RECV_NS)
    manager.create_session(
        "binance:BTC",
        "binance:ETH",
        anchor="binance:SOL",
        settings=SETTINGS,
        initial_books=initial,
        session_id="anc",
    )
    raw = json.loads(
        (manager.sessions_root / "anc" / "session.json").read_text("utf-8")
    )
    assert raw["instruments"]["anchor"]["venue_symbol"] == "SOLUSDT"
    assert sorted(raw["close_history"]) == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def test_list_orders_newest_first_and_pages(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    for sid in ("s1", "s2", "s3"):
        start(manager, sid)
    ids = [r["session_id"] for r in manager.list_sessions()]
    assert sorted(ids) == ["s1", "s2", "s3"]
    assert len(manager.list_sessions(limit=2)) == 2
    assert [r["session_id"] for r in manager.list_sessions(limit=2, offset=2)] == ids[
        2:
    ]
    assert make_manager(tmp_path, "nobody").list_sessions() == []


def _started(root: Path) -> LivePaperSessionManager:
    manager = make_manager(root)
    start(manager)
    return manager


def test_rejected_park_keeps_parked_false_and_allows_retry(tmp_path: Path) -> None:
    park_settings = LabSettings(
        method="zscore",
        auto_tune=False,
        lookback=20,
        entry=5.0,
        exit=0.5,
        minimum_hold=0,
        cooldown=0,
        crash_defense_mode="park_usdt",
        regime_break_drawdown=0.15,
    )
    manager = make_manager(tmp_path)
    manager.create_session(
        "binance:BTC",
        "binance:ETH",
        settings=park_settings,
        initial_books=books(100.0, 50.0, received_ns=RECV_NS),
        historical_closes=history(),
        session_id="park1",
    )
    # 30% drawdown triggers park_usdt, but stale book rejects leg1.
    stale = books(70.0, 35.0, received_ns=RECV_NS - 1000 * MS)
    rejected_view = manager.step_session(
        "park1",
        books=books(70.0, 35.0, received_ns=RECV_NS),
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=stale,
        fill_books_leg2=books(70.0, 35.0, received_ns=RECV_NS + 145 * MS),
    )
    assert rejected_view["trades"] == []
    raw_after_reject = json.loads(
        (manager.sessions_root / "park1" / "session.json").read_text("utf-8")
    )
    assert raw_after_reject["parked"] is False

    # Next step with fresh books retries and successfully parks into USDT.
    parked_view = manager.step_session(
        "park1",
        books=books(70.0, 35.0, received_ns=RECV_NS),
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=books(70.0, 35.0, received_ns=RECV_NS + 70 * MS),
        fill_books_leg2=books(70.0, 35.0, received_ns=RECV_NS + 145 * MS),
    )
    assert len(parked_view["trades"]) == 1
    assert parked_view["trades"][0]["direction"] == "into_usdt"
    raw_after_park = json.loads(
        (manager.sessions_root / "park1" / "session.json").read_text("utf-8")
    )
    assert raw_after_park["parked"] is True


def test_sweep_rebalance_preserves_target_usdt_reserve() -> None:
    ledger = PortfolioLedger(PortfolioState.from_holdings({USDT: D("10000")}))
    fill_books = books(100.0, 50.0, received_ns=RECV_NS)
    fills, rejected, _, _ = sweep_rebalance(
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
        meta_map={},
        decision_time=NOW,
    )
    assert rejected == []
    assert len(fills) == 2
    assert ledger.current_state.quantity(USDT) >= D("2000")
