# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""PyArrow schemas for scanner prospective evidence."""

import pyarrow as pa

COHORT_DEFINITION = "cohort.json"
FREEZES_TABLE = "freezes.parquet"
CHECKPOINTS_INDEX = "checkpoints.parquet"
OUTCOMES_INDEX = "outcomes.parquet"
CHECKPOINT_TABLE = "checkpoint.parquet"
LIQUIDITY_TABLE = "liquidity.parquet"
QUALIFICATION_TABLE = "qualification.parquet"
MANIFEST = "manifest.json"
CHECKPOINT_DIRECTORY = "checkpoint-generations"
CHECKPOINT_AUTHORITATIVE_FILES = frozenset(
    {CHECKPOINT_TABLE, LIQUIDITY_TABLE, QUALIFICATION_TABLE, MANIFEST}
)

FREEZE_SCHEMA = pa.schema(
    [
        ("cohort_id", pa.string()),
        ("freeze_id", pa.string()),
        ("candidate_id", pa.string()),
        ("scan_id", pa.string()),
        ("scanner_protocol_version", pa.string()),
        ("scanner_protocol_identity", pa.string()),
        ("prospective_protocol_version", pa.string()),
        ("prospective_protocol_identity", pa.string()),
        ("automatic_selected", pa.bool_()),
        ("manual_selected", pa.bool_()),
        ("frozen_at", pa.timestamp("us", tz="UTC")),
        ("eligible_information_end", pa.timestamp("us", tz="UTC")),
        ("forward_start", pa.timestamp("us", tz="UTC")),
        ("forward_end", pa.timestamp("us", tz="UTC")),
        ("horizon", pa.string()),
        ("venue", pa.string()),
        ("pair_id", pa.string()),
        ("orientation", pa.string()),
        ("resolution", pa.string()),
        ("model_family", pa.string()),
        ("template_id", pa.string()),
        ("model_parameters_json", pa.string()),
        ("source_artifact_fingerprints", pa.list_(pa.string())),
        ("selection_slice_fingerprints", pa.list_(pa.string())),
        ("universe_snapshot_id", pa.string()),
        ("cost_policy_reference", pa.string()),
        ("primary_control_reference", pa.string()),
        ("candidate_deep_replay_run_id", pa.string()),
        ("candidate_deep_replay_gate_status", pa.string()),
    ]
)

CHECKPOINT_SCHEMA = pa.schema(
    [
        ("checkpoint_id", pa.string()),
        ("cohort_id", pa.string()),
        ("candidate_id", pa.string()),
        ("freeze_id", pa.string()),
        ("checkpoint_index", pa.int64()),
        ("freeze_at", pa.timestamp("us", tz="UTC")),
        ("eligible_information_end", pa.timestamp("us", tz="UTC")),
        ("forward_start", pa.timestamp("us", tz="UTC")),
        ("first_outcome_complete_at", pa.timestamp("us", tz="UTC")),
        ("evidence_window_start", pa.timestamp("us", tz="UTC")),
        ("evidence_window_end", pa.timestamp("us", tz="UTC")),
        ("information_end", pa.timestamp("us", tz="UTC")),
        ("forward_slices_json", pa.string()),
        ("evidence_role", pa.string()),
        ("prospective_protocol_version", pa.string()),
        ("prospective_protocol_identity", pa.string()),
        ("prospective_complete", pa.bool_()),
        ("prospective_status", pa.string()),
        ("authoritative_run_id", pa.string()),
    ]
)

LIQUIDITY_SCHEMA = pa.schema(
    [
        ("checkpoint_id", pa.string()),
        ("candidate_id", pa.string()),
        ("snapshot_id", pa.string()),
        ("side", pa.string()),
        ("quote_notional", pa.string()),
        ("fillable", pa.bool_()),
        ("fee_bps", pa.string()),
        ("book_price_impact_bps", pa.string()),
        ("total_friction_bps", pa.string()),
    ]
)

QUALIFICATION_SCHEMA = pa.schema(
    [
        ("checkpoint_id", pa.string()),
        ("candidate_id", pa.string()),
        ("as_of", pa.timestamp("us", tz="UTC")),
        ("requested_capital", pa.string()),
        ("q_star_buy", pa.string()),
        ("q_safe_buy", pa.string()),
        ("q_star_sell", pa.string()),
        ("q_safe_sell", pa.string()),
        ("current_base_weight", pa.string()),
        ("required_buy_fraction", pa.string()),
        ("required_sell_fraction", pa.string()),
        ("candidate_capital_ceiling", pa.string()),
        ("qualification_state", pa.string()),
        ("reason", pa.string()),
        ("capture_contract_satisfied", pa.bool_()),
        ("current_two_way_trading", pa.bool_()),
        ("order_constraints_satisfied", pa.bool_()),
        ("economic_gates_at_requested_capital", pa.bool_()),
        ("lower_tested_capital", pa.string()),
        ("economic_gates_at_lower_capital", pa.bool_()),
    ]
)

OUTCOME_INDEX_SCHEMA = pa.schema(
    [
        ("checkpoint_id", pa.string()),
        ("cohort_id", pa.string()),
        ("candidate_id", pa.string()),
        ("checkpoint_index", pa.int64()),
        ("information_end", pa.timestamp("us", tz="UTC")),
        ("prospective_status", pa.string()),
        ("authoritative_run_id", pa.string()),
        ("qualification_state", pa.string()),
        ("qualification_reason", pa.string()),
        ("requested_capital", pa.string()),
        ("candidate_capital_ceiling", pa.string()),
    ]
)

__all__ = [
    "CHECKPOINT_AUTHORITATIVE_FILES",
    "CHECKPOINT_DIRECTORY",
    "CHECKPOINT_SCHEMA",
    "CHECKPOINT_TABLE",
    "CHECKPOINTS_INDEX",
    "COHORT_DEFINITION",
    "FREEZE_SCHEMA",
    "FREEZES_TABLE",
    "LIQUIDITY_SCHEMA",
    "LIQUIDITY_TABLE",
    "MANIFEST",
    "OUTCOME_INDEX_SCHEMA",
    "OUTCOMES_INDEX",
    "QUALIFICATION_SCHEMA",
    "QUALIFICATION_TABLE",
]
