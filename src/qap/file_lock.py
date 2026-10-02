"""Scoped local file locks that preserve immutable boundary exceptions."""

import fcntl
from pathlib import Path
from threading import Lock
from types import TracebackType
from typing import BinaryIO, Self


class FileLock:
    """Combine process and optional thread locks without rewriting exceptions."""

    def __init__(self, path: Path, thread_lock: Lock | None = None) -> None:
        self.path = path
        self.thread_lock = thread_lock
        self._handle: BinaryIO | None = None

    def __enter__(self) -> Self:
        if self.thread_lock is not None:
            self.thread_lock.acquire()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = self.path.open("a+b")
            fcntl.flock(self._handle, fcntl.LOCK_EX)
        except BaseException:
            self._release()
            raise
        return self

    def _release(self) -> None:
        try:
            if self._handle is not None:
                self._handle.close()
                self._handle = None
        finally:
            if self.thread_lock is not None:
                self.thread_lock.release()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._release()
