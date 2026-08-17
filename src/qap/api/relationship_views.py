"""Descriptive pair HTTP projections over fingerprint-admitted run data."""

from datetime import datetime
from pathlib import Path
from typing import cast

from qap.api.errors import (
    anchor_unavailable,
    invalid_pair_orientation,
    market_data_unavailable,
)
from qap.api.schemas import (
    AnchorLensDto,
    FloatPointDto,
    PairSeriesDto,
    RebalanceMarkerDto,
)
from qap.experiment import LoadedRunArtifacts, load_experiment_data
from qap.market import AlignedBarSeries
from qap.portfolio import AssetId, PairOrientation
from qap.relationship import (
    NormalizationScale,
    RelationshipDataError,
    build_anchor_lens,
    build_log_ratio_series,
    build_normalized_path,
    build_ratio_series,
)


def pair_series(
    loaded: LoadedRunArtifacts,
    *,
    market_data_root: Path | None,
    asset_x: str,
    asset_y: str,
    orientation: str | None,
) -> PairSeriesDto:
    requested = _pair_orientation(
        asset_x=asset_x,
        asset_y=asset_y,
        orientation=orientation,
    )
    aligned, source_fingerprints = _relationship_inputs(
        loaded,
        market_data_root=market_data_root,
    )
    try:
        ratio = build_ratio_series(
            aligned,
            orientation=requested,
            source_fingerprints=source_fingerprints,
            as_of=loaded.manifest.data_window.end,
        )
        log_ratio = build_log_ratio_series(
            aligned,
            orientation=requested,
            source_fingerprints=source_fingerprints,
            as_of=loaded.manifest.data_window.end,
        )
        normalized_base = build_normalized_path(
            aligned,
            asset=requested.base,
            scale=NormalizationScale.ONE,
            source_fingerprint=source_fingerprints[requested.base],
            as_of=loaded.manifest.data_window.end,
        )
        normalized_quote = build_normalized_path(
            aligned,
            asset=requested.quote,
            scale=NormalizationScale.ONE,
            source_fingerprint=source_fingerprints[requested.quote],
            as_of=loaded.manifest.data_window.end,
        )
    except (KeyError, RelationshipDataError) as exc:
        raise market_data_unavailable(loaded.provenance.run_id) from exc

    pair_id = requested.pair_id
    return PairSeriesDto(
        run_id=loaded.provenance.run_id,
        canonical_pair=(pair_id.first.key, pair_id.second.key),
        requested_orientation=f"{requested.base.key}/{requested.quote.key}",
        interval=aligned.interval.label,
        base_source_fingerprint=ratio.base_source_fingerprint,
        quote_source_fingerprint=ratio.quote_source_fingerprint,
        fit_reciprocity=ratio.fit_reciprocity.value,
        evidence_reciprocity=ratio.evidence_reciprocity.value,
        ratio=_float_points(ratio.timestamps, ratio.values),
        log_ratio=_float_points(log_ratio.timestamps, log_ratio.values),
        normalized_base=_float_points(
            normalized_base.timestamps,
            normalized_base.values,
        ),
        normalized_quote=_float_points(
            normalized_quote.timestamps,
            normalized_quote.values,
        ),
        rebalance_markers=_rebalance_markers(loaded),
        descriptive_only=True,
    )


def anchor_lens(
    loaded: LoadedRunArtifacts,
    *,
    market_data_root: Path | None,
    asset_x: str,
    asset_y: str,
    anchor: str,
) -> AnchorLensDto:
    requested = _pair_orientation(
        asset_x=asset_x,
        asset_y=asset_y,
        orientation=None,
    )
    aligned, source_fingerprints = _relationship_inputs(
        loaded,
        market_data_root=market_data_root,
    )
    try:
        anchor_asset = loaded.manifest.asset(anchor)
    except (KeyError, TypeError, ValueError) as exc:
        raise anchor_unavailable(
            run_id=loaded.provenance.run_id,
            anchor=anchor.strip().upper(),
        ) from exc
    try:
        lens = build_anchor_lens(
            aligned,
            orientation=requested,
            anchor=anchor_asset,
            source_fingerprints=source_fingerprints,
            as_of=loaded.manifest.data_window.end,
        )
    except (KeyError, RelationshipDataError) as exc:
        raise anchor_unavailable(
            run_id=loaded.provenance.run_id,
            anchor=anchor_asset.key,
        ) from exc

    pair_id = requested.pair_id
    return AnchorLensDto(
        run_id=loaded.provenance.run_id,
        canonical_pair=(pair_id.first.key, pair_id.second.key),
        requested_orientation=f"{requested.base.key}/{requested.quote.key}",
        anchor=anchor_asset.key,
        interval=aligned.interval.label,
        base_source_fingerprint=lens.base_source_fingerprint,
        quote_source_fingerprint=lens.quote_source_fingerprint,
        anchor_source_fingerprint=lens.anchor_source_fingerprint,
        fit_reciprocity=lens.fit_reciprocity.value,
        evidence_reciprocity=lens.evidence_reciprocity.value,
        reduction=lens.reduction.value,
        pair_ratio=_float_points(lens.timestamps, lens.pair_ratio),
        pair_log_ratio=_float_points(lens.timestamps, lens.pair_log_ratio),
        base_to_anchor=_float_points(lens.timestamps, lens.base_to_anchor),
        quote_to_anchor=_float_points(lens.timestamps, lens.quote_to_anchor),
        base_to_anchor_log=_float_points(lens.timestamps, lens.base_to_anchor_log),
        quote_to_anchor_log=_float_points(lens.timestamps, lens.quote_to_anchor_log),
        max_ratio_decomposition_error=lens.max_ratio_decomposition_error,
        max_log_decomposition_error=lens.max_log_decomposition_error,
        descriptive_only=lens.descriptive_only,
    )


def _rebalance_markers(
    loaded: LoadedRunArtifacts,
) -> tuple[RebalanceMarkerDto, ...]:
    events = tuple(loaded.events)
    strategy_events = tuple(
        event for event in events if event.get("role") == "strategy"
    )
    markers: list[RebalanceMarkerDto] = []
    for decision in strategy_events:
        if decision.get("event_type") != "policy_decision":
            continue
        decision_index = decision.get("decision_index")
        related = tuple(
            event
            for event in strategy_events
            if event.get("decision_index") == decision_index
        )
        rebalance = next(
            (event for event in related if event.get("event_type") == "rebalance"),
            None,
        )
        if rebalance is None:
            continue
        fill = next(
            (event for event in related if event.get("event_type") == "fill"),
            None,
        )
        decision_payload = decision.get("payload")
        rebalance_payload = rebalance.get("payload")
        if not isinstance(decision_payload, dict) or not isinstance(
            rebalance_payload, dict
        ):
            raise ValueError("event marker payload must be an object")
        typed_decision_payload = cast(dict[str, object], decision_payload)
        typed_rebalance_payload = cast(dict[str, object], rebalance_payload)
        raw_time = decision.get("event_time")
        if not isinstance(raw_time, str):
            raise ValueError("event marker time must be an ISO-8601 string")
        timestamp = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        fill_id: str | None = None
        if fill is not None:
            fill_payload = fill.get("payload")
            if not isinstance(fill_payload, dict):
                raise ValueError("fill marker payload must be an object")
            typed_fill_payload = cast(dict[str, object], fill_payload)
            fill_id = str(typed_fill_payload["fill_id"])
        markers.append(
            RebalanceMarkerDto(
                timestamp=timestamp,
                decision_id=str(typed_decision_payload["decision_id"]),
                selected=bool(typed_rebalance_payload.get("selected")),
                executed=fill is not None,
                fill_id=fill_id,
            )
        )
    return tuple(markers)


def _relationship_inputs(
    loaded: LoadedRunArtifacts,
    *,
    market_data_root: Path | None,
) -> tuple[AlignedBarSeries, dict[AssetId, str]]:
    if market_data_root is None:
        raise market_data_unavailable(loaded.provenance.run_id)
    try:
        admitted = load_experiment_data(
            loaded.manifest,
            data_root=market_data_root,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        raise market_data_unavailable(loaded.provenance.run_id) from exc

    fingerprints_by_dataset = {
        item.dataset_id: item.fingerprint for item in admitted.data_fingerprints
    }
    instruments = loaded.manifest.instruments_by_id()
    source_fingerprints: dict[AssetId, str] = {}
    for source in loaded.manifest.data_sources:
        asset = instruments[source.instrument_id].base
        fingerprint = fingerprints_by_dataset[source.dataset_id]
        existing = source_fingerprints.get(asset)
        if existing is not None and existing != fingerprint:
            raise market_data_unavailable(loaded.provenance.run_id)
        source_fingerprints[asset] = fingerprint
    return admitted.aligned, source_fingerprints


def _pair_orientation(
    *,
    asset_x: str,
    asset_y: str,
    orientation: str | None,
) -> PairOrientation:
    try:
        x = AssetId(asset_x)
        y = AssetId(asset_y)
    except (TypeError, ValueError) as exc:
        requested = "" if orientation is None else orientation
        raise invalid_pair_orientation(
            asset_x=asset_x,
            asset_y=asset_y,
            orientation=requested,
        ) from exc
    raw = f"{x.key}/{y.key}" if orientation is None else orientation.strip().upper()
    parts = raw.split("/")
    if len(parts) != 2:
        raise invalid_pair_orientation(
            asset_x=x.key,
            asset_y=y.key,
            orientation=raw,
        )
    try:
        requested = PairOrientation(base=AssetId(parts[0]), quote=AssetId(parts[1]))
        path_pair = PairOrientation(base=x, quote=y).pair_id
    except (TypeError, ValueError) as exc:
        raise invalid_pair_orientation(
            asset_x=x.key,
            asset_y=y.key,
            orientation=raw,
        ) from exc
    if requested.pair_id != path_pair:
        raise invalid_pair_orientation(
            asset_x=x.key,
            asset_y=y.key,
            orientation=raw,
        )
    return requested


def _float_points(
    timestamps: tuple[datetime, ...],
    values: tuple[float, ...],
) -> tuple[FloatPointDto, ...]:
    if len(timestamps) != len(values):
        raise ValueError("relationship timestamps and values must align")
    return tuple(
        FloatPointDto(timestamp=timestamp, value=value)
        for timestamp, value in zip(timestamps, values, strict=True)
    )


__all__ = ["anchor_lens", "pair_series"]
