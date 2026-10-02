"""Shared raw inputs and predeclared settings, independent of either engine."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Strategy = Literal["hodl", "periodic", "threshold", "signal"]
STRATEGIES: tuple[Strategy, ...] = ("hodl", "periodic", "threshold", "signal")


@dataclass(frozen=True)
class PairInputs:
    assets: tuple[str, str]
    dates: tuple[datetime, ...]
    opens: tuple[tuple[float, float], ...]
    closes: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class Settings:
    starting_value: float = 10000.0
    fee_rate: float = 0.001
    slippage_rate: float = 0.0005
    minimum_notional: float = 1.0
    period_bars: int = 96
    drift: float = 0.05
    signal_deviation: float = 0.01


@dataclass(frozen=True)
class Outcome:
    terminal_value: float
    legs: int
    holdings: tuple[float, float]
    settlement: float


def target_weight(
    strategy: Strategy,
    index: int,
    first_value: float,
    total_value: float,
    ratios: tuple[float, ...],
    settings: Settings,
) -> float | None:
    """Causal fixed settings; each engine supplies its own inventory valuation."""
    if strategy == "hodl":
        return None
    if strategy == "threshold":
        return 0.5 if abs(first_value / total_value - 0.5) >= settings.drift else None
    if (index + 1) % settings.period_bars:
        return None
    if strategy == "periodic":
        return 0.5
    window = ratios[max(0, index + 1 - settings.period_bars) : index + 1]
    mean = sum(window) / len(window)
    deviation = ratios[index] / mean - 1
    return (
        0.25
        if deviation > settings.signal_deviation
        else (0.75 if deviation < -settings.signal_deviation else 0.5)
    )
