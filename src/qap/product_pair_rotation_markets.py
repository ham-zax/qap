"""Observed direct-market selection for the Pair Rotation Lab."""

from dataclasses import replace

from qap.market import VenueInstrument
from qap.product_pair_rotation_analysis import PairAnalysisError
from qap.product_universe import (
    ProductResearchScope,
    ProductUniverse,
    ResolvedProductInstrument,
)


def direct_instrument(
    universe: ProductUniverse, scope: ProductResearchScope
) -> ResolvedProductInstrument | None:
    directory = universe.read_directory()
    if directory is None:
        raise PairAnalysisError("Market directory is unavailable.")
    first, second = scope.instruments[:2]
    for base, quote in ((first, second), (second, first)):
        # Source codes come from the observed USDT listings, not canonical guesses.
        base_market = next(
            row
            for row in directory.markets
            if row.venue == "binance"
            and row.venue_symbol == base.instrument.venue_symbol
        )
        quote_market = next(
            row
            for row in directory.markets
            if row.venue == "binance"
            and row.venue_symbol == quote.instrument.venue_symbol
        )
        market = next(
            (
                row
                for row in directory.markets
                if row.venue == "binance"
                and row.trading
                and row.venue_base_asset == base_market.venue_base_asset
                and row.venue_quote_asset == quote_market.venue_base_asset
            ),
            None,
        )
        if market is not None:
            return replace(
                base,
                instrument=VenueInstrument(
                    "binance",
                    market.venue_symbol,
                    base.instrument.base,
                    quote.instrument.base,
                ),
                quote_asset_identity_version=quote.base_asset_identity_version,
            )
    return None
