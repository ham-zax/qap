# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Versioned exact Parquet tables for experiment performance and inventory."""

import json
from decimal import Decimal
from typing import Any

import pyarrow as pa

from qap.experiment.data import ExperimentSetupError
from qap.experiment.runner import ExperimentRun
from qap.portfolio._decimal import divide, exact_multiply, exact_subtract

_ONE = Decimal("1")
_ZERO = Decimal("0")
_PERFORMANCE_SCHEMA = "qap.experiment.performance.v1"
_INVENTORY_SCHEMA = "qap.experiment.inventory.v1"


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
    "build_inventory_table",
    "build_performance_table",
    "validate_artifact_table",
]
