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
from qap.market.lifecycle import (
    AssetIdentityContinuity,
    InstrumentLifecycleEvent,
    InstrumentLifecycleEvidence,
    LifecycleConfidence,
    LifecycleEventType,
    LifecycleSourceType,
    lifecycle_source_priority,
    source_supports_historical_state,
)
from qap.market.metadata import MarketMetadata
from qap.market.microstructure import BookLevel, PublicBookSnapshot
from qap.market.microstructure_storage import (
    MicrostructureStorageError,
    read_public_book_snapshots,
    write_public_book_snapshots,
)
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
    "AssetIdentityContinuity",
    "BarInterval",
    "BarAlignmentError",
    "BarSeriesValidationError",
    "CompletedBarHistory",
    "InstrumentLifecycleEvent",
    "InstrumentLifecycleEvidence",
    "LifecycleConfidence",
    "LifecycleEventType",
    "LifecycleSourceType",
    "BookLevel",
    "MarketBar",
    "MarketDataStorageError",
    "MarketMetadata",
    "MicrostructureStorageError",
    "PriceSnapshot",
    "PublicBookSnapshot",
    "ValidatedBarSeries",
    "VenueInstrument",
    "align_bar_series",
    "fingerprint_bar_series",
    "lifecycle_source_priority",
    "load_csv_bar_series",
    "read_parquet_bar_series",
    "read_public_book_snapshots",
    "source_supports_historical_state",
    "validate_bar_series",
    "write_parquet_bar_series",
    "write_public_book_snapshots",
]
