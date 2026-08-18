"""Frozen Scanner-V1 Slice-1 trial enumeration and semantic identities."""

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import cast

from qap.market import BarInterval
from qap.portfolio import AssetId, PairOrientation
from qap.scanner.graph import NeighborRecord, SsdGraph
from qap.scanner.protocol import (
    SCANNER_V1_SLICE1,
    ScannerHorizon,
    ScannerProtocol,
    TemplateId,
    protocol_identity,
)
from qap.scanner.slices import EvaluatedSeries


class ScannerModelFamily(StrEnum):
    LOG_RATIO_MEAN_REVERSION = "log_ratio_mean_reversion"
    RESIDUAL_MEAN_REVERSION = "residual_mean_reversion"


@dataclass(frozen=True, slots=True)
class ScannerTrial:
    candidate_id: str
    scan_id: str
    venue: str
    horizon: ScannerHorizon
    universe_snapshot_id: str
    pair_id: str
    asset_a: AssetId
    asset_b: AssetId
    orientation: PairOrientation
    resolution: BarInterval
    model_family: ScannerModelFamily
    template_id: TemplateId
    window_bars: int
    minimum_observations: int
    source_artifact_fingerprints: tuple[str, str]
    selection_slice_fingerprints: tuple[str, str]
    evidence_dataset_ids: tuple[str, str]
    automatic_neighbor_selected: bool
    manual_pinned: bool
    preference_sign: int = -1


def preference_score(z_score: float) -> float:
    """Convert oriented mean-reversion z-score to the frozen tilt preference sign."""

    if not isinstance(cast(object, z_score), float):
        if isinstance(cast(object, z_score), int) and not isinstance(
            cast(object, z_score), bool
        ):
            z_score = float(z_score)
        else:
            raise TypeError("z_score must be numeric")
    if not math.isfinite(z_score):
        raise ValueError("z_score must be finite")
    return -z_score


def _series_for(
    model_series_by_asset: Mapping[tuple[str, str], EvaluatedSeries],
    *,
    asset: AssetId,
    resolution: BarInterval,
) -> EvaluatedSeries:
    key = (asset.key, resolution.label)
    try:
        series = model_series_by_asset[key]
    except KeyError as exc:
        raise ValueError(
            f"missing model-resolution slice for {asset.key}/{resolution.label}"
        ) from exc
    if not isinstance(cast(object, series), EvaluatedSeries):
        raise TypeError("model_series_by_asset values must be EvaluatedSeries")
    return series


def _validated_model_pair(
    *,
    graph: SsdGraph,
    asset_a: AssetId,
    asset_b: AssetId,
    resolution: BarInterval,
    model_series_by_asset: Mapping[tuple[str, str], EvaluatedSeries],
    protocol: ScannerProtocol,
) -> tuple[EvaluatedSeries, EvaluatedSeries]:
    left = _series_for(
        model_series_by_asset,
        asset=asset_a,
        resolution=resolution,
    )
    right = _series_for(
        model_series_by_asset,
        asset=asset_b,
        resolution=resolution,
    )
    for asset, series in ((asset_a, left), (asset_b, right)):
        if series.instrument.base != asset:
            raise ValueError("model slice base asset does not match requested pair")
        if series.instrument.quote.key != protocol.quote_asset:
            raise ValueError("model slice must use the frozen scanner quote coordinate")
        if series.instrument.venue != graph.venue:
            raise ValueError("model slice must belong to the graph venue")
        if series.interval != resolution:
            raise ValueError("model slice interval does not match requested resolution")
        if series.bar_coverage < protocol.minimum_asset_coverage:
            raise ValueError("model slice coverage is below the frozen minimum")

    if (
        left.window_start != right.window_start
        or left.eligible_information_end != right.eligible_information_end
        or left.expected_bar_count != right.expected_bar_count
    ):
        raise ValueError("model slices must share one exact evaluation grid")

    horizon = protocol.horizon(ScannerHorizon(graph.horizon))
    maximum_template = max(duration for _template, duration in horizon.template_windows)
    if left.eligible_information_end - left.window_start < maximum_template:
        raise ValueError("model slice does not cover the maximum template warm-up")

    left_times = {bar.bar_end_exclusive for bar in left.bars}
    right_times = {bar.bar_end_exclusive for bar in right.bars}
    common_coverage = len(left_times & right_times) / left.expected_bar_count
    if common_coverage < protocol.minimum_pair_coverage:
        raise ValueError("model slice common coverage is below the frozen minimum")
    return left, right


def _candidate_id(
    *,
    graph: SsdGraph,
    record: NeighborRecord,
    orientation: PairOrientation,
    resolution: BarInterval,
    model_family: ScannerModelFamily,
    template_id: TemplateId,
    window_bars: int,
    minimum_observations: int,
    left: EvaluatedSeries,
    right: EvaluatedSeries,
    protocol: ScannerProtocol,
) -> str:
    payload = {
        "identity_version": "qap.scanner.candidate.v1",
        "scan_id": graph.scan_id,
        "protocol_identity": protocol_identity(protocol),
        "venue": graph.venue,
        "horizon": graph.horizon,
        "universe_snapshot_id": graph.universe_snapshot_id,
        "pair_id": record.pair_id,
        "orientation": [orientation.base.key, orientation.quote.key],
        "resolution": resolution.label,
        "model_family": model_family.value,
        "template_id": template_id.value,
        "window_bars": window_bars,
        "minimum_observations": minimum_observations,
        "source_artifact_fingerprints": [
            left.source_artifact_fingerprint,
            right.source_artifact_fingerprint,
        ],
        "selection_slice_fingerprints": [
            left.selection_slice_fingerprint,
            right.selection_slice_fingerprint,
        ],
        "evidence_dataset_ids": [left.dataset_id, right.dataset_id],
        "automatic_neighbor_selected": record.automatic_neighbor_selected,
        "manual_pinned": record.manual_pinned,
        "generator_rank_from_a": record.rank_from_a,
        "generator_rank_from_b": record.rank_from_b,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _trial(
    *,
    graph: SsdGraph,
    record: NeighborRecord,
    asset_a: AssetId,
    asset_b: AssetId,
    orientation: PairOrientation,
    resolution: BarInterval,
    model_family: ScannerModelFamily,
    template_id: TemplateId,
    left: EvaluatedSeries,
    right: EvaluatedSeries,
    protocol: ScannerProtocol,
) -> ScannerTrial:
    horizon = protocol.horizon(ScannerHorizon(graph.horizon))
    window_bars = horizon.window_bars(template_id, resolution)
    minimum_observations = max(
        3, math.ceil(window_bars * protocol.minimum_pair_coverage)
    )
    return ScannerTrial(
        candidate_id=_candidate_id(
            graph=graph,
            record=record,
            orientation=orientation,
            resolution=resolution,
            model_family=model_family,
            template_id=template_id,
            window_bars=window_bars,
            minimum_observations=minimum_observations,
            left=left,
            right=right,
            protocol=protocol,
        ),
        scan_id=graph.scan_id,
        venue=graph.venue,
        horizon=ScannerHorizon(graph.horizon),
        universe_snapshot_id=graph.universe_snapshot_id,
        pair_id=record.pair_id,
        asset_a=asset_a,
        asset_b=asset_b,
        orientation=orientation,
        resolution=resolution,
        model_family=model_family,
        template_id=template_id,
        window_bars=window_bars,
        minimum_observations=minimum_observations,
        source_artifact_fingerprints=(
            left.source_artifact_fingerprint,
            right.source_artifact_fingerprint,
        ),
        selection_slice_fingerprints=(
            left.selection_slice_fingerprint,
            right.selection_slice_fingerprint,
        ),
        evidence_dataset_ids=(left.dataset_id, right.dataset_id),
        automatic_neighbor_selected=record.automatic_neighbor_selected,
        manual_pinned=record.manual_pinned,
    )


def enumerate_fixed_trials(
    graph: SsdGraph,
    *,
    model_series_by_asset: Mapping[tuple[str, str], EvaluatedSeries],
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> tuple[ScannerTrial, ...]:
    """Enumerate the frozen ratio/residual template family for every retained pair."""

    if not isinstance(cast(object, graph), SsdGraph):
        raise TypeError("graph must be an SsdGraph")
    if not isinstance(cast(object, model_series_by_asset), Mapping):
        raise TypeError("model_series_by_asset must be a mapping")
    horizon = ScannerHorizon(graph.horizon)
    horizon_protocol = protocol.horizon(horizon)

    trials: list[ScannerTrial] = []
    for record in sorted(graph.records, key=lambda item: item.pair_id):
        if record.scan_id != graph.scan_id or record.venue != graph.venue:
            raise ValueError("neighbor record does not belong to the supplied graph")
        if record.horizon != graph.horizon:
            raise ValueError(
                "neighbor record horizon does not match the supplied graph"
            )
        asset_a = AssetId(record.asset_a)
        asset_b = AssetId(record.asset_b)
        canonical_orientation = PairOrientation(base=asset_a, quote=asset_b)
        reverse_orientation = canonical_orientation.inverted()

        for resolution in horizon_protocol.model_resolutions:
            left, right = _validated_model_pair(
                graph=graph,
                asset_a=asset_a,
                asset_b=asset_b,
                resolution=resolution,
                model_series_by_asset=model_series_by_asset,
                protocol=protocol,
            )
            for template_id, _duration in horizon_protocol.template_windows:
                trials.append(
                    _trial(
                        graph=graph,
                        record=record,
                        asset_a=asset_a,
                        asset_b=asset_b,
                        orientation=canonical_orientation,
                        resolution=resolution,
                        model_family=ScannerModelFamily.LOG_RATIO_MEAN_REVERSION,
                        template_id=template_id,
                        left=left,
                        right=right,
                        protocol=protocol,
                    )
                )
                for orientation in (canonical_orientation, reverse_orientation):
                    trials.append(
                        _trial(
                            graph=graph,
                            record=record,
                            asset_a=asset_a,
                            asset_b=asset_b,
                            orientation=orientation,
                            resolution=resolution,
                            model_family=ScannerModelFamily.RESIDUAL_MEAN_REVERSION,
                            template_id=template_id,
                            left=left,
                            right=right,
                            protocol=protocol,
                        )
                    )

    ordered = tuple(
        sorted(
            trials,
            key=lambda trial: (
                trial.venue,
                trial.pair_id,
                trial.resolution.label,
                trial.model_family.value,
                trial.template_id.value,
                trial.orientation.base.key,
                trial.orientation.quote.key,
            ),
        )
    )
    if len({trial.candidate_id for trial in ordered}) != len(ordered):
        raise ValueError("deterministic scanner candidate ID collision")
    return ordered


__all__ = [
    "ScannerModelFamily",
    "ScannerTrial",
    "enumerate_fixed_trials",
    "preference_score",
]
