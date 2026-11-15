"""The Lab composes real QAP fills: causal next opens, costs and inventory."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest

from qap.experiment.lab_replay import LabInputs, run_lab_replay
from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    VenueInstrument,
    validate_bar_series,
)
from qap.market.metadata import MarketMetadata
from qap.market.microstructure import public_market_metadata_snapshot_from_metadata
from qap.policy.lab_settings import LabSettings
from qap.policy.lab_signals import LabSignal, signal_path
from qap.portfolio import AssetId


def inputs(*, gap: float = 1.0, direct: bool = False) -> LabInputs:
    interval = BarInterval("1h")
    times = [
        datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=index)
        for index in range(100)
    ]
    instruments = [
        VenueInstrument("binance", f"{code}USDT", AssetId(code), AssetId("USDT"))
        for code in ("A", "B")
    ]
    series: list[ValidatedBarSeries] = []
    for instrument in instruments:
        series.append(
            validate_bar_series(
                tuple(
                    MarketBar(
                        instrument=instrument,
                        interval=interval,
                        candle_open_time=time,
                        open=gap if index == 21 else 1.0,
                        close=1.0,
                        high=max(gap, 1.0),
                        low=min(gap, 1.0),
                        volume=1_000_000.0,
                    )
                    for index, time in enumerate(times)
                )
            )
        )
    cross = None
    if direct:
        instrument = VenueInstrument("binance", "AB", AssetId("A"), AssetId("B"))
        cross = validate_bar_series(
            tuple(
                MarketBar(
                    instrument=instrument,
                    interval=interval,
                    candle_open_time=time,
                    open=1.0,
                    close=1.0,
                    high=1.0,
                    low=1.0,
                    volume=1_000_000.0,
                )
                for time in times
            )
        )
    return LabInputs(series[0], series[1], cross)


def one_signal(size: int = 100, at: int = 20) -> LabSignal:
    preference = np.zeros(size)
    preference[at:] = 1.0
    return LabSignal(preference.copy(), preference, "test", 1, -1, True)


def test_next_open_and_both_leg_costs_use_authoritative_fills() -> None:
    data = inputs(gap=1.1)
    result = run_lab_replay(data, LabSettings(minimum_hold=0, cooldown=0), one_signal())
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.decision_index == 20 and trade.fill_index == 21
    assert len(trade.fills) == 2
    assert all(fill.reference_price == Decimal("1.1") for fill in trade.fills)
    assert all(fill.fee_amount > 0 and fill.slippage_value > 0 for fill in trade.fills)
    flat = run_lab_replay(inputs(), LabSettings(), one_signal())
    assert flat.terminal_value < Decimal("10000")
    assert all(quantity >= 0 for quantity in result.ending_state.holdings.values())


def test_direct_market_uses_one_real_fill() -> None:
    result = run_lab_replay(inputs(direct=True), LabSettings(), one_signal())
    assert len(result.trades) == 1
    assert len(result.trades[0].fills) == 1
    assert result.trades[0].fills[0].venue_symbol == "AB"


@pytest.mark.parametrize(
    "minimum,maximum,expected_trades",
    [("5", None, 1), (None, "100000", 1), ("1000000", None, 0), (None, "1", 0)],
)
def test_direct_market_filters_use_an_explicit_notional_reference(
    minimum: str | None, maximum: str | None, expected_trades: int
) -> None:
    data = inputs(direct=True)
    assert data.direct is not None
    metadata = MarketMetadata(
        instrument=data.direct.instrument,
        status="TRADING",
        price_tick=Decimal("0.000001"),
        minimum_price=None,
        maximum_price=None,
        quantity_step=Decimal("0.000001"),
        minimum_quantity=None,
        maximum_quantity=None,
        minimum_notional=None if minimum is None else Decimal(minimum),
        maximum_notional=None if maximum is None else Decimal(maximum),
        minimum_notional_applies_to_market=minimum is not None,
        maximum_notional_applies_to_market=maximum is not None,
        notional_average_price_minutes=5,
    )
    snapshot = public_market_metadata_snapshot_from_metadata(
        metadata=metadata,
        observed_at=data.first.bars[0].candle_open_time,
        source_id="offline-direct-metadata",
    )
    result = run_lab_replay(
        replace(data, metadata=(snapshot,)), LabSettings(), one_signal()
    )
    assert len(result.trades) == expected_trades
    assert all(len(trade.fills) == 1 for trade in result.trades)
    assert all(quantity >= 0 for quantity in result.ending_state.holdings.values())


def test_last_bar_never_fills_and_hodl_keeps_starting_inventory() -> None:
    settings = LabSettings()
    data = inputs()
    assert run_lab_replay(data, settings, one_signal(at=99)).trades == ()
    result = run_lab_replay(data, settings, one_signal(), kind="hodl")
    assert result.terminal_value == settings.starting_value
    assert result.ending_state.quantity(AssetId("A")) == Decimal("5000")


@pytest.mark.parametrize("method", ["zscore", "trend", "lead_lag", "copula"])
def test_signals_do_not_change_when_only_future_prices_change(method: str) -> None:
    generator = np.random.default_rng(4)
    anchor = np.exp(np.cumsum(generator.normal(0, 0.01, 600)))
    a = anchor * np.exp(generator.normal(0, 0.01, 600))
    b = anchor * np.exp(generator.normal(0, 0.01, 600))
    settings = LabSettings.model_validate({"method": method, "lookback": 80})
    original = signal_path(a, b, settings, anchor)
    changed = a.copy()
    changed[400:] *= 2
    later = signal_path(changed, b, settings, anchor)
    np.testing.assert_allclose(
        original.values[:400], later.values[:400], equal_nan=True, atol=1e-8
    )
    np.testing.assert_allclose(
        original.preference[:400], later.preference[:400], equal_nan=True
    )
