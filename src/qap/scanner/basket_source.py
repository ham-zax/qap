"""Basket source-claim admission and immutable Product execution bindings."""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.portfolio import AssetId
from qap.product_current_approved_policy import (
    current_approved_claim_identity,
    current_approved_scanner_protocol,
)
from qap.product_market_data_generation import (
    ProductGenerationReadError,
    resolve_immutable_generation,
)
from qap.product_market_data_models import safe_relative_path, validated_text
from qap.scanner.basket_protocol import (
    PRODUCT_CURRENT_APPROVED_BASKET,
    SCANNER_V1_BASKET,
    BasketProtocol,
)
from qap.scanner.current_scope import CURRENT_APPROVED_UNIVERSE_POLICY_VERSION
from qap.scanner.models import ScanDefinition
from qap.scanner.protocol import SCANNER_V1_SLICE1, protocol_identity


class BasketSourceError(ValueError):
    """Raised when a source scan cannot truthfully support basket research."""


class ProductBasketExecutionGeneration(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    asset_id: str
    dataset_id: str
    relative_path: str
    source_artifact_fingerprint: str

    @field_validator("asset_id", mode="before")
    @classmethod
    def validate_asset_id(cls, value: object) -> str:
        return AssetId(validated_text(value, field="asset_id")).key

    @field_validator("dataset_id", mode="before")
    @classmethod
    def validate_dataset_id(cls, value: object) -> str:
        return validated_text(value, field="dataset_id")

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return safe_relative_path(value)

    @field_validator("source_artifact_fingerprint", mode="before")
    @classmethod
    def validate_fingerprint(cls, value: object) -> str:
        normalized = validated_text(value, field="source_artifact_fingerprint").lower()
        if len(normalized) != 64 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            raise ValueError("source_artifact_fingerprint must be a SHA-256 hex string")
        return normalized

    @model_validator(mode="after")
    def validate_generation(self) -> Self:
        if not self.relative_path.endswith(
            f"/{self.source_artifact_fingerprint}.parquet"
        ):
            raise ValueError("Product execution path does not match its fingerprint")
        return self


@dataclass(frozen=True, slots=True)
class BasketSourceContract:
    basket_protocol: BasketProtocol
    product_current_approved: bool


def basket_source_contract(definition: ScanDefinition) -> BasketSourceContract:
    """Admit only strict Scanner-V1 or the exact current-approved Product-v1."""

    if (
        definition.scanner_protocol_version == SCANNER_V1_SLICE1.protocol_id
        and definition.protocol_identity == protocol_identity(SCANNER_V1_SLICE1)
    ):
        return BasketSourceContract(SCANNER_V1_BASKET, False)

    product = current_approved_scanner_protocol(definition.venues)
    if (
        definition.venues != product.venues
        or definition.scanner_protocol_version != product.protocol_id
        or definition.protocol_identity != protocol_identity(product)
        or definition.universe_policy_version
        != CURRENT_APPROVED_UNIVERSE_POLICY_VERSION
        or definition.research_claim_identity != current_approved_claim_identity()
        or definition.research_scope_identity is None
        or definition.candidate_generator_version != product.candidate_generator_version
        or definition.template_set_version != product.template_set_version
        or definition.promotion_policy_version != product.promotion_policy_version
        or definition.cost_policy_reference != product.cost_policy.policy_id
    ):
        raise BasketSourceError(
            "source scan is neither strict Scanner-V1 nor exact current-approved "
            "Product-v1"
        )
    return BasketSourceContract(PRODUCT_CURRENT_APPROVED_BASKET, True)


def resolve_product_execution_generations(
    definition: ScanDefinition,
    *,
    data_root: str | Path,
    venue: str,
    resolution: str,
    economic_assets: tuple[str, ...],
    execution_bridge: str,
) -> tuple[ProductBasketExecutionGeneration, ...]:
    """Resolve selected execution assets only from source-scan M3 input commitments."""

    source_fingerprints: dict[str, str] = {}
    for input_slice in definition.input_slices:
        existing = source_fingerprints.get(input_slice.dataset_id)
        if existing is not None and existing != input_slice.source_artifact_fingerprint:
            raise BasketSourceError(
                "source scan contains ambiguous fingerprints for one logical dataset"
            )
        source_fingerprints[input_slice.dataset_id] = (
            input_slice.source_artifact_fingerprint
        )

    matches: dict[str, list[ProductBasketExecutionGeneration]] = {
        asset: [] for asset in economic_assets
    }
    for dataset_id, fingerprint in source_fingerprints.items():
        try:
            provenance, _series = resolve_immutable_generation(
                data_root,
                dataset_id=dataset_id,
                semantic_fingerprint=fingerprint,
            )
        except ProductGenerationReadError as exc:
            raise BasketSourceError(
                "source scan input is not backed by an exact immutable M3 generation"
            ) from exc
        if (
            provenance.venue == venue
            and provenance.quote_asset == execution_bridge
            and provenance.interval == resolution
            and provenance.base_asset in matches
        ):
            matches[provenance.base_asset].append(
                ProductBasketExecutionGeneration(
                    asset_id=provenance.base_asset,
                    dataset_id=provenance.dataset_id,
                    relative_path=provenance.relative_path,
                    source_artifact_fingerprint=provenance.semantic_fingerprint,
                )
            )

    result: list[ProductBasketExecutionGeneration] = []
    for asset in economic_assets:
        candidates = matches[asset]
        if len(candidates) != 1:
            raise BasketSourceError(
                "economic asset requires exactly one frozen "
                f"{asset}/{execution_bridge} Product execution generation"
            )
        result.append(candidates[0])
    return tuple(sorted(result, key=lambda item: item.asset_id))


__all__ = [
    "BasketSourceContract",
    "BasketSourceError",
    "ProductBasketExecutionGeneration",
    "basket_source_contract",
    "resolve_product_execution_generations",
]
