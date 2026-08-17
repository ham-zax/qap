"""Public market-data domain contracts."""

from qap.market.alignment import (
    AlignedBarSeries,
    AlignedInstrumentSeries,
    BarAlignmentError,
    align_bar_series,
)
from qap.market.bars import BarInterval, MarketBar
from qap.market.fingerprint import fingerprint_bar_series
from qap.market.instruments import VenueInstrument
from qap.market.prices import PriceSnapshot
from qap.market.storage import (
    MarketDataStorageError,
    load_csv_bar_series,
    read_parquet_bar_series,
    write_parquet_bar_series,
)
from qap.market.validation import (
    BarSeriesValidationError,
    CompletedBarHistory,
    ValidatedBarSeries,
    validate_bar_series,
)

__all__ = [
    "AlignedBarSeries",
    "AlignedInstrumentSeries",
    "BarInterval",
    "BarAlignmentError",
    "BarSeriesValidationError",
    "CompletedBarHistory",
    "MarketBar",
    "MarketDataStorageError",
    "PriceSnapshot",
    "ValidatedBarSeries",
    "VenueInstrument",
    "align_bar_series",
    "fingerprint_bar_series",
    "load_csv_bar_series",
    "read_parquet_bar_series",
    "validate_bar_series",
    "write_parquet_bar_series",
]
