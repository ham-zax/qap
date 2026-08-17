"""Pure read-only portfolio valuation."""

from decimal import Decimal

from qap.evaluation._decimal import exact_multiply, exact_sum
from qap.market import PriceSnapshot
from qap.portfolio import PortfolioState


def value_portfolio(state: PortfolioState, prices: PriceSnapshot) -> Decimal:
    """Value owned quantities at one explicit market snapshot."""

    terms: list[Decimal] = []
    for asset, quantity in state.holdings.items():
        try:
            price = prices.price(asset)
        except KeyError as exc:
            raise ValueError(
                f"explicit price is required for held asset {asset.key}"
            ) from exc
        terms.append(exact_multiply(quantity, price))
    return exact_sum(terms)
