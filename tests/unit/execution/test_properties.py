from datetime import UTC, datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from qap.execution import CostModel, build_buy_fill, build_sell_fill
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

_positive_amounts = st.integers(min_value=1, max_value=10**12)
_admissible_bps = st.integers(min_value=0, max_value=9_999)


@given(
    quote_budget=_positive_amounts,
    reference_price=_positive_amounts,
    fee_bps=_admissible_bps,
    slippage_bps=_admissible_bps,
)
def test_buy_fill_never_debits_more_than_its_owned_quote_budget(
    quote_budget: int,
    reference_price: int,
    fee_bps: int,
    slippage_bps: int,
) -> None:
    budget = D(quote_budget)
    fill = build_buy_fill(
        fill_id="property-buy",
        decision_id="property-decision",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        quote_budget=budget,
        reference_price=D(reference_price),
        cost_model=CostModel(
            fee_bps=D(fee_bps),
            slippage_bps=D(slippage_bps),
        ),
    )

    total_debit = -fill.balance_deltas[USDT]
    assert D("0") < total_debit <= budget
    assert total_debit == fill.gross_quote_notional + fill.fee_amount
    assert fill.balance_deltas[BTC] == fill.base_quantity > D("0")


@given(
    base_quantity=_positive_amounts,
    reference_price=_positive_amounts,
    fee_pair=st.tuples(_admissible_bps, _admissible_bps),
    slippage_pair=st.tuples(_admissible_bps, _admissible_bps),
)
def test_higher_fixed_path_costs_cannot_create_more_sell_proceeds(
    base_quantity: int,
    reference_price: int,
    fee_pair: tuple[int, int],
    slippage_pair: tuple[int, int],
) -> None:
    lower_fee, higher_fee = sorted(fee_pair)
    lower_slippage, higher_slippage = sorted(slippage_pair)

    lower_cost_fill = build_sell_fill(
        fill_id="property-sell-lower",
        decision_id="property-decision",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        base_quantity=D(base_quantity),
        reference_price=D(reference_price),
        cost_model=CostModel(
            fee_bps=D(lower_fee),
            slippage_bps=D(lower_slippage),
        ),
    )
    higher_cost_fill = build_sell_fill(
        fill_id="property-sell-higher",
        decision_id="property-decision",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        base_quantity=D(base_quantity),
        reference_price=D(reference_price),
        cost_model=CostModel(
            fee_bps=D(higher_fee),
            slippage_bps=D(higher_slippage),
        ),
    )

    assert higher_cost_fill.execution_price <= lower_cost_fill.execution_price
    assert higher_cost_fill.balance_deltas[USDT] <= lower_cost_fill.balance_deltas[USDT]
    assert higher_cost_fill.balance_deltas[BTC] == lower_cost_fill.balance_deltas[BTC]
