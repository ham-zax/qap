"""Validated declarative long-only allocation targets."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Self

from qap.portfolio._decimal import canonical_decimal, exact_sum
from qap.portfolio.assets import AssetId

ALLOCATION_SUM_TOLERANCE = Decimal("1e-12")
_ONE = Decimal("1")
_NEGATIVE_ONE = Decimal("-1")
_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True, init=False)
class AllocationTarget:
    """An immutable long-only target over a declared admitted basket."""

    _items: tuple[tuple[AssetId, Decimal], ...]

    def __init__(self) -> None:
        raise TypeError("use AllocationTarget.for_basket()")

    @classmethod
    def for_basket(
        cls,
        weights: Mapping[AssetId, Decimal],
        *,
        basket: Iterable[AssetId],
    ) -> Self:
        """Validate weights against a declared basket without renormalizing them."""

        if not weights:
            raise ValueError("allocation target must contain at least one asset")

        admitted = cls._validated_basket(basket)
        normalized: list[tuple[AssetId, Decimal]] = []
        for asset, weight in weights.items():
            cls._validate_asset(asset, context="weight keys")
            cls._validate_weight(asset, weight)
            normalized.append((asset, canonical_decimal(weight)))

        outside = sorted(asset for asset, _ in normalized if asset not in admitted)
        if outside:
            outside_keys = ", ".join(asset.key for asset in outside)
            raise ValueError(
                "allocation contains assets outside the declared basket: "
                f"{outside_keys}"
            )

        ordered = tuple(sorted(normalized))
        total = exact_sum(weight for _, weight in ordered)
        difference = exact_sum((total, _NEGATIVE_ONE)).copy_abs()
        if difference > ALLOCATION_SUM_TOLERANCE:
            raise ValueError(
                "allocation weights must sum to 1 within "
                f"{ALLOCATION_SUM_TOLERANCE}; got {total}"
            )

        target = object.__new__(cls)
        object.__setattr__(target, "_items", ordered)
        return target

    @property
    def weights(self) -> Mapping[AssetId, Decimal]:
        """Return a read-only mapping ordered by stable asset identity."""

        return MappingProxyType(dict(self._items))

    def __repr__(self) -> str:
        return f"AllocationTarget(weights={dict(self._items)!r})"

    @classmethod
    def _validated_basket(cls, basket: Iterable[AssetId]) -> frozenset[AssetId]:
        try:
            admitted = frozenset(basket)
        except TypeError as exc:
            raise TypeError("basket must be iterable") from exc
        for asset in admitted:
            cls._validate_asset(asset, context="basket members")
        return admitted

    @staticmethod
    def _validate_asset(asset: object, *, context: str) -> None:
        if not isinstance(asset, AssetId):
            raise TypeError(f"{context} must be AssetId values")

    @staticmethod
    def _validate_weight(asset: AssetId, weight: object) -> None:
        if not isinstance(weight, Decimal):
            raise TypeError(f"weight for {asset.key} must be Decimal")
        if not weight.is_finite() or weight < _ZERO:
            raise ValueError(f"weight for {asset.key} must be finite and non-negative")
