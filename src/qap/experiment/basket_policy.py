"""Ordinary-QAP policy composition for one frozen manual relationship basket."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import cast

from qap.execution import ReplayPolicy
from qap.experiment.basket_manifest import (
    BASKET_MAXIMUM_TILT,
    basket_edge_rule,
    basket_horizon,
)
from qap.experiment.data import ExperimentSetupError, LoadedExperimentData
from qap.experiment.manifest import ExperimentManifest
from qap.market import PriceSnapshot
from qap.policy import DecisionReason, PolicyDecision
from qap.policy.graph_basket import (
    BasketGraphEdge,
    resolve_graph_target,
    update_edge_opinions,
)
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    ExternalInventoryFlow,
    PairOrientation,
    PortfolioState,
)
from qap.portfolio._decimal import divide
from qap.relationship import (
    RelationshipObservation,
    RelationshipObservationStatus,
    RelationshipSeries,
    build_log_ratio_series,
)
from qap.relationship.models import (
    rolling_log_ratio_observation,
    rolling_residual_observation,
)


@dataclass(frozen=True, slots=True)
class _EdgeRule:
    graph_edge: BasketGraphEdge
    model_family: str
    window_bars: int
    min_observations: int
    source_fingerprints: Mapping[AssetId, str]
    log_ratio_source: RelationshipSeries | None


@dataclass(frozen=True, slots=True)
class BasketPolicyComposition:
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


def _sequence(value: object, *, field_name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ExperimentSetupError(f"{field_name} must be a list")
    return cast(Sequence[object], value)


def _asset(manifest: ExperimentManifest, value: object, *, field_name: str) -> AssetId:
    if not isinstance(value, str):
        raise ExperimentSetupError(f"{field_name} must be an asset key")
    try:
        return manifest.asset(value)
    except KeyError as exc:
        raise ExperimentSetupError(f"{field_name} is outside the basket") from exc


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
                f"basket replay requires one admitted execution leg for {asset.key}"
            )
        result[asset] = fingerprint.fingerprint
    return result


def _evidence_id(observation: RelationshipObservation) -> str:
    return (
        f"{observation.model_id}:v{observation.model_version}:"
        f"{observation.input_fingerprint}"
    )


@dataclass(slots=True)
class _BasketGraphReplayPolicy:
    policy_id: str
    loaded: LoadedExperimentData
    assets: tuple[AssetId, ...]
    neutral_target: AllocationTarget
    edges: tuple[_EdgeRule, ...]
    maximum_tilt: Decimal
    observations: list[RelationshipObservation]
    opinions: dict[str, int] = field(default_factory=dict[str, int])

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
        scores: dict[str, float | None] = {}
        decision_evidence: list[str] = []
        for edge in self.edges:
            if edge.model_family == "log_ratio_mean_reversion":
                assert edge.log_ratio_source is not None
                observation = rolling_log_ratio_observation(
                    edge.log_ratio_source,
                    window_bars=edge.window_bars,
                    min_observations=edge.min_observations,
                    as_of=as_of,
                )
            else:
                observation = rolling_residual_observation(
                    self.loaded.aligned,
                    orientation=edge.graph_edge.candidate_orientation,
                    source_fingerprints=edge.source_fingerprints,
                    window_bars=edge.window_bars,
                    min_observations=edge.min_observations,
                    as_of=as_of,
                )
            self.observations.append(observation)
            decision_evidence.append(_evidence_id(observation))
            scores[edge.graph_edge.edge_id] = (
                observation.values.get("score")
                if observation.status is RelationshipObservationStatus.VALID
                else None
            )

        update = update_edge_opinions(
            tuple(edge.graph_edge for edge in self.edges),
            previous=(self.opinions or None),
            scores=scores,
        )
        decision_id = f"{self.policy_id}:{as_of.isoformat()}"
        if not update.complete:
            return PolicyDecision.no_action_decision(
                decision_id=decision_id,
                as_of=as_of,
                policy_id=self.policy_id,
                current_state=current_state,
                reason=DecisionReason.INSUFFICIENT_EVIDENCE,
                evidence_ids=decision_evidence,
            )
        self.opinions = dict(update.opinions)
        decision_evidence.extend(
            f"basket-opinion:v1:{edge_id}:{self.opinions[edge_id]}"
            for edge_id in sorted(self.opinions)
        )
        decision_evidence.append(f"basket-resolver:v1:maximum_tilt={self.maximum_tilt}")
        target = resolve_graph_target(
            self.neutral_target,
            self.assets,
            tuple(edge.graph_edge for edge in self.edges),
            self.opinions,
            maximum_tilt=self.maximum_tilt,
        )
        return PolicyDecision.for_target(
            decision_id=decision_id,
            as_of=as_of,
            policy_id=self.policy_id,
            current_state=current_state,
            target=target,
            reason=DecisionReason.EVIDENCE_TARGET,
            evidence_ids=decision_evidence,
        )


def compose_basket_strategy_policy(
    manifest: ExperimentManifest,
    loaded: LoadedExperimentData,
) -> BasketPolicyComposition:
    """Compose one frozen selected-edge basket into an ordinary replay policy."""

    if manifest.relationship.component_id != "none" or manifest.relationship.config:
        raise ExperimentSetupError("basket_graph requires relationship 'none'")
    if manifest.policy.component_id != "basket_graph":
        raise ExperimentSetupError("basket policy component must be basket_graph")
    config = _mapping(manifest.policy.config, field_name="policy.config")
    if set(config) != {"horizon", "edges"}:
        raise ExperimentSetupError(
            "basket_graph config must contain exactly horizon and edges"
        )
    try:
        basket_horizon(manifest.policy.config, manifest.interval)
    except ValueError as exc:
        raise ExperimentSetupError(str(exc)) from exc
    maximum_tilt = BASKET_MAXIMUM_TILT
    raw_edges = _sequence(config["edges"], field_name="policy.config.edges")
    if not raw_edges:
        raise ExperimentSetupError("basket_graph requires at least one selected edge")
    source_fingerprints = _source_fingerprints(manifest, loaded)
    edge_rules: list[_EdgeRule] = []
    seen_pairs: set[tuple[AssetId, AssetId]] = set()
    seen_ids: set[str] = set()
    for position, raw in enumerate(raw_edges):
        entry = _mapping(raw, field_name=f"policy.config.edges[{position}]")
        required = {
            "edge_id",
            "asset_a",
            "asset_b",
            "candidate_base",
            "candidate_quote",
            "model_family",
            "template_id",
        }
        if set(entry) != required:
            raise ExperimentSetupError(
                "basket edge config keys do not match the frozen contract"
            )
        edge_id = entry["edge_id"]
        if not isinstance(edge_id, str) or not edge_id.strip():
            raise ExperimentSetupError("basket edge_id must be a non-empty string")
        normalized_edge_id = edge_id.strip()
        if normalized_edge_id in seen_ids:
            raise ExperimentSetupError("basket edge IDs must be unique")
        asset_a = _asset(
            manifest,
            entry["asset_a"],
            field_name=f"policy.config.edges[{position}].asset_a",
        )
        asset_b = _asset(
            manifest,
            entry["asset_b"],
            field_name=f"policy.config.edges[{position}].asset_b",
        )
        if asset_a >= asset_b:
            raise ExperimentSetupError("basket edge assets must use canonical order")
        pair = (asset_a, asset_b)
        if pair in seen_pairs:
            raise ExperimentSetupError("basket graph permits one edge per pair")
        orientation = PairOrientation(
            base=_asset(
                manifest,
                entry["candidate_base"],
                field_name=f"policy.config.edges[{position}].candidate_base",
            ),
            quote=_asset(
                manifest,
                entry["candidate_quote"],
                field_name=f"policy.config.edges[{position}].candidate_quote",
            ),
        )
        if {orientation.base, orientation.quote} != {asset_a, asset_b}:
            raise ExperimentSetupError(
                "candidate orientation does not match edge assets"
            )
        model_family = entry["model_family"]
        if model_family not in {
            "log_ratio_mean_reversion",
            "residual_mean_reversion",
        }:
            raise ExperimentSetupError("basket edge model family is unsupported")
        fingerprints = {
            asset: source_fingerprints[asset] for asset in (asset_a, asset_b)
        }
        source = (
            build_log_ratio_series(
                loaded.aligned,
                orientation=orientation,
                source_fingerprints=fingerprints,
                as_of=manifest.data_window.end,
            )
            if model_family == "log_ratio_mean_reversion"
            else None
        )
        template_id = entry["template_id"]
        if not isinstance(template_id, str):
            raise ExperimentSetupError("basket edge template_id must be a string")
        try:
            window_bars, min_observations = basket_edge_rule(
                manifest.policy.config,
                manifest.interval,
                template_id,
            )
        except ValueError as exc:
            raise ExperimentSetupError(str(exc)) from exc
        edge_rules.append(
            _EdgeRule(
                graph_edge=BasketGraphEdge(
                    edge_id=normalized_edge_id,
                    asset_a=asset_a,
                    asset_b=asset_b,
                    candidate_orientation=orientation,
                ),
                model_family=cast(str, model_family),
                window_bars=window_bars,
                min_observations=min_observations,
                source_fingerprints=fingerprints,
                log_ratio_source=source,
            )
        )
        seen_ids.add(normalized_edge_id)
        seen_pairs.add(pair)

    policy_id = "strategy:basket_graph"
    observations: list[RelationshipObservation] = []
    assets = tuple(manifest.asset(key) for key in manifest.basket)
    neutral_weight = divide(Decimal("1"), Decimal(len(assets)))
    neutral_target = AllocationTarget.for_basket(
        {asset: neutral_weight for asset in assets},
        basket=assets,
    )
    policy = _BasketGraphReplayPolicy(
        policy_id=policy_id,
        loaded=loaded,
        assets=assets,
        neutral_target=neutral_target,
        edges=tuple(edge_rules),
        maximum_tilt=maximum_tilt,
        observations=observations,
    )
    return BasketPolicyComposition(
        policy_id=policy_id,
        policy=policy,
        _relationship_observations=observations,
    )


__all__ = ["BasketPolicyComposition", "compose_basket_strategy_policy"]
