"""Backend-composed longitudinal History read models."""

from typing import Literal

from qap.api.basket_schemas import BasketSummaryDto
from qap.api.paper_operation_schemas import PaperOperationSummaryDto
from qap.api.scanner_schemas import (
    CandidateSummaryDto,
    ForwardCohortSummaryDto,
    ResearchIdeaCurrentAssessmentDto,
    ResearchIdeaLongitudinalDto,
    ScanSummaryDto,
)
from qap.api.schemas import ApiDto, RunSummaryDto


class HistoryResearchIdeaDto(ApiDto):
    candidate: CandidateSummaryDto
    longitudinal: ResearchIdeaLongitudinalDto
    latest_current_assessment: ResearchIdeaCurrentAssessmentDto | None
    forward_cohort_ids: tuple[str, ...]
    basket_memberships: tuple[BasketSummaryDto, ...]


class HistoryResearchGenerationDto(ApiDto):
    summary: ScanSummaryDto
    research_ideas: tuple[HistoryResearchIdeaDto, ...]


class HistoryDto(ApiDto):
    schema_version: Literal["qap.api.history.v1"] = "qap.api.history.v1"
    research_generations: tuple[HistoryResearchGenerationDto, ...]
    specialist_forward_evidence: tuple[ForwardCohortSummaryDto, ...]
    portfolio_research: tuple[BasketSummaryDto, ...]
    other_research_runs: tuple[RunSummaryDto, ...]
    paper_operations: tuple[PaperOperationSummaryDto, ...]


__all__ = [
    "HistoryDto",
    "HistoryResearchGenerationDto",
    "HistoryResearchIdeaDto",
]
