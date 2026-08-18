from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qap.market import BookLevel, MarketMetadata, PublicBookSnapshot, VenueInstrument
from qap.portfolio import AssetId
from qap.scanner.liquidity import (
    BookSide,
    FrictionEvidence,
)
from qap.scanner.liquidity_policy import (
    candidate_capital_ceiling,
    evaluate_capture_contract,
    evaluate_two_sided_c95,
    find_directional_safe_size,
    required_trade_fractions,
)
from qap.scanner.prospective_protocol import (
    C95_QUANTILE,
    DAILY_COVERAGE_MINIMUM,
    DEPTH_CADENCE,
    L1_CADENCE,
    LIQUIDITY_POLICY_VERSION,
    MINIMUM_QUALIFICATION_WINDOW,
    OVERALL_COVERAGE_MINIMUM,
    SAFE_CAPACITY_HAIRCUT,
    STRUCTURAL_REBALANCE_FRACTION,
)

BTC = AssetId("BTC")
ETH = AssetId("ETH")
INSTRUMENT = VenueInstrument(
    venue="binance",
    venue_symbol="BTCETH",
    base=BTC,
    quote=ETH,
)
AS_OF = datetime(2026, 8, 18, 0, 0, tzinfo=UTC)


def _metadata() -> MarketMetadata:
    return MarketMetadata(
        instrument=INSTRUMENT,
        status="TRADING",
        price_tick=Decimal("0.01"),
        minimum_price=None,
        maximum_price=None,
        quantity_step=Decimal("0.001"),
        minimum_quantity=None,
        maximum_quantity=None,
        minimum_notional=Decimal("10"),
        maximum_notional=None,
        minimum_notional_applies_to_market=True,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=0,
        market_quantity_step=Decimal("0.001"),
        market_minimum_quantity=None,
        market_maximum_quantity=None,
    )


def _book(observed_at: datetime, *, source: str) -> PublicBookSnapshot:
    return PublicBookSnapshot(
        instrument=INSTRUMENT,
        observed_at=observed_at,
        source_id=source,
        source_fingerprint="a" * 64,
        bids=(
            BookLevel(price=99.98, quantity=1.0),
            BookLevel(price=99.80, quantity=10.0),
        ),
        asks=(
            BookLevel(price=100.00, quantity=1.0),
            BookLevel(price=100.20, quantity=10.0),
        ),
    )


def _friction(
    *,
    snapshot_id: str,
    side: BookSide,
    total_bps: str | None,
    q: str = "100",
) -> FrictionEvidence:
    fee = Decimal("20")
    total = None if total_bps is None else Decimal(total_bps)
    return FrictionEvidence(
        snapshot_id=snapshot_id,
        side=side,
        quote_notional_requested=Decimal(q),
        fillable=total is not None,
        fee_bps=fee,
        book_price_impact_bps=None if total is None else total - fee,
        total_friction_bps=total,
    )


def test_liquidity_contract_uses_typed_prospective_protocol_values() -> None:
    assert LIQUIDITY_POLICY_VERSION == "liquidity-policy-v1"
    assert L1_CADENCE == timedelta(seconds=60)
    assert DEPTH_CADENCE == timedelta(minutes=5)
    assert MINIMUM_QUALIFICATION_WINDOW == timedelta(days=14)
    assert OVERALL_COVERAGE_MINIMUM == Decimal("0.95")
    assert DAILY_COVERAGE_MINIMUM == Decimal("0.90")
    assert C95_QUANTILE == Decimal("0.95")
    assert SAFE_CAPACITY_HAIRCUT == Decimal("0.5")
    assert STRUCTURAL_REBALANCE_FRACTION == Decimal("0.20")


def test_two_sided_c95_uses_nearest_rank_and_fixed_snapshot_denominator() -> None:
    rows: list[FrictionEvidence] = []
    for index in range(1, 21):
        snapshot_id = f"{index:064x}"
        rows.append(
            _friction(
                snapshot_id=snapshot_id,
                side=BookSide.BUY_BASE,
                total_bps=str(20 + index),
            )
        )
        rows.append(
            _friction(
                snapshot_id=snapshot_id,
                side=BookSide.SELL_BASE,
                total_bps=str(21 + index),
            )
        )

    result = evaluate_two_sided_c95(tuple(rows), quote_notional=Decimal("100"))

    assert result.required_snapshots == 20
    assert result.infeasible_snapshots == 0
    assert result.buy_c95_friction_bps == Decimal("39")
    assert result.sell_c95_friction_bps == Decimal("40")
    assert result.c95_friction_bps == Decimal("40")


def test_two_sided_c95_keeps_unfillable_snapshot_in_denominator() -> None:
    rows = (
        _friction(snapshot_id="1" * 64, side=BookSide.BUY_BASE, total_bps="22"),
        _friction(snapshot_id="1" * 64, side=BookSide.SELL_BASE, total_bps="23"),
        _friction(snapshot_id="2" * 64, side=BookSide.BUY_BASE, total_bps=None),
        _friction(snapshot_id="2" * 64, side=BookSide.SELL_BASE, total_bps="24"),
    )

    result = evaluate_two_sided_c95(rows, quote_notional=Decimal("100"))

    assert result.required_snapshots == 2
    assert result.infeasible_snapshots == 1
    assert result.c95_friction_bps is None
    assert result.feasible is False


def test_directional_safe_size_bisects_recorded_depth_and_applies_half_haircut() -> (
    None
):
    snapshots = (
        _book(AS_OF - timedelta(minutes=10), source="a"),
        _book(AS_OF - timedelta(minutes=5), source="b"),
    )

    result = find_directional_safe_size(
        snapshots,
        side=BookSide.BUY_BASE,
        market_metadata=_metadata(),
    )

    assert result.q_star is not None
    assert Decimal("100") < result.q_star < Decimal("200")
    assert result.q_safe == result.q_star * Decimal("0.5")
    assert result.quote_notional_tolerance == Decimal("0.09999")
    assert result.adverse_fee_bps == Decimal("20")
    assert result.adverse_slippage_budget_bps == Decimal("10")
    assert result.evaluations
    assert all(item.side is BookSide.BUY_BASE for item in result.evaluations)


def test_capture_contract_requires_14d_95pct_overall_and_90pct_each_utc_day() -> None:
    start = AS_OF - timedelta(days=14)
    l1 = tuple(start + index * L1_CADENCE for index in range(14 * 24 * 60))
    depth = tuple(start + index * DEPTH_CADENCE for index in range(14 * 24 * 12))

    complete = evaluate_capture_contract(l1, depth, window_end=AS_OF)
    assert complete.satisfied is True
    assert complete.l1_overall_coverage == Decimal("1")
    assert complete.depth_overall_coverage == Decimal("1")

    # Remove 11% of one UTC day's depth slots while keeping the rest perfect.
    bad_day = start.date() + timedelta(days=5)
    filtered_depth = tuple(
        timestamp
        for timestamp in depth
        if not (timestamp.date() == bad_day and timestamp.hour < 3)
    )
    insufficient = evaluate_capture_contract(l1, filtered_depth, window_end=AS_OF)
    assert insufficient.satisfied is False
    assert insufficient.minimum_depth_daily_coverage < Decimal("0.90")


def test_required_trade_fractions_are_direction_specific_and_include_drift() -> None:
    neutral = required_trade_fractions(Decimal("0.50"))
    assert neutral.required_buy == Decimal("0.20")
    assert neutral.required_sell == Decimal("0.20")

    drifted_high = required_trade_fractions(Decimal("0.72"))
    assert drifted_high.required_buy == Decimal("0.20")
    assert drifted_high.required_sell == Decimal("0.32")

    drifted_low = required_trade_fractions(Decimal("0.30"))
    assert drifted_low.required_buy == Decimal("0.30")
    assert drifted_low.required_sell == Decimal("0.20")


def test_candidate_capital_ceiling_uses_buy_and_sell_demand_not_ten_pct_shortcut() -> (
    None
):
    result = candidate_capital_ceiling(
        q_safe_buy=Decimal("100"),
        q_safe_sell=Decimal("160"),
        current_base_weight=Decimal("0.72"),
    )

    assert result is not None
    assert result.required_buy_fraction == Decimal("0.20")
    assert result.required_sell_fraction == Decimal("0.32")
    assert result.buy_capital_ceiling == Decimal("500")
    assert result.sell_capital_ceiling == Decimal("500")
    assert result.candidate_capital_ceiling == Decimal("500")
    assert result.candidate_capital_ceiling < Decimal("100") / Decimal("0.10")
