"""Immutable authoritative owned-inventory snapshots."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Self

from qap.portfolio._decimal import canonical_decimal, exact_add
from qap.portfolio.assets import AssetId

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True, init=False)
class PortfolioState:
    """An immutable snapshot of non-negative owned asset quantities."""

    _items: tuple[tuple[AssetId, Decimal], ...]

    def __init__(self) -> None:
        raise TypeError("use PortfolioState.from_holdings()")

    @classmethod
    def from_holdings(cls, holdings: Mapping[AssetId, Decimal]) -> Self:
        """Validate and copy holdings into a deterministic immutable snapshot."""

        normalized: list[tuple[AssetId, Decimal]] = []
        for asset, quantity in holdings.items():
            cls._validate_asset(asset)
            cls._validate_quantity(asset, quantity)
            canonical_quantity = canonical_decimal(quantity)
            if canonical_quantity != _ZERO:
                normalized.append((asset, canonical_quantity))

        state = object.__new__(cls)
        object.__setattr__(state, "_items", tuple(sorted(normalized)))
        return state

    @property
    def holdings(self) -> Mapping[AssetId, Decimal]:
        """Return a read-only mapping ordered by stable asset identity."""

        return MappingProxyType(dict(self._items))

    def quantity(self, asset: AssetId) -> Decimal:
        """Return the owned quantity, or exact zero when the asset is absent."""

        self._validate_asset(asset)
        for held_asset, quantity in self._items:
            if held_asset == asset:
                return quantity
        return _ZERO

    def apply_deltas(self, deltas: Mapping[AssetId, Decimal]) -> Self:
        """Atomically apply explicit quantity deltas and return a new snapshot."""

        updated = dict(self._items)
        for asset, delta in deltas.items():
            self._validate_asset(asset)
            self._validate_delta(asset, delta)
            next_quantity = exact_add(updated.get(asset, _ZERO), delta)
            if next_quantity < _ZERO:
                raise ValueError(f"delta would create negative balance for {asset.key}")
            if next_quantity == _ZERO:
                updated.pop(asset, None)
            else:
                updated[asset] = next_quantity

        return type(self).from_holdings(updated)

    def __repr__(self) -> str:
        return f"PortfolioState(holdings={dict(self._items)!r})"

    @staticmethod
    def _validate_asset(asset: object) -> None:
        if not isinstance(asset, AssetId):
            raise TypeError("holding keys must be AssetId values")

    @staticmethod
    def _validate_quantity(asset: AssetId, quantity: object) -> None:
        if not isinstance(quantity, Decimal):
            raise TypeError(f"quantity for {asset.key} must be Decimal")
        if not quantity.is_finite() or quantity < _ZERO:
            raise ValueError(
                f"quantity for {asset.key} must be finite and non-negative"
            )

    @staticmethod
    def _validate_delta(asset: AssetId, delta: object) -> None:
        if not isinstance(delta, Decimal):
            raise TypeError(f"delta for {asset.key} must be Decimal")
        if not delta.is_finite():
            raise ValueError(f"delta for {asset.key} must be finite")
