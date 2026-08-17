"""Matched passive HODL benchmark."""

from dataclasses import dataclass
from typing import Self

from qap.portfolio import PortfolioState


@dataclass(frozen=True, slots=True)
class HodlBenchmark:
    """The exact frozen starting ownership vector held passively."""

    starting_state: PortfolioState

    @classmethod
    def from_start(cls, starting_state: PortfolioState) -> Self:
        return cls(starting_state=starting_state)

    @property
    def state(self) -> PortfolioState:
        """Return the unchanged benchmark inventory at every comparison time."""

        return self.starting_state

    def require_same_start(self, strategy_start: PortfolioState) -> None:
        if strategy_start != self.starting_state:
            raise ValueError("strategy and HODL must use the same starting inventory")
