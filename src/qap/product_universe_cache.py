"""Versioned (stat-keyed) cache for immutable JSON state files."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Lock
from typing import TypeVar

T = TypeVar("T")
_VersionKey = tuple[int, int, int]


class VersionedFileCache:
    """Cache parsed frozen models keyed by (st_ino, st_mtime_ns, st_size)."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._entries: dict[Path, tuple[_VersionKey, object]] = {}

    def get(self, path: Path, parse: Callable[[str], T]) -> T:
        stat = path.stat()
        key: _VersionKey = (stat.st_ino, stat.st_mtime_ns, stat.st_size)
        with self._lock:
            cached = self._entries.get(path)
            if cached is not None and cached[0] == key:
                return cached[1]  # type: ignore[return-value]
        value = parse(path.read_text(encoding="utf-8"))
        with self._lock:
            self._entries[path] = (key, value)
        return value

    def drop(self, path: Path) -> None:
        with self._lock:
            self._entries.pop(path, None)
