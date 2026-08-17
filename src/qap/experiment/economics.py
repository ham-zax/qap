"""Exact role-level economics and benchmark-ladder result construction."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qap.evaluation import incremental_log_relative_series, value_portfolio
from qap.execution import ReplayTrace
from qap.experiment.data import ExperimentSetupError
from qap.experiment.manifest import DataRole, ExperimentManifest, PrimaryMetric
from qap.experiment.provenance import RunProvenance
from qap.experiment.result import ExperimentResult, ResultStatus, RoleSummary
from qap.portfolio._decimal import (
    divide,
    exact_add,
    exact_multiply,
    exact_subtract,
    exact_sum,
)

_ZERO = Decimal("0")
_ONE = Decimal("1")


@dataclass(frozen=True, slots=True)
class RoleRun:
    role: str
    policy_id: str
    trace: ReplayTrace
    values: tuple[Decimal, ...]
    unitized_nav: tuple[Decimal, ...]
    fees_value: Decimal
    slippage_value: Decimal
    turnover_value: Decimal

    def __post_init__(self) -> None:
        if not self.role.strip() or not self.policy_id.strip():
            raise ValueError("role and policy_id must not be empty")
        if not self.values or len(self.values) != len(self.trace.steps):
            raise ValueError("role values must align exactly with replay steps")
        if len(self.unitized_nav) != len(self.values):
            raise ValueError("unitized NAV must align exactly with role values")

    @property
    def timestamps(self) -> tuple[datetime, ...]:
        return tuple(step.decision_time for step in self.trace.steps)

    @property
    def terminal_value(self) -> Decimal:
        return self.values[-1]


def _unitized_nav(trace: ReplayTrace) -> tuple[Decimal, ...]:
    units = _ONE
    values: list[Decimal] = []
    for step in trace.steps:
        pre_flow_value = value_portfolio(
            step.state_before_flows,
            step.price_snapshot,
        )
        if step.applied_flows:
            if pre_flow_value <= _ZERO:
                raise ExperimentSetupError(
                    "flow-adjusted unitization requires positive pre-flow wealth"
                )
            pre_flow_nav = divide(pre_flow_value, units)
            flow_value = exact_sum(
                exact_multiply(
                    flow.quantity_delta,
                    step.price_snapshot.price(flow.asset),
                )
                for flow in step.applied_flows
            )
            units = exact_add(units, divide(flow_value, pre_flow_nav))
            if units <= _ZERO:
                raise ExperimentSetupError(
                    "external withdrawals exhausted flow-adjusted units"
                )
        post_value = value_portfolio(step.state_after, step.price_snapshot)
        values.append(divide(post_value, units))
    return tuple(values)


def _role_costs(trace: ReplayTrace) -> tuple[Decimal, Decimal, Decimal]:
    fees = _ZERO
    slippage = _ZERO
    turnover = _ZERO
    for step in trace.steps:
        fill = step.fill
        if fill is None:
            continue
        quote_price = step.price_snapshot.price(fill.quote)
        fees = exact_add(fees, exact_multiply(fill.fee_amount, quote_price))
        slippage = exact_add(
            slippage,
            exact_multiply(fill.slippage_value, quote_price),
        )
        turnover = exact_add(
            turnover,
            exact_multiply(fill.gross_quote_notional, quote_price),
        )
    return fees, slippage, turnover


def build_role_run(
    *,
    role: str,
    policy_id: str,
    trace: ReplayTrace,
) -> RoleRun:
    values = tuple(
        value_portfolio(step.state_after, step.price_snapshot) for step in trace.steps
    )
    fees, slippage, turnover = _role_costs(trace)
    return RoleRun(
        role=role,
        policy_id=policy_id,
        trace=trace,
        values=values,
        unitized_nav=_unitized_nav(trace),
        fees_value=fees,
        slippage_value=slippage,
        turnover_value=turnover,
    )


def _relative(candidate: Decimal, control: Decimal, *, field: str) -> Decimal:
    if control <= _ZERO:
        raise ExperimentSetupError(f"{field} control terminal wealth must be positive")
    return exact_subtract(divide(candidate, control), _ONE)


def _maximum_relative_drawdown(
    candidate: tuple[Decimal, ...],
    control: tuple[Decimal, ...],
) -> Decimal:
    if not candidate or len(candidate) != len(control):
        raise ExperimentSetupError(
            "relative drawdown paths must align and be non-empty"
        )
    ratios = tuple(
        divide(candidate_value, control_value)
        for candidate_value, control_value in zip(
            candidate,
            control,
            strict=True,
        )
    )
    peak = ratios[0]
    maximum = _ZERO
    for ratio in ratios:
        if ratio > peak:
            peak = ratio
        drawdown = exact_subtract(_ONE, divide(ratio, peak))
        if drawdown > maximum:
            maximum = drawdown
    return maximum


def _role_summary(role: RoleRun) -> RoleSummary:
    return RoleSummary(
        role=role.role,
        policy_id=role.policy_id,
        terminal_value=role.terminal_value,
        unitized_terminal_value=role.unitized_nav[-1],
        terminal_quantities={
            asset.key: quantity
            for asset, quantity in role.trace.ending_state.holdings.items()
        },
        fill_count=len(role.trace.fills),
        fees_value=role.fees_value,
        slippage_value=role.slippage_value,
        turnover_value=role.turnover_value,
        external_flow_ids=tuple(flow.flow_id for flow in role.trace.applied_flows),
    )


def _status(metric: Decimal, threshold: Decimal) -> ResultStatus:
    if metric > threshold:
        return ResultStatus.POSITIVE
    if metric == threshold:
        return ResultStatus.NEUTRAL
    return ResultStatus.NEGATIVE


def build_experiment_result(
    *,
    manifest: ExperimentManifest,
    provenance: RunProvenance,
    roles: tuple[RoleRun, ...],
) -> ExperimentResult:
    role_map = {role.role: role for role in roles}
    if len(role_map) != len(roles):
        raise ExperimentSetupError("experiment role names must be unique")
    strategy = role_map["strategy"]
    hodl = role_map["hodl"]
    starting = manifest.starting_state()
    timestamps = strategy.timestamps
    for role in roles:
        if role.trace.starting_state != starting:
            raise ExperimentSetupError(
                f"role {role.role} violates the same-start invariant"
            )
        if role.trace.declared_flows != strategy.trace.declared_flows:
            raise ExperimentSetupError(
                f"role {role.role} received a different external flow stream"
            )
        if role.timestamps != timestamps:
            raise ExperimentSetupError(
                f"role {role.role} evaluation timestamps do not align"
            )

    strategy_vs_hodl = _relative(
        strategy.terminal_value,
        hodl.terminal_value,
        field="HODL",
    )
    matched = role_map.get("matched_contribution")
    strategy_vs_matched = (
        _relative(
            strategy.terminal_value,
            matched.terminal_value,
            field="matched-contribution HODL",
        )
        if matched is not None
        else None
    )
    primary_id = manifest.benchmarks.primary_incremental_benchmark
    primary_role = role_map.get(f"control:{primary_id}") if primary_id else None
    strategy_vs_primary = (
        _relative(
            strategy.terminal_value,
            primary_role.terminal_value,
            field="primary control",
        )
        if primary_role is not None
        else None
    )
    if manifest.primary_metric is PrimaryMetric.HODL_RELATIVE_TERMINAL_WEALTH:
        primary_value = strategy_vs_hodl
    else:
        if strategy_vs_primary is None:
            raise ExperimentSetupError(
                "primary-control metric requires a completed primary control"
            )
        primary_value = strategy_vs_primary

    try:
        log_relative: tuple[Decimal, ...] | None = incremental_log_relative_series(
            strategy.values, hodl.values
        )
    except ValueError:
        log_relative = None

    return ExperimentResult(
        run_id=provenance.run_id,
        research_family_id=manifest.research_family_id,
        parent_run_id=manifest.parent_run_id,
        data_role=manifest.data_role,
        final_oos_consumed=manifest.data_role is DataRole.FINAL_OOS,
        start_timestamp=timestamps[0],
        terminal_timestamp=timestamps[-1],
        primary_metric=manifest.primary_metric,
        primary_metric_value=primary_value,
        success_threshold=manifest.success_threshold,
        status=_status(primary_value, manifest.success_threshold),
        primary_incremental_benchmark=primary_id,
        strategy_vs_hodl=strategy_vs_hodl,
        strategy_vs_matched_contribution=strategy_vs_matched,
        strategy_vs_primary_control=strategy_vs_primary,
        strategy_unitized_vs_hodl=_relative(
            strategy.unitized_nav[-1],
            hodl.unitized_nav[-1],
            field="unitized HODL",
        ),
        maximum_relative_drawdown_vs_hodl=_maximum_relative_drawdown(
            strategy.values,
            hodl.values,
        ),
        incremental_log_relative_to_hodl=log_relative,
        roles=tuple(_role_summary(role) for role in roles),
        notes=(
            "Benchmark-rung differences compare frozen policies and are not an "
            "additive causal decomposition.",
        ),
    )


__all__ = ["RoleRun", "build_experiment_result", "build_role_run"]
