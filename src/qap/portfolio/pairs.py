"""Canonical pair identity and explicit requested orientation."""

from dataclasses import dataclass

from qap.portfolio.assets import AssetId


def _validated_assets(first: object, second: object) -> tuple[AssetId, AssetId]:
    if not isinstance(first, AssetId) or not isinstance(second, AssetId):
        raise TypeError("pair members must be AssetId values")
    if first == second:
        raise ValueError("pair assets must be distinct")
    return first, second


@dataclass(frozen=True, order=True, slots=True, init=False)
class PairId:
    """Orientation-independent identity for two distinct assets."""

    first: AssetId
    second: AssetId

    def __init__(self, first: AssetId, second: AssetId) -> None:
        validated_first, validated_second = _validated_assets(first, second)
        canonical_first, canonical_second = sorted((validated_first, validated_second))
        object.__setattr__(self, "first", canonical_first)
        object.__setattr__(self, "second", canonical_second)


@dataclass(frozen=True, slots=True)
class PairOrientation:
    """Requested BASE/QUOTE view, meaning quote units per one base unit."""

    base: AssetId
    quote: AssetId

    def __post_init__(self) -> None:
        _validated_assets(self.base, self.quote)

    @property
    def pair_id(self) -> PairId:
        """Return the canonical identity shared by both orientations."""

        return PairId(self.base, self.quote)

    def inverted(self) -> "PairOrientation":
        """Return the reciprocal orientation without changing pair identity."""

        return PairOrientation(base=self.quote, quote=self.base)
