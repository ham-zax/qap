# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Deterministic PyArrow serialization for Scanner-V1 Slice-1 records."""

from typing import Any

import pyarrow as pa

from qap.scanner.artifact_schemas import (
    ELIGIBLE_SCHEMA,
    GRAPH_METADATA_SCHEMA,
    NEIGHBOR_SCHEMA,
    PROMOTION_SCHEMA,
    SCOUT_SCHEMA,
)
from qap.scanner.graph import GraphMetadataRecord, NeighborRecord
from qap.scanner.promotion import PromotionRecord
from qap.scanner.scout import ScoutTrialRecord
from qap.scanner.universe import EligibleAssetRecord


def eligible_table(records: tuple[EligibleAssetRecord, ...]) -> Any:
    rows = [
        {
            "scan_id": item.scan_id,
            "venue": item.venue,
            "horizon": item.horizon.value,
            "asset_id": item.asset_id,
            "venue_symbol": item.venue_symbol,
            "eligibility_state": item.eligibility_state.value,
            "eligibility_reason": item.eligibility_reason,
            "lifecycle_evidence_refs": list(item.lifecycle_evidence_refs),
            "source_artifact_fingerprint": item.source_artifact_fingerprint,
            "selection_slice_fingerprint": item.selection_slice_fingerprint,
            "bar_coverage": item.bar_coverage,
            "longest_missing_run": item.longest_missing_run,
            "automatic_eligible": item.automatic_eligible,
            "forensic_research_allowed": item.forensic_research_allowed,
        }
        for item in sorted(
            records,
            key=lambda value: (value.venue, value.horizon.value, value.asset_id),
        )
    ]
    return pa.Table.from_pylist(rows, schema=ELIGIBLE_SCHEMA)


def graph_metadata_table(records: tuple[GraphMetadataRecord, ...]) -> Any:
    rows = [
        {
            "scan_id": item.scan_id,
            "venue": item.venue,
            "horizon": item.horizon,
            "universe_snapshot_id": item.universe_snapshot_id,
            "generator_version": item.generator_version,
            "graph_interval": item.graph_interval,
            "graph_window_seconds": item.graph_window_seconds,
            "neighbors_per_asset": item.neighbors_per_asset,
            "minimum_pair_coverage": item.minimum_pair_coverage,
            "maximum_missing_generator_bars": item.maximum_missing_generator_bars,
            "eligible_asset_count": item.eligible_asset_count,
            "total_valid_pair_comparisons": item.total_valid_pair_comparisons,
            "input_selection_slice_fingerprints": list(
                item.input_selection_slice_fingerprints
            ),
            "distance_digest": item.distance_digest,
        }
        for item in sorted(records, key=lambda value: (value.venue, value.horizon))
    ]
    return pa.Table.from_pylist(rows, schema=GRAPH_METADATA_SCHEMA)


def neighbor_table(records: tuple[NeighborRecord, ...]) -> Any:
    rows = [
        {
            "scan_id": item.scan_id,
            "venue": item.venue,
            "horizon": item.horizon,
            "pair_id": item.pair_id,
            "asset_a": item.asset_a,
            "asset_b": item.asset_b,
            "ssd_distance": item.ssd_distance,
            "rank_from_a": item.rank_from_a,
            "rank_from_b": item.rank_from_b,
            "selected_by_a": item.selected_by_a,
            "selected_by_b": item.selected_by_b,
            "automatic_neighbor_selected": item.automatic_neighbor_selected,
            "manual_pinned": item.manual_pinned,
        }
        for item in sorted(
            records, key=lambda value: (value.venue, value.horizon, value.pair_id)
        )
    ]
    return pa.Table.from_pylist(rows, schema=NEIGHBOR_SCHEMA)


def scout_table(records: tuple[ScoutTrialRecord, ...]) -> Any:
    rows = [
        {
            "candidate_id": item.candidate_id,
            "scan_id": item.scan_id,
            "venue": item.venue,
            "horizon": item.horizon,
            "pair_id": item.pair_id,
            "orientation": item.orientation,
            "resolution": item.resolution,
            "model_family": item.model_family,
            "template_id": item.template_id,
            "trial_status": item.trial_status.value,
            "failure_reason": item.failure_reason,
            "scout_relative_wealth_proxy": item.scout_relative_wealth_proxy,
            "scout_turnover_proxy": item.scout_turnover_proxy,
            "signal_count": item.signal_count,
            "automatic_neighbor_selected": item.automatic_neighbor_selected,
            "manual_pinned": item.manual_pinned,
        }
        for item in sorted(records, key=lambda value: value.candidate_id)
    ]
    return pa.Table.from_pylist(rows, schema=SCOUT_SCHEMA)


def promotion_table(records: tuple[PromotionRecord, ...]) -> Any:
    rows = [
        {
            "candidate_id": item.candidate_id,
            "promotion_rank": item.promotion_rank,
            "promotion_status": item.promotion_status.value,
            "budget_reason": item.budget_reason,
            "automatic_selected": item.automatic_selected,
            "manual_selected": item.manual_selected,
            "selected_for_replay": item.selected_for_replay,
            "direct_execution_instrument_id": item.direct_execution_instrument_id,
            "deep_replay_run_id": item.deep_replay_run_id,
            "deep_replay_status": item.deep_replay_status,
            "economic_gate_status": item.economic_gate_status,
        }
        for item in sorted(records, key=lambda value: value.candidate_id)
    ]
    return pa.Table.from_pylist(rows, schema=PROMOTION_SCHEMA)


__all__ = [
    "eligible_table",
    "graph_metadata_table",
    "neighbor_table",
    "promotion_table",
    "scout_table",
]
