"""Crash defense mode tests: coins_only, park_usdt, and park_anchor."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import numpy as np

from qap.experiment.lab_proof import prove_lab_strategy
from qap.experiment.lab_replay import USDT, LabInputs, run_lab_replay
from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    VenueInstrument,
    validate_bar_series,
)
from qap.policy.lab_settings import LabSettings
from qap.policy.lab_signals import LabSignal
from qap.portfolio import AssetId


def _crash_inputs(size: int = 80) -> LabInputs:
    interval = BarInterval("1h")
    times = [
        datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=index)
        for index in range(size)
    ]
    inst_a = VenueInstrument("binance", "AUSDT", AssetId("A"), AssetId("USDT"))
    inst_b = VenueInstrument("binance", "BUSDT", AssetId("B"), AssetId("USDT"))

    def make_series(inst: VenueInstrument) -> ValidatedBarSeries:
        bars: list[MarketBar] = []
        for i, t in enumerate(times):
            price = 1.0 if i < 20 else (0.78 if i < 50 else 0.78)
            bars.append(
                MarketBar(inst, interval, t, price, price, price, price, 1_000_000.0)
            )
        return validate_bar_series(tuple(bars))

    return LabInputs(make_series(inst_a), make_series(inst_b))


def test_coins_only_stays_in_ab_during_crash() -> None:
    data = _crash_inputs()
    sig = LabSignal(np.zeros(80), np.zeros(80), "test", 1, -1, True)
    settings = LabSettings(
        crash_defense_mode="coins_only",
        regime_break_drawdown=0.15,
        minimum_hold=0,
        cooldown=0,
    )
    res = run_lab_replay(data, settings, sig)
    assert res.ending_state.quantity(USDT) == Decimal(0)
    assert res.ending_state.quantity(AssetId("A")) > 0
    assert res.ending_state.quantity(AssetId("B")) > 0


def test_park_usdt_exits_on_drawdown_and_pays_fees() -> None:
    data = _crash_inputs()
    sig = LabSignal(np.zeros(80), np.zeros(80), "test", 1, -1, True)
    settings = LabSettings(
        crash_defense_mode="park_usdt",
        regime_break_drawdown=0.15,
        minimum_hold=0,
        cooldown=0,
    )
    res = run_lab_replay(data, settings, sig)
    assert any(t.direction == "into_usdt" for t in res.trades)
    assert res.ending_state.quantity(USDT) > Decimal("7000")
    assert res.ending_state.quantity(AssetId("A")) == Decimal(0)
    assert res.ending_state.quantity(AssetId("B")) == Decimal(0)
    usdt_trade = next(t for t in res.trades if t.direction == "into_usdt")
    assert Decimal(usdt_trade.fees_usdt) > 0


def test_park_anchor_without_anchor_returns_execution_data_missing() -> None:
    data = _crash_inputs(size=120)
    settings = LabSettings(crash_defense_mode="park_anchor")
    proof = prove_lab_strategy(
        data,
        settings,
        trial_count=1,
        identity_confirmed=True,
        execution_ready=True,
    )
    assert proof.call["status"] == "execution_data_missing"
    assert "Anchor" in proof.call["headline"]
