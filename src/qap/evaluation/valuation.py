"""Pure read-only portfolio valuation."""

from decimal import Decimal

from qap.market import PriceSnapshot
from qap.portfolio import PortfolioState, value_holdings_at_prices
from qap.portfolio.valuation import MissingHoldingPriceError


def value_portfolio(state: PortfolioState, prices: PriceSnapshot) -> Decimal:
    """Value owned quantities at one explicit market snapshot."""

    try:
        return value_holdings_at_prices(state, prices.prices)
    except MissingHoldingPriceError as exc:
        raise ValueError(
            f"explicit price is required for held asset {exc.asset.key}"
        ) from exc
