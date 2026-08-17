import runpy
import socket
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

ROOT = Path(__file__).resolve().parents[3]
NAMESPACE = runpy.run_path(
    str(ROOT / "scripts/run_playwright_e2e.py"), run_name="__test__"
)
available_loopback_ports = cast(
    Callable[[int], tuple[int, ...]],
    NAMESPACE["_available_loopback_ports"],
)


def test_playwright_runner_selects_free_distinct_loopback_ports() -> None:
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen()
        occupied = cast(tuple[str, int], blocker.getsockname())[1]

        selected = available_loopback_ports(2)

        assert len(selected) == 2
        assert len(set(selected)) == 2
        assert occupied not in selected
    finally:
        blocker.close()


def test_playwright_runner_rejects_non_positive_port_count() -> None:
    with pytest.raises(ValueError, match="count must be positive"):
        available_loopback_ports(0)
