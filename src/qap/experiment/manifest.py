"""Strict frozen experiment manifests and domain composition helpers."""

import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal, Self, cast

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    field_validator,
    model_validator,
)

from qap.execution import CostModel, ExecutionQuantization
from qap.experiment.basket_manifest import validate_basket_manifest_contract
from qap.experiment.control_specs import (
    BandPartialControlSpec,
    ContributionAwareBandControlSpec,
    ControlSpec,
    PairBlindRelativeMomentumControlSpec,
    PeriodicFixedWeightControlSpec,
)
from qap.market import BarInterval, VenueInstrument
from qap.portfolio import AssetId, ExternalInventoryFlow, PortfolioState

_MANIFEST_SCHEMA_VERSION = "qap.experiment.manifest.v1"
_ZERO = Decimal("0")
_ONE = Decimal("1")
_FINGERPRINT_PATTERN = re.compile(r"[0-9a-fA-F]{64}")

Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _parse_exact_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            raise ValueError("exact decimal string must not be empty")
        try:
            result = Decimal(normalized)
        except InvalidOperation as exc:
            raise ValueError("value must be an exact decimal string") from exc
    else:
        raise ValueError("value must be an exact decimal string")
    if not result.is_finite():
        raise ValueError("exact decimal value must be finite")
    return result


ExactDecimal = Annotated[Decimal, BeforeValidator(_parse_exact_decimal)]


def _asset_key(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a valid asset key")
    try:
        return AssetId(value).key
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a valid asset key") from exc


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _no_float_json(value: JsonValue, *, path: str = "config") -> JsonValue:
    if isinstance(value, float):
        raise ValueError(
            f"{path} must encode exact financial values as strings, not floats"
        )
    if isinstance(value, list):
        return [
            _no_float_json(item, path=f"{path}[{position}]")
            for position, item in enumerate(value)
        ]
    if isinstance(value, dict):
        return {
            key: _no_float_json(item, path=f"{path}.{key}")
            for key, item in value.items()
        }
    return value


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DataRole(StrEnum):
    EXPLORATORY = "exploratory"
    DEVELOPMENT = "development"
    FINAL_OOS = "final_oos"
    FORWARD_PAPER = "forward_paper"


class UniverseMode(StrEnum):
    DECLARED_FIXED_BASKET = "declared_fixed_basket"
    POINT_IN_TIME_INVESTABLE = "point_in_time_investable"


class PrimaryMetric(StrEnum):
    HODL_RELATIVE_TERMINAL_WEALTH = "hodl_relative_terminal_wealth"
    PRIMARY_CONTROL_RELATIVE_TERMINAL_WEALTH = (
        "primary_control_relative_terminal_wealth"
    )


class InstrumentSpec(_FrozenModel):
    instrument_id: Identifier
    venue: Identifier
    venue_symbol: Identifier
    base_asset: Identifier
    quote_asset: Identifier
    valid_from: datetime | None = None
    valid_to: datetime | None = None

    @field_validator("base_asset", "quote_asset", mode="before")
    @classmethod
    def normalize_assets(cls, value: object, info: Any) -> str:
        return _asset_key(value, field=info.field_name)

    @field_validator("valid_from", "valid_to")
    @classmethod
    def validate_optional_utc(
        cls,
        value: datetime | None,
        info: Any,
    ) -> datetime | None:
        if value is None:
            return None
        return _utc(value, field=info.field_name)

    @model_validator(mode="after")
    def validate_orientation_and_window(self) -> Self:
        if self.base_asset == self.quote_asset:
            raise ValueError("instrument base_asset and quote_asset must differ")
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and self.valid_from >= self.valid_to
        ):
            raise ValueError("instrument valid_from must be before valid_to")
        return self

    def to_domain(self) -> VenueInstrument:
        return VenueInstrument(
            venue=self.venue,
            venue_symbol=self.venue_symbol,
            base=AssetId(self.base_asset),
            quote=AssetId(self.quote_asset),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
        )


class DataWindowSpec(_FrozenModel):
    start: datetime
    end: datetime

    @field_validator("start", "end")
    @classmethod
    def validate_utc(cls, value: datetime, info: Any) -> datetime:
        return _utc(value, field=f"data_window.{info.field_name}")

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.start >= self.end:
            raise ValueError("data_window start must be before end")
        return self


class DataSourceSpec(_FrozenModel):
    dataset_id: Identifier
    instrument_id: Identifier
    relative_path: str
    expected_semantic_fingerprint: str

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or "\\" in normalized:
            raise ValueError("relative_path must be a non-empty POSIX path")
        path = PurePosixPath(normalized)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError(
                "relative_path must be relative and must not contain '.' or '..'"
            )
        return path.as_posix()

    @field_validator("expected_semantic_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        normalized = value.strip().lower()
        if _FINGERPRINT_PATTERN.fullmatch(normalized) is None:
            raise ValueError(
                "expected_semantic_fingerprint must be a 64-character SHA-256 hex"
            )
        return normalized


class ComponentSpec(_FrozenModel):
    component_id: Identifier
    config: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("config")
    @classmethod
    def reject_float_config(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], _no_float_json(value))


class CostScenarioSpec(_FrozenModel):
    fee_bps: ExactDecimal
    slippage_bps: ExactDecimal

    @model_validator(mode="after")
    def validate_costs(self) -> Self:
        CostModel(fee_bps=self.fee_bps, slippage_bps=self.slippage_bps)
        return self

    def cost_model(self) -> CostModel:
        return CostModel(fee_bps=self.fee_bps, slippage_bps=self.slippage_bps)


class ExecutionSpec(_FrozenModel):
    mode: Literal["direct", "multi_asset_bridge"] = "direct"
    execution_instrument_id: Identifier | None = None
    execution_instrument_ids: tuple[Identifier, ...] = ()
    bridge_asset: Identifier | None = None
    market_metadata_mode: Literal["required", "historical_unconstrained"] = "required"
    numeraire_asset: Identifier
    fee_bps: ExactDecimal
    slippage_bps: ExactDecimal
    minimum_rebalance_notional: ExactDecimal
    base_step: ExactDecimal | None = None
    adverse_cost_scenario: CostScenarioSpec | None = None

    @field_validator("numeraire_asset", mode="before")
    @classmethod
    def normalize_numeraire(cls, value: object) -> str:
        return _asset_key(value, field="execution.numeraire_asset")

    @field_validator("bridge_asset", mode="before")
    @classmethod
    def normalize_optional_bridge(cls, value: object) -> str | None:
        if value is None:
            return None
        return _asset_key(value, field="execution.bridge_asset")

    @model_validator(mode="after")
    def validate_execution(self) -> Self:
        CostModel(fee_bps=self.fee_bps, slippage_bps=self.slippage_bps)
        if self.minimum_rebalance_notional < _ZERO:
            raise ValueError("minimum_rebalance_notional must be non-negative")
        if self.base_step is not None and self.base_step <= _ZERO:
            raise ValueError("base_step must be strictly positive when present")
        if self.mode == "direct":
            if self.execution_instrument_id is None:
                raise ValueError("direct execution requires execution_instrument_id")
            if self.execution_instrument_ids:
                raise ValueError(
                    "direct execution cannot declare execution_instrument_ids"
                )
            if self.bridge_asset is not None:
                raise ValueError("direct execution cannot declare bridge_asset")
        else:
            if self.execution_instrument_id is not None:
                raise ValueError(
                    "multi_asset_bridge cannot use singular execution_instrument_id"
                )
            if not self.execution_instrument_ids:
                raise ValueError("multi_asset_bridge requires execution_instrument_ids")
            if len(set(self.execution_instrument_ids)) != len(
                self.execution_instrument_ids
            ):
                raise ValueError("execution_instrument_ids must be unique")
            if self.bridge_asset is None:
                raise ValueError("multi_asset_bridge requires bridge_asset")
            if self.base_step is not None:
                raise ValueError("multi_asset_bridge cannot use singular base_step")
        return self

    def cost_model(self) -> CostModel:
        return CostModel(fee_bps=self.fee_bps, slippage_bps=self.slippage_bps)

    def quantization(self) -> ExecutionQuantization:
        return ExecutionQuantization(base_step=self.base_step)


class ExternalFlowSpec(_FrozenModel):
    flow_id: Identifier
    effective_time: datetime
    asset: Identifier
    quantity_delta: ExactDecimal

    @field_validator("effective_time")
    @classmethod
    def validate_effective_time(cls, value: datetime) -> datetime:
        return _utc(value, field="external flow effective_time")

    @field_validator("asset", mode="before")
    @classmethod
    def normalize_asset(cls, value: object) -> str:
        return _asset_key(value, field="external flow asset")

    @model_validator(mode="after")
    def validate_delta(self) -> Self:
        if self.quantity_delta == _ZERO:
            raise ValueError("external flow quantity_delta must be non-zero")
        return self

    def to_domain(self) -> ExternalInventoryFlow:
        return ExternalInventoryFlow(
            flow_id=self.flow_id,
            effective_time=self.effective_time,
            asset=AssetId(self.asset),
            quantity_delta=self.quantity_delta,
        )


class BenchmarkSpec(_FrozenModel):
    relationship_alpha_claim: bool = False
    primary_incremental_benchmark: Identifier | None = None
    controls: tuple[ControlSpec, ...] = ()

    @model_validator(mode="after")
    def validate_primary_control(self) -> Self:
        identifiers = tuple(control.control_id for control in self.controls)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("benchmark control_id values must be unique")
        if self.relationship_alpha_claim and self.primary_incremental_benchmark is None:
            raise ValueError(
                "primary_incremental_benchmark is required for a "
                "relationship-alpha claim"
            )
        if (
            self.primary_incremental_benchmark is not None
            and self.primary_incremental_benchmark not in identifiers
        ):
            raise ValueError(
                "primary_incremental_benchmark must reference one declared "
                "simple control"
            )
        return self


class ExperimentManifest(_FrozenModel):
    schema_version: Literal["qap.experiment.manifest.v1"]
    experiment_name: Identifier
    description: str
    research_family_id: Identifier
    parent_run_id: Identifier | None = None
    basket: tuple[str, ...]
    starting_quantities: dict[str, ExactDecimal]
    universe_mode: UniverseMode
    analysis_anchor: str | None = None
    instruments: tuple[InstrumentSpec, ...]
    evidence_instrument_ids: tuple[Identifier, ...] = ()
    relationship_instrument_ids: tuple[Identifier, ...] = ()
    interval: Identifier
    data_window: DataWindowSpec
    evaluation_window: DataWindowSpec | None = None
    data_sources: tuple[DataSourceSpec, ...]
    relationship: ComponentSpec
    policy: ComponentSpec
    execution: ExecutionSpec
    external_flows: tuple[ExternalFlowSpec, ...] = ()
    benchmarks: BenchmarkSpec
    data_role: DataRole
    primary_metric: PrimaryMetric
    success_threshold: ExactDecimal
    random_seed: int | None = None

    @field_validator("basket", mode="before")
    @classmethod
    def normalize_basket(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
            raise TypeError("basket must be a list of asset keys")
        items = cast(list[object] | tuple[object, ...], value)
        normalized = tuple(
            _asset_key(item, field=f"basket[{position}]")
            for position, item in enumerate(items)
        )
        if not normalized:
            raise ValueError("basket must contain at least one asset")
        if len(set(normalized)) != len(normalized):
            raise ValueError("basket assets must be unique")
        return normalized

    @field_validator("starting_quantities", mode="before")
    @classmethod
    def normalize_starting_quantity_keys(
        cls,
        value: object,
    ) -> dict[str, object]:
        if not isinstance(value, Mapping):
            raise TypeError("starting_quantities must be a mapping")
        normalized: dict[str, object] = {}
        for raw_asset, quantity in cast(Mapping[object, object], value).items():
            asset = _asset_key(raw_asset, field="starting_quantities key")
            if asset in normalized:
                raise ValueError(
                    "starting_quantities contains duplicate normalized asset keys"
                )
            normalized[asset] = quantity
        return normalized

    @field_validator("analysis_anchor", mode="before")
    @classmethod
    def normalize_optional_anchor(cls, value: object) -> str | None:
        if value is None:
            return None
        return _asset_key(value, field="analysis_anchor")

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, value: str) -> str:
        return BarInterval(value).label

    @field_validator("random_seed")
    @classmethod
    def validate_seed(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("random_seed must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_cross_fields(self) -> Self:
        if self.universe_mode is UniverseMode.POINT_IN_TIME_INVESTABLE:
            raise ValueError(
                "point_in_time_investable requires eligibility-aware replay; "
                "current experiment execution only supports declared_fixed_basket"
            )
        basket = set(self.basket)
        start_keys = set(self.starting_quantities)
        if start_keys != basket:
            missing = sorted(basket - start_keys)
            extra = sorted(start_keys - basket)
            raise ValueError(
                "starting_quantities keys must exactly match basket; "
                f"missing={missing}, extra={extra}"
            )
        if any(quantity < _ZERO for quantity in self.starting_quantities.values()):
            raise ValueError("starting_quantities must be non-negative")
        if not any(quantity > _ZERO for quantity in self.starting_quantities.values()):
            raise ValueError("starting_quantities must contain owned inventory")
        execution_bridge = (
            None if self.execution.mode == "direct" else self.execution.bridge_asset
        )
        admitted_run_assets = set(basket)
        if execution_bridge is not None:
            admitted_run_assets.add(execution_bridge)
        if (
            self.analysis_anchor is not None
            and self.analysis_anchor not in admitted_run_assets
        ):
            raise ValueError("analysis_anchor must belong to the admitted run assets")

        instrument_ids = tuple(item.instrument_id for item in self.instruments)
        if not instrument_ids:
            raise ValueError("at least one instrument is required")
        if len(set(instrument_ids)) != len(instrument_ids):
            raise ValueError("instrument_id values must be unique")
        evidence_ids = tuple(self.evidence_instrument_ids)
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidence_instrument_ids must be unique")
        unknown_evidence = set(evidence_ids) - set(instrument_ids)
        if unknown_evidence:
            raise ValueError(
                "evidence_instrument_ids must reference declared instruments; "
                f"missing={sorted(unknown_evidence)}"
            )
        relationship_ids = tuple(self.relationship_instrument_ids)
        if len(set(relationship_ids)) != len(relationship_ids):
            raise ValueError("relationship_instrument_ids must be unique")
        unknown_relationship = set(relationship_ids) - set(instrument_ids)
        if unknown_relationship:
            raise ValueError(
                "relationship_instrument_ids must reference declared instruments; "
                f"missing={sorted(unknown_relationship)}"
            )
        symbols = tuple((item.venue, item.venue_symbol) for item in self.instruments)
        if len(set(symbols)) != len(symbols):
            raise ValueError("venue/instrument symbols must be unique")
        evidence_set = set(evidence_ids)
        relationship_set = set(relationship_ids)
        for instrument in self.instruments:
            if instrument.instrument_id in evidence_set:
                if (
                    instrument.base_asset not in basket
                    and instrument.quote_asset not in basket
                ):
                    raise ValueError(
                        "evidence-only instrument must reference at least one "
                        "basket asset"
                    )
                continue
            if instrument.instrument_id in relationship_set and (
                instrument.base_asset not in basket
                and instrument.quote_asset not in basket
            ):
                raise ValueError(
                    "relationship instrument must reference at least one basket asset"
                )
            if (
                instrument.base_asset not in admitted_run_assets
                or instrument.quote_asset not in admitted_run_assets
            ):
                raise ValueError(
                    "instrument assets must belong to the admitted run assets"
                )

        source_ids = tuple(source.dataset_id for source in self.data_sources)
        if not source_ids:
            raise ValueError("at least one data source is required")
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("dataset_id values must be unique")
        source_instruments = tuple(source.instrument_id for source in self.data_sources)
        if len(set(source_instruments)) != len(source_instruments):
            raise ValueError("each instrument must have exactly one data source")
        if set(source_instruments) != set(instrument_ids):
            raise ValueError(
                "data_sources must map exactly one dataset to every instrument"
            )

        if self.execution.mode == "direct":
            execution_id = self.execution.execution_instrument_id
            assert execution_id is not None
            if execution_id not in set(instrument_ids):
                raise ValueError(
                    "execution_instrument_id must reference a declared instrument"
                )
            if execution_id in evidence_set:
                raise ValueError(
                    "execution instrument cannot be an evidence-only instrument"
                )
        else:
            execution_ids = set(self.execution.execution_instrument_ids)
            unknown_execution = execution_ids - set(instrument_ids)
            if unknown_execution:
                raise ValueError(
                    "execution_instrument_ids must reference declared instruments; "
                    f"missing={sorted(unknown_execution)}"
                )
            if execution_ids & evidence_set:
                raise ValueError(
                    "multi-asset execution instruments cannot be evidence-only"
                )
        if self.execution.numeraire_asset not in admitted_run_assets:
            raise ValueError(
                "execution numeraire_asset must belong to admitted run assets"
            )

        evaluation = self.effective_evaluation_window()
        if (
            evaluation.start < self.data_window.start
            or evaluation.end > self.data_window.end
        ):
            raise ValueError("evaluation_window must be contained in data_window")
        if self.evaluation_window is not None and evaluation == self.data_window:
            raise ValueError("explicit evaluation_window must be a strict subwindow")

        flow_ids = tuple(flow.flow_id for flow in self.external_flows)
        if len(set(flow_ids)) != len(flow_ids):
            raise ValueError("external flow IDs must be unique")
        previous_time: datetime | None = None
        for flow in self.external_flows:
            if flow.asset not in basket:
                raise ValueError("external flow asset must belong to basket")
            if not (
                self.data_window.start <= flow.effective_time <= self.data_window.end
            ):
                raise ValueError("external flow must fall within the data window")
            if not (evaluation.start <= flow.effective_time <= evaluation.end):
                raise ValueError("external flow must fall within the evaluation_window")
            if previous_time is not None and flow.effective_time < previous_time:
                raise ValueError("external_flows must be ordered by effective_time")
            previous_time = flow.effective_time

        if (
            self.benchmarks.relationship_alpha_claim
            and self.primary_metric
            is not PrimaryMetric.PRIMARY_CONTROL_RELATIVE_TERMINAL_WEALTH
        ):
            raise ValueError(
                "relationship-alpha claim must classify success against the "
                "predeclared primary incremental control"
            )
        if (
            self.primary_metric
            is PrimaryMetric.PRIMARY_CONTROL_RELATIVE_TERMINAL_WEALTH
            and self.benchmarks.primary_incremental_benchmark is None
        ):
            raise ValueError(
                "primary-control metric requires primary_incremental_benchmark"
            )
        validate_basket_manifest_contract(
            policy_component_id=self.policy.component_id,
            policy_config=self.policy.config,
            interval=self.interval,
            relationship_component_id=self.relationship.component_id,
            relationship_config=self.relationship.config,
            execution_mode=self.execution.mode,
            data_role=self.data_role.value,
            has_adverse_cost=self.execution.adverse_cost_scenario is not None,
            relationship_alpha_claim=self.benchmarks.relationship_alpha_claim,
            primary_incremental_benchmark=(
                self.benchmarks.primary_incremental_benchmark
            ),
            controls=self.benchmarks.controls,
        )
        return self

    def asset(self, key: str) -> AssetId:
        asset = AssetId(key)
        if asset.key not in self.basket:
            raise KeyError(asset.key)
        return asset

    def starting_state(self) -> PortfolioState:
        return PortfolioState.from_holdings(
            {
                AssetId(asset): quantity
                for asset, quantity in self.starting_quantities.items()
            }
        )

    def interval_domain(self) -> BarInterval:
        return BarInterval(self.interval)

    def effective_evaluation_window(self) -> DataWindowSpec:
        return self.evaluation_window or self.data_window

    def instruments_by_id(self) -> dict[str, VenueInstrument]:
        return {
            instrument.instrument_id: instrument.to_domain()
            for instrument in self.instruments
        }

    def execution_instrument(self) -> VenueInstrument:
        if self.execution.mode != "direct":
            raise ValueError("execution_instrument is only available for direct mode")
        execution_id = self.execution.execution_instrument_id
        assert execution_id is not None
        return self.instruments_by_id()[execution_id]

    def execution_instruments(self) -> tuple[VenueInstrument, ...]:
        instruments = self.instruments_by_id()
        if self.execution.mode == "direct":
            return (self.execution_instrument(),)
        return tuple(
            instruments[instrument_id]
            for instrument_id in self.execution.execution_instrument_ids
        )

    def execution_numeraire(self) -> AssetId:
        return AssetId(self.execution.numeraire_asset)

    def external_inventory_flows(self) -> tuple[ExternalInventoryFlow, ...]:
        return tuple(flow.to_domain() for flow in self.external_flows)


def load_manifest(path: str | Path) -> ExperimentManifest:
    source = Path(path)
    return ExperimentManifest.model_validate_json(source.read_text(encoding="utf-8"))


__all__ = [
    "BandPartialControlSpec",
    "BenchmarkSpec",
    "ComponentSpec",
    "ContributionAwareBandControlSpec",
    "CostScenarioSpec",
    "DataRole",
    "DataSourceSpec",
    "DataWindowSpec",
    "ExecutionSpec",
    "ExperimentManifest",
    "ExternalFlowSpec",
    "InstrumentSpec",
    "PairBlindRelativeMomentumControlSpec",
    "PeriodicFixedWeightControlSpec",
    "PrimaryMetric",
    "UniverseMode",
    "load_manifest",
]
