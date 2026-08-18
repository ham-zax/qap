# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""PyArrow schemas for Scanner-V1 Slice-2 prospective evidence."""

import pyarrow as pa

FREEZE_SCHEMA = pa.schema(
    [
        ("cohort_id", pa.string()),
        ("candidate_id", pa.string()),
        ("deep_replay_run_id", pa.string()),
        ("slice1_economic_gate_status", pa.string()),
        ("freeze_at", pa.timestamp("us", tz="UTC")),
        ("source_scan_id", pa.string()),
        ("slice2_protocol_version", pa.string()),
        ("protocol_identity", pa.string()),
    ]
)

CHECKPOINT_SCHEMA = pa.schema(
    [
        ("checkpoint_id", pa.string()),
        ("cohort_id", pa.string()),
        ("candidate_id", pa.string()),
        ("checkpoint_index", pa.int64()),
        ("freeze_at", pa.timestamp("us", tz="UTC")),
        ("evidence_window_start", pa.timestamp("us", tz="UTC")),
        ("evidence_window_end", pa.timestamp("us", tz="UTC")),
        ("information_end", pa.timestamp("us", tz="UTC")),
        ("forward_slices_json", pa.string()),
        ("evidence_role", pa.string()),
        ("slice2_protocol_version", pa.string()),
        ("protocol_identity", pa.string()),
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
    "CHECKPOINT_SCHEMA",
    "FREEZE_SCHEMA",
    "LIQUIDITY_SCHEMA",
    "OUTCOME_INDEX_SCHEMA",
    "QUALIFICATION_SCHEMA",
]
