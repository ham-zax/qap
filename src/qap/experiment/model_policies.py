import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from qap.execution import ReplayPolicy
from qap.experiment.data import ExperimentSetupError, LoadedExperimentData
from qap.experiment.manifest import ExperimentManifest
from qap.experiment.momentum import slow_log_momentum
from qap.market import AlignedBarSeries, AlignedInstrumentSeries, PriceSnapshot
from qap.policy import PolicyDecision
from qap.policy.evidence_tilt import (
    CrossSectionalTiltPolicy,
    EvidenceTiltPolicy,
    NeutralBandMode,
)
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    ExternalInventoryFlow,
    PairOrientation,
    PortfolioState,
)
from qap.relationship import (
    RelationshipObservation,
    RelationshipSeries,
    build_log_ratio_series,
)
from qap.relationship.models import (
    CrossSectionalRelativeStatus,
    cross_sectional_relative_observation,
    rolling_log_ratio_observation,
    rolling_residual_observation,
)

_PAIR_TILT_KEYS = frozenset(
    {
        "base_asset",
        "quote_asset",
        "neutral_weights",
        "neutral_threshold",
        "enter_threshold",
        "maximum_tilt",
        "neutral_mode",
    }
)


@dataclass(frozen=True, slots=True)
class ModelPolicyComposition:
    """One explicit model-backed replay policy plus captured pair observations."""

    policy_id: str
    policy: ReplayPolicy
    _relationship_observations: list[RelationshipObservation] = field(
        default_factory=list[RelationshipObservation], repr=False, compare=False
    )

    @property
    def relationship_observations(self) -> tuple[RelationshipObservation, ...]:
        return tuple(self._relationship_observations)


def _mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ExperimentSetupError(f"{field_name} must be an object")
    result: dict[str, object] = {}
    for key, item in cast(Mapping[object, object], value).items():
        if not isinstance(key, str):
            raise ExperimentSetupError(f"{field_name} keys must be strings")
        result[key] = item
    return result


def _exact_decimal(value: object, *, field_name: str) -> Decimal:
    if not isinstance(value, str):
        raise ExperimentSetupError(f"{field_name} must be an exact decimal string")
    try:
        result = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ExperimentSetupError(
            f"{field_name} must be an exact decimal string"
        ) from exc
    if not result.is_finite():
        raise ExperimentSetupError(f"{field_name} must be finite")
    return result


def _exact_float(value: object, *, field_name: str) -> float:
    result = float(_exact_decimal(value, field_name=field_name))
    if not math.isfinite(result):
        raise ExperimentSetupError(f"{field_name} must fit a finite float")
    return result


def _positive_int(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ExperimentSetupError(f"{field_name} must be an integer")
    if value <= 0:
        raise ExperimentSetupError(f"{field_name} must be positive")
    return value


def _non_negative_int(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ExperimentSetupError(f"{field_name} must be an integer")
    if value < 0:
        raise ExperimentSetupError(f"{field_name} must be non-negative")
    return value


def _asset(manifest: ExperimentManifest, value: object, *, field_name: str) -> AssetId:
    if not isinstance(value, str):
        raise ExperimentSetupError(f"{field_name} must be an asset key")
    try:
        return manifest.asset(value)
    except KeyError as exc:
        raise ExperimentSetupError(
            f"{field_name} is not in the manifest basket"
        ) from exc


def _orientation_from_config(
    manifest: ExperimentManifest,
    config: Mapping[str, object],
    *,
    field_name: str,
) -> PairOrientation:
    base = _asset(
        manifest, config.get("base_asset"), field_name=f"{field_name}.base_asset"
    )
    quote = _asset(
        manifest, config.get("quote_asset"), field_name=f"{field_name}.quote_asset"
    )
    return PairOrientation(base=base, quote=quote)


def _neutral_target(
    manifest: ExperimentManifest,
    config: Mapping[str, object],
) -> AllocationTarget:
    raw_weights = _mapping(
        config.get("neutral_weights"),
        field_name="policy.config.neutral_weights",
    )
    weights: dict[AssetId, Decimal] = {}
    for key, raw_weight in raw_weights.items():
        asset = _asset(
            manifest,
            key,
            field_name=f"policy.config.neutral_weights.{key}",
        )
        if asset in weights:
            raise ExperimentSetupError("neutral_weights contains duplicate asset keys")
        weights[asset] = _exact_decimal(
            raw_weight,
            field_name=f"policy.config.neutral_weights.{asset.key}",
        )
    basket = tuple(manifest.asset(key) for key in manifest.basket)
    return AllocationTarget.for_basket(weights, basket=basket)


def _pair_policy(
    manifest: ExperimentManifest,
    config: Mapping[str, object],
    *,
    policy_id: str,
) -> EvidenceTiltPolicy:
    extra = set(config) - _PAIR_TILT_KEYS
    if extra:
        raise ExperimentSetupError(
            f"unexpected pair-tilt policy config keys: {sorted(extra)}"
        )
    try:
        neutral_mode = NeutralBandMode(config.get("neutral_mode"))
    except (TypeError, ValueError) as exc:
        raise ExperimentSetupError("policy.config.neutral_mode is invalid") from exc
    return EvidenceTiltPolicy(
        policy_id=policy_id,
        orientation=_orientation_from_config(
            manifest,
            config,
            field_name="policy.config",
        ),
        neutral_target=_neutral_target(manifest, config),
        neutral_threshold=_exact_float(
            config.get("neutral_threshold"),
            field_name="policy.config.neutral_threshold",
        ),
        enter_threshold=_exact_float(
            config.get("enter_threshold"),
            field_name="policy.config.enter_threshold",
        ),
        maximum_tilt=_exact_decimal(
            config.get("maximum_tilt"),
            field_name="policy.config.maximum_tilt",
        ),
        neutral_mode=neutral_mode,
    )


def _source_fingerprints(
    manifest: ExperimentManifest,
    loaded: LoadedExperimentData,
) -> dict[AssetId, str]:
    instruments = manifest.instruments_by_id()
    result: dict[AssetId, str] = {}
    for source, fingerprint in zip(
        manifest.data_sources,
        loaded.data_fingerprints,
        strict=True,
    ):
        asset = instruments[source.instrument_id].base
        if asset in result:
            raise ExperimentSetupError(
                f"multiple admitted datasets provide relationship leg {asset.key}"
            )
        result[asset] = fingerprint.fingerprint
    return result


def _named_relationship_inputs(
    manifest: ExperimentManifest,
    loaded: LoadedExperimentData,
    config: Mapping[str, object],
) -> tuple[AlignedBarSeries, dict[AssetId, str]]:
    raw_ids = config.get("evidence_instrument_ids")
    if isinstance(raw_ids, (str, bytes)) or not isinstance(raw_ids, (list, tuple)):
        raise ExperimentSetupError(
            "relationship.config.evidence_instrument_ids must be a two-item list"
        )
    ids = tuple(cast(list[object] | tuple[object, ...], raw_ids))
    if len(ids) != 2 or any(
        not isinstance(item, str) or not item.strip() for item in ids
    ):
        raise ExperimentSetupError(
            "relationship.config.evidence_instrument_ids must contain two "
            "instrument IDs"
        )
    normalized = tuple(cast(str, item).strip() for item in ids)
    if len(set(normalized)) != 2:
        raise ExperimentSetupError(
            "relationship.config.evidence_instrument_ids must be unique"
        )
    declared = set(manifest.evidence_instrument_ids)
    if not set(normalized) <= declared:
        raise ExperimentSetupError(
            "relationship evidence instruments must be declared evidence-only "
            "instruments"
        )

    instruments = manifest.instruments_by_id()
    fingerprints: dict[AssetId, str] = {}
    for instrument_id in normalized:
        asset = instruments[instrument_id].base
        if asset in fingerprints:
            raise ExperimentSetupError(
                "relationship evidence instruments must provide distinct base assets"
            )
        fingerprints[asset] = loaded.fingerprint_for_instrument_id(instrument_id)
    return loaded.aligned_for_instrument_ids(normalized), fingerprints


def _decision_evidence_id(
    model_id: str, model_version: str, input_fingerprint: str
) -> str:
    return f"{model_id}:v{model_version}:{input_fingerprint}"


@dataclass(slots=True)
class _MomentumReplayPolicy:
    policy_id: str
    series: AlignedInstrumentSeries
    lookback_bars: int
    evidence_delay_bars: int
    tilt: EvidenceTiltPolicy

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        del price_snapshot, applied_flows, evidence_ids
        evidence_as_of = as_of - (
            self.series.interval.duration * self.evidence_delay_bars
        )
        evidence = slow_log_momentum(
            self.series,
            lookback_bars=self.lookback_bars,
            as_of=evidence_as_of,
        )
        timestamp = (
            evidence.current_timestamp.isoformat()
            if evidence.current_timestamp
            else "none"
        )
        evidence_id = (
            f"slow_log_momentum:v1:{evidence.asset.key}:"
            f"{self.lookback_bars}:delay={self.evidence_delay_bars}:{timestamp}"
        )
        return self.tilt.decide(
            as_of=as_of,
            current_state=current_state,
            score=evidence.score,
            evidence_id=evidence_id,
        )


@dataclass(slots=True)
class _RollingLogRatioReplayPolicy:
    policy_id: str
    source: RelationshipSeries
    window_bars: int
    min_observations: int
    tilt: EvidenceTiltPolicy
    observations: list[RelationshipObservation]

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        del price_snapshot, applied_flows, evidence_ids
        observation = rolling_log_ratio_observation(
            self.source,
            window_bars=self.window_bars,
            min_observations=self.min_observations,
            as_of=as_of,
        )
        self.observations.append(observation)
        return self.tilt.decide(
            as_of=as_of,
            current_state=current_state,
            score=observation.values.get("score"),
            evidence_id=_decision_evidence_id(
                model_id=observation.model_id,
                model_version=observation.model_version,
                input_fingerprint=observation.input_fingerprint,
            ),
        )


@dataclass(slots=True)
class _RollingResidualReplayPolicy:
    policy_id: str
    source: AlignedBarSeries
    orientation: PairOrientation
    source_fingerprints: Mapping[AssetId, str]
    window_bars: int
    min_observations: int
    tilt: EvidenceTiltPolicy
    observations: list[RelationshipObservation]

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        del price_snapshot, applied_flows, evidence_ids
        observation = rolling_residual_observation(
            self.source,
            orientation=self.orientation,
            source_fingerprints=self.source_fingerprints,
            window_bars=self.window_bars,
            min_observations=self.min_observations,
            as_of=as_of,
        )
        self.observations.append(observation)
        return self.tilt.decide(
            as_of=as_of,
            current_state=current_state,
            score=observation.values.get("score"),
            evidence_id=_decision_evidence_id(
                model_id=observation.model_id,
                model_version=observation.model_version,
                input_fingerprint=observation.input_fingerprint,
            ),
        )


@dataclass(slots=True)
class _CrossSectionalReplayPolicy:
    policy_id: str
    loaded: LoadedExperimentData
    basket: tuple[AssetId, ...]
    window_returns: int
    tilt: CrossSectionalTiltPolicy

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        del price_snapshot, applied_flows, evidence_ids
        observation = cross_sectional_relative_observation(
            self.loaded.aligned,
            basket=self.basket,
            window_returns=self.window_returns,
            as_of=as_of,
        )
        scores = (
            observation.scores
            if observation.status is CrossSectionalRelativeStatus.VALID
            else None
        )
        return self.tilt.decide(
            as_of=as_of,
            current_state=current_state,
            scores=scores,
            evidence_id=_decision_evidence_id(
                model_id=observation.model_id,
                model_version=observation.model_version,
                input_fingerprint=observation.input_fingerprint,
            ),
        )


def _compose_momentum(
    manifest: ExperimentManifest,
    loaded: LoadedExperimentData,
) -> ModelPolicyComposition:
    if manifest.relationship.component_id != "none" or manifest.relationship.config:
        raise ExperimentSetupError("slow_momentum_tilt requires relationship 'none'")
    config = _mapping(manifest.policy.config, field_name="policy.config")
    allowed = {*_PAIR_TILT_KEYS, "lookback_bars", "evidence_delay_bars"}
    required = {*_PAIR_TILT_KEYS, "lookback_bars"}
    if not required <= set(config) or not set(config) <= allowed:
        raise ExperimentSetupError(
            "slow_momentum_tilt config keys must match the frozen Phase-10 contract"
        )
    orientation = _orientation_from_config(
        manifest,
        config,
        field_name="policy.config",
    )
    matches = tuple(
        item
        for item in loaded.aligned.series
        if item.instrument.base == orientation.base
    )
    if len(matches) != 1:
        raise ExperimentSetupError(
            "slow_momentum_tilt base_asset must have exactly one admitted market leg"
        )
    policy_id = "strategy:slow_momentum_tilt"
    policy = _MomentumReplayPolicy(
        policy_id=policy_id,
        series=matches[0],
        lookback_bars=_positive_int(
            config["lookback_bars"],
            field_name="policy.config.lookback_bars",
        ),
        evidence_delay_bars=_non_negative_int(
            config.get("evidence_delay_bars", 0),
            field_name="policy.config.evidence_delay_bars",
        ),
        tilt=_pair_policy(
            manifest,
            {
                key: value
                for key, value in config.items()
                if key not in {"lookback_bars", "evidence_delay_bars"}
            },
            policy_id=policy_id,
        ),
    )
    return ModelPolicyComposition(policy_id=policy_id, policy=policy)


def _compose_rolling_log_ratio(
    manifest: ExperimentManifest,
    loaded: LoadedExperimentData,
) -> ModelPolicyComposition:
    relationship = _mapping(
        manifest.relationship.config,
        field_name="relationship.config",
    )
    required = {
        "base_asset",
        "quote_asset",
        "window_bars",
        "min_observations",
    }
    allowed = {*required, "evidence_instrument_ids"}
    if not required <= set(relationship) or not set(relationship) <= allowed:
        raise ExperimentSetupError(
            "rolling_log_ratio_zscore config keys must match the admitted contract"
        )
    policy_config = _mapping(manifest.policy.config, field_name="policy.config")
    orientation = _orientation_from_config(
        manifest,
        relationship,
        field_name="relationship.config",
    )
    policy_id = "strategy:evidence_tilt"
    tilt = _pair_policy(manifest, policy_config, policy_id=policy_id)
    if tilt.orientation != orientation:
        raise ExperimentSetupError(
            "relationship and evidence_tilt orientations must match exactly"
        )
    observations: list[RelationshipObservation] = []
    if "evidence_instrument_ids" in relationship:
        aligned, source_fingerprints = _named_relationship_inputs(
            manifest,
            loaded,
            relationship,
        )
    else:
        aligned = loaded.aligned
        source_fingerprints = _source_fingerprints(manifest, loaded)
    source = build_log_ratio_series(
        aligned,
        orientation=orientation,
        source_fingerprints=source_fingerprints,
        as_of=manifest.data_window.end,
    )
    policy = _RollingLogRatioReplayPolicy(
        policy_id=policy_id,
        source=source,
        window_bars=_positive_int(
            relationship["window_bars"],
            field_name="relationship.config.window_bars",
        ),
        min_observations=_positive_int(
            relationship["min_observations"],
            field_name="relationship.config.min_observations",
        ),
        tilt=tilt,
        observations=observations,
    )
    return ModelPolicyComposition(
        policy_id=policy_id,
        policy=policy,
        _relationship_observations=observations,
    )


def _compose_rolling_residual(
    manifest: ExperimentManifest,
    loaded: LoadedExperimentData,
) -> ModelPolicyComposition:
    relationship = _mapping(
        manifest.relationship.config,
        field_name="relationship.config",
    )
    required = {
        "base_asset",
        "quote_asset",
        "window_bars",
        "min_observations",
        "evidence_instrument_ids",
    }
    if set(relationship) != required:
        raise ExperimentSetupError(
            "residual_mean_reversion config keys must match the admitted contract"
        )
    orientation = _orientation_from_config(
        manifest,
        relationship,
        field_name="relationship.config",
    )
    policy_id = "strategy:evidence_tilt"
    tilt = _pair_policy(
        manifest,
        _mapping(manifest.policy.config, field_name="policy.config"),
        policy_id=policy_id,
    )
    if tilt.orientation != orientation:
        raise ExperimentSetupError(
            "relationship and evidence_tilt orientations must match exactly"
        )
    aligned, source_fingerprints = _named_relationship_inputs(
        manifest,
        loaded,
        relationship,
    )
    observations: list[RelationshipObservation] = []
    policy = _RollingResidualReplayPolicy(
        policy_id=policy_id,
        source=aligned,
        orientation=orientation,
        source_fingerprints=source_fingerprints,
        window_bars=_positive_int(
            relationship["window_bars"],
            field_name="relationship.config.window_bars",
        ),
        min_observations=_positive_int(
            relationship["min_observations"],
            field_name="relationship.config.min_observations",
        ),
        tilt=tilt,
        observations=observations,
    )
    return ModelPolicyComposition(
        policy_id=policy_id,
        policy=policy,
        _relationship_observations=observations,
    )


def _compose_cross_sectional(
    manifest: ExperimentManifest,
    loaded: LoadedExperimentData,
) -> ModelPolicyComposition:
    relationship = _mapping(
        manifest.relationship.config,
        field_name="relationship.config",
    )
    if set(relationship) != {"window_returns"}:
        raise ExperimentSetupError(
            "cross_sectional_relative_log_return config must contain window_returns"
        )
    policy_config = _mapping(manifest.policy.config, field_name="policy.config")
    if set(policy_config) != {"neutral_weights", "maximum_tilt"}:
        raise ExperimentSetupError(
            "cross_sectional_tilt config must contain neutral_weights and maximum_tilt"
        )
    policy_id = "strategy:cross_sectional_tilt"
    policy = _CrossSectionalReplayPolicy(
        policy_id=policy_id,
        loaded=loaded,
        basket=tuple(manifest.asset(key) for key in manifest.basket),
        window_returns=_positive_int(
            relationship["window_returns"],
            field_name="relationship.config.window_returns",
        ),
        tilt=CrossSectionalTiltPolicy(
            policy_id=policy_id,
            neutral_target=_neutral_target(manifest, policy_config),
            maximum_tilt=_exact_decimal(
                policy_config["maximum_tilt"],
                field_name="policy.config.maximum_tilt",
            ),
        ),
    )
    return ModelPolicyComposition(policy_id=policy_id, policy=policy)


def compose_model_strategy_policy(
    manifest: ExperimentManifest,
    loaded: LoadedExperimentData,
) -> ModelPolicyComposition:
    """Compose only the three explicitly admitted Phase-10 strategy variants."""

    relationship_id = manifest.relationship.component_id
    policy_id = manifest.policy.component_id
    if relationship_id == "none" and policy_id == "slow_momentum_tilt":
        return _compose_momentum(manifest, loaded)
    if relationship_id == "rolling_log_ratio_zscore" and policy_id == "evidence_tilt":
        return _compose_rolling_log_ratio(manifest, loaded)
    if relationship_id == "residual_mean_reversion" and policy_id == "evidence_tilt":
        return _compose_rolling_residual(manifest, loaded)
    if (
        relationship_id == "cross_sectional_relative_log_return"
        and policy_id == "cross_sectional_tilt"
    ):
        return _compose_cross_sectional(manifest, loaded)
    raise ExperimentSetupError(
        "unsupported admitted relationship/policy strategy combination: "
        f"{relationship_id}/{policy_id}"
    )
