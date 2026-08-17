from decimal import Decimal, localcontext

import pytest

from qap.execution import CostModel

D = Decimal


def test_cost_model_exposes_explicit_rates_and_adverse_prices() -> None:
    model = CostModel(fee_bps=D("10"), slippage_bps=D("25"))

    assert model.fee_rate == D("0.001")
    assert model.slippage_rate == D("0.0025")
    assert model.buy_execution_price(D("100")) == D("100.25")
    assert model.sell_execution_price(D("100")) == D("99.75")


def test_zero_cost_model_preserves_reference_price() -> None:
    model = CostModel.zero()

    assert model.fee_rate == D("0")
    assert model.slippage_rate == D("0")
    assert model.buy_execution_price(D("12.5")) == D("12.5")
    assert model.sell_execution_price(D("12.5")) == D("12.5")


@pytest.mark.parametrize(
    ("fee_bps", "slippage_bps", "message"),
    [
        (D("-1"), D("0"), "fee_bps"),
        (D("0"), D("-1"), "slippage_bps"),
        (D("0"), D("10000"), "below 10000"),
        (D("NaN"), D("0"), "fee_bps"),
    ],
)
def test_cost_model_rejects_invalid_basis_points(
    fee_bps: Decimal,
    slippage_bps: Decimal,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        CostModel(fee_bps=fee_bps, slippage_bps=slippage_bps)


def test_cost_arithmetic_is_independent_of_ambient_decimal_context() -> None:
    model = CostModel(fee_bps=D("10"), slippage_bps=D("25"))

    with localcontext() as context:
        context.prec = 2
        context.Emax = 2
        context.Emin = -2
        actual = model.buy_execution_price(D("9.85e999"))

    assert actual == D("9.874625e999")
