from datetime import UTC, datetime
from decimal import Decimal

from qap.execution import CostModel, ReplayNoFillReason, run_deterministic_replay
from qap.market import (
    BarInterval,
    MarketBar,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.policy import ScheduledTargetPolicy
from qap.portfolio import AllocationTarget, AssetId, PortfolioLedger, PortfolioState

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
                for index in range(3)
            ]
        )

    return align_bar_series([series(BTC_USDT, 10.0), series(ETH_USDT, 2.0)])


def test_final_bar_target_is_recorded_but_cannot_fill_without_next_open() -> None:
    final_decision_time = START + 3 * INTERVAL.duration
    target = AllocationTarget.for_basket(
        {BTC: D("1"), USDT: D("0")},
        basket={BTC, USDT},
    )
    starting = PortfolioState.from_holdings({USDT: D("100")})

    trace = run_deterministic_replay(
        run_id="last-bar-run",
        aligned=_aligned(),
        ledger=PortfolioLedger(starting),
        policy=ScheduledTargetPolicy(
            policy_id="final-bar-policy-v1",
            schedule={final_decision_time: target},
        ),
        execution_instrument=BTC_USDT,
        numeraire=USDT,
        cost_model=CostModel.zero(),
        min_rebalance_notional=D("0"),
    )

    final_step = trace.steps[-1]
    assert final_step.decision_time == final_decision_time
    assert final_step.decision.target == target
    assert final_step.rebalance is not None
    assert final_step.rebalance.actionable is True
    assert final_step.execution is None
    assert final_step.fill is None
    assert final_step.no_fill_reason is ReplayNoFillReason.NO_NEXT_BAR
    assert final_step.execution_reference_time is None
    assert final_step.execution_reference_price is None
    assert final_step.state_after is final_step.state_at_decision
    assert trace.fills == ()
    assert trace.ending_state is starting
