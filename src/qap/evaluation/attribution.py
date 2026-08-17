"""Per-asset terminal attribution and concentration diagnostics."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from qap.evaluation._decimal import (
    divide,
    exact_multiply,
    exact_subtract,
    exact_sum,
)
from qap.evaluation.valuation import value_portfolio
from qap.market import PriceSnapshot
from qap.portfolio import AssetId, PortfolioState

_ZERO = Decimal("0")


class QuantityRatioStatus(StrEnum):
    COMPARABLE = "comparable"
    NO_HODL_QUANTITY = "no_hodl_quantity"


@dataclass(frozen=True, slots=True)
class AssetAttribution:
    asset: AssetId
    strategy_quantity: Decimal
    hodl_quantity: Decimal
    quantity_delta: Decimal
    quantity_ratio: Decimal | None
    quantity_ratio_status: QuantityRatioStatus
    strategy_value: Decimal
    hodl_value: Decimal
    value_delta: Decimal
    relative_value_contribution: Decimal


@dataclass(frozen=True, slots=True)
class ConcentrationDiagnostics:
    max_single_asset_weight: Decimal | None
    herfindahl_index: Decimal | None
    largest_positive_contributor_share: Decimal | None


def terminal_attribution(
    strategy_state: PortfolioState,
    hodl_state: PortfolioState,
    prices: PriceSnapshot,
) -> tuple[AssetAttribution, ...]:
    """Attribute terminal quantity/value differences with exact reconciliation."""

    strategy_total = value_portfolio(strategy_state, prices)
    hodl_total = value_portfolio(hodl_state, prices)
    if hodl_total <= _ZERO:
        raise ValueError("HODL terminal value must be positive for attribution")

    assets = tuple(sorted(set(strategy_state.holdings) | set(hodl_state.holdings)))
    items: list[AssetAttribution] = []
    for asset in assets:
        strategy_quantity = strategy_state.quantity(asset)
        hodl_quantity = hodl_state.quantity(asset)
        price = prices.price(asset)
        strategy_value = exact_multiply(strategy_quantity, price)
        hodl_value = exact_multiply(hodl_quantity, price)
        value_delta = exact_subtract(strategy_value, hodl_value)
        if hodl_quantity > _ZERO:
            quantity_ratio = divide(strategy_quantity, hodl_quantity)
            ratio_status = QuantityRatioStatus.COMPARABLE
        else:
            quantity_ratio = None
            ratio_status = QuantityRatioStatus.NO_HODL_QUANTITY
        items.append(
            AssetAttribution(
                asset=asset,
                strategy_quantity=strategy_quantity,
                hodl_quantity=hodl_quantity,
                quantity_delta=exact_subtract(strategy_quantity, hodl_quantity),
                quantity_ratio=quantity_ratio,
                quantity_ratio_status=ratio_status,
                strategy_value=strategy_value,
                hodl_value=hodl_value,
                value_delta=value_delta,
                relative_value_contribution=divide(value_delta, hodl_total),
            )
        )

    result = tuple(items)
    expected_delta = exact_subtract(strategy_total, hodl_total)
    if exact_sum(item.value_delta for item in result) != expected_delta:
        raise ArithmeticError(
            "asset attribution did not reconcile to total value delta"
        )
    return result


def concentration_diagnostics(
    strategy_state: PortfolioState,
    prices: PriceSnapshot,
    attribution: Iterable[AssetAttribution],
) -> ConcentrationDiagnostics:
    """Return terminal value and positive-contributor concentration diagnostics."""

    items = tuple(attribution)

    total_value = value_portfolio(strategy_state, prices)
    if total_value == _ZERO:
        max_weight: Decimal | None = None
        herfindahl: Decimal | None = None
    else:
        asset_values = tuple(
            exact_multiply(quantity, prices.price(asset))
            for asset, quantity in strategy_state.holdings.items()
        )
        max_weight = max(
            (divide(asset_value, total_value) for asset_value in asset_values),
            default=_ZERO,
        )
        herfindahl = divide(
            exact_sum(exact_multiply(value, value) for value in asset_values),
            exact_multiply(total_value, total_value),
        )

    positive = tuple(item.value_delta for item in items if item.value_delta > _ZERO)
    if positive:
        positive_total = exact_sum(positive)
        largest_positive_share: Decimal | None = divide(max(positive), positive_total)
    else:
        largest_positive_share = None

    return ConcentrationDiagnostics(
        max_single_asset_weight=max_weight,
        herfindahl_index=herfindahl,
        largest_positive_contributor_share=largest_positive_share,
    )
