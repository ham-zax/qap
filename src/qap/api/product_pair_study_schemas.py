"""HTTP DTOs for the backend-owned Product Pair Study boundary."""

from datetime import datetime
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, field_validator


class PairStudyApiDto(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PairStudyReasonDto(PairStudyApiDto):
    code: str
    message: str


class PairStudyGenerationRefDto(PairStudyApiDto):
    dataset_id: str
    relative_path: str
    provenance_relative_path: str
    semantic_fingerprint: str
    venue: Literal["binance", "gate"]
    venue_symbol: str
    base_asset: str
    quote_asset: str
    interval: str
    coverage_start: datetime
    coverage_end_exclusive: datetime
    directory_source_id: str
    directory_source_fingerprint: str


class PairStudyQuestionDto(PairStudyApiDto):
    asset_a: str
    asset_b: str
    canonical_pair: tuple[str, str]
    orientation: str
    horizon: Literal["short", "medium", "swing"]
    venue: Literal["binance", "gate"]
    available_venues: tuple[Literal["binance", "gate"], ...]
    coordinate_asset: str
    interval: str
    safe_cutoff: datetime | None


class PairStudyDirectMarketDto(PairStudyApiDto):
    status: Literal["ready", "needs_data", "unavailable"]
    venue: Literal["binance", "gate"]
    venue_symbol: str | None
    base_asset: str | None
    quote_asset: str | None
    generation: PairStudyGenerationRefDto | None


class PairStudyDataDto(PairStudyApiDto):
    status: Literal["ready", "needs_setup"]
    reasons: tuple[PairStudyReasonDto, ...]
    asset_a_path: PairStudyGenerationRefDto | None
    asset_b_path: PairStudyGenerationRefDto | None
    direct_market: PairStudyDirectMarketDto


class PairStudyObservationDto(PairStudyApiDto):
    model_id: str
    model_version: str
    orientation: str
    fit_reciprocity: str
    evidence_reciprocity: str
    status: Literal["valid", "insufficient_history", "insufficient_variance"]
    window_observations: int
    required_observations: int
    coverage_observations: int
    as_of: datetime
    base_source_fingerprint: str
    quote_source_fingerprint: str
    input_fingerprint: str
    values: dict[str, float]

    @field_validator("values", mode="before")
    @classmethod
    def values_from_pairs(cls, value: object) -> object:
        if isinstance(value, (tuple, list)):
            pairs = cast(
                tuple[tuple[str, float], ...] | list[tuple[str, float]],
                value,
            )
            return dict(pairs)
        return value


class PairStudyRelationshipDto(PairStudyApiDto):
    raw_ratio_current: float
    log_ratio_current: float
    normalized_base_current: float
    normalized_quote_current: float
    rolling_log_ratio: PairStudyObservationDto
    residual_ols: PairStudyObservationDto


class PairStudyAnalysisLensDto(PairStudyApiDto):
    asset: str
    status: Literal["ready", "needs_data", "unavailable"]
    generation: PairStudyGenerationRefDto | None
    reason: PairStudyReasonDto | None


class PairStudyEconomicExpressionDto(PairStudyApiDto):
    direct_status: Literal["ready", "needs_data", "unavailable"]
    bridge_status: Literal["not_available_in_current_recipe_contract"]
    default_recipe_declarable: bool
    reasons: tuple[PairStudyReasonDto, ...]


class ProductPairStudyContextDto(PairStudyApiDto):
    schema_version: Literal["qap.api.product_pair_study_context.v1"] = (
        "qap.api.product_pair_study_context.v1"
    )
    question: PairStudyQuestionDto
    data: PairStudyDataDto
    relationship: PairStudyRelationshipDto | None
    analysis_lens: PairStudyAnalysisLensDto | None
    economic_expression: PairStudyEconomicExpressionDto
    directory_id: str


class PairStudyPointDto(PairStudyApiDto):
    timestamp: datetime
    value: float


class PairStudyReferenceSeriesDto(PairStudyApiDto):
    asset: str
    generation: PairStudyGenerationRefDto
    base_to_reference: tuple[PairStudyPointDto, ...]
    quote_to_reference: tuple[PairStudyPointDto, ...]
    base_to_reference_log: tuple[PairStudyPointDto, ...]
    quote_to_reference_log: tuple[PairStudyPointDto, ...]


class ProductPairStudySeriesDto(PairStudyApiDto):
    schema_version: Literal["qap.api.product_pair_study_series.v1"] = (
        "qap.api.product_pair_study_series.v1"
    )
    question: PairStudyQuestionDto
    asset_a_path: PairStudyGenerationRefDto
    asset_b_path: PairStudyGenerationRefDto
    base_source_fingerprint: str
    quote_source_fingerprint: str
    ratio: tuple[PairStudyPointDto, ...]
    log_ratio: tuple[PairStudyPointDto, ...]
    normalized_base: tuple[PairStudyPointDto, ...]
    normalized_quote: tuple[PairStudyPointDto, ...]
    analysis_reference: PairStudyReferenceSeriesDto | None


__all__ = ["ProductPairStudyContextDto", "ProductPairStudySeriesDto"]
