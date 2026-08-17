from datetime import UTC, datetime
from decimal import Decimal, localcontext

import pytest

from qap.execution import (
    CostModel,
    DirectExecutionReason,
    FillSide,
    execute_direct_rebalance_leg,
)
from qap.market import MarketMetadata, VenueInstrument
from qap.portfolio import AssetId, PortfolioState

D = Decimal
BTC = AssetId("BTC")
USDT = AssetId("USDT")
AT = datetime(2024, 1, 1, 1, tzinfo=UTC)
INSTRUMENT = VenueInstrument(
    venue="fixture",
    venue_symbol="BTCUSDT",
    base=BTC,
    quote=USDT,
)


def _metadata(
    *,
    tick: str = "0.05",
    step: str = "0.1",
    minimum_quantity: str | None = "0.1",
    maximum_quantity: str | None = "100",
    minimum_notional: str | None = "10",
    maximum_notional: str | None = "100000",
) -> MarketMetadata:
    return MarketMetadata(
        instrument=INSTRUMENT,
        status="TRADING",
        price_tick=D(tick),
        minimum_price=D("0.05"),
        maximum_price=D("1000000"),
        quantity_step=D(step),
        minimum_quantity=(
            D(minimum_quantity) if minimum_quantity is not None else None
        ),
        maximum_quantity=(
            D(maximum_quantity) if maximum_quantity is not None else None
        ),
        minimum_notional=(
            D(minimum_notional) if minimum_notional is not None else None
        ),
        maximum_notional=(
            D(maximum_notional) if maximum_notional is not None else None
        ),
        minimum_notional_applies_to_market=True,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=5,
    )


def test_market_precision_rounds_quantity_down_and_price_adversely_by_side() -> None:
    from qap.execution.precision import MarketPrecision

    precision = MarketPrecision(_metadata())

    assert precision.quantity_down(D("1.234")) == D("1.2")
    assert precision.execution_price(D("3.031"), side=FillSide.BUY) == D("3.05")
    assert precision.execution_price(D("3.031"), side=FillSide.SELL) == D("3")


def test_market_precision_rejects_post_rounding_minimums_explicitly() -> None:
    from qap.execution.precision import (
        MarketPrecision,
        MarketPrecisionError,
        MarketPrecisionReason,
    )

    precision = MarketPrecision(_metadata())

    with pytest.raises(MarketPrecisionError) as quantity_error:
        precision.validate_fill(base_quantity=D("0"), execution_price=D("100"))
    assert quantity_error.value.reason is MarketPrecisionReason.BELOW_MINIMUM_QUANTITY

    with pytest.raises(MarketPrecisionError) as notional_error:
        precision.validate_fill(base_quantity=D("0.1"), execution_price=D("50"))
    assert notional_error.value.reason is MarketPrecisionReason.BELOW_MINIMUM_NOTIONAL


def test_market_precision_is_independent_of_ambient_decimal_context() -> None:
    from qap.execution.precision import MarketPrecision

    precision = MarketPrecision(_metadata(tick="0.0001", step="0.00001"))
    expected_quantity = precision.quantity_down(D("123456789.123456789"))
    expected_price = precision.execution_price(
        D("987654321.987654321"),
        side=FillSide.BUY,
    )

    with localcontext() as context:
        context.prec = 3
        context.Emax = 4
        context.Emin = -4
        actual_quantity = precision.quantity_down(D("123456789.123456789"))
        actual_price = precision.execution_price(
            D("987654321.987654321"),
            side=FillSide.BUY,
        )

    assert actual_quantity == expected_quantity
    assert actual_price == expected_price


def test_direct_execution_applies_market_precision_without_overspending() -> None:
    result = execute_direct_rebalance_leg(
        fill_id="precision:buy",
        decision_id="precision",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        quantity_deltas={BTC: D("100"), USDT: D("-100")},
        current_state=PortfolioState.from_holdings({USDT: D("100")}),
        reference_price=D("3.031"),
        cost_model=CostModel.zero(),
        market_metadata=_metadata(),
    )

    assert result.reason is None
    assert result.fill is not None
    assert result.fill.execution_price == D("3.05")
    assert result.fill.base_quantity == D("32.7")
    assert result.fill.gross_quote_notional == D("99.735")
    assert -result.fill.balance_deltas[USDT] <= D("100")


def test_direct_execution_returns_explicit_minimum_notional_no_fill() -> None:
    result = execute_direct_rebalance_leg(
        fill_id="precision:min-notional",
        decision_id="precision",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        quantity_deltas={BTC: D("1"), USDT: D("-5")},
        current_state=PortfolioState.from_holdings({USDT: D("5")}),
        reference_price=D("50"),
        cost_model=CostModel.zero(),
        market_metadata=_metadata(minimum_notional="10"),
    )

    assert result.fill is None
    assert result.reason is DirectExecutionReason.BELOW_MINIMUM_NOTIONAL
