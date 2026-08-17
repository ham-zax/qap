from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.execution import CostModel, build_sell_fill
from qap.market import VenueInstrument
from qap.portfolio import (
    AssetId,
    DuplicateLedgerEventError,
    ExternalInventoryFlow,
    PortfolioLedger,
    PortfolioState,
)

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


def _sell_fill(*, fill_id: str, base_quantity: str = "1"):
    return build_sell_fill(
        fill_id=fill_id,
        decision_id="decision-1",
        execution_timestamp=AT,
        instrument=INSTRUMENT,
        base_quantity=D(base_quantity),
        reference_price=D("10"),
        cost_model=CostModel.zero(),
    )


def test_ledger_applies_fill_once_and_preserves_prior_snapshot() -> None:
    starting = PortfolioState.from_holdings({BTC: D("2")})
    ledger = PortfolioLedger(starting)
    fill = _sell_fill(fill_id="fill-1")

    next_state = ledger.apply_fill(fill)

    assert starting.holdings == {BTC: D("2")}
    assert next_state is ledger.current_state
    assert next_state.holdings == {BTC: D("1"), USDT: D("10")}
    assert ledger.applied_event_ids == ("fill-1",)
    assert ledger.applied_fills == (fill,)

    with pytest.raises(DuplicateLedgerEventError, match="fill-1"):
        ledger.apply_fill(fill)

    assert ledger.current_state is next_state
    assert ledger.applied_event_ids == ("fill-1",)


def test_ledger_rejects_fill_that_would_create_negative_inventory() -> None:
    starting = PortfolioState.from_holdings({BTC: D("1")})
    ledger = PortfolioLedger(starting)
    fill = _sell_fill(fill_id="oversell", base_quantity="2")

    with pytest.raises(ValueError, match="negative balance for BTC"):
        ledger.apply_fill(fill)

    assert ledger.current_state is starting
    assert ledger.applied_event_ids == ()


def test_ledger_applies_deposit_and_withdrawal_in_event_order() -> None:
    ledger = PortfolioLedger(PortfolioState.from_holdings({BTC: D("1")}))
    deposit = ExternalInventoryFlow(
        flow_id="flow-1",
        effective_time=AT,
        asset=BTC,
        quantity_delta=D("0.5"),
    )
    withdrawal = ExternalInventoryFlow(
        flow_id="flow-2",
        effective_time=AT,
        asset=BTC,
        quantity_delta=D("-0.25"),
    )

    ledger.apply_flow(deposit)
    final_state = ledger.apply_flow(withdrawal)

    assert final_state.holdings == {BTC: D("1.25")}
    assert ledger.applied_event_ids == ("flow-1", "flow-2")
    assert ledger.applied_flows == (deposit, withdrawal)

    with pytest.raises(DuplicateLedgerEventError, match="flow-1"):
        ledger.apply_flow(deposit)

    assert ledger.current_state is final_state


def test_ledger_rejects_withdrawal_without_recording_it() -> None:
    starting = PortfolioState.from_holdings({BTC: D("1")})
    ledger = PortfolioLedger(starting)
    withdrawal = ExternalInventoryFlow(
        flow_id="too-large",
        effective_time=AT,
        asset=BTC,
        quantity_delta=D("-1.1"),
    )

    with pytest.raises(ValueError, match="negative balance for BTC"):
        ledger.apply_flow(withdrawal)

    assert ledger.current_state is starting
    assert ledger.applied_event_ids == ()


def test_ledger_rejects_external_flow_through_fill_path() -> None:
    starting = PortfolioState.from_holdings({BTC: D("1")})
    ledger = PortfolioLedger(starting)
    flow = ExternalInventoryFlow(
        flow_id="misclassified-flow",
        effective_time=AT,
        asset=BTC,
        quantity_delta=D("0.5"),
    )

    with pytest.raises(TypeError, match="fill event"):
        ledger.apply_fill(flow)

    assert ledger.current_state is starting
    assert ledger.applied_event_ids == ()
    assert ledger.applied_fills == ()
    assert ledger.applied_flows == ()
