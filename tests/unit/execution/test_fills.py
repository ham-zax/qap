from collections.abc import MutableMapping
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import cast

import pytest

from qap.execution import (
    CostModel,
    ExecutionQuantization,
    FillSide,
    build_buy_fill,
    build_sell_fill,
)
from qap.market import VenueInstrument
from qap.portfolio import AssetId

D = Decimal
BTC = AssetId("BTC")
USDT = AssetId("USDT")
INSTRUMENT = VenueInstrument(
    venue="fixture",
    venue_symbol="BTCUSDT",
    base=BTC,
    quote=USDT,
)
AT = datetime(2024, 1, 1, 1, tzinfo=UTC)


def test_buy_reserves_quote_fee_inside_budget() -> None:
    fill = build_buy_fill(
        fill_id="run-1:decision-1:leg-0",
        decision_id="decision-1",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        quote_budget=D("101"),
        reference_price=D("10"),
        cost_model=CostModel(fee_bps=D("100"), slippage_bps=D("0")),
    )

    assert fill.side is FillSide.BUY
    assert fill.reference_price == D("10")
    assert fill.execution_price == D("10")
    assert fill.base_quantity == D("10")
    assert fill.gross_quote_notional == D("100")
    assert fill.fee_amount == D("1")
    assert fill.fee_asset == USDT
    assert fill.slippage_value == D("0")
    assert dict(fill.balance_deltas) == {BTC: D("10"), USDT: D("-101")}


def test_buy_rounds_sizing_down_instead_of_rejecting_a_valid_tiny_budget() -> None:
    fill = build_buy_fill(
        fill_id="run-1:rounding-regression:leg-0",
        decision_id="rounding-regression",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        quote_budget=D("1"),
        reference_price=D("1"),
        cost_model=CostModel(fee_bps=D("1"), slippage_bps=D("0")),
    )

    total_quote_debit = -fill.balance_deltas[USDT]
    assert total_quote_debit <= D("1")
    assert total_quote_debit == fill.gross_quote_notional + fill.fee_amount


def test_sell_applies_adverse_slippage_then_quote_fee_once() -> None:
    fill = build_sell_fill(
        fill_id="run-1:decision-2:leg-0",
        decision_id="decision-2",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        base_quantity=D("10"),
        reference_price=D("10"),
        cost_model=CostModel(fee_bps=D("100"), slippage_bps=D("100")),
    )

    assert fill.side is FillSide.SELL
    assert fill.execution_price == D("9.9")
    assert fill.base_quantity == D("10")
    assert fill.gross_quote_notional == D("99")
    assert fill.fee_amount == D("0.99")
    assert fill.slippage_value == D("1")
    assert dict(fill.balance_deltas) == {BTC: D("-10"), USDT: D("98.01")}


def test_buy_repeating_quotient_rounds_down_to_preserve_budget() -> None:
    fill = build_buy_fill(
        fill_id="run-1:rounding-regression:leg-0",
        decision_id="rounding-regression",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        quote_budget=D("1"),
        reference_price=D("1"),
        cost_model=CostModel(fee_bps=D("0"), slippage_bps=D("1")),
    )

    assert fill.base_quantity > D("0")
    assert -fill.balance_deltas[USDT] <= D("1")
    assert -fill.balance_deltas[USDT] == (fill.gross_quote_notional + fill.fee_amount)


def test_buy_quantization_rounds_down_and_never_overspends() -> None:
    fill = build_buy_fill(
        fill_id="run-1:decision-3:leg-0",
        decision_id="decision-3",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        quote_budget=D("100"),
        reference_price=D("3"),
        cost_model=CostModel.zero(),
        quantization=ExecutionQuantization(base_step=D("0.1")),
    )

    assert fill.base_quantity == D("33.3")
    assert fill.gross_quote_notional == D("99.9")
    assert fill.fee_amount == D("0")
    assert fill.balance_deltas[USDT] == D("-99.9")
    assert -fill.balance_deltas[USDT] <= D("100")


def test_fill_is_immutable_and_balance_deltas_are_read_only() -> None:
    fill = build_sell_fill(
        fill_id="run-1:decision-4:leg-0",
        decision_id="decision-4",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        base_quantity=D("1"),
        reference_price=D("10"),
        cost_model=CostModel.zero(),
    )

    mutable = cast(MutableMapping[AssetId, Decimal], fill.balance_deltas)
    with pytest.raises(TypeError):
        mutable[BTC] = D("0")


def test_buy_fill_is_independent_of_ambient_decimal_context() -> None:
    def build():
        return build_buy_fill(
            fill_id="run-1:ambient-context:leg-0",
            decision_id="ambient-context",
            execution_timestamp=AT,
            instrument=INSTRUMENT,
            quote_budget=D("1"),
            reference_price=D("1"),
            cost_model=CostModel(fee_bps=D("3"), slippage_bps=D("1")),
        )

    expected = build()

    with localcontext() as context:
        context.prec = 2
        context.Emax = 2
        context.Emin = -2
        actual = build()

    assert actual == expected
    assert -actual.balance_deltas[USDT] <= D("1")
