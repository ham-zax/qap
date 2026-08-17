"""Read-time semantic reconciliation across persisted experiment artifacts."""

from decimal import Decimal, InvalidOperation
from typing import Any

from qap.experiment.manifest import PrimaryMetric
from qap.experiment.result import ExperimentResult
from qap.portfolio._decimal import divide, exact_subtract

_ONE = Decimal("1")
_ZERO = Decimal("0")


def _column_values(table: Any, name: str) -> list[object]:
    if name not in table.column_names:
        raise ValueError(f"artifact table is missing semantic column {name}")
    return list(table.column(name).to_pylist())


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an exact decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be an exact decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")
    return parsed


def _terminal_decimal(table: Any, name: str) -> Decimal:
    values = _column_values(table, name)
    if not values:
        raise ValueError(f"artifact semantic column is empty: {name}")
    return _decimal(values[-1], field=f"terminal {name}")


def _relative(candidate: Decimal, control: Decimal) -> Decimal:
    if control <= _ZERO:
        raise ValueError("artifact semantic comparator must be positive")
    return exact_subtract(divide(candidate, control), _ONE)


def _validate_performance(result: ExperimentResult, performance: Any) -> None:
    if performance.num_rows <= 0:
        raise ValueError("performance artifact must contain at least one row")
    timestamps = _column_values(performance, "timestamp")
    if timestamps[0] != result.start_timestamp:
        raise ValueError("performance start timestamp disagrees with result")
    if timestamps[-1] != result.terminal_timestamp:
        raise ValueError("performance terminal timestamp disagrees with result")

    terminal_values: dict[str, Decimal] = {}
    for role in result.roles:
        terminal_value = _terminal_decimal(performance, f"value::{role.role}")
        terminal_unitized = _terminal_decimal(performance, f"unitized_nav::{role.role}")
        if terminal_value != role.terminal_value:
            raise ValueError(f"terminal value disagrees for role {role.role}")
        if terminal_unitized != role.unitized_terminal_value:
            raise ValueError(f"terminal unitized NAV disagrees for role {role.role}")
        terminal_values[role.role] = terminal_value

    strategy = terminal_values["strategy"]
    hodl = terminal_values["hodl"]
    hodl_relative = _terminal_decimal(performance, "relative::strategy_vs_hodl")
    if hodl_relative != _relative(strategy, hodl):
        raise ValueError("performance HODL-relative terminal value is inconsistent")
    if hodl_relative != result.strategy_vs_hodl:
        raise ValueError(
            "performance HODL-relative terminal value disagrees with result"
        )

    unitized_hodl_relative = _terminal_decimal(
        performance, "relative_unitized::strategy_vs_hodl"
    )
    strategy_unitized = result.role("strategy").unitized_terminal_value
    hodl_unitized = result.role("hodl").unitized_terminal_value
    if unitized_hodl_relative != _relative(strategy_unitized, hodl_unitized):
        raise ValueError("performance unitized HODL-relative value is inconsistent")
    if unitized_hodl_relative != result.strategy_unitized_vs_hodl:
        raise ValueError(
            "performance unitized HODL-relative value disagrees with result"
        )

    if result.primary_incremental_benchmark is not None:
        control_role = f"control:{result.primary_incremental_benchmark}"
        primary_relative = _terminal_decimal(
            performance, "relative::strategy_vs_primary_control"
        )
        if primary_relative != _relative(strategy, terminal_values[control_role]):
            raise ValueError(
                "performance primary-control relative value is inconsistent"
            )
        if primary_relative != result.strategy_vs_primary_control:
            raise ValueError(
                "performance primary-control relative value disagrees with result"
            )

    if result.strategy_vs_matched_contribution is not None:
        matched = terminal_values.get("matched_contribution")
        if matched is None:
            raise ValueError(
                "matched-contribution result is missing its performance role"
            )
        if _relative(strategy, matched) != result.strategy_vs_matched_contribution:
            raise ValueError(
                "matched-contribution terminal value disagrees with result"
            )

    expected_primary = (
        result.strategy_vs_hodl
        if result.primary_metric is PrimaryMetric.HODL_RELATIVE_TERMINAL_WEALTH
        else result.strategy_vs_primary_control
    )
    if expected_primary is None or result.primary_metric_value != expected_primary:
        raise ValueError("primary metric value disagrees with its declared comparison")


def _validate_inventory(result: ExperimentResult, inventory: Any) -> None:
    required = {"timestamp", "role", "asset", "quantity"}
    if not required.issubset(inventory.column_names):
        raise ValueError(
            "inventory artifact is missing terminal reconciliation columns"
        )
    timestamps = inventory.column("timestamp").to_pylist()
    roles = inventory.column("role").to_pylist()
    assets = inventory.column("asset").to_pylist()
    quantities = inventory.column("quantity").to_pylist()

    terminal_by_role: dict[str, dict[str, Decimal]] = {}
    seen: set[tuple[str, str]] = set()
    for timestamp, role, asset, quantity in zip(
        timestamps,
        roles,
        assets,
        quantities,
        strict=True,
    ):
        if timestamp != result.terminal_timestamp:
            continue
        if not isinstance(role, str) or not isinstance(asset, str):
            raise ValueError("inventory role and asset must be strings")
        identity = (role, asset)
        if identity in seen:
            raise ValueError("inventory terminal rows contain duplicate role/asset")
        seen.add(identity)
        parsed = _decimal(quantity, field=f"terminal quantity {role}/{asset}")
        if parsed < _ZERO:
            raise ValueError("inventory terminal quantities must be non-negative")
        if parsed > _ZERO:
            terminal_by_role.setdefault(role, {})[asset] = parsed

    for role in result.roles:
        actual = terminal_by_role.get(role.role, {})
        if actual != role.terminal_quantities:
            raise ValueError(f"terminal inventory disagrees for role {role.role}")


def validate_run_artifact_semantics(
    *,
    result: ExperimentResult,
    performance: Any,
    inventory: Any,
) -> None:
    """Cross-check compact results against terminal/path evidence tables."""

    _validate_performance(result, performance)
    _validate_inventory(result, inventory)


__all__ = ["validate_run_artifact_semantics"]
