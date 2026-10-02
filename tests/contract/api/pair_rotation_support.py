"""Offline venue and history fixtures for the Pair Rotation API."""

import hashlib
from datetime import UTC, datetime, timedelta

from qap.market import BarInterval, MarketBar, validate_bar_series
from qap.product_market_data_binance import BinanceHistoricalAcquirer
from qap.product_market_data_models import (
    MarketDataGenerationInput,
    MarketDataUpstreamSource,
)
from qap.product_universe import (
    DirectoryMarket,
    DirectorySource,
    ProductMarketDirectory,
    ProductResearchScope,
    ProductUniverse,
    ResolvedProductInstrument,
)

NOW = datetime(2026, 10, 2, 14, 7, tzinfo=UTC)


def publish_directory(owner: ProductUniverse) -> ProductMarketDirectory:
    directory = ProductMarketDirectory(
        sources=(
            DirectorySource(
                venue="binance",
                observed_at=NOW,
                source_id="offline-exchangeInfo",
                source_fingerprint="1" * 64,
            ),
        ),
        markets=tuple(
            DirectoryMarket(
                venue="binance",
                venue_symbol=f"{code}USDT",
                venue_base_asset=code,
                venue_quote_asset="USDT",
                status="TRADING",
                trading=True,
                base_name=name,
                permissions=permissions,
            )
            for code, name, permissions in (
                ("BTC", "Bitcoin", ()),
                ("W", "Wormhole", ()),
                ("BTCUP", "Leveraged BTC", ()),
                ("AAPLB", "Stock", ("TRD_GRP_261",)),
            )
        ),
    )
    owner.root.mkdir(parents=True, exist_ok=True)
    owner.directory_path.write_text(directory.model_dump_json())
    return directory


class OfflineBinance(BinanceHistoricalAcquirer):
    def __init__(self) -> None:
        self.windows: list[tuple[datetime, datetime]] = []

    def close(self) -> None:
        pass

    def acquire_generation_input(
        self,
        *,
        scope: ProductResearchScope,
        instrument: ResolvedProductInstrument,
        dataset_id: str,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
    ) -> MarketDataGenerationInput:
        self.windows.append((start, end_exclusive))
        assert interval.label == "15m"
        bars = tuple(
            MarketBar(
                instrument=instrument.instrument,
                interval=interval,
                candle_open_time=start + index * timedelta(minutes=15),
                open=10.0,
                high=11.0,
                low=9.0,
                close=10.0,
                volume=1.0,
            )
            for index in range(int((end_exclusive - start).total_seconds()) // 900)
        )
        return MarketDataGenerationInput(
            dataset_id=dataset_id,
            resolved_instrument=instrument,
            series=validate_bar_series(bars),
            acquisition_implementation="offline-binance-v1",
            upstream_sources=(
                MarketDataUpstreamSource(
                    provider="binance",
                    source_family="offline-contract",
                    source_id=dataset_id,
                    retrieved_at=NOW,
                    source_fingerprint=hashlib.sha256(dataset_id.encode()).hexdigest(),
                ),
            ),
        )
