# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Versioned exact Parquet tables for experiment performance and inventory."""

import json
from decimal import Decimal
from typing import Any

import pyarrow as pa

from qap.evaluation import incremental_log_relative_series
from qap.experiment.data import ExperimentSetupError
from qap.experiment.runner import ExperimentRun
from qap.portfolio._decimal import divide, exact_add, exact_multiply, exact_subtract

_ONE = Decimal("1")
_ZERO = Decimal("0")
_PERFORMANCE_SCHEMA = "qap.experiment.performance.v1"
_INVENTORY_SCHEMA = "qap.experiment.inventory.v1"
_EVIDENCE_SCHEMA = "qap.experiment.evidence.v1"


def _metadata(run: ExperimentRun, *, schema: str) -> dict[bytes, bytes]:
    return {
        b"qap_schema": schema.encode("utf-8"),
        b"qap_run_id": run.provenance.run_id.encode("utf-8"),
        b"qap_research_family_id": run.manifest.research_family_id.encode("utf-8"),
        b"qap_data_role": run.manifest.data_role.value.encode("utf-8"),
        b"qap_roles": json.dumps(
            [role.role for role in run.roles],
            separators=(",", ":"),
        ).encode("utf-8"),
    }


def _relative(candidate: Decimal, control: Decimal) -> str:
    if control <= _ZERO:
        raise ExperimentSetupError("artifact relative comparator must be positive")
    return str(exact_subtract(divide(candidate, control), _ONE))


def _log_relative_path(
    candidate: tuple[Decimal, ...],
    control: tuple[Decimal, ...],
) -> list[str] | None:
    try:
        increments = incremental_log_relative_series(candidate, control)
    except ValueError:
        return None
    cumulative = _ZERO
    path = [str(cumulative)]
    for increment in increments:
        cumulative = exact_add(cumulative, increment)
        path.append(str(cumulative))
    return path


def build_performance_table(run: ExperimentRun) -> Any:
    """Build one exact wide row per shared evaluation timestamp."""

    strategy = run.role("strategy")
    hodl = run.role("hodl")
    columns: dict[str, list[str]] = {}
    for role in run.roles:
        columns[f"value::{role.role}"] = [str(value) for value in role.values]
        columns[f"unitized_nav::{role.role}"] = [
            str(value) for value in role.unitized_nav
        ]
    columns["relative::strategy_vs_hodl"] = [
        _relative(strategy_value, hodl_value)
        for strategy_value, hodl_value in zip(
            strategy.values,
            hodl.values,
            strict=True,
        )
    ]
    columns["relative_unitized::strategy_vs_hodl"] = [
        _relative(strategy_value, hodl_value)
        for strategy_value, hodl_value in zip(
            strategy.unitized_nav,
            hodl.unitized_nav,
            strict=True,
        )
    ]
    log_hodl = _log_relative_path(strategy.values, hodl.values)
    if log_hodl is not None:
        columns["log_relative::strategy_vs_hodl"] = log_hodl
    primary_id = run.result.primary_incremental_benchmark
    if primary_id is not None:
        primary = run.role(f"control:{primary_id}")
        columns["relative::strategy_vs_primary_control"] = [
            _relative(strategy_value, control_value)
            for strategy_value, control_value in zip(
                strategy.values,
                primary.values,
                strict=True,
            )
        ]
        log_primary = _log_relative_path(strategy.values, primary.values)
        if log_primary is not None:
            columns["log_relative::strategy_vs_primary_control"] = log_primary

    try:
        matched = run.role("matched_contribution")
    except KeyError:
        matched = None
    if matched is not None:
        log_matched = _log_relative_path(strategy.values, matched.values)
        if log_matched is not None:
            columns["log_relative::strategy_vs_matched_contribution"] = log_matched

    fields = [pa.field("timestamp", pa.timestamp("us", tz="UTC"), nullable=False)]
    fields.extend(pa.field(name, pa.string(), nullable=False) for name in columns)
    schema = pa.schema(fields, metadata=_metadata(run, schema=_PERFORMANCE_SCHEMA))
    arrays: list[Any] = [
        pa.array(strategy.timestamps, type=pa.timestamp("us", tz="UTC"))
    ]
    arrays.extend(pa.array(values, type=pa.string()) for values in columns.values())
    return pa.Table.from_arrays(arrays, schema=schema)


def build_inventory_table(run: ExperimentRun) -> Any:
    """Build exact long-form quantity, value, and weight rows for every role."""

    timestamps: list[object] = []
    roles: list[str] = []
    assets: list[str] = []
    quantities: list[str] = []
    values: list[str] = []
    weights: list[str] = []
    basket = tuple(run.manifest.asset(key) for key in run.manifest.basket)
    for role in run.roles:
        for position, step in enumerate(role.trace.steps):
            total = role.values[position]
            for asset in basket:
                quantity = step.state_after.quantity(asset)
                value = exact_multiply(
                    quantity,
                    step.valuation_price_snapshot.price(asset),
                )
                weight = divide(value, total) if total > _ZERO else _ZERO
                timestamps.append(step.decision_time)
                roles.append(role.role)
                assets.append(asset.key)
                quantities.append(str(quantity))
                values.append(str(value))
                weights.append(str(weight))

    schema = pa.schema(
        [
            pa.field("timestamp", pa.timestamp("us", tz="UTC"), nullable=False),
            pa.field("role", pa.string(), nullable=False),
            pa.field("asset", pa.string(), nullable=False),
            pa.field("quantity", pa.string(), nullable=False),
            pa.field("value", pa.string(), nullable=False),
            pa.field("weight", pa.string(), nullable=False),
        ],
        metadata=_metadata(run, schema=_INVENTORY_SCHEMA),
    )
    return pa.Table.from_arrays(
        [
            pa.array(timestamps, type=pa.timestamp("us", tz="UTC")),
            pa.array(roles, type=pa.string()),
            pa.array(assets, type=pa.string()),
            pa.array(quantities, type=pa.string()),
            pa.array(values, type=pa.string()),
            pa.array(weights, type=pa.string()),
        ],
        schema=schema,
    )


def build_evidence_table(run: ExperimentRun) -> Any:
    """Build long-form model evidence without coercing accounting values."""

    timestamps: list[object] = []
    canonical_first: list[str] = []
    canonical_second: list[str] = []
    orientation_base: list[str] = []
    orientation_quote: list[str] = []
    model_ids: list[str] = []
    model_versions: list[str] = []
    evidence_fields: list[str] = []
    values: list[float | None] = []
    statuses: list[str] = []
    fit_reciprocity: list[str] = []
    evidence_reciprocity: list[str] = []
    window_observations: list[int] = []
    required_observations: list[int] = []
    coverage_observations: list[int] = []
    input_fingerprints: list[str] = []
    base_source_fingerprints: list[str] = []
    quote_source_fingerprints: list[str] = []

    for observation in run.relationship_observations:
        fields = tuple(observation.values.items()) or (("score", None),)
        for evidence_field, value in fields:
            timestamps.append(observation.as_of)
            canonical_first.append(observation.pair_id.first.key)
            canonical_second.append(observation.pair_id.second.key)
            orientation_base.append(observation.orientation.base.key)
            orientation_quote.append(observation.orientation.quote.key)
            model_ids.append(observation.model_id)
            model_versions.append(observation.model_version)
            evidence_fields.append(evidence_field)
            values.append(value)
            statuses.append(observation.status.value)
            fit_reciprocity.append(observation.fit_reciprocity.value)
            evidence_reciprocity.append(observation.evidence_reciprocity.value)
            window_observations.append(observation.window_observations)
            required_observations.append(observation.required_observations)
            coverage_observations.append(observation.coverage_observations)
            input_fingerprints.append(observation.input_fingerprint)
            base_source_fingerprints.append(observation.base_source_fingerprint)
            quote_source_fingerprints.append(observation.quote_source_fingerprint)

    schema = pa.schema(
        [
            pa.field("timestamp", pa.timestamp("us", tz="UTC"), nullable=False),
            pa.field("canonical_first", pa.string(), nullable=False),
            pa.field("canonical_second", pa.string(), nullable=False),
            pa.field("orientation_base", pa.string(), nullable=False),
            pa.field("orientation_quote", pa.string(), nullable=False),
            pa.field("model_id", pa.string(), nullable=False),
            pa.field("model_version", pa.string(), nullable=False),
            pa.field("evidence_field", pa.string(), nullable=False),
            pa.field("value", pa.float64(), nullable=True),
            pa.field("status", pa.string(), nullable=False),
            pa.field("fit_reciprocity", pa.string(), nullable=False),
            pa.field("evidence_reciprocity", pa.string(), nullable=False),
            pa.field("window_observations", pa.int32(), nullable=False),
            pa.field("required_observations", pa.int32(), nullable=False),
            pa.field("coverage_observations", pa.int32(), nullable=False),
            pa.field("input_fingerprint", pa.string(), nullable=False),
            pa.field("base_source_fingerprint", pa.string(), nullable=False),
            pa.field("quote_source_fingerprint", pa.string(), nullable=False),
        ],
        metadata=_metadata(run, schema=_EVIDENCE_SCHEMA),
    )
    return pa.Table.from_arrays(
        [
            pa.array(timestamps, type=pa.timestamp("us", tz="UTC")),
            pa.array(canonical_first, type=pa.string()),
            pa.array(canonical_second, type=pa.string()),
            pa.array(orientation_base, type=pa.string()),
            pa.array(orientation_quote, type=pa.string()),
            pa.array(model_ids, type=pa.string()),
            pa.array(model_versions, type=pa.string()),
            pa.array(evidence_fields, type=pa.string()),
            pa.array(values, type=pa.float64()),
            pa.array(statuses, type=pa.string()),
            pa.array(fit_reciprocity, type=pa.string()),
            pa.array(evidence_reciprocity, type=pa.string()),
            pa.array(window_observations, type=pa.int32()),
            pa.array(required_observations, type=pa.int32()),
            pa.array(coverage_observations, type=pa.int32()),
            pa.array(input_fingerprints, type=pa.string()),
            pa.array(base_source_fingerprints, type=pa.string()),
            pa.array(quote_source_fingerprints, type=pa.string()),
        ],
        schema=schema,
    )


def validate_artifact_table(
    table: Any,
    *,
    expected_schema: str,
    run_id: str,
) -> None:
    metadata = table.schema.metadata
    if metadata is None:
        raise ValueError("artifact Parquet table is missing schema metadata")
    if metadata.get(b"qap_schema") != expected_schema.encode("utf-8"):
        raise ValueError(f"unexpected artifact table schema: {expected_schema}")
    if metadata.get(b"qap_run_id") != run_id.encode("utf-8"):
        raise ValueError("artifact Parquet run_id does not match run directory")


__all__ = [
    "build_evidence_table",
    "build_inventory_table",
    "build_performance_table",
    "validate_artifact_table",
]
