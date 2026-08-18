# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Immutable manual basket research definitions and semantic identities."""

import json
import re
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.market import BarInterval
from qap.portfolio import AssetId
from qap.scanner.artifacts import ScanArtifactError, read_completed_scan
from qap.scanner.asset_momentum import AssetMomentumGeneration
from qap.scanner.basket_protocol import (
    SCANNER_V1_BASKET,
    basket_protocol_identity,
)
from qap.scanner.catalog import (
    ScannerCatalog,
    ScannerSourceSpec,
    catalog_semantic_identity,
)
from qap.scanner.protocol import (
    SCANNER_V1_SLICE1,
    ScannerHorizon,
    TemplateId,
    protocol_identity,
)
from qap.scanner.trials import ScannerModelFamily

_FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")


class BasketDefinitionError(ValueError):
    """Raised when a manual basket violates the frozen Scanner-V1 contract."""


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


def _identity(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if _FINGERPRINT.fullmatch(normalized) is None:
        raise ValueError(f"{field} must be a 64-character SHA-256 identity")
    return normalized


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


class BasketEdge(_FrozenModel):
    candidate_id: str
    scan_id: str
    venue: str
    horizon: ScannerHorizon
    pair_id: str
    asset_a: str
    asset_b: str
    candidate_orientation: str
    resolution: str
    model_family: ScannerModelFamily
    template_id: TemplateId
    scout_status: str
    scout_failure_reason: str | None = None
    automatic_neighbor_selected: bool
    manual_pinned: bool
    automatic_selected: bool = False
    manual_selected: bool = False
    deep_replay_status: str | None = None
    deep_replay_failure_reason: str | None = None
    deep_replay_run_id: str | None = None
    economic_gate_status: str | None = None

    @field_validator("candidate_id", "scan_id")
    @classmethod
    def validate_identity(cls, value: str, info: object) -> str:
        return _identity(value, field=getattr(info, "field_name", "identity"))

    @field_validator("venue")
    @classmethod
    def validate_venue(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SCANNER_V1_BASKET.venues:
            raise ValueError("edge venue is not admitted by basket protocol")
        return normalized

    @field_validator("asset_a", "asset_b")
    @classmethod
    def validate_asset(cls, value: str) -> str:
        return AssetId(value).key

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, value: str) -> str:
        return BarInterval(value).label

    @model_validator(mode="after")
    def validate_edge(self) -> Self:
        first, second = sorted((self.asset_a, self.asset_b))
        if first == second:
            raise ValueError("basket edge assets must be distinct")
        if (self.asset_a, self.asset_b) != (first, second):
            object.__setattr__(self, "asset_a", first)
            object.__setattr__(self, "asset_b", second)
        if self.pair_id != f"{first}/{second}":
            raise ValueError("basket edge pair_id must use canonical asset order")
        orientations = {f"{first}/{second}", f"{second}/{first}"}
        if self.candidate_orientation not in orientations:
            raise ValueError("candidate orientation does not match basket edge assets")
        if self.resolution not in {
            item.label
            for item in SCANNER_V1_BASKET.allowed_basket_resolutions(self.horizon)
        }:
            raise ValueError("edge resolution is not admitted for the horizon")
        if self.scout_status != "valid" or self.scout_failure_reason is not None:
            raise ValueError("selected basket edges require a valid scout trial")
        if self.deep_replay_status == "replay_failed":
            raise ValueError("replay-integrity/data failures are not basket evidence")
        if self.deep_replay_status == "setup_failed":
            if self.deep_replay_failure_reason != "unsupported_direct_market":
                raise ValueError(
                    "only unsupported_direct_market setup failure is admissible"
                )
        elif self.deep_replay_failure_reason is not None:
            raise ValueError("deep replay failure reason requires setup_failed status")
        if self.deep_replay_status == "completed" and not self.deep_replay_run_id:
            raise ValueError("completed deep replay evidence requires a run ID")
        if (
            self.deep_replay_run_id is not None
            and self.deep_replay_status != "completed"
        ):
            raise ValueError("deep replay run ID requires completed status")
        if (
            self.economic_gate_status is not None
            and self.deep_replay_status != "completed"
        ):
            raise ValueError("economic gate status requires completed deep replay")
        return self

    @property
    def unordered_pair(self) -> tuple[str, str]:
        return (self.asset_a, self.asset_b)


class BasketDefinition(_FrozenModel):
    schema_version: str = "qap.scanner.basket-definition.v1"
    basket_protocol_id: str = SCANNER_V1_BASKET.protocol_id
    basket_protocol_identity: str = basket_protocol_identity(SCANNER_V1_BASKET)
    source_scan_id: str
    source_momentum_scan_id: str | None = None
    source_as_of: datetime
    venue: str
    horizon: ScannerHorizon
    decision_resolution: str
    economic_assets: tuple[str, ...]
    selected_edges: tuple[BasketEdge, ...]
    execution_dataset_ids: tuple[tuple[str, str], ...]
    forensic_assets: tuple[str, ...] = ()
    execution_bridge: str = SCANNER_V1_BASKET.execution_bridge
    neutral_allocation_rule: str = SCANNER_V1_BASKET.neutral_allocation_rule
    maximum_asset_tilt: Decimal = SCANNER_V1_BASKET.maximum_asset_tilt
    cost_policy_reference: str = SCANNER_V1_BASKET.cost_policy_reference
    mechanical_control_reference: str = SCANNER_V1_BASKET.mechanical_control_reference
    pair_blind_control_reference: str = SCANNER_V1_BASKET.pair_blind_control_reference
    created_at: datetime

    @field_validator("source_scan_id", "source_momentum_scan_id")
    @classmethod
    def validate_optional_identity(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        return _identity(value, field=getattr(info, "field_name", "identity"))

    @field_validator("source_as_of", "created_at")
    @classmethod
    def validate_timestamp(cls, value: datetime, info: object) -> datetime:
        return _utc(value, field=getattr(info, "field_name", "timestamp"))

    @field_validator("venue")
    @classmethod
    def validate_venue(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SCANNER_V1_BASKET.venues:
            raise ValueError("basket venue is not admitted")
        return normalized

    @field_validator("decision_resolution")
    @classmethod
    def validate_decision_resolution(cls, value: str) -> str:
        return BarInterval(value).label

    @field_validator("economic_assets", "forensic_assets")
    @classmethod
    def validate_asset_tuple(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(AssetId(value).key for value in values)
        if len(set(normalized)) != len(normalized):
            raise ValueError("asset tuple must be unique")
        return tuple(sorted(normalized))

    @model_validator(mode="after")
    def validate_definition(self) -> Self:
        protocol = SCANNER_V1_BASKET
        if self.basket_protocol_id != protocol.protocol_id:
            raise ValueError("basket protocol ID mismatch")
        if self.basket_protocol_identity != basket_protocol_identity(protocol):
            raise ValueError("basket protocol identity mismatch")
        if not (
            protocol.minimum_economic_assets
            <= len(self.economic_assets)
            <= protocol.maximum_economic_assets
        ):
            raise ValueError("basket must contain 3-6 economic assets")
        if self.decision_resolution not in {
            item.label for item in protocol.allowed_basket_resolutions(self.horizon)
        }:
            raise ValueError("basket decision resolution is not admitted for horizon")
        if not self.selected_edges:
            raise ValueError("basket requires at least one selected edge")
        assets = set(self.economic_assets)
        pairs: set[tuple[str, str]] = set()
        candidate_ids: set[str] = set()
        for edge in self.selected_edges:
            if edge.scan_id != self.source_scan_id:
                raise ValueError("edge source scan does not match basket")
            if edge.venue != self.venue or edge.horizon is not self.horizon:
                raise ValueError("edge venue/horizon does not match basket")
            if edge.resolution != self.decision_resolution:
                raise ValueError("edge resolution does not match basket")
            if not set(edge.unordered_pair) <= assets:
                raise ValueError("selected edge assets must belong to basket")
            if edge.unordered_pair in pairs:
                raise ValueError("only one candidate is allowed per unordered pair")
            if edge.candidate_id in candidate_ids:
                raise ValueError("duplicate candidate selection is not allowed")
            pairs.add(edge.unordered_pair)
            candidate_ids.add(edge.candidate_id)
        execution = dict(self.execution_dataset_ids)
        if len(execution) != len(self.execution_dataset_ids):
            raise ValueError("execution dataset asset keys must be unique")
        if set(execution) != assets:
            raise ValueError("every economic asset requires one execution dataset")
        if any(not dataset_id.strip() for dataset_id in execution.values()):
            raise ValueError("execution dataset IDs must not be empty")
        if not set(self.forensic_assets) <= assets:
            raise ValueError("forensic assets must belong to the economic basket")
        if self.execution_bridge != protocol.execution_bridge:
            raise ValueError("basket execution bridge must be USDT")
        if self.neutral_allocation_rule != protocol.neutral_allocation_rule:
            raise ValueError("basket neutral allocation rule mismatch")
        if self.maximum_asset_tilt != protocol.maximum_asset_tilt:
            raise ValueError("basket maximum tilt mismatch")
        if self.cost_policy_reference != protocol.cost_policy_reference:
            raise ValueError("basket cost policy reference mismatch")
        if self.mechanical_control_reference != protocol.mechanical_control_reference:
            raise ValueError("basket mechanical control reference mismatch")
        if self.pair_blind_control_reference != protocol.pair_blind_control_reference:
            raise ValueError("basket pair-blind control reference mismatch")
        object.__setattr__(
            self,
            "selected_edges",
            tuple(sorted(self.selected_edges, key=lambda edge: edge.unordered_pair)),
        )
        object.__setattr__(
            self,
            "execution_dataset_ids",
            tuple(sorted(self.execution_dataset_ids)),
        )
        return self

    @property
    def forensic(self) -> bool:
        return bool(self.forensic_assets)

    @property
    def basket_id(self) -> str:
        payload = {
            "identity_version": "qap.scanner.basket.v1",
            "basket_protocol_identity": self.basket_protocol_identity,
            "source_scan_id": self.source_scan_id,
            "source_momentum_scan_id": self.source_momentum_scan_id,
            "venue": self.venue,
            "horizon": self.horizon.value,
            "decision_resolution": self.decision_resolution,
            "economic_assets": list(self.economic_assets),
            "selected_edges": [
                [edge.asset_a, edge.asset_b, edge.candidate_id]
                for edge in self.selected_edges
            ],
            "execution_dataset_ids": [
                list(item) for item in self.execution_dataset_ids
            ],
            "forensic_assets": list(self.forensic_assets),
            "neutral_allocation_rule": self.neutral_allocation_rule,
            "maximum_asset_tilt": str(self.maximum_asset_tilt),
            "execution_bridge": self.execution_bridge,
            "cost_policy_reference": self.cost_policy_reference,
            "mechanical_control_reference": self.mechanical_control_reference,
            "pair_blind_control_reference": self.pair_blind_control_reference,
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return sha256(encoded).hexdigest()

    @property
    def research_family_id(self) -> str:
        payload = {
            "identity_version": "qap.scanner.basket-family.v1",
            "basket_protocol_identity": self.basket_protocol_identity,
            "source_scan_id": self.source_scan_id,
            "venue": self.venue,
            "horizon": self.horizon.value,
            "decision_resolution": self.decision_resolution,
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return sha256(encoded).hexdigest()


def _execution_source(
    catalog: ScannerCatalog,
    *,
    venue: str,
    asset_id: str,
    resolution: str,
) -> ScannerSourceSpec:
    matches = tuple(
        source
        for source in catalog.sources
        if source.venue == venue
        and source.base_asset == asset_id
        and source.quote_asset == SCANNER_V1_BASKET.execution_bridge
        and source.interval == resolution
    )
    if len(matches) != 1:
        raise BasketDefinitionError(
            f"economic asset requires exactly one {asset_id}/USDT execution source"
        )
    return matches[0]


def build_basket_definition_from_scan(
    source_scan_directory: str | Path,
    catalog: ScannerCatalog,
    *,
    venue: str,
    horizon: ScannerHorizon,
    decision_resolution: str,
    economic_assets: Sequence[str],
    candidate_ids: Sequence[str],
    created_at: datetime,
    source_momentum: AssetMomentumGeneration | None = None,
) -> BasketDefinition:
    """Validate one manual basket directly against immutable Slice-1 evidence."""

    try:
        definition, tables = read_completed_scan(source_scan_directory)
    except ScanArtifactError as exc:
        raise BasketDefinitionError(
            "source scan integrity/provenance is invalid"
        ) from exc
    if (
        definition.scanner_protocol_version != SCANNER_V1_SLICE1.protocol_id
        or definition.protocol_identity != protocol_identity(SCANNER_V1_SLICE1)
    ):
        raise BasketDefinitionError("source scan is not Scanner-V1 Slice-1 evidence")
    normalized_venue = venue.strip().lower()
    resolution = BarInterval(decision_resolution).label
    assets = tuple(sorted(AssetId(value).key for value in economic_assets))
    selected_ids = tuple(candidate_ids)
    if len(set(selected_ids)) != len(selected_ids):
        raise BasketDefinitionError("candidate IDs must be unique")
    if normalized_venue not in definition.venues or horizon not in definition.horizons:
        raise BasketDefinitionError("basket scope is absent from source scan")
    if catalog_semantic_identity(catalog) != definition.catalog_identity:
        raise BasketDefinitionError("catalog does not match frozen source scan")
    eligible_by_asset = {
        str(row["asset_id"]): row
        for row in tables["eligible_assets.parquet"]
        if row["venue"] == normalized_venue and row["horizon"] == horizon.value
    }
    forensic_assets: list[str] = []
    for asset in assets:
        row = eligible_by_asset.get(asset)
        if row is None or not (
            bool(row["automatic_eligible"]) or bool(row["forensic_research_allowed"])
        ):
            raise BasketDefinitionError(
                f"basket asset is not admitted by source PIT universe: {asset}"
            )
        if bool(row["forensic_research_allowed"]):
            forensic_assets.append(asset)

    input_dataset_ids = {item.dataset_id for item in definition.input_slices}
    execution_sources = tuple(
        _execution_source(
            catalog,
            venue=normalized_venue,
            asset_id=asset,
            resolution=resolution,
        )
        for asset in assets
    )
    if any(source.dataset_id not in input_dataset_ids for source in execution_sources):
        raise BasketDefinitionError(
            "basket execution source was not admitted by the source scan"
        )

    neighbors = {
        str(row["pair_id"]): row
        for row in tables["neighbors.parquet"]
        if row["venue"] == normalized_venue and row["horizon"] == horizon.value
    }
    scouts = {
        str(row["candidate_id"]): row
        for row in tables["scout_trials.parquet"]
        if row["venue"] == normalized_venue and row["horizon"] == horizon.value
    }
    promotions = {str(row["candidate_id"]): row for row in tables["promotions.parquet"]}
    attempts = {
        str(row["candidate_id"]): row for row in tables["replay_attempts.parquet"]
    }

    edges: list[BasketEdge] = []
    for candidate_id in selected_ids:
        scout = scouts.get(candidate_id)
        if scout is None:
            raise BasketDefinitionError(
                "selected candidate is absent from source scout ledger"
            )
        if scout["trial_status"] != "valid" or scout["failure_reason"] is not None:
            raise BasketDefinitionError("selected candidate scout trial is not valid")
        if scout["resolution"] != resolution:
            raise BasketDefinitionError(
                "selected candidate resolution does not match basket"
            )
        pair_id = str(scout["pair_id"])
        neighbor = neighbors.get(pair_id)
        if neighbor is None:
            raise BasketDefinitionError(
                "selected candidate pair is absent from graph evidence"
            )

        attempt = attempts.get(candidate_id)
        attempt_status = None if attempt is None else str(attempt["attempt_status"])
        failure_reason = None if attempt is None else attempt["failure_reason"]
        run_id = None if attempt is None else attempt["deep_replay_run_id"]
        promotion = promotions.get(candidate_id)
        economic_gate = None if promotion is None else promotion["economic_gate_status"]
        edges.append(
            BasketEdge(
                candidate_id=candidate_id,
                scan_id=definition.scan_id,
                venue=normalized_venue,
                horizon=horizon,
                pair_id=pair_id,
                asset_a=str(neighbor["asset_a"]),
                asset_b=str(neighbor["asset_b"]),
                candidate_orientation=str(scout["orientation"]),
                resolution=resolution,
                model_family=ScannerModelFamily(str(scout["model_family"])),
                template_id=TemplateId(str(scout["template_id"])),
                scout_status=str(scout["trial_status"]),
                scout_failure_reason=scout["failure_reason"],
                automatic_neighbor_selected=bool(scout["automatic_neighbor_selected"]),
                manual_pinned=bool(scout["manual_pinned"]),
                automatic_selected=(
                    False
                    if promotion is None
                    else bool(promotion["automatic_selected"])
                ),
                manual_selected=(
                    False if promotion is None else bool(promotion["manual_selected"])
                ),
                deep_replay_status=attempt_status,
                deep_replay_failure_reason=(
                    None if failure_reason is None else str(failure_reason)
                ),
                deep_replay_run_id=None if run_id is None else str(run_id),
                economic_gate_status=(
                    None if economic_gate is None else str(economic_gate)
                ),
            )
        )

    momentum_id: str | None = None
    if source_momentum is not None:
        if (
            source_momentum.venue != normalized_venue
            or source_momentum.horizon is not horizon
            or source_momentum.as_of != definition.eligible_information_end
        ):
            raise BasketDefinitionError(
                "source momentum generation does not match basket source scope"
            )
        momentum_id = source_momentum.momentum_scan_id

    return BasketDefinition(
        source_scan_id=definition.scan_id,
        source_momentum_scan_id=momentum_id,
        source_as_of=definition.eligible_information_end,
        venue=normalized_venue,
        horizon=horizon,
        decision_resolution=resolution,
        economic_assets=assets,
        selected_edges=tuple(edges),
        execution_dataset_ids=tuple(
            (source.base_asset, source.dataset_id) for source in execution_sources
        ),
        forensic_assets=tuple(forensic_assets),
        created_at=created_at,
    )


__all__ = [
    "BasketDefinition",
    "BasketDefinitionError",
    "BasketEdge",
    "build_basket_definition_from_scan",
]
