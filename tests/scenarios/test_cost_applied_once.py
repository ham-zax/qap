import re
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.execution import CostModel, run_deterministic_replay
from qap.market import (
    BarInterval,
    MarketBar,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.policy import ScheduledTargetPolicy
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    DuplicateLedgerEventError,
    PortfolioLedger,
    PortfolioState,
)

D = Decimal
BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
INTERVAL = BarInterval("1h")
START = datetime(2024, 1, 1, tzinfo=UTC)
BTC_USDT = VenueInstrument("fixture", "BTCUSDT", BTC, USDT)
ETH_USDT = VenueInstrument("fixture", "ETHUSDT", ETH, USDT)


def _aligned():
    def series(instrument: VenueInstrument, price: float):
        return validate_bar_series(
            [
                MarketBar(
                    instrument=instrument,
                    interval=INTERVAL,
                    candle_open_time=START + index * INTERVAL.duration,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1.0,
                )
                for index in range(2)
            ]
        )

    return align_bar_series([series(BTC_USDT, 10.0), series(ETH_USDT, 2.0)])


def test_replay_applies_ten_bps_slippage_and_fee_exactly_once() -> None:
    first_decision_time = START + INTERVAL.duration
    starting = PortfolioState.from_holdings({BTC: D("10")})
    target = AllocationTarget.for_basket(
        {BTC: D("0"), USDT: D("1")},
        basket={BTC, USDT},
    )

    trace = run_deterministic_replay(
        run_id="cost-run",
        aligned=_aligned(),
        ledger=PortfolioLedger(starting),
        policy=ScheduledTargetPolicy(
            policy_id="rotate-to-usdt-v1",
            schedule={first_decision_time: target},
        ),
        execution_instrument=BTC_USDT,
        numeraire=USDT,
        cost_model=CostModel(fee_bps=D("10"), slippage_bps=D("10")),
        min_rebalance_notional=D("0"),
    )

    assert len(trace.fills) == 1
    fill = trace.fills[0]
    assert fill.reference_price == D("10")
    assert fill.execution_price == D("9.99")
    assert fill.base_quantity == D("10")
    assert fill.gross_quote_notional == D("99.9")
    assert fill.slippage_value == D("0.1")
    assert fill.fee_amount == D("0.0999")
    assert fill.balance_deltas == {BTC: D("-10"), USDT: D("99.8001")}
    assert trace.ending_state.holdings == {USDT: D("99.8001")}

    ledger = PortfolioLedger(starting)
    first_application = ledger.apply_fill(fill)
    with pytest.raises(DuplicateLedgerEventError, match=re.escape(fill.fill_id)):
        ledger.apply_fill(fill)
    assert ledger.current_state is first_application
    assert ledger.current_state.holdings == {USDT: D("99.8001")}
