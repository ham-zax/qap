from datetime import UTC, datetime
from decimal import Decimal

from qap.execution import ReplayPolicy
from qap.experiment.controls import (
    BandPartialPolicy,
    ContributionAwareBandPolicy,
    MatchedContributionStaticPolicy,
    PeriodicFixedWeightPolicy,
    StrictHodlPolicy,
    starting_value_target,
)
from qap.market import BarInterval, PriceSnapshot
from qap.policy import DecisionReason, PolicyDecision
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    ExternalInventoryFlow,
    PortfolioState,
)

D = Decimal
BTC = AssetId("BTC")
USDT = AssetId("USDT")
BASKET = (BTC, USDT)
AT = datetime(2024, 1, 1, 1, tzinfo=UTC)
TARGET = AllocationTarget.for_basket(
    {BTC: D("0.5"), USDT: D("0.5")},
    basket=BASKET,
)


def _prices(*, btc: str, at: datetime = AT) -> PriceSnapshot:
    return PriceSnapshot.from_prices(
        timestamp=at,
        numeraire=USDT,
        prices={BTC: D(btc), USDT: D("1")},
    )


def _decide(
    policy: ReplayPolicy,
    *,
    state: PortfolioState,
    prices: PriceSnapshot,
    flows: tuple[ExternalInventoryFlow, ...] = (),
) -> PolicyDecision:
    return policy.decide(
        as_of=prices.timestamp,
        current_state=state,
        price_snapshot=prices,
        applied_flows=flows,
        evidence_ids=("fixture",),
    )


def test_starting_value_target_freezes_exact_initial_value_weights() -> None:
    state = PortfolioState.from_holdings({BTC: D("1"), USDT: D("100")})

    target = starting_value_target(
        starting_state=state,
        price_snapshot=_prices(btc="100"),
        basket=BASKET,
    )

    assert target.weights == {BTC: D("0.5"), USDT: D("0.5")}


def test_strict_hodl_never_emits_a_trade_target() -> None:
    policy = StrictHodlPolicy(policy_id="strict-hodl")
    state = PortfolioState.from_holdings({BTC: D("1")})

    decision = _decide(policy, state=state, prices=_prices(btc="100"))

    assert decision.no_action
    assert decision.reason is DecisionReason.NOT_SCHEDULED
    assert decision.current_state is state


def test_matched_contribution_static_hodl_allocates_only_new_contribution() -> None:
    policy = MatchedContributionStaticPolicy(
        policy_id="matched-contribution",
        target=TARGET,
    )
    # Before the flow: BTC=1 and USDT=100. BTC has appreciated to 200, so a
    # full 50/50 rebalance would do nothing after the deposit. Matched static
    # HODL instead preserves old inventory and deploys only the new 100 USDT.
    current = PortfolioState.from_holdings({BTC: D("1"), USDT: D("200")})
    deposit = ExternalInventoryFlow(
        flow_id="deposit-1",
        effective_time=AT,
        asset=USDT,
        quantity_delta=D("100"),
    )

    decision = _decide(
        policy,
        state=current,
        prices=_prices(btc="200"),
        flows=(deposit,),
    )

    assert decision.target is not None
    assert decision.target.weights == {BTC: D("0.625"), USDT: D("0.375")}
    assert decision.reason is DecisionReason.EVIDENCE_TARGET


def test_periodic_fixed_weight_triggers_only_on_declared_cadence() -> None:
    policy = PeriodicFixedWeightPolicy(
        policy_id="periodic-2",
        target=TARGET,
        first_decision_time=AT,
        interval=BarInterval("1h"),
        cadence_bars=2,
    )
    state = PortfolioState.from_holdings({BTC: D("1"), USDT: D("100")})

    at_start = _decide(policy, state=state, prices=_prices(btc="100", at=AT))
    one_bar = _decide(
        policy,
        state=state,
        prices=_prices(btc="100", at=datetime(2024, 1, 1, 2, tzinfo=UTC)),
    )
    two_bars = _decide(
        policy,
        state=state,
        prices=_prices(btc="100", at=datetime(2024, 1, 1, 3, tzinfo=UTC)),
    )

    assert at_start.no_action
    assert one_bar.no_action
    assert two_bars.target == TARGET


def test_band_partial_control_applies_declared_fraction_after_breach() -> None:
    policy = BandPartialPolicy(
        policy_id="band-half",
        target=TARGET,
        band_width=D("0.05"),
        partial_correction_fraction=D("0.5"),
    )
    drifted = PortfolioState.from_holdings({BTC: D("1"), USDT: D("80")})

    decision = _decide(policy, state=drifted, prices=_prices(btc="120"))

    assert decision.target is not None
    assert decision.target.weights == {BTC: D("0.55"), USDT: D("0.45")}
    assert decision.reason is DecisionReason.EVIDENCE_TARGET


def test_contribution_aware_control_routes_contributed_excess_to_underweight() -> None:
    policy = ContributionAwareBandPolicy(
        policy_id="contribution-aware",
        target=TARGET,
        band_width=D("0.05"),
        partial_correction_fraction=D("0.5"),
    )
    # Before the flow: BTC=1, USDT=0. The 200 USDT deposit creates a 50-value
    # excess in USDT and a 50-value BTC deficit at the post-flow target.
    current = PortfolioState.from_holdings({BTC: D("1"), USDT: D("200")})
    deposit = ExternalInventoryFlow(
        flow_id="deposit-1",
        effective_time=AT,
        asset=USDT,
        quantity_delta=D("200"),
    )

    decision = _decide(
        policy,
        state=current,
        prices=_prices(btc="100"),
        flows=(deposit,),
    )

    assert decision.target == TARGET
    assert decision.reason is DecisionReason.EVIDENCE_TARGET


def test_contribution_aware_control_falls_back_to_band_rule_without_flow() -> None:
    policy = ContributionAwareBandPolicy(
        policy_id="contribution-aware",
        target=TARGET,
        band_width=D("0.05"),
        partial_correction_fraction=D("0.5"),
    )
    drifted = PortfolioState.from_holdings({BTC: D("1"), USDT: D("80")})

    decision = _decide(policy, state=drifted, prices=_prices(btc="120"))

    assert decision.target is not None
    assert decision.target.weights == {BTC: D("0.55"), USDT: D("0.45")}
