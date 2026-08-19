"""Gate-specific Product historical market-data publication."""

from datetime import datetime

from qap.market import BarInterval
from qap.market.adapters.gate_historical import GateHistoricalAdapter
from qap.product_market_data import ProductMarketData
from qap.product_market_data_models import (
    MarketDataGenerationInput,
    MarketDataGenerationProvenance,
    MarketDataUpstreamSource,
)
from qap.product_universe import ProductResearchScope, ResolvedProductInstrument

_GATE_ACQUISITION_IMPLEMENTATION = "qap.product.gate-historical-acquisition.v1"


def gate_dataset_id(
    resolved_instrument: ResolvedProductInstrument,
    interval: BarInterval,
) -> str:
    """Return the stable logical dataset identity for one explicit Gate mapping."""

    instrument = resolved_instrument.instrument
    if instrument.venue != "gate":
        raise ValueError("Gate dataset identity requires a gate instrument")
    return ":".join(
        (
            "gate-spot",
            instrument.venue_symbol,
            resolved_instrument.base_asset_identity_version,
            resolved_instrument.quote_asset_identity_version,
            interval.label,
        )
    )


def publish_gate_historical_generation(
    *,
    market_data: ProductMarketData,
    adapter: GateHistoricalAdapter,
    scope: ProductResearchScope,
    resolved_instrument: ResolvedProductInstrument,
    interval: BarInterval,
    start: datetime,
    end_exclusive: datetime,
) -> MarketDataGenerationProvenance:
    """Acquire and publish one exact Gate generation through the shared M3 owner."""

    if resolved_instrument not in scope.instruments:
        raise ValueError(
            "Gate acquisition instrument is not in the Product research scope"
        )
    if resolved_instrument.instrument.venue != "gate":
        raise ValueError("Gate acquisition requires a gate instrument")

    acquisition = adapter.fetch_candlesticks(
        instrument=resolved_instrument.instrument,
        interval=interval,
        start=start,
        end_exclusive=end_exclusive,
    )
    upstream_sources = tuple(
        MarketDataUpstreamSource(
            provider="gate",
            source_family=source.source_family,
            source_id=source.source_id,
            retrieved_at=source.retrieved_at,
            source_fingerprint=source.source_fingerprint,
        )
        for source in acquisition.sources
    )
    generation = MarketDataGenerationInput(
        dataset_id=gate_dataset_id(resolved_instrument, interval),
        resolved_instrument=resolved_instrument,
        series=acquisition.series,
        acquisition_implementation=_GATE_ACQUISITION_IMPLEMENTATION,
        upstream_sources=upstream_sources,
    )
    return market_data.publish_generation(scope, generation)


__all__ = ["gate_dataset_id", "publish_gate_historical_generation"]
