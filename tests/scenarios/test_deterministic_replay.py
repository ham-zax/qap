from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from qap.evaluation import value_portfolio
from qap.execution import CostModel, run_deterministic_replay
from qap.market import (
    BarInterval,
    CompletedBarHistory,
    MarketBar,
    PriceSnapshot,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.policy import DecisionReason, PolicyDecision, ScheduledTargetPolicy
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    ExternalInventoryFlow,
    PortfolioLedger,
    PortfolioState,
)

D = Decimal
BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
INTERVAL = BarInterval("1h")
START = datetime(2024, 1, 1, tzinfo=UTC)
BTC_USDT = VenueInstrument(
    venue="fixture",
    venue_symbol="BTCUSDT",
    base=BTC,
    quote=USDT,
)
ETH_USDT = VenueInstrument(
    venue="fixture",
    venue_symbol="ETHUSDT",
    base=ETH,
    quote=USDT,
)
BTC_ETH = VenueInstrument(
    venue="fixture",
    venue_symbol="BTCETH",
    base=BTC,
    quote=ETH,
)


def _series(
    instrument: VenueInstrument,
    *,
    opens: tuple[float, ...],
    closes: tuple[float, ...],
):
    return validate_bar_series(
        [
            MarketBar(
                instrument=instrument,
                interval=INTERVAL,
                candle_open_time=START + index * INTERVAL.duration,
                open=open_price,
                high=max(open_price, close_price),
                low=min(open_price, close_price),
                close=close_price,
                volume=1.0,
            )
            for index, (open_price, close_price) in enumerate(
                zip(opens, closes, strict=True)
            )
        ]
    )


def _aligned():
    return align_bar_series(
        [
            _series(
                BTC_USDT,
                opens=(10.0, 20.0, 30.0),
                closes=(10.0, 20.0, 30.0),
            ),
            _series(
                ETH_USDT,
                opens=(2.0, 2.0, 2.0),
                closes=(2.0, 2.0, 2.0),
            ),
        ]
    )


def test_replay_is_causal_deterministic_and_applies_due_flow_before_policy() -> None:
    first_decision_time = START + INTERVAL.duration
    target = AllocationTarget.for_basket(
        {BTC: D("0.5"), USDT: D("0.5")},
        basket={BTC, USDT},
    )
    policy = ScheduledTargetPolicy(
        policy_id="scheduled-50-50-v1",
        schedule={first_decision_time: target},
    )
    deposit = ExternalInventoryFlow(
        flow_id="deposit-1",
        effective_time=first_decision_time,
        asset=USDT,
        quantity_delta=D("100"),
    )
    future_deposit = ExternalInventoryFlow(
        flow_id="deposit-after-replay",
        effective_time=START + 4 * INTERVAL.duration,
        asset=USDT,
        quantity_delta=D("1"),
    )
    observed: list[tuple[datetime, ...]] = []

    def evidence_ids(
        histories: tuple[CompletedBarHistory, ...],
    ) -> tuple[str, ...]:
        timestamps = histories[0].timestamps
        assert all(history.timestamps == timestamps for history in histories)
        observed.append(timestamps)
        return (f"visible-bars:{len(timestamps)}",)

    def run_once():
        return run_deterministic_replay(
            run_id="deterministic-run-1",
            aligned=_aligned(),
            ledger=PortfolioLedger(PortfolioState.from_holdings({})),
            policy=policy,
            execution_instrument=BTC_USDT,
            numeraire=USDT,
            cost_model=CostModel.zero(),
            min_rebalance_notional=D("0"),
            external_flows=(future_deposit, deposit),
            evidence_builder=evidence_ids,
        )

    first = run_once()
    second = run_once()

    assert first == second
    assert observed[:3] == [
        (START,),
        (START, START + INTERVAL.duration),
        (
            START,
            START + INTERVAL.duration,
            START + 2 * INTERVAL.duration,
        ),
    ]
    assert first.applied_flows == (deposit,)
    assert first.unapplied_flows == (future_deposit,)
    assert len(first.fills) == 1

    step = first.steps[0]
    assert step.decision_time == first_decision_time
    assert step.visible_timestamps == (START,)
    assert step.applied_flows == (deposit,)
    assert step.state_before_flows.holdings == {}
    assert step.state_at_decision.holdings == {USDT: D("100")}
    assert step.decision.evidence_ids == ("visible-bars:1",)
    assert step.execution_reference_time == first_decision_time
    assert step.execution_reference_price == D("20")
    assert step.fill is not None
    assert step.fill.execution_timestamp == first_decision_time
    assert step.fill.reference_price == D("20")
    assert step.fill.execution_price == D("20")
    assert step.state_after.holdings == {BTC: D("2.5"), USDT: D("50")}
    assert step.valuation_price_snapshot.timestamp == first_decision_time
    assert step.valuation_price_snapshot.price(BTC) == D("20")
    assert value_portfolio(step.state_after, step.valuation_price_snapshot) == D("100")
    assert first.ending_state.holdings == {BTC: D("2.5"), USDT: D("50")}


@given(
    starting_quote=st.integers(min_value=1, max_value=10**9),
    decision_close=st.integers(min_value=1, max_value=10**6),
    execution_open=st.integers(min_value=1, max_value=10**6),
    base_percent=st.integers(min_value=1, max_value=99),
)
def test_zero_cost_rebalance_conserves_wealth_across_open_gaps(
    starting_quote: int,
    decision_close: int,
    execution_open: int,
    base_percent: int,
) -> None:
    decision_time = START + INTERVAL.duration
    base_weight = D(base_percent) / D("100")
    aligned = align_bar_series(
        [
            _series(
                BTC_USDT,
                opens=(float(decision_close), float(execution_open)),
                closes=(float(decision_close), float(execution_open)),
            )
        ]
    )
    target = AllocationTarget.for_basket(
        {BTC: base_weight, USDT: D("1") - base_weight},
        basket={BTC, USDT},
    )

    trace = run_deterministic_replay(
        run_id="gap-conservation-property",
        aligned=aligned,
        ledger=PortfolioLedger(PortfolioState.from_holdings({USDT: D(starting_quote)})),
        policy=ScheduledTargetPolicy(
            policy_id="gap-conservation-policy",
            schedule={decision_time: target},
        ),
        execution_instrument=BTC_USDT,
        numeraire=USDT,
        cost_model=CostModel.zero(),
        min_rebalance_notional=D("0"),
    )

    first = trace.steps[0]
    assert first.fill is not None
    assert first.valuation_price_snapshot.price(BTC) == D(execution_open)
    assert value_portfolio(
        first.state_after,
        first.valuation_price_snapshot,
    ) == D(starting_quote)


@pytest.mark.parametrize("minimum", [D("-1"), D("NaN"), D("Infinity")])
def test_replay_rejects_invalid_minimum_notional_before_policy_runs(
    minimum: Decimal,
) -> None:
    with pytest.raises(ValueError, match="min_rebalance_notional"):
        run_deterministic_replay(
            run_id="invalid-minimum",
            aligned=_aligned(),
            ledger=PortfolioLedger(PortfolioState.from_holdings({USDT: D("100")})),
            policy=ScheduledTargetPolicy(policy_id="never-runs", schedule={}),
            execution_instrument=BTC_USDT,
            numeraire=USDT,
            cost_model=CostModel.zero(),
            min_rebalance_notional=minimum,
        )


class _NoActionPolicy:
    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        del price_snapshot, applied_flows
        return PolicyDecision.no_action_decision(
            decision_id=f"structural:{as_of.isoformat()}",
            as_of=as_of,
            policy_id="structural-no-action-v1",
            current_state=current_state,
            reason=DecisionReason.INSUFFICIENT_EVIDENCE,
            evidence_ids=evidence_ids,
        )


def test_replay_accepts_the_policy_decision_contract_not_one_concrete_policy() -> None:
    starting = PortfolioState.from_holdings({USDT: D("100")})

    trace = run_deterministic_replay(
        run_id="structural-policy-run",
        aligned=_aligned(),
        ledger=PortfolioLedger(starting),
        policy=_NoActionPolicy(),
        execution_instrument=BTC_USDT,
        numeraire=USDT,
        cost_model=CostModel.zero(),
        min_rebalance_notional=D("0"),
    )

    assert trace.ending_state is starting
    assert trace.fills == ()
    assert all(step.decision.no_action for step in trace.steps)


class _MismatchedDecisionPolicy:
    def __init__(self, mismatch: str) -> None:
        self._mismatch = mismatch

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        del price_snapshot, applied_flows
        decision_time = as_of + INTERVAL.duration if self._mismatch == "time" else as_of
        decision_state = (
            PortfolioState.from_holdings({BTC: D("1")})
            if self._mismatch == "state"
            else current_state
        )
        return PolicyDecision.no_action_decision(
            decision_id=f"mismatched-{self._mismatch}",
            as_of=decision_time,
            policy_id="mismatched-policy-v1",
            current_state=decision_state,
            reason=DecisionReason.INSUFFICIENT_EVIDENCE,
            evidence_ids=evidence_ids,
        )


@pytest.mark.parametrize(
    ("mismatch", "message"),
    [("time", "decision time"), ("state", "inventory snapshot")],
)
def test_replay_rejects_policy_decisions_for_another_boundary(
    mismatch: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        run_deterministic_replay(
            run_id=f"mismatched-{mismatch}-run",
            aligned=_aligned(),
            ledger=PortfolioLedger(PortfolioState.from_holdings({USDT: D("100")})),
            policy=_MismatchedDecisionPolicy(mismatch),
            execution_instrument=BTC_USDT,
            numeraire=USDT,
            cost_model=CostModel.zero(),
            min_rebalance_notional=D("0"),
        )


def test_replay_executes_explicit_cross_market_with_numeraire_valuation_legs() -> None:
    first_decision_time = START + INTERVAL.duration
    aligned = align_bar_series(
        [
            _series(
                BTC_USDT,
                opens=(100.0, 100.0),
                closes=(100.0, 100.0),
            ),
            _series(
                ETH_USDT,
                opens=(10.0, 10.0),
                closes=(10.0, 10.0),
            ),
            _series(
                BTC_ETH,
                opens=(10.0, 10.0),
                closes=(10.0, 10.0),
            ),
        ]
    )
    target = AllocationTarget.for_basket(
        {BTC: D("0"), ETH: D("1")},
        basket={BTC, ETH},
    )

    trace = run_deterministic_replay(
        run_id="explicit-cross-run",
        aligned=aligned,
        ledger=PortfolioLedger(PortfolioState.from_holdings({BTC: D("1")})),
        policy=ScheduledTargetPolicy(
            policy_id="rotate-btc-to-eth-v1",
            schedule={first_decision_time: target},
        ),
        execution_instrument=BTC_ETH,
        numeraire=USDT,
        cost_model=CostModel.zero(),
        min_rebalance_notional=D("0"),
    )

    assert len(trace.fills) == 1
    fill = trace.fills[0]
    assert fill.instrument == BTC_ETH
    assert fill.reference_price == D("10")
    assert fill.balance_deltas == {BTC: D("-1"), ETH: D("10")}
    assert trace.ending_state.holdings == {ETH: D("10")}


def test_replay_preserves_declared_order_for_flows_at_the_same_time() -> None:
    effective_time = START + INTERVAL.duration
    deposit = ExternalInventoryFlow(
        flow_id="z-deposit-first",
        effective_time=effective_time,
        asset=BTC,
        quantity_delta=D("1"),
    )
    withdrawal = ExternalInventoryFlow(
        flow_id="a-withdraw-second",
        effective_time=effective_time,
        asset=BTC,
        quantity_delta=D("-1"),
    )

    trace = run_deterministic_replay(
        run_id="same-time-flow-order",
        aligned=_aligned(),
        ledger=PortfolioLedger(PortfolioState.from_holdings({})),
        policy=ScheduledTargetPolicy(policy_id="no-actions", schedule={}),
        execution_instrument=BTC_USDT,
        numeraire=USDT,
        cost_model=CostModel.zero(),
        min_rebalance_notional=D("0"),
        external_flows=(deposit, withdrawal),
    )

    assert trace.applied_flows == (deposit, withdrawal)
    assert trace.ending_state.holdings == {}


class _ContextCapturingPolicy:
    def __init__(self) -> None:
        self.calls: list[
            tuple[datetime, PriceSnapshot, tuple[ExternalInventoryFlow, ...]]
        ] = []

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        self.calls.append((as_of, price_snapshot, applied_flows))
        return PolicyDecision.no_action_decision(
            decision_id=f"context:{as_of.isoformat()}",
            as_of=as_of,
            policy_id="context-capturing-v1",
            current_state=current_state,
            reason=DecisionReason.INSUFFICIENT_EVIDENCE,
            evidence_ids=evidence_ids,
        )


def test_replay_passes_decision_prices_and_exact_due_flows_to_policy() -> None:
    decision_time = START + INTERVAL.duration
    due = ExternalInventoryFlow(
        flow_id="context-deposit",
        effective_time=decision_time,
        asset=USDT,
        quantity_delta=D("25"),
    )
    policy = _ContextCapturingPolicy()

    trace = run_deterministic_replay(
        run_id="context-run",
        aligned=_aligned(),
        ledger=PortfolioLedger(PortfolioState.from_holdings({BTC: D("1")})),
        policy=policy,
        execution_instrument=BTC_USDT,
        numeraire=USDT,
        cost_model=CostModel.zero(),
        min_rebalance_notional=D("0"),
        external_flows=(due,),
    )

    first_time, first_prices, first_flows = policy.calls[0]
    assert first_time == decision_time
    assert first_prices.timestamp == decision_time
    assert first_prices.price(BTC) == D("10")
    assert first_prices.price(USDT) == D("1")
    assert first_flows == (due,)
    assert trace.steps[0].price_snapshot is first_prices
