"""Five explicit arithmetic oracles; exact QAP inventory and bt accounting checks."""

from datetime import UTC, datetime
from decimal import Decimal

from qap.execution import (
    CostModel,
    ExecutionQuantization,
    execute_direct_rebalance_leg,
    execute_routed_conversion,
    plan_execution_route,
)
from qap.market import VenueInstrument
from qap.portfolio import AssetId, PortfolioState
from scripts.engine_parity_support.bt_reference import initialize, sell_owned
from scripts.engine_parity_support.contracts import PairInputs, Settings

D = Decimal
A, B, USD = (AssetId(key) for key in ("AAA", "BBB", "USDT"))
NOW = datetime(2026, 1, 1, tzinfo=UTC)
AB = VenueInstrument(venue="fixture", venue_symbol="AAABBB", base=A, quote=B)
AU = VenueInstrument(venue="fixture", venue_symbol="AAAUSDT", base=A, quote=USD)
BU = VenueInstrument(venue="fixture", venue_symbol="BBBUSDT", base=B, quote=USD)


def direct(
    holdings: dict[AssetId, Decimal],
    deltas: dict[AssetId, Decimal],
    price: str,
    fee_bps: str = "0",
    step: str | None = None,
) -> tuple[dict[str, str], int]:
    state = PortfolioState.from_holdings(holdings)
    result = execute_direct_rebalance_leg(
        fill_id="hand-fill",
        decision_id="hand-decision",
        execution_timestamp=NOW,
        instrument=AB,
        quantity_deltas=deltas,
        current_state=state,
        reference_price=D(price),
        cost_model=CostModel(fee_bps=D(fee_bps), slippage_bps=D(0)),
        quantization=ExecutionQuantization(base_step=None if step is None else D(step)),
    )
    end = (
        state if result.fill is None else state.apply_deltas(result.fill.balance_deltas)
    )
    return {A.key: str(end.quantity(A)), B.key: str(end.quantity(B))}, int(
        result.fill is not None
    )


def verify_hand_cases() -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    for name, holdings, deltas, price, fees, step, expected, legs in (
        (
            "single_swap",
            {A: D(2)},
            {A: D(-2), B: D(6)},
            "3",
            "0",
            None,
            {A.key: "0", B.key: "6"},
            1,
        ),
        (
            "fee_rounding",
            {B: D(100)},
            {A: D(1), B: D(-100)},
            "3",
            "10",
            "0.01",
            {A.key: "33.3", B.key: "0.0001"},
            1,
        ),
        (
            "partial_rotation",
            {A: D(2)},
            {A: D("-0.5"), B: D("1.5")},
            "3",
            "0",
            None,
            {A.key: "1.5", B.key: "1.5"},
            1,
        ),
        (
            "insufficient_inventory",
            {B: D(7)},
            {A: D(-2), B: D(6)},
            "3",
            "0",
            None,
            {A.key: "0", B.key: "7"},
            0,
        ),
    ):
        actual, count = direct(holdings, deltas, price, fees, step)
        # Numeric Decimal equality: exponent normalization is not a difference.
        passed = (
            all(D(actual[key]) == D(value) for key, value in expected.items())
            and count == legs
        )
        cases.append(
            {
                "case": name,
                "expected": expected,
                "actual": actual,
                "legs": count,
                "passed": passed,
            }
        )
    route = plan_execution_route(
        source=A,
        destination=B,
        instruments=(AU, BU),
        declared_assets={A, B, USD},
        bridge=USD,
    )
    result = execute_routed_conversion(
        route=route,
        fill_id_prefix="hand-bridge",
        decision_id="hand-bridge",
        execution_timestamp=NOW,
        source_quantity=D(2),
        current_state=PortfolioState.from_holdings({A: D(2)}),
        reference_prices={AU: D(11), BU: D(3)},
        market_notional_reference_prices={},
        market_metadata={},
        cost_model=CostModel(fee_bps=D(1000), slippage_bps=D(0)),
        require_market_metadata=False,
    )
    actual = {
        asset.key: str(result.ending_state.quantity(asset)) for asset in (A, B, USD)
    }
    expected = {A.key: "0", B.key: "6", USD.key: "0"}
    passed = (
        all(D(actual[key]) == D(value) for key, value in expected.items())
        and len(result.fills) == 2
    )
    cases.append(
        {
            "case": "two_leg_route",
            "expected": expected,
            "actual": actual,
            "legs": len(result.fills),
            "passed": passed,
        }
    )
    return cases


def verify_bt_arithmetic() -> None:
    """bt owns transaction accounting; known decimals agree at floating precision.

    This checks the same five hand cases without importing QAP fills or ending
    inventory into bt. Exact inventory expectations above are Decimal oracles.
    """
    inputs = PairInputs(("AAA", "BBB"), (NOW,), ((3.0, 1.0),), ((3.0, 1.0),))
    engine = initialize(
        inputs, Settings(starting_value=12, fee_rate=0, slippage_rate=0)
    )
    # Seed was A=2,B=6; sell the starting B holding and withdraw that cash.
    engine.children["BBB"].transact(-6)
    engine.adjust(-6)
    engine.children["AAA"].transact(-2, price=3)
    assert abs(engine.capital - 6) < 1e-10
    assert engine.children["AAA"].position == 0
    # Buy-budget rounding oracle: gross99.9 + fee0.0999, residual0.0001.
    engine.adjust(94)
    engine.set_commissions(lambda q, p: abs(q) * p * 0.001)
    engine.children["AAA"].transact(33.3, price=3)
    assert abs(engine.capital - 0.0001) < 1e-10
    # A separately seeded two-leg conversion: 2*11*.9 / (3*1.1) = 6.
    bridge = initialize(
        inputs, Settings(starting_value=12, fee_rate=0, slippage_rate=0)
    )
    bridge.children["BBB"].transact(-6)
    bridge.adjust(-6)
    bridge.set_commissions(lambda q, p: abs(q) * p * 0.1)
    bridge.children["AAA"].transact(-2, price=11)
    bridge.children["BBB"].transact(6, price=3)
    assert abs(bridge.capital) < 1e-10
    assert bridge.children["BBB"].position == 6
    partial = initialize(
        inputs, Settings(starting_value=12, fee_rate=0, slippage_rate=0)
    )
    partial.children["BBB"].transact(-6)
    partial.adjust(-6)
    partial.children["AAA"].transact(-0.5, price=3)
    assert partial.children["AAA"].position == 1.5
    assert partial.capital == 1.5
    insufficient = initialize(
        inputs,
        Settings(starting_value=12, fee_rate=0, slippage_rate=0),
    )
    insufficient.children["AAA"].transact(-2)
    insufficient.children["BBB"].transact(-6)
    insufficient.adjust(-5)
    # Refuse an unavailable sale through the same reference inventory gate.
    assert sell_owned(insufficient.children["AAA"], 2, 3) == 0
    assert insufficient.children["AAA"].position == 0
    assert insufficient.capital == 7
