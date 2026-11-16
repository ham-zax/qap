"""Stat-keyed caches for immutable market-data projection rows and series."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qap.market import ValidatedBarSeries
    from qap.product_market_data_models import (
        CurrentMarketDataGeneration,
        MarketDataGenerationProvenance,
    )

_StatKey = tuple[int, int, int] | None
ProjectionKey = tuple[Path, str, str, str, _StatKey, _StatKey]
GenerationKey = tuple[Path, str, str, _StatKey, _StatKey]


def stat_key(path: Path) -> _StatKey:
    """Return (st_ino, st_mtime_ns, st_size) or None when missing."""
    try:
        st = path.stat()
    except OSError:
        return None
    return (st.st_ino, st.st_mtime_ns, st.st_size)


class ProjectionRowCache:
    """Thread-safe cache of immutable CurrentMarketDataGeneration rows."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._entries: dict[
            tuple[Path, str], tuple[ProjectionKey, CurrentMarketDataGeneration]
        ] = {}

    def get(
        self, data_root: Path, dataset_id: str, key: ProjectionKey
    ) -> CurrentMarketDataGeneration | None:
        with self._lock:
            entry = self._entries.get((data_root, dataset_id))
            if entry is not None and entry[0] == key:
                return entry[1]
        return None

    def put(
        self,
        data_root: Path,
        dataset_id: str,
        key: ProjectionKey,
        value: CurrentMarketDataGeneration,
    ) -> None:
        with self._lock:
            self._entries[(data_root, dataset_id)] = (key, value)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


class GenerationCache:
    """Bounded stat-keyed cache of immutable (provenance, series) pairs."""

    def __init__(self, maxsize: int = 128) -> None:
        self._lock = Lock()
        self._maxsize = maxsize
        self._entries: OrderedDict[
            GenerationKey, tuple[MarketDataGenerationProvenance, ValidatedBarSeries]
        ] = OrderedDict()

    def get(
        self, key: GenerationKey
    ) -> tuple[MarketDataGenerationProvenance, ValidatedBarSeries] | None:
        with self._lock:
            value = self._entries.get(key)
            if value is not None:
                self._entries.move_to_end(key)
            return value

    def put(
        self,
        key: GenerationKey,
        value: tuple[MarketDataGenerationProvenance, ValidatedBarSeries],
    ) -> None:
        with self._lock:
            self._entries[key] = value
            self._entries.move_to_end(key)
            while len(self._entries) > self._maxsize:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


PROJECTION_ROW_CACHE = ProjectionRowCache()
GENERATION_CACHE = GenerationCache()
