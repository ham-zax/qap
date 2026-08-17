"""Transparent anchor decomposition over one admitted aligned dataset."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

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
from qap.relationship.ratio import aligned_leg, log_ratio, positive_vector, raw_ratio

_DECOMPOSITION_RTOL = 1e-12
_DECOMPOSITION_ATOL = 1e-12


class AnchorReduction(StrEnum):
    """Whether an anchor lens has three distinct assets or a reduced identity."""

    NONE = "none"
    ANCHOR_IS_BASE = "anchor_is_base"
    ANCHOR_IS_QUOTE = "anchor_is_quote"


@dataclass(frozen=True, slots=True, init=False)
class AnchorLens:
    """Synchronized descriptive X/Y, X/A, and Y/A evidence."""

    pair_id: PairId
    orientation: PairOrientation
    anchor: AssetId
    interval: BarInterval
    timestamps: tuple[datetime, ...]
    window_start: datetime
    window_end_exclusive: datetime
    as_of: datetime
    base_source_fingerprint: str
    quote_source_fingerprint: str
    anchor_source_fingerprint: str | None
    fit_reciprocity: FitReciprocity
    evidence_reciprocity: EvidenceReciprocity
    reduction: AnchorReduction
    pair_ratio: tuple[float, ...]
    pair_log_ratio: tuple[float, ...]
    base_to_anchor: tuple[float, ...]
    quote_to_anchor: tuple[float, ...]
    base_to_anchor_log: tuple[float, ...]
    quote_to_anchor_log: tuple[float, ...]
    max_ratio_decomposition_error: float
    max_log_decomposition_error: float
    descriptive_only: bool

    def __init__(self) -> None:
        raise TypeError("use build_anchor_lens()")


def _tuple(array: NDArray[np.float64]) -> tuple[float, ...]:
    return tuple(float(value) for value in array)


def _fingerprints(
    source_fingerprints: Mapping[AssetId, str],
    *,
    orientation: PairOrientation,
    anchor: AssetId,
    common_quote: AssetId,
) -> tuple[str, str, str | None]:
    fingerprints = validated_source_fingerprints(source_fingerprints)
    try:
        base_fingerprint = fingerprints[orientation.base]
        quote_fingerprint = fingerprints[orientation.quote]
    except KeyError as exc:
        missing = exc.args[0]
        missing_key = missing.key if isinstance(missing, AssetId) else str(missing)
        raise RelationshipDataError(
            f"missing source fingerprint for {missing_key}"
        ) from exc
    if anchor == orientation.base:
        return base_fingerprint, quote_fingerprint, base_fingerprint
    if anchor == orientation.quote:
        return base_fingerprint, quote_fingerprint, quote_fingerprint
    if anchor == common_quote:
        return base_fingerprint, quote_fingerprint, None
    try:
        anchor_fingerprint = fingerprints[anchor]
    except KeyError as exc:
        raise RelationshipDataError(
            f"missing source fingerprint for {anchor.key}"
        ) from exc
    return base_fingerprint, quote_fingerprint, anchor_fingerprint


def _anchor_values(
    aligned: AlignedBarSeries,
    *,
    orientation: PairOrientation,
    anchor: AssetId,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    AnchorReduction,
    AssetId,
]:
    base_leg = aligned_leg(aligned, orientation.base)
    quote_leg = aligned_leg(aligned, orientation.quote)
    common_quote = base_leg.instrument.quote
    if quote_leg.instrument.quote != common_quote:
        raise RelationshipDataError(
            "oriented legs must share one common quote/reference coordinate"
        )

    base = positive_vector(base_leg.closes, field="base prices")
    quote = positive_vector(quote_leg.closes, field="quote prices")
    if anchor == orientation.base:
        return base, quote, base, AnchorReduction.ANCHOR_IS_BASE, common_quote
    if anchor == orientation.quote:
        return base, quote, quote, AnchorReduction.ANCHOR_IS_QUOTE, common_quote
    if anchor == common_quote:
        return (
            base,
            quote,
            np.ones(base.shape, dtype=np.float64),
            AnchorReduction.NONE,
            common_quote,
        )

    anchor_leg = aligned_leg(aligned, anchor)
    if anchor_leg.instrument.quote != common_quote:
        raise RelationshipDataError(
            "anchor leg must share the pair's common quote/reference coordinate"
        )
    anchor_values = positive_vector(anchor_leg.closes, field="anchor prices")
    return base, quote, anchor_values, AnchorReduction.NONE, common_quote


def build_anchor_lens(
    aligned: AlignedBarSeries,
    *,
    orientation: PairOrientation,
    anchor: AssetId,
    source_fingerprints: Mapping[AssetId, str],
    as_of: datetime,
) -> AnchorLens:
    """Build and verify ratio/log anchor identities on one aligned dataset."""

    timestamps = validated_timestamps(aligned.timestamps, interval=aligned.interval)
    normalized_as_of = validated_utc(as_of, field="as_of")
    window_end_exclusive = timestamps[-1] + aligned.interval.duration
    if normalized_as_of < window_end_exclusive:
        raise RelationshipDataError("as_of must include the entire completed window")
    base, quote, anchor_values, reduction, common_quote = _anchor_values(
        aligned,
        orientation=orientation,
        anchor=anchor,
    )
    base_fingerprint, quote_fingerprint, anchor_fingerprint = _fingerprints(
        source_fingerprints,
        orientation=orientation,
        anchor=anchor,
        common_quote=common_quote,
    )

    direct = raw_ratio(base, quote)
    direct_log = log_ratio(base, quote)
    base_anchor = raw_ratio(base, anchor_values)
    quote_anchor = raw_ratio(quote, anchor_values)
    base_anchor_log = log_ratio(base, anchor_values)
    quote_anchor_log = log_ratio(quote, anchor_values)
    reconstructed = raw_ratio(base_anchor, quote_anchor)
    reconstructed_log = base_anchor_log - quote_anchor_log
    ratio_error = float(np.max(np.abs(direct - reconstructed)))
    log_error = float(np.max(np.abs(direct_log - reconstructed_log)))
    if not np.allclose(
        direct,
        reconstructed,
        rtol=_DECOMPOSITION_RTOL,
        atol=_DECOMPOSITION_ATOL,
    ):
        raise RelationshipDataError(
            "anchor ratio decomposition exceeded the declared tolerance"
        )
    if not np.allclose(
        direct_log,
        reconstructed_log,
        rtol=_DECOMPOSITION_RTOL,
        atol=_DECOMPOSITION_ATOL,
    ):
        raise RelationshipDataError(
            "anchor log decomposition exceeded the declared tolerance"
        )

    result = object.__new__(AnchorLens)
    object.__setattr__(result, "pair_id", orientation.pair_id)
    object.__setattr__(result, "orientation", orientation)
    object.__setattr__(result, "anchor", anchor)
    object.__setattr__(result, "interval", aligned.interval)
    object.__setattr__(result, "timestamps", timestamps)
    object.__setattr__(result, "window_start", timestamps[0])
    object.__setattr__(result, "window_end_exclusive", window_end_exclusive)
    object.__setattr__(result, "as_of", normalized_as_of)
    object.__setattr__(result, "base_source_fingerprint", base_fingerprint)
    object.__setattr__(result, "quote_source_fingerprint", quote_fingerprint)
    object.__setattr__(result, "anchor_source_fingerprint", anchor_fingerprint)
    object.__setattr__(result, "fit_reciprocity", FitReciprocity.EXACT_TRANSFORM)
    object.__setattr__(
        result,
        "evidence_reciprocity",
        EvidenceReciprocity.EXACT_TRANSFORM,
    )
    object.__setattr__(result, "reduction", reduction)
    object.__setattr__(result, "pair_ratio", _tuple(direct))
    object.__setattr__(result, "pair_log_ratio", _tuple(direct_log))
    object.__setattr__(result, "base_to_anchor", _tuple(base_anchor))
    object.__setattr__(result, "quote_to_anchor", _tuple(quote_anchor))
    object.__setattr__(result, "base_to_anchor_log", _tuple(base_anchor_log))
    object.__setattr__(result, "quote_to_anchor_log", _tuple(quote_anchor_log))
    object.__setattr__(result, "max_ratio_decomposition_error", ratio_error)
    object.__setattr__(result, "max_log_decomposition_error", log_error)
    object.__setattr__(result, "descriptive_only", True)
    return result
