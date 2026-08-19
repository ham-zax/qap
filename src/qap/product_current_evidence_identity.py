"""Exact current venue-code binding for frozen collector instruments."""

from qap.market import VenueInstrument
from qap.product_universe import ProductUniverse, ProductUniverseError


def frozen_market_codes(
    universe: ProductUniverse,
    instrument: VenueInstrument,
) -> tuple[str, str]:
    """Resolve current venue-local asset codes without ticker inference or approval."""

    directory = universe.read_directory()
    if directory is None:
        raise ProductUniverseError("Current market directory has not been refreshed.")
    markets = tuple(
        item
        for item in directory.markets
        if item.venue == instrument.venue
        and item.venue_symbol == instrument.venue_symbol
    )
    if len(markets) != 1:
        raise ProductUniverseError(
            "Frozen execution instrument is not uniquely present in the current "
            "directory."
        )
    market = markets[0]
    state = universe.read_state()
    base = tuple(
        item
        for item in state.identity_mappings
        if item.venue == market.venue
        and item.venue_asset_code == market.venue_base_asset
    )
    quote = tuple(
        item
        for item in state.identity_mappings
        if item.venue == market.venue
        and item.venue_asset_code == market.venue_quote_asset
    )
    if len(base) != 1 or len(quote) != 1:
        raise ProductUniverseError(
            "Frozen execution instrument requires confirmed current venue-code "
            "identity."
        )
    if (
        base[0].canonical_asset_id != instrument.base.key
        or quote[0].canonical_asset_id != instrument.quote.key
    ):
        raise ProductUniverseError(
            "Current venue-code identity disagrees with the frozen execution "
            "instrument."
        )
    return market.venue_base_asset, market.venue_quote_asset


__all__ = ["frozen_market_codes"]
