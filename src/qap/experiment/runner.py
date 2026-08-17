"""Direct composition of frozen experiment inputs and shared replay roles."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import cast

from qap.execution import CostModel, ReplayPolicy, run_deterministic_replay
from qap.experiment.controls import (
    BandPartialPolicy,
    ContributionAwareBandPolicy,
    MatchedContributionStaticPolicy,
    PeriodicFixedWeightPolicy,
    StrictHodlPolicy,
    starting_value_target,
)
from qap.experiment.data import (
    DatasetFingerprintMismatchError,
    ExperimentSetupError,
    LoadedExperimentData,
    load_experiment_data,
)
from qap.experiment.economics import (
    RoleRun,
    build_experiment_result,
    build_role_run,
)
from qap.experiment.manifest import (
    BandPartialControlSpec,
    ContributionAwareBandControlSpec,
    ExperimentManifest,
    PeriodicFixedWeightControlSpec,
)
from qap.experiment.provenance import RunProvenance, capture_run_provenance
from qap.experiment.result import ExperimentResult
from qap.market import AlignedBarSeries
from qap.policy import ScheduledTargetPolicy
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    ExternalInventoryFlow,
    PortfolioLedger,
)

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class PreparedExperiment:
    manifest: ExperimentManifest
    loaded: LoadedExperimentData
    provenance: RunProvenance


@dataclass(frozen=True, slots=True)
class ExperimentRun:
    manifest: ExperimentManifest
    provenance: RunProvenance
    roles: tuple[RoleRun, ...]
    result: ExperimentResult

    def role(self, name: str) -> RoleRun:
        for role in self.roles:
            if role.role == name:
                return role
        raise KeyError(name)


@dataclass(frozen=True, slots=True)
class _PolicyComposition:
    policy_id: str
    policy: ReplayPolicy


def prepare_experiment(
    manifest: ExperimentManifest,
    *,
    data_root: str | Path,
    repository_root: str | Path,
    run_timestamp: datetime | None = None,
) -> PreparedExperiment:
    loaded = load_experiment_data(manifest, data_root=data_root)
    provenance = capture_run_provenance(
        manifest=manifest,
        data_fingerprints=loaded.data_fingerprints,
        repository_root=repository_root,
        run_timestamp=run_timestamp,
    )
    return PreparedExperiment(
        manifest=manifest,
        loaded=loaded,
        provenance=provenance,
    )


def _exact_decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str):
        raise ExperimentSetupError(f"{field} must be an exact decimal string")
    try:
        result = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ExperimentSetupError(f"{field} must be an exact decimal string") from exc
    if not result.is_finite():
        raise ExperimentSetupError(f"{field} must be finite")
    return result


def _utc_config_timestamp(value: object, *, field: str) -> datetime:
    if not isinstance(value, str):
        raise ExperimentSetupError(f"{field} must be an ISO-8601 UTC string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ExperimentSetupError(f"{field} must be an ISO-8601 UTC string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ExperimentSetupError(f"{field} must be timezone-aware UTC")
    return parsed.astimezone(UTC)


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ExperimentSetupError(f"{field} must be an object")
    result: dict[str, object] = {}
    for key, item in cast(Mapping[object, object], value).items():
        if not isinstance(key, str):
            raise ExperimentSetupError(f"{field} keys must be strings")
        result[key] = item
    return result


def _sequence(value: object, *, field: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ExperimentSetupError(f"{field} must be a list")
    return cast(Sequence[object], value)


def _strategy_policy(
    manifest: ExperimentManifest,
    aligned: AlignedBarSeries,
) -> _PolicyComposition:
    if manifest.relationship.component_id != "none" or manifest.relationship.config:
        raise ExperimentSetupError(
            "Phase 07 admits only relationship component 'none' with empty config"
        )
    if manifest.policy.component_id != "scheduled_target":
        raise ExperimentSetupError(
            "Phase 07 admits only the explicit scheduled_target strategy policy"
        )
    config = _mapping(manifest.policy.config, field="policy.config")
    if set(config) != {"schedule"}:
        raise ExperimentSetupError(
            "scheduled_target config must contain exactly 'schedule'"
        )
    decision_times = frozenset(
        timestamp + aligned.interval.duration for timestamp in aligned.timestamps
    )
    basket = tuple(manifest.asset(key) for key in manifest.basket)
    schedule: dict[datetime, AllocationTarget] = {}
    for position, raw in enumerate(
        _sequence(config["schedule"], field="policy.config.schedule")
    ):
        entry = _mapping(raw, field=f"policy.config.schedule[{position}]")
        if set(entry) != {"as_of", "weights"}:
            raise ExperimentSetupError(
                "scheduled target entries must contain exactly as_of and weights"
            )
        as_of = _utc_config_timestamp(
            entry["as_of"],
            field=f"policy.config.schedule[{position}].as_of",
        )
        if as_of not in decision_times:
            raise ExperimentSetupError(
                f"scheduled target timestamp is not a replay decision boundary: {as_of}"
            )
        raw_weights = _mapping(
            entry["weights"],
            field=f"policy.config.schedule[{position}].weights",
        )
        normalized_weights: dict[AssetId, Decimal] = {}
        for raw_asset, raw_weight in raw_weights.items():
            asset = manifest.asset(raw_asset)
            if asset in normalized_weights:
                raise ExperimentSetupError(
                    "scheduled target contains duplicate normalized asset keys"
                )
            normalized_weights[asset] = _exact_decimal(
                raw_weight,
                field=(f"policy.config.schedule[{position}].weights.{asset.key}"),
            )
        if as_of in schedule:
            raise ExperimentSetupError("scheduled target timestamps must be unique")
        schedule[as_of] = AllocationTarget.for_basket(
            normalized_weights,
            basket=basket,
        )
    policy_id = "strategy:scheduled_target"
    return _PolicyComposition(
        policy_id=policy_id,
        policy=ScheduledTargetPolicy(policy_id=policy_id, schedule=schedule),
    )


def _run_role(
    *,
    prepared: PreparedExperiment,
    role: str,
    composition: _PolicyComposition,
    flows: tuple[ExternalInventoryFlow, ...],
    cost_model_override: CostModel | None = None,
) -> RoleRun:
    manifest = prepared.manifest
    cost_model = cost_model_override or manifest.execution.cost_model()
    trace = run_deterministic_replay(
        run_id=f"{prepared.provenance.run_id}:{role}",
        aligned=prepared.loaded.aligned,
        ledger=PortfolioLedger(manifest.starting_state()),
        policy=composition.policy,
        execution_instrument=manifest.execution_instrument(),
        numeraire=manifest.asset(manifest.execution.numeraire_asset),
        cost_model=cost_model,
        min_rebalance_notional=manifest.execution.minimum_rebalance_notional,
        quantization=manifest.execution.quantization(),
        external_flows=flows,
    )
    if trace.unapplied_flows:
        raise ExperimentSetupError(f"role {role} left declared flows unapplied")
    return build_role_run(
        role=role,
        policy_id=composition.policy_id,
        trace=trace,
    )


def _control_policy(
    *,
    control: object,
    target: AllocationTarget,
    first_decision_time: datetime,
    manifest: ExperimentManifest,
) -> _PolicyComposition:
    if isinstance(control, PeriodicFixedWeightControlSpec):
        policy: ReplayPolicy = PeriodicFixedWeightPolicy(
            policy_id=f"control:{control.control_id}",
            target=target,
            first_decision_time=first_decision_time,
            interval=manifest.interval_domain(),
            cadence_bars=control.cadence_bars,
        )
        control_id = control.control_id
    elif isinstance(control, BandPartialControlSpec):
        policy = BandPartialPolicy(
            policy_id=f"control:{control.control_id}",
            target=target,
            band_width=control.band_width,
            partial_correction_fraction=control.partial_correction_fraction,
        )
        control_id = control.control_id
    else:
        validated = cast(ContributionAwareBandControlSpec, control)
        policy = ContributionAwareBandPolicy(
            policy_id=f"control:{validated.control_id}",
            target=target,
            band_width=validated.band_width,
            partial_correction_fraction=validated.partial_correction_fraction,
        )
        control_id = validated.control_id
    return _PolicyComposition(
        policy_id=f"control:{control_id}",
        policy=policy,
    )


def execute_prepared_experiment(prepared: PreparedExperiment) -> ExperimentRun:
    """Run one strategy and its frozen comparator ladder through shared replay."""

    if not isinstance(cast(object, prepared), PreparedExperiment):
        raise TypeError("prepared must be a PreparedExperiment")
    manifest = prepared.manifest
    flows = manifest.external_inventory_flows()
    hodl = _run_role(
        prepared=prepared,
        role="hodl",
        composition=_PolicyComposition(
            policy_id="hodl:strict",
            policy=StrictHodlPolicy(policy_id="hodl:strict"),
        ),
        flows=flows,
    )
    if not hodl.trace.steps:
        raise ExperimentSetupError("experiment replay produced no evaluation steps")
    target = starting_value_target(
        starting_state=manifest.starting_state(),
        price_snapshot=hodl.trace.steps[0].price_snapshot,
        basket=tuple(manifest.asset(key) for key in manifest.basket),
    )
    strategy = _run_role(
        prepared=prepared,
        role="strategy",
        composition=_strategy_policy(manifest, prepared.loaded.aligned),
        flows=flows,
    )

    role_runs: list[RoleRun] = [strategy, hodl]
    if any(flow.quantity_delta > _ZERO for flow in flows):
        policy_id = "hodl:matched-contribution-static"
        role_runs.append(
            _run_role(
                prepared=prepared,
                role="matched_contribution",
                composition=_PolicyComposition(
                    policy_id=policy_id,
                    policy=MatchedContributionStaticPolicy(
                        policy_id=policy_id,
                        target=target,
                    ),
                ),
                flows=flows,
            )
        )

    first_decision_time = hodl.trace.steps[0].decision_time
    for control in manifest.benchmarks.controls:
        composition = _control_policy(
            control=control,
            target=target,
            first_decision_time=first_decision_time,
            manifest=manifest,
        )
        role_runs.append(
            _run_role(
                prepared=prepared,
                role=composition.policy_id,
                composition=composition,
                flows=flows,
            )
        )

    adverse = manifest.execution.adverse_cost_scenario
    if adverse is not None:
        role_runs.append(
            _run_role(
                prepared=prepared,
                role="strategy:adverse_cost",
                composition=_strategy_policy(manifest, prepared.loaded.aligned),
                flows=flows,
                cost_model_override=adverse.cost_model(),
            )
        )

    roles = tuple(role_runs)
    return ExperimentRun(
        manifest=manifest,
        provenance=prepared.provenance,
        roles=roles,
        result=build_experiment_result(
            manifest=manifest,
            provenance=prepared.provenance,
            roles=roles,
        ),
    )


def execute_experiment(
    manifest: ExperimentManifest,
    *,
    data_root: str | Path,
    repository_root: str | Path,
    run_timestamp: datetime | None = None,
) -> ExperimentRun:
    """Prepare and execute one frozen experiment without writing artifacts."""

    return execute_prepared_experiment(
        prepare_experiment(
            manifest,
            data_root=data_root,
            repository_root=repository_root,
            run_timestamp=run_timestamp,
        )
    )


__all__ = [
    "DatasetFingerprintMismatchError",
    "ExperimentRun",
    "ExperimentSetupError",
    "LoadedExperimentData",
    "PreparedExperiment",
    "RoleRun",
    "execute_experiment",
    "execute_prepared_experiment",
    "load_experiment_data",
    "prepare_experiment",
]
