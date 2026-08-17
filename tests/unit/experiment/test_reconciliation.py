from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.execution import CostModel, build_buy_fill, build_sell_fill
from qap.market import VenueInstrument
from qap.portfolio import AssetId, PortfolioState

D = Decimal
AT = datetime(2024, 1, 1, 1, tzinfo=UTC)
BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
BTCUSDT = VenueInstrument(venue="fixture", venue_symbol="BTCUSDT", base=BTC, quote=USDT)
ETHUSDT = VenueInstrument(venue="fixture", venue_symbol="ETHUSDT", base=ETH, quote=USDT)


def _fills():
    sell = build_sell_fill(
        fill_id="sell-btc",
        decision_id="reconcile",
        execution_timestamp=AT,
        instrument=BTCUSDT,
        base_quantity=D("0.5"),
        reference_price=D("100"),
        cost_model=CostModel.zero(),
    )
    buy = build_buy_fill(
        fill_id="buy-eth",
        decision_id="reconcile",
        execution_timestamp=AT,
        instrument=ETHUSDT,
        quote_budget=D("25"),
        reference_price=D("50"),
        cost_model=CostModel.zero(),
    )
    return sell, buy


def test_reconciliation_recomputes_each_state_from_raw_fill_deltas() -> None:
    from qap.experiment.reconciliation import reconcile_fill_sequence

    sell, buy = _fills()
    starting = PortfolioState.from_holdings({BTC: D("1")})
    expected = (
        PortfolioState.from_holdings({BTC: D("0.5"), USDT: D("50")}),
        PortfolioState.from_holdings({BTC: D("0.5"), ETH: D("0.5"), USDT: D("25")}),
    )

    report = reconcile_fill_sequence(
        starting_state=starting,
        fills=(sell, buy),
        expected_states=expected,
    )

    assert report.matches is True
    assert report.ending_state == expected[-1]
    assert len(report.steps) == 2
    assert all(step.matches for step in report.steps)
    assert all(step.differences == () for step in report.steps)


def test_reconciliation_reports_tampered_expected_balance_without_hiding_delta() -> (
    None
):
    from qap.experiment.reconciliation import reconcile_fill_sequence

    sell, buy = _fills()
    starting = PortfolioState.from_holdings({BTC: D("1")})
    expected = (
        PortfolioState.from_holdings({BTC: D("0.5"), USDT: D("50")}),
        PortfolioState.from_holdings({BTC: D("0.5"), ETH: D("0.4"), USDT: D("25")}),
    )

    report = reconcile_fill_sequence(
        starting_state=starting,
        fills=(sell, buy),
        expected_states=expected,
    )

    assert report.matches is False
    assert report.steps[0].matches is True
    assert report.steps[1].matches is False
    assert report.steps[1].differences == (report.steps[1].differences[0],)
    difference = report.steps[1].differences[0]
    assert difference.asset == ETH
    assert difference.expected == D("0.4")
    assert difference.recomputed == D("0.5")
    assert difference.delta == D("0.1")


def test_reconciliation_detects_tampered_fill_economics() -> None:
    from qap.experiment.reconciliation import reconcile_fill_sequence
    from qap.market import PriceSnapshot

    sell, buy = _fills()
    object.__setattr__(sell, "fee_amount", D("999999"))
    starting = PortfolioState.from_holdings({BTC: D("1")})
    expected = (
        PortfolioState.from_holdings({BTC: D("0.5"), USDT: D("50")}),
        PortfolioState.from_holdings({BTC: D("0.5"), ETH: D("0.5"), USDT: D("25")}),
    )
    prices = PriceSnapshot.from_prices(
        timestamp=AT,
        numeraire=USDT,
        prices={BTC: D("100"), ETH: D("50"), USDT: D("1")},
    )

    report = reconcile_fill_sequence(
        starting_state=starting,
        fills=(sell, buy),
        expected_states=expected,
        valuation_prices=prices,
    )

    assert report.matches is False
    fee_difference = next(
        item
        for item in report.economic_differences
        if item.fill_id == "sell-btc" and item.field == "fee_amount"
    )
    assert fee_difference.reported == D("999999")
    assert fee_difference.recomputed == D("0")
    assert report.reported_fee_total == D("999999")
    assert report.recomputed_fee_total == D("0")
    assert report.recomputed_turnover == D("75")
    assert report.recomputed_terminal_value == D("100")
    assert report.expected_terminal_value == D("100")


def test_reconciliation_rejects_fill_state_length_mismatch() -> None:
    from qap.experiment.reconciliation import reconcile_fill_sequence

    sell, buy = _fills()
    starting = PortfolioState.from_holdings({BTC: D("1")})

    with pytest.raises(ValueError, match="same length"):
        reconcile_fill_sequence(
            starting_state=starting,
            fills=(sell, buy),
            expected_states=(
                PortfolioState.from_holdings({BTC: D("0.5"), USDT: D("50")}),
            ),
        )
