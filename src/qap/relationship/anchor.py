"""Common-reference anchor lenses with explicit reduced identities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import cast

import numpy as np
from numpy.typing import NDArray

from qap.market import AlignedBarSeries, BarInterval
from qap.portfolio import AssetId, PairId, PairOrientation
from qap.relationship.observation import (
    EvidenceReciprocity,
    FitReciprocity,
    RelationshipDataError,
    validated_source_fingerprints,
    validated_timestamps,
    validated_utc,
)
from qap.relationship.ratio import (
    aligned_asset_values,
    frozen_array,
    log_ratio,
    raw_ratio,
    source_fingerprint_for_asset,
)


class AnchorReduction(StrEnum):
    NONE = "none"
    ANCHOR_IS_BASE = "anchor_is_base"
    ANCHOR_IS_QUOTE = "anchor_is_quote"


@dataclass(frozen=True, slots=True, init=False)
class AnchorLens:
    pair_id: PairId
    orientation: PairOrientation
    anchor: AssetId
    interval: BarInterval
    timestamps: tuple[datetime, ...]
    as_of: datetime
    base_source_fingerprint: str
    quote_source_fingerprint: str
    anchor_source_fingerprint: str | None
    fit_reciprocity: FitReciprocity
    evidence_reciprocity: EvidenceReciprocity
    reduction: AnchorReduction
    identity_values: Mapping[str, float]
    pair_ratio: NDArray[np.float64]
    pair_log_ratio: NDArray[np.float64]
    base_to_anchor: NDArray[np.float64]
    quote_to_anchor: NDArray[np.float64]
    base_to_anchor_log: NDArray[np.float64]
    quote_to_anchor_log: NDArray[np.float64]
    max_ratio_decomposition_error: float
    max_log_decomposition_error: float

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("use build_anchor_lens()")

    def __post_init__(self) -> None:
        if self.orientation.pair_id != self.pair_id:
            raise ValueError("orientation must match pair_id")
        if not isinstance(cast(object, self.reduction), AnchorReduction):
            raise TypeError("reduction must be AnchorReduction")
        if self.max_ratio_decomposition_error < 0 or not np.isfinite(
            self.max_ratio_decomposition_error
        ):
            raise ValueError("max_ratio_decomposition_error must be finite and >= 0")
        if self.max_log_decomposition_error < 0 or not np.isfinite(
            self.max_log_decomposition_error
        ):
            raise ValueError("max_log_decomposition_error must be finite and >= 0")
        object.__setattr__(
            self,
            "identity_values",
            MappingProxyType(dict(self.identity_values)),
        )
        for field_name in (
            "pair_ratio",
            "pair_log_ratio",
            "base_to_anchor",
            "quote_to_anchor",
            "base_to_anchor_log",
            "quote_to_anchor_log",
        ):
            object.__setattr__(
                self,
                field_name,
                frozen_array(getattr(self, field_name)),
            )

    @property
    def descriptive_only(self) -> bool:
        return True


def _anchor_values(
    aligned: AlignedBarSeries,
    *,
    orientation: PairOrientation,
    anchor: AssetId,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    AssetId,
    bool,
    bool,
    bool,
]:
    base_values, base_reference, base_identity = aligned_asset_values(
        aligned,
        orientation.base,
    )
    quote_values, quote_reference, quote_identity = aligned_asset_values(
        aligned,
        orientation.quote,
    )
    if base_reference != quote_reference:
        raise RelationshipDataError(
            "oriented legs must share one common quote/reference coordinate"
        )
    anchor_values, anchor_reference, anchor_identity = aligned_asset_values(
        aligned,
        anchor,
    )
    if anchor_reference != base_reference:
        raise RelationshipDataError(
            "anchor path must use the same common quote/reference coordinate"
        )
    return (
        base_values,
        quote_values,
        anchor_values,
        base_reference,
        base_identity,
        quote_identity,
        anchor_identity,
    )


def _fingerprints(
    *,
    orientation: PairOrientation,
    anchor: AssetId,
    common_quote: AssetId,
    source_fingerprints: Mapping[AssetId, str],
    base_identity: bool,
    quote_identity: bool,
    anchor_identity: bool,
) -> tuple[str, str, str | None]:
    fingerprints = validated_source_fingerprints(source_fingerprints)
    base_fingerprint = source_fingerprint_for_asset(
        fingerprints,
        asset=orientation.base,
        identity_coordinate=base_identity,
    )
    quote_fingerprint = source_fingerprint_for_asset(
        fingerprints,
        asset=orientation.quote,
        identity_coordinate=quote_identity,
    )
    if anchor == orientation.base:
        return base_fingerprint, quote_fingerprint, base_fingerprint
    if anchor == orientation.quote:
        return base_fingerprint, quote_fingerprint, quote_fingerprint
    if anchor == common_quote and anchor_identity:
        return (
            base_fingerprint,
            quote_fingerprint,
            source_fingerprint_for_asset(
                fingerprints,
                asset=anchor,
                identity_coordinate=True,
            ),
        )
    anchor_fingerprint = source_fingerprint_for_asset(
        fingerprints,
        asset=anchor,
        identity_coordinate=anchor_identity,
    )
    return base_fingerprint, quote_fingerprint, anchor_fingerprint


def _reduction(
    *,
    orientation: PairOrientation,
    anchor: AssetId,
) -> tuple[AnchorReduction, Mapping[str, float]]:
    if anchor == orientation.base:
        return (
            AnchorReduction.ANCHOR_IS_BASE,
            MappingProxyType({f"{orientation.base.key}/{anchor.key}": 1.0}),
        )
    if anchor == orientation.quote:
        return (
            AnchorReduction.ANCHOR_IS_QUOTE,
            MappingProxyType({f"{orientation.quote.key}/{anchor.key}": 1.0}),
        )
    return AnchorReduction.NONE, MappingProxyType({})


def build_anchor_lens(
    aligned: AlignedBarSeries,
    *,
    orientation: PairOrientation,
    anchor: AssetId,
    source_fingerprints: Mapping[AssetId, str],
    as_of: datetime,
) -> AnchorLens:
    """Build pair and anchor paths from one admitted aligned close-price window."""

    timestamps = validated_timestamps(aligned.timestamps, interval=aligned.interval)
    validated_time = validated_utc(as_of, field="as_of")
    window_end_exclusive = timestamps[-1] + aligned.interval.duration
    if validated_time < window_end_exclusive:
        raise RelationshipDataError("as_of must include the entire completed window")
    (
        base_values,
        quote_values,
        anchor_values,
        common_quote,
        base_identity,
        quote_identity,
        anchor_identity,
    ) = _anchor_values(
        aligned,
        orientation=orientation,
        anchor=anchor,
    )
    base_fingerprint, quote_fingerprint, anchor_fingerprint = _fingerprints(
        orientation=orientation,
        anchor=anchor,
        common_quote=common_quote,
        source_fingerprints=source_fingerprints,
        base_identity=base_identity,
        quote_identity=quote_identity,
        anchor_identity=anchor_identity,
    )

    pair = raw_ratio(base_values, quote_values)
    pair_log = log_ratio(base_values, quote_values)
    base_anchor = raw_ratio(base_values, anchor_values)
    quote_anchor = raw_ratio(quote_values, anchor_values)
    base_anchor_log = log_ratio(base_values, anchor_values)
    quote_anchor_log = log_ratio(quote_values, anchor_values)
    reconstructed_ratio = raw_ratio(base_anchor, quote_anchor)
    reconstructed_log = base_anchor_log - quote_anchor_log
    ratio_error = float(np.max(np.abs(pair - reconstructed_ratio)))
    log_error = float(np.max(np.abs(pair_log - reconstructed_log)))
    ratio_ok = np.allclose(pair, reconstructed_ratio, rtol=1e-12, atol=1e-12)
    log_ok = np.allclose(pair_log, reconstructed_log, rtol=1e-12, atol=1e-12)
    if not ratio_ok or not log_ok:
        raise RelationshipDataError(
            "anchor decomposition tolerance exceeded; evidence is not aligned"
        )
    reduction, identity_values = _reduction(orientation=orientation, anchor=anchor)

    lens = object.__new__(AnchorLens)
    for field_name, value in {
        "pair_id": orientation.pair_id,
        "orientation": orientation,
        "anchor": anchor,
        "interval": aligned.interval,
        "timestamps": timestamps,
        "as_of": validated_time,
        "base_source_fingerprint": base_fingerprint,
        "quote_source_fingerprint": quote_fingerprint,
        "anchor_source_fingerprint": anchor_fingerprint,
        "fit_reciprocity": FitReciprocity.EXACT_TRANSFORM,
        "evidence_reciprocity": EvidenceReciprocity.EXACT_TRANSFORM,
        "reduction": reduction,
        "identity_values": identity_values,
        "pair_ratio": pair,
        "pair_log_ratio": pair_log,
        "base_to_anchor": base_anchor,
        "quote_to_anchor": quote_anchor,
        "base_to_anchor_log": base_anchor_log,
        "quote_to_anchor_log": quote_anchor_log,
        "max_ratio_decomposition_error": ratio_error,
        "max_log_decomposition_error": log_error,
    }.items():
        object.__setattr__(lens, field_name, value)
    lens.__post_init__()
    return lens
