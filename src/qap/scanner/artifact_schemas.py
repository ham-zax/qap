# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Frozen PyArrow table schemas for Scanner-V1 Slice-1 artifacts."""

from typing import Any

import pyarrow as pa

ELIGIBLE_SCHEMA = pa.schema(
    [
        ("scan_id", pa.string()),
        ("venue", pa.string()),
        ("horizon", pa.string()),
        ("asset_id", pa.string()),
        ("venue_symbol", pa.string()),
        ("eligibility_state", pa.string()),
        ("eligibility_reason", pa.string()),
        ("lifecycle_evidence_refs", pa.list_(pa.string())),
        ("source_artifact_fingerprint", pa.string()),
        ("selection_slice_fingerprint", pa.string()),
        ("bar_coverage", pa.float64()),
        ("longest_missing_run", pa.int64()),
        ("automatic_eligible", pa.bool_()),
        ("forensic_research_allowed", pa.bool_()),
    ]
)
NEIGHBOR_SCHEMA = pa.schema(
    [
        ("scan_id", pa.string()),
        ("venue", pa.string()),
        ("horizon", pa.string()),
        ("pair_id", pa.string()),
        ("asset_a", pa.string()),
        ("asset_b", pa.string()),
        ("ssd_distance", pa.float64()),
        ("rank_from_a", pa.int64()),
        ("rank_from_b", pa.int64()),
        ("selected_by_a", pa.bool_()),
        ("selected_by_b", pa.bool_()),
        ("automatic_neighbor_selected", pa.bool_()),
        ("manual_pinned", pa.bool_()),
    ]
)
SCOUT_SCHEMA = pa.schema(
    [
        ("candidate_id", pa.string()),
        ("scan_id", pa.string()),
        ("venue", pa.string()),
        ("horizon", pa.string()),
        ("pair_id", pa.string()),
        ("orientation", pa.string()),
        ("resolution", pa.string()),
        ("model_family", pa.string()),
        ("template_id", pa.string()),
        ("trial_status", pa.string()),
        ("failure_reason", pa.string()),
        ("scout_relative_wealth_proxy", pa.float64()),
        ("scout_turnover_proxy", pa.float64()),
        ("signal_count", pa.int64()),
        ("automatic_neighbor_selected", pa.bool_()),
        ("manual_pinned", pa.bool_()),
    ]
)
PROMOTION_SCHEMA = pa.schema(
    [
        ("candidate_id", pa.string()),
        ("promotion_rank", pa.int64()),
        ("promotion_status", pa.string()),
        ("budget_reason", pa.string()),
        ("automatic_selected", pa.bool_()),
        ("manual_selected", pa.bool_()),
        ("selected_for_replay", pa.bool_()),
        ("direct_execution_instrument_id", pa.string()),
        ("deep_replay_run_id", pa.string()),
        ("deep_replay_status", pa.string()),
        ("economic_gate_status", pa.string()),
    ]
)
REPLAY_SCHEMA = pa.schema(
    [
        ("attempt_id", pa.string()),
        ("scan_id", pa.string()),
        ("candidate_id", pa.string()),
        ("promotion_rank", pa.int64()),
        ("attempt_status", pa.string()),
        ("failure_stage", pa.string()),
        ("failure_reason", pa.string()),
        ("deep_replay_run_id", pa.string()),
    ]
)
TABLE_SCHEMAS: dict[str, Any] = {
    "eligible_assets.parquet": ELIGIBLE_SCHEMA,
    "neighbors.parquet": NEIGHBOR_SCHEMA,
    "scout_trials.parquet": SCOUT_SCHEMA,
    "promotions.parquet": PROMOTION_SCHEMA,
    "replay_attempts.parquet": REPLAY_SCHEMA,
}

__all__ = [
    "ELIGIBLE_SCHEMA",
    "NEIGHBOR_SCHEMA",
    "PROMOTION_SCHEMA",
    "REPLAY_SCHEMA",
    "SCOUT_SCHEMA",
    "TABLE_SCHEMAS",
]
