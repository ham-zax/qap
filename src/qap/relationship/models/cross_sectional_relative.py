"""Pair-blind rolling relative-return control against the owned-basket common mode."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from types import MappingProxyType
from typing import cast

import numpy as np

from qap.market import AlignedBarSeries
from qap.portfolio import AssetId
from qap.relationship.observation import RelationshipDataError, validated_utc
from qap.relationship.ratio import aligned_asset_values

_MODEL_ID = "cross_sectional_relative_log_return"
_MODEL_VERSION = "1"


class CrossSectionalRelativeStatus(StrEnum):
    """Validity state for one pair-blind common-mode observation."""

    VALID = "valid"
    INSUFFICIENT_HISTORY = "insufficient_history"


@dataclass(frozen=True, slots=True)
class CrossSectionalRelativeObservation:
    """Trailing asset-relative log-return scores with explicit degeneracy metadata."""

    as_of: datetime
    model_id: str
    model_version: str
    assets: tuple[AssetId, ...]
    window_returns: int
    coverage_returns: int
    status: CrossSectionalRelativeStatus
    pair_independence_limited: bool
    common_mode_returns: tuple[float, ...]
    scores: Mapping[AssetId, float]
    input_fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "scores", MappingProxyType(dict(self.scores)))


def _validated_basket(basket: Iterable[AssetId]) -> tuple[AssetId, ...]:
    try:
        copied = tuple(basket)
    except TypeError as exc:
        raise TypeError("basket must be iterable") from exc
    if len(copied) < 2:
        raise ValueError("cross-sectional basket must contain at least two assets")
    if any(not isinstance(cast(object, asset), AssetId) for asset in copied):
        raise TypeError("basket members must be AssetId values")
    if len(set(copied)) != len(copied):
        raise ValueError("cross-sectional basket assets must be unique")
    return tuple(sorted(copied))


def _validated_window(value: int) -> int:
    raw = cast(object, value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError("window_returns must be an integer")
    if value <= 0:
        raise ValueError("window_returns must be positive")
    return value


def _input_fingerprint(
    aligned: AlignedBarSeries,
    *,
    assets: tuple[AssetId, ...],
    visible_timestamps: tuple[datetime, ...],
    prices: Mapping[AssetId, tuple[float, ...]],
) -> str:
    digest = sha256()
    digest.update(b"qap.relationship.cross-sectional-relative-input.v1\0")
    digest.update(aligned.interval.label.encode("utf-8"))
    digest.update(b"\0")
    for asset in assets:
        digest.update(asset.key.encode("utf-8"))
        digest.update(b"\0")
    for position, timestamp in enumerate(visible_timestamps):
        digest.update(timestamp.isoformat().encode("utf-8"))
        digest.update(b"\0")
        for asset in assets:
            digest.update(prices[asset][position].hex().encode("ascii"))
            digest.update(b"\0")
    return digest.hexdigest()


def cross_sectional_relative_observation(
    aligned: AlignedBarSeries,
    *,
    basket: Iterable[AssetId],
    window_returns: int,
    as_of: datetime,
) -> CrossSectionalRelativeObservation:
    """Compute trailing pair-blind relative log returns from completed bars only."""

    assets = _validated_basket(basket)
    window = _validated_window(window_returns)
    validated_time = validated_utc(as_of, field="as_of")
    latest_completion = aligned.timestamps[-1] + aligned.interval.duration
    if validated_time > latest_completion:
        raise RelationshipDataError("as_of cannot exceed the aligned data window")

    visible_timestamps = tuple(
        timestamp
        for timestamp in aligned.timestamps
        if timestamp + aligned.interval.duration <= validated_time
    )
    visible_count = len(visible_timestamps)
    prices: dict[AssetId, tuple[float, ...]] = {}
    references: set[AssetId] = set()
    for asset in assets:
        values, reference, _identity = aligned_asset_values(aligned, asset)
        references.add(reference)
        prices[asset] = tuple(float(value) for value in values[:visible_count])
    if len(references) != 1:
        raise RelationshipDataError(
            "cross-sectional basket assets must share one common reference coordinate"
        )

    coverage = min(max(visible_count - 1, 0), window)
    fingerprint = _input_fingerprint(
        aligned,
        assets=assets,
        visible_timestamps=visible_timestamps,
        prices=prices,
    )
    limited = len(assets) == 2
    if coverage < window:
        return CrossSectionalRelativeObservation(
            as_of=validated_time,
            model_id=_MODEL_ID,
            model_version=_MODEL_VERSION,
            assets=assets,
            window_returns=window,
            coverage_returns=coverage,
            status=CrossSectionalRelativeStatus.INSUFFICIENT_HISTORY,
            pair_independence_limited=limited,
            common_mode_returns=(),
            scores={},
            input_fingerprint=fingerprint,
        )

    price_matrix = np.asarray([prices[asset] for asset in assets], dtype=np.float64)
    log_returns = np.diff(np.log(price_matrix), axis=1)[:, -window:]
    common_mode = np.mean(log_returns, axis=0)
    relative = log_returns - common_mode
    raw_scores = np.sum(relative, axis=1)
    if not np.isfinite(raw_scores).all() or not np.isfinite(common_mode).all():
        raise RelationshipDataError(
            "cross-sectional relative returns must remain finite"
        )
    scores = {
        asset: float(score) for asset, score in zip(assets, raw_scores, strict=True)
    }
    return CrossSectionalRelativeObservation(
        as_of=validated_time,
        model_id=_MODEL_ID,
        model_version=_MODEL_VERSION,
        assets=assets,
        window_returns=window,
        coverage_returns=window,
        status=CrossSectionalRelativeStatus.VALID,
        pair_independence_limited=limited,
        common_mode_returns=tuple(float(value) for value in common_mode),
        scores=scores,
        input_fingerprint=fingerprint,
    )


__all__ = [
    "CrossSectionalRelativeObservation",
    "CrossSectionalRelativeStatus",
    "cross_sectional_relative_observation",
]
