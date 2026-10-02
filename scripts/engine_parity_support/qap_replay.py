"""Bounded-window invocation of the authoritative replay on every eligible bar."""

from decimal import Decimal

from qap.evaluation import value_portfolio
from qap.execution import CostModel, run_deterministic_replay
from qap.market import (
    PriceSnapshot,
    ValidatedBarSeries,
    align_bar_series,
    validate_bar_series,
)
from qap.policy import ScheduledTargetPolicy
from qap.portfolio import AllocationTarget, AssetId, PortfolioLedger, PortfolioState
from scripts.engine_parity_support.contracts import (
    Outcome,
    PairInputs,
    Settings,
    Strategy,
    target_weight,
)


def run_qap(
    inputs: PairInputs,
    series: tuple[ValidatedBarSeries, ValidatedBarSeries],
    strategy: Strategy,
    settings: Settings,
) -> Outcome:
    """A two-bar replay window avoids retaining quadratic diagnostic histories.

    Every decision/fill uses ordinary QAP replay. Policies here require only the
    current completed close or the causal raw ratio window. The ledger is shared
    across windows; no fill or inventory logic is reimplemented by the harness.
    """
    assets = tuple(item.instrument.base for item in series)
    usdt = AssetId("USDT")
    starting = {
        asset: Decimal(str(settings.starting_value / 2)) / Decimal(str(price))
        for asset, price in zip(assets, inputs.closes[0], strict=True)
    }
    ledger = PortfolioLedger(PortfolioState.from_holdings(starting))
    costs = CostModel(
        fee_bps=Decimal(str(settings.fee_rate * 10000)),
        slippage_bps=Decimal(str(settings.slippage_rate * 10000)),
    )
    ratios = tuple(a / b for a, b in inputs.closes)
    legs = 0
    for index, prices in enumerate(inputs.closes[:-1]):
        quantities = tuple(
            float(ledger.current_state.quantity(asset)) for asset in assets
        )
        values = tuple(q * p for q, p in zip(quantities, prices, strict=True))
        total = sum(values) + float(ledger.current_state.quantity(usdt))
        weight = target_weight(strategy, index, values[0], total, ratios, settings)
        if weight is None:
            continue
        as_of = series[0].bars[index].bar_end_exclusive
        target = AllocationTarget.for_basket(
            {
                assets[0]: Decimal(str(weight)),
                assets[1]: Decimal(str(1 - weight)),
                usdt: Decimal(0),
            },
            basket=(*assets, usdt),
        )
        aligned = align_bar_series(
            tuple(validate_bar_series(item.bars[index : index + 2]) for item in series)
        )
        result = run_deterministic_replay(
            run_id=f"parity-{strategy}-{index}",
            aligned=aligned,
            ledger=ledger,
            policy=ScheduledTargetPolicy(
                policy_id=f"parity-{strategy}", schedule={as_of: target}
            ),
            execution_instrument=None,
            execution_instruments=tuple(item.instrument for item in series),
            execution_bridge=usdt,
            numeraire=usdt,
            cost_model=costs,
            min_rebalance_notional=Decimal(str(settings.minimum_notional)),
            evaluation_start=as_of,
            evaluation_end=as_of,
            require_market_metadata=False,
            valuation_assets=(*assets, usdt),
        )
        legs += len(result.fills)
    end_prices = PriceSnapshot.from_prices(
        timestamp=series[0].bars[-1].bar_end_exclusive,
        numeraire=usdt,
        prices={
            **{
                asset: Decimal(str(price))
                for asset, price in zip(assets, inputs.closes[-1], strict=True)
            },
            usdt: Decimal(1),
        },
    )
    holdings = tuple(float(ledger.current_state.quantity(asset)) for asset in assets)
    return Outcome(
        float(value_portfolio(ledger.current_state, end_prices)),
        legs,
        (holdings[0], holdings[1]),
        float(ledger.current_state.quantity(usdt)),
    )
